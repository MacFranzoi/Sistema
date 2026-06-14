import requests
import json
import os
import time
import urllib.parse
from datetime import datetime

ACCESS_TOKEN = "998d6e5bed008c2023d5c5bc062ac9311e05c045"
SECRET_TOKEN = "884b009905a80a147cea7172f25c83700c097166"
BASE_URL = "https://api.gestaoclick.com/api"

HEADERS = {
    "access-token": ACCESS_TOKEN,
    "secret-access-token": SECRET_TOKEN,
    "Content-Type": "application/json"
}

LOJAS = {
    "277761": "Plaza",
    "282073": "Centro",
    "282941": "Miller",
    "472451": "Estoque",
}

DIR = os.path.dirname(__file__)
DIR_LISTAS = os.path.join(DIR, "listas")
os.makedirs(DIR_LISTAS, exist_ok=True)
DISPONIBILIDADE_FILE = os.path.join(DIR, "disponibilidade_lojas.json")
CUSTOS_TIPO_FILE     = os.path.join(DIR, "custos_tipo.json")

CUSTOS_TIPO_PADRAO = {
    "Aveludada":        "25.00",
    "Silicone Líquido": "35.00",
    "Brilho":           "20.00",
    "Very Rio":         "35.00",
    "MagSafe":          "55.00",
    "Carteira":         "30.00",
    "Transparente":     "18.00",
    "Anti-Impacto":     "28.00",
    "Clear Case":       "22.00",
}


def carregar_custos_tipo():
    if not os.path.exists(CUSTOS_TIPO_FILE):
        return dict(CUSTOS_TIPO_PADRAO)
    with open(CUSTOS_TIPO_FILE, encoding="utf-8") as f:
        return json.load(f)


def salvar_custos_tipo(dados):
    with open(CUSTOS_TIPO_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def detectar_custo_tipo(produto_nome, grupo_nome="", custos=None):
    """Retorna o custo string do primeiro tipo que bater no nome do produto/grupo."""
    if custos is None:
        custos = carregar_custos_tipo()
    texto = (produto_nome + " " + grupo_nome).lower()
    for tipo, custo in custos.items():
        if tipo.lower() in texto:
            return custo
    return None


def cache_path(loja_id=None):
    sufixo = f"_{loja_id}" if loja_id else "_todas"
    return os.path.join(DIR, f"cache_produtos{sufixo}.json")


# ──────────────────────────────────────────────
# HTTP
# ──────────────────────────────────────────────

def _request(method, endpoint, params=None, body=None, loja_id=None, tentativas=3):
    url = f"{BASE_URL}/{endpoint}"
    p = dict(params or {})
    if loja_id:
        p["loja_id"] = loja_id
    for i in range(tentativas):
        try:
            time.sleep(0.4)
            r = requests.request(method, url, headers=HEADERS, params=p or None, json=body, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            if i == tentativas - 1:
                raise Exception(f"API não respondeu após {tentativas} tentativas. Tente novamente.")
            time.sleep(2 ** i)
        except requests.exceptions.HTTPError:
            raise Exception(f"Erro HTTP {r.status_code}: {r.text[:300]}")


def _get(endpoint, params=None, loja_id=None):
    return _request("GET", endpoint, params=params, loja_id=loja_id)


def _put(endpoint, body, loja_id=None):
    return _request("PUT", endpoint, body=body, loja_id=loja_id)


def _post(endpoint, body, loja_id=None):
    return _request("POST", endpoint, body=body, loja_id=loja_id)


# ──────────────────────────────────────────────
# Cache de produtos
# ──────────────────────────────────────────────

def sincronizar_produtos(loja_id=None, progress_callback=None):
    todos = []
    pagina = 1
    total_paginas = None
    while True:
        data = _get("produtos", {"pagina": pagina, "limite": 100}, loja_id=loja_id)
        meta = data.get("meta", {})
        if total_paginas is None:
            total_paginas = meta.get("total_paginas", 1)
        produtos = data.get("data", [])
        if not produtos:
            break
        todos.extend(produtos)
        if progress_callback:
            progress_callback(pagina, total_paginas)
        if pagina >= total_paginas:
            break
        pagina += 1

    cache = {
        "sincronizado_em": datetime.now().isoformat(),
        "loja_id": loja_id,
        "loja_nome": LOJAS.get(str(loja_id), "Todas") if loja_id else "Todas",
        "total": len(todos),
        "produtos": todos
    }
    with open(cache_path(loja_id), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return cache


def carregar_cache(loja_id=None):
    p = cache_path(loja_id)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def buscar_produtos(termo, cache):
    termo = termo.lower().strip()
    if not termo or not cache:
        return []
    return [
        p for p in cache.get("produtos", [])
        if termo in (p.get("nome") or "").lower()
        or termo in (p.get("codigo_interno") or "").lower()
    ][:30]


# ──────────────────────────────────────────────
# Estoque
# ──────────────────────────────────────────────

def atualizar_estoque_variacao(produto_id, variacao_id, quantidade, loja_id=None, modo="set"):
    """
    modo='set'  → define o estoque absoluto
    modo='soma' → soma ao estoque atual
    """
    produto = _get(f"produtos/{produto_id}", loja_id=loja_id)
    dados = produto.get("data", produto)

    novas_variacoes = []
    for v in dados.get("variacoes", []):
        vd = v["variacao"]
        if vd["id"] == variacao_id:
            if modo == "soma":
                novo_estoque = float(vd["estoque"]) + quantidade
            else:
                novo_estoque = quantidade
        else:
            novo_estoque = vd["estoque"]
        novas_variacoes.append({
            "variacao": {
                "id": vd["id"],
                "nome": vd["nome"],
                "codigo": vd["codigo"],
                "estoque": str(novo_estoque)
            }
        })

    body = {
        "nome": dados["nome"],
        "codigo_interno": dados["codigo_interno"],
        "valor_custo": dados.get("valor_custo", "0.00"),
        "variacoes": novas_variacoes
    }
    return _put(f"produtos/{produto_id}", body, loja_id=loja_id)


def atualizar_estoque_lote(entradas, loja_id=None, modo="set", progress_callback=None):
    resultados = []
    for i, e in enumerate(entradas):
        try:
            atualizar_estoque_variacao(
                e["produto_id"], e["variacao_id"], e["quantidade"],
                loja_id=loja_id, modo=modo
            )
            resultados.append({"ok": True, **e})
        except Exception as ex:
            resultados.append({"ok": False, "erro": str(ex), **e})
        if progress_callback:
            progress_callback(i + 1, len(entradas))
    return resultados


def estoque_produto_por_loja(produto_id):
    resultado = {}
    for loja_id, loja_nome in LOJAS.items():
        try:
            dados = _get(f"produtos/{produto_id}", loja_id=loja_id)
            p = dados.get("data", dados)
            resultado[loja_nome] = {
                (v["variacao"]["nome"] or "(sem nome)"): {
                    "estoque": float(v["variacao"]["estoque"]),
                    "variacao_id": v["variacao"]["id"],
                    "codigo": v["variacao"]["codigo"],
                }
                for v in p.get("variacoes", [])
            }
        except Exception:
            resultado[loja_nome] = {}
    return resultado


# ──────────────────────────────────────────────
# Etiquetas
# ──────────────────────────────────────────────

def gerar_url_etiquetas(entradas):
    obj = {str(e["variacao_id"]): int(e["quantidade"]) for e in entradas if e.get("quantidade", 0) > 0}
    encoded = urllib.parse.quote(json.dumps(obj))
    return f"https://plug.gestaoclick.com/etiquetas/gerar_etiquetas?busca=a150&selecionados={encoded}"


# ──────────────────────────────────────────────
# Listas salvas
# ──────────────────────────────────────────────

def salvar_lista(nome, tipo, itens, loja_id=None, loja_nome=None):
    dados = {
        "nome": nome,
        "tipo": tipo,
        "loja_id": loja_id,
        "loja_nome": loja_nome,
        "criado_em": datetime.now().isoformat(),
        "itens": itens
    }
    slug = nome.replace(" ", "_").replace("/", "-")[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = os.path.join(DIR_LISTAS, f"{tipo}_{slug}_{ts}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return caminho


def listar_listas_salvas(tipo=None):
    arquivos = sorted(
        [f for f in os.listdir(DIR_LISTAS) if f.endswith(".json")],
        reverse=True
    )
    listas = []
    for arq in arquivos:
        if tipo and not arq.startswith(tipo):
            continue
        try:
            with open(os.path.join(DIR_LISTAS, arq), encoding="utf-8") as f:
                dados = json.load(f)
            dados["_arquivo"] = arq
            listas.append(dados)
        except Exception:
            pass
    return listas


def carregar_lista(arquivo):
    with open(os.path.join(DIR_LISTAS, arquivo), encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# Produtos
# ──────────────────────────────────────────────

def criar_produto(nome, codigo_interno, grupo_id, valor_custo, valor_venda, ativo, variacoes, loja_id=None):
    body = {
        "nome": nome,
        "codigo_interno": codigo_interno,
        "grupo_id": grupo_id,
        "valor_custo": valor_custo,
        "valor_venda": valor_venda,
        "ativo": ativo,
        "variacoes": [
            {"variacao": {"nome": v["nome"], "codigo": v["codigo"], "estoque": "0"}}
            for v in variacoes
        ]
    }
    return _post("produtos", body, loja_id=loja_id)


# ──────────────────────────────────────────────
# Disponibilidade por loja (ativo/inativo por store)
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# Hierarquia de grupos
# ──────────────────────────────────────────────

_grupos_cache = None

def carregar_grupos():
    global _grupos_cache
    if _grupos_cache:
        return _grupos_cache
    try:
        data = _get("grupos_produtos", {"limite": 200})
        _grupos_cache = data.get("data", [])
    except Exception:
        _grupos_cache = []
    return _grupos_cache


def grupos_filhos_ids(grupo_id):
    """Retorna set com o próprio ID e todos os IDs descendentes recursivamente."""
    grupos = carregar_grupos()
    filhos = {str(grupo_id)}
    fila = [str(grupo_id)]
    while fila:
        pai = fila.pop()
        for g in grupos:
            if str(g.get("grupo_pai_id", "")) == pai:
                gid = str(g["id"])
                if gid not in filhos:
                    filhos.add(gid)
                    fila.append(gid)
    return filhos


def grupos_arvore():
    """Retorna lista ordenada para exibição com indentação:
    [{"id": ..., "nome": ..., "nivel": 0|1|2, "label": "  ↳ Nome"}]
    """
    grupos = carregar_grupos()
    por_id = {str(g["id"]): g for g in grupos}
    raizes = [g for g in grupos if not g.get("grupo_pai_id")]
    resultado = []

    def visitar(g, nivel):
        label = ("  " * nivel + ("↳ " if nivel else "")) + g["nome"]
        resultado.append({"id": str(g["id"]), "nome": g["nome"], "nivel": nivel, "label": label})
        filhos = sorted(
            [f for f in grupos if str(f.get("grupo_pai_id", "")) == str(g["id"])],
            key=lambda x: x["nome"]
        )
        for filho in filhos:
            visitar(filho, nivel + 1)

    for r in sorted(raizes, key=lambda x: x["nome"]):
        visitar(r, 0)

    return resultado


def carregar_disponibilidade():
    """Retorna {loja_id: {produto_id: bool}}"""
    if not os.path.exists(DISPONIBILIDADE_FILE):
        return {}
    with open(DISPONIBILIDADE_FILE, encoding="utf-8") as f:
        return json.load(f)


def salvar_disponibilidade(dados):
    with open(DISPONIBILIDADE_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def toggle_produto_loja(produto_id, loja_id, ativo: bool):
    """
    Tenta ativar/desativar produto via API com loja_id.
    Salva resultado local como fallback de visibilidade.
    """
    try:
        produto = _get(f"produtos/{produto_id}", loja_id=loja_id)
        dados = produto.get("data", produto)
        body = {
            "nome": dados["nome"],
            "codigo_interno": dados["codigo_interno"],
            "valor_custo": dados.get("valor_custo", "0.00"),
            "ativo": "1" if ativo else "0",
        }
        _put(f"produtos/{produto_id}", body, loja_id=loja_id)
    except Exception:
        pass  # Salva local mesmo se API falhar

    disp = carregar_disponibilidade()
    lid = str(loja_id)
    pid = str(produto_id)
    if lid not in disp:
        disp[lid] = {}
    disp[lid][pid] = ativo
    salvar_disponibilidade(disp)


def produto_ativo_na_loja(produto_id, loja_id):
    disp = carregar_disponibilidade()
    return disp.get(str(loja_id), {}).get(str(produto_id), True)  # default: ativo


# ──────────────────────────────────────────────
# Atualização de preços
# ──────────────────────────────────────────────

def atualizar_precos_produto(produto_id, valor_custo=None, valor_venda=None,
                              precos_por_tipo=None, loja_id=None):
    """
    precos_por_tipo = [{"tipo_id": "452073", "valor_venda": 49.99}, ...]
    """
    produto = _get(f"produtos/{produto_id}", loja_id=loja_id)
    dados = produto.get("data", produto)

    body = {
        "nome": dados["nome"],
        "codigo_interno": dados["codigo_interno"],
        "valor_custo": str(valor_custo) if valor_custo is not None else dados.get("valor_custo", "0.00"),
        "valor_venda": str(valor_venda) if valor_venda is not None else dados.get("valor_venda", "0.00"),
    }

    if precos_por_tipo:
        body["valores"] = precos_por_tipo

    return _put(f"produtos/{produto_id}", body, loja_id=loja_id)


def atualizar_precos_lote(entradas, loja_id=None, progress_callback=None):
    """
    entradas = [{"produto_id": ..., "valor_custo": ..., "valor_venda": ...,
                 "produto_nome": ..., "precos_por_tipo": [...]}, ...]
    """
    resultados = []
    for i, e in enumerate(entradas):
        try:
            atualizar_precos_produto(
                e["produto_id"],
                valor_custo=e.get("valor_custo"),
                valor_venda=e.get("valor_venda"),
                precos_por_tipo=e.get("precos_por_tipo"),
                loja_id=loja_id,
            )
            resultados.append({"ok": True, **e})
        except Exception as ex:
            resultados.append({"ok": False, "erro": str(ex), **e})
        if progress_callback:
            progress_callback(i + 1, len(entradas))
    return resultados


def clonar_produto(produto_id, novo_nome, novo_codigo, loja_id=None):
    produto = _get(f"produtos/{produto_id}", loja_id=loja_id)
    origem = produto.get("data", produto)
    cod_origem = origem.get("codigo_interno", "")
    novas_variacoes = []
    for v in sorted(origem.get("variacoes", []), key=lambda v: v["variacao"].get("codigo", "") or ""):
        vd = v["variacao"]
        sufixo = vd["codigo"].replace(cod_origem, "") if cod_origem and vd["codigo"] else ""
        novas_variacoes.append({
            "variacao": {"nome": vd["nome"], "codigo": novo_codigo + sufixo, "estoque": "0"}
        })
    body = {
        "nome": novo_nome,
        "codigo_interno": novo_codigo,
        "grupo_id": origem.get("grupo_id", ""),
        "valor_custo": origem.get("valor_custo", "0.00"),
        "valor_venda": origem.get("valor_venda", "0.00"),
        "ativo": "1",
        "variacoes": novas_variacoes
    }
    return _post("produtos", body, loja_id=loja_id)
