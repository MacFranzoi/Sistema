import requests
import json
import os
import time
import secrets
import urllib.parse
from datetime import datetime, timedelta

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
USUARIOS_FILE        = os.path.join(DIR, "usuarios.json")
SETORES_FILE         = os.path.join(DIR, "setores.json")

_SETORES_PADRAO = {
    "admin": {
        "label": "Administrador",
        "paginas": [
            "dashboard","clientes","fornecedores",
            "novo_modelo","clonar_modelo","precos",
            "vendas","orcamentos",
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas",
            "pedido","compras_hist",
            "financeiro","relatorios",
            "sincronizacao","usuarios",
        ],
    },
    "gerencia": {
        "label": "Gerência",
        "paginas": [
            "dashboard","clientes","fornecedores",
            "novo_modelo","clonar_modelo","precos",
            "vendas","orcamentos",
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas",
            "pedido","compras_hist",
            "financeiro","relatorios",
        ],
    },
    "estoque": {
        "label": "Estoque",
        "paginas": [
            "dashboard",
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas",
            "pedido","compras_hist",
        ],
    },
    "compras": {
        "label": "Compras",
        "paginas": [
            "dashboard",
            "pedido","compras_hist",
            "estoque_loja","disponibilidade",
        ],
    },
    "vendas": {
        "label": "Vendas",
        "paginas": [
            "dashboard",
            "vendas","orcamentos",
            "estoque_loja","disponibilidade","etiquetas",
        ],
    },
}

def carregar_setores():
    if not os.path.exists(SETORES_FILE):
        _gh_baixar_arquivo("setores.json", SETORES_FILE)
    if os.path.exists(SETORES_FILE):
        try:
            with open(SETORES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(_SETORES_PADRAO))

def salvar_setores(setores):
    conteudo = json.dumps(setores, ensure_ascii=False, indent=2)
    with open(SETORES_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("setores.json", conteudo, "Atualiza setores")

SETORES = carregar_setores()

USUARIOS_PADRAO = {
    "gustavo": {"nome": "Gustavo", "senha": "admin", "setor": "admin"},
}

SESSOES_FILE = os.path.join(DIR, "sessoes.json")
SESSAO_DIAS  = 30  # dias até expirar o token

def _carregar_sessoes():
    if os.path.exists(SESSOES_FILE):
        with open(SESSOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _salvar_sessoes(s):
    with open(SESSOES_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def criar_sessao(usuario):
    token = secrets.token_urlsafe(32)
    sessoes = _carregar_sessoes()
    sessoes[token] = {
        "usuario": usuario,
        "expira":  (datetime.now() + timedelta(days=SESSAO_DIAS)).isoformat()
    }
    # limpa tokens expirados
    agora = datetime.now().isoformat()
    sessoes = {t: v for t, v in sessoes.items() if v["expira"] > agora}
    sessoes[token] = {"usuario": usuario, "expira": (datetime.now() + timedelta(days=SESSAO_DIAS)).isoformat()}
    _salvar_sessoes(sessoes)
    return token

def validar_sessao(token):
    if not token:
        return None
    sessoes = _carregar_sessoes()
    s = sessoes.get(token)
    if not s:
        return None
    if s["expira"] < datetime.now().isoformat():
        sessoes.pop(token, None)
        _salvar_sessoes(sessoes)
        return None
    return s["usuario"]

def revogar_sessao(token):
    sessoes = _carregar_sessoes()
    sessoes.pop(token, None)
    _salvar_sessoes(sessoes)

def carregar_usuarios():
    # Tenta puxar do GitHub se o arquivo local não existe
    if not os.path.exists(USUARIOS_FILE):
        _gh_baixar_arquivo("usuarios.json", USUARIOS_FILE)
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    salvar_usuarios(USUARIOS_PADRAO)
    return dict(USUARIOS_PADRAO)

def salvar_usuarios(usuarios):
    conteudo = json.dumps(usuarios, ensure_ascii=False, indent=2)
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("usuarios.json", conteudo, "Atualiza usuarios")

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
        _gh_baixar_arquivo("custos_tipo.json", CUSTOS_TIPO_FILE)
    if not os.path.exists(CUSTOS_TIPO_FILE):
        return dict(CUSTOS_TIPO_PADRAO)
    with open(CUSTOS_TIPO_FILE, encoding="utf-8") as f:
        return json.load(f)


def salvar_custos_tipo(dados):
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(CUSTOS_TIPO_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("custos_tipo.json", conteudo, "Atualiza custos por tipo")


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
# GitHub sync para listas
# ──────────────────────────────────────────────

import base64

_GH_REPO   = "MacFranzoi/Sistema"
_GH_BRANCH = "main"
_GH_API    = "https://api.github.com"

def _gh_headers():
    try:
        import streamlit as _st
        token = _st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token = os.environ.get("GITHUB_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

_GH_HEADERS = None  # legacy alias — use _gh_headers() instead

def _gh_get_sha(path):
    """Retorna SHA do arquivo no GitHub (necessário para atualizar)."""
    try:
        r = requests.get(f"{_GH_API}/repos/{_GH_REPO}/contents/{path}",
                         headers=_gh_headers(), params={"ref": _GH_BRANCH}, timeout=10)
        if r.status_code == 200:
            return r.json().get("sha")
    except Exception:
        pass
    return None

def _gh_push_arquivo(path, conteudo_str, mensagem):
    """Cria ou atualiza um arquivo no GitHub."""
    try:
        sha = _gh_get_sha(path)
        payload = {
            "message": mensagem,
            "content": base64.b64encode(conteudo_str.encode()).decode(),
            "branch":  _GH_BRANCH,
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(f"{_GH_API}/repos/{_GH_REPO}/contents/{path}",
                         headers=_gh_headers(), json=payload, timeout=15)
        return r.status_code in (200, 201)
    except Exception:
        return False

def _gh_delete_arquivo(path):
    """Remove um arquivo do GitHub."""
    try:
        sha = _gh_get_sha(path)
        if not sha:
            return False
        r = requests.delete(f"{_GH_API}/repos/{_GH_REPO}/contents/{path}",
                            headers=_gh_headers(),
                            json={"message": f"Remove lista {path}", "sha": sha, "branch": _GH_BRANCH},
                            timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def _gh_listar_listas():
    """Lista arquivos em listas/ no GitHub."""
    try:
        r = requests.get(f"{_GH_API}/repos/{_GH_REPO}/contents/listas",
                         headers=_gh_headers(), params={"ref": _GH_BRANCH}, timeout=10)
        if r.status_code == 200:
            return [item["name"] for item in r.json() if item["name"].endswith(".json")]
    except Exception:
        pass
    return []

def _gh_baixar_arquivo(gh_path, destino_local):
    """Baixa qualquer arquivo do GitHub e salva localmente."""
    try:
        r = requests.get(f"{_GH_API}/repos/{_GH_REPO}/contents/{gh_path}",
                         headers=_gh_headers(), params={"ref": _GH_BRANCH}, timeout=10)
        if r.status_code == 200:
            conteudo = base64.b64decode(r.json()["content"]).decode()
            with open(destino_local, "w", encoding="utf-8") as f:
                f.write(conteudo)
            return True
    except Exception:
        pass
    return False

def _gh_baixar_lista(nome_arquivo):
    """Baixa conteúdo de uma lista do GitHub e salva localmente."""
    return _gh_baixar_arquivo(f"listas/{nome_arquivo}", os.path.join(DIR_LISTAS, nome_arquivo))

def sincronizar_listas_do_github():
    """Puxa do GitHub todos os arquivos de lista que não existem localmente (ou são mais antigos)."""
    remotos = _gh_listar_listas()
    baixados = 0
    for nome in remotos:
        local = os.path.join(DIR_LISTAS, nome)
        if not os.path.exists(local):
            if _gh_baixar_lista(nome):
                baixados += 1
    return baixados


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
    nome_arq = f"{tipo}_{slug}_{ts}.json"
    caminho = os.path.join(DIR_LISTAS, nome_arq)
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    # Sobe pro GitHub em background (falha silenciosamente)
    _gh_push_arquivo(f"listas/{nome_arq}", conteudo, f"Lista: {nome}")
    return caminho


def listar_listas_salvas(tipo=None):
    # Puxa do GitHub arquivos que ainda não existem localmente
    sincronizar_listas_do_github()
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


def excluir_lista(arquivo):
    """Remove lista local e do GitHub."""
    caminho = os.path.join(DIR_LISTAS, arquivo)
    if os.path.exists(caminho):
        os.remove(caminho)
    _gh_delete_arquivo(f"listas/{arquivo}")


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
        _gh_baixar_arquivo("disponibilidade_lojas.json", DISPONIBILIDADE_FILE)
    if not os.path.exists(DISPONIBILIDADE_FILE):
        return {}
    with open(DISPONIBILIDADE_FILE, encoding="utf-8") as f:
        return json.load(f)


def salvar_disponibilidade(dados):
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(DISPONIBILIDADE_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("disponibilidade_lojas.json", conteudo, "Atualiza disponibilidade por loja")


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


# ──────────────────────────────────────────────
# Clientes
# ──────────────────────────────────────────────
def buscar_clientes(termo="", pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if termo:
        params["pesquisa"] = termo
    r = _get("clientes", params=params)
    return r.get("data", r) if isinstance(r, dict) else []

def buscar_cliente(cliente_id):
    r = _get(f"clientes/{cliente_id}")
    return r.get("data", r) if isinstance(r, dict) else {}

# ──────────────────────────────────────────────
# Fornecedores
# ──────────────────────────────────────────────
def buscar_fornecedores(termo="", pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if termo:
        params["pesquisa"] = termo
    r = _get("fornecedores", params=params)
    return r.get("data", r) if isinstance(r, dict) else []

# ──────────────────────────────────────────────
# Vendas (pedidos de venda)
# ──────────────────────────────────────────────
def buscar_vendas(data_ini=None, data_fim=None, loja_id=None, pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    r = _get("pedidosvendas", params=params, loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else []

def buscar_venda(pedido_id, loja_id=None):
    r = _get(f"pedidosvendas/{pedido_id}", loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else {}

# ──────────────────────────────────────────────
# Orçamentos
# ──────────────────────────────────────────────
def buscar_orcamentos(data_ini=None, data_fim=None, loja_id=None, pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    r = _get("orcamentos", params=params, loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else []

# ──────────────────────────────────────────────
# Compras (pedidos de compra histórico)
# ──────────────────────────────────────────────
def buscar_compras(data_ini=None, data_fim=None, loja_id=None, pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    r = _get("pedidoscompras", params=params, loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else []

# ──────────────────────────────────────────────
# Financeiro
# ──────────────────────────────────────────────
def buscar_contas_receber(data_ini=None, data_fim=None, pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    r = _get("contasreceber", params=params)
    return r.get("data", r) if isinstance(r, dict) else []

def buscar_contas_pagar(data_ini=None, data_fim=None, pagina=1, limite=50):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    r = _get("contaspagar", params=params)
    return r.get("data", r) if isinstance(r, dict) else []


# ──────────────────────────────────────────────
# Parse de pedido via IA (Claude)
# ──────────────────────────────────────────────
def parse_pedido_whatsapp(texto: str, catalogo_resumo: str) -> list[dict]:
    """
    Envia o texto colado do WhatsApp para o Claude e retorna
    lista de dicts: [{modelo, variacao, quantidade, observacao}]
    """
    import anthropic as _ant
    client = _ant.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    prompt = f"""Você é um assistente de compras de uma loja de capinhas e acessórios para celular.

O usuário colou um texto do WhatsApp com pedidos de reposição. Cada linha tem:
  [modelo do aparelho] - [tipo(s) de capa]

Tipos comuns: masculino, feminino, brilho, silicone, anti-impacto, carteira, transparente, magsafe

Catálogo disponível (cod_interno | nome do produto):
{catalogo_resumo}

Texto colado:
{texto}

Retorne SOMENTE um JSON válido, array de objetos com esta estrutura:
[
  {{
    "modelo_digitado": "texto original do modelo",
    "cod_interno": "código do produto mais próximo no catálogo ou null",
    "nome_produto": "nome do produto mais próximo ou null",
    "variacoes": ["masculino", "brilho"],
    "quantidade": 1,
    "confianca": "alta|media|baixa"
  }}
]

- quantidade padrão = 1 por variação
- se o modelo não existir no catálogo, deixe cod_interno e nome_produto como null
- retorne apenas o JSON, sem explicações"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    import json, re
    raw = msg.content[0].text
    # extrai JSON do output
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if m:
        return json.loads(m.group())
    return json.loads(raw)
