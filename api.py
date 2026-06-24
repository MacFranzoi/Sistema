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
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas","aprovacoes",
            "pedido","compras_hist",
            "financeiro","relatorios","rel_estoque",
            "sincronizacao","listas","usuarios",
        ],
    },
    "gerencia": {
        "label": "Gerência",
        "paginas": [
            "dashboard","clientes","fornecedores",
            "novo_modelo","clonar_modelo","precos",
            "vendas","orcamentos",
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas","aprovacoes",
            "pedido","compras_hist",
            "financeiro","relatorios","rel_estoque",
            "listas",
        ],
    },
    "estoque": {
        "label": "Estoque",
        "paginas": [
            "dashboard",
            "entrada","acerto","estoque_loja","disponibilidade","etiquetas",
            "pedido","compras_hist",
            "rel_estoque",
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
    salvos = None
    if os.path.exists(SETORES_FILE):
        try:
            with open(SETORES_FILE, encoding="utf-8") as f:
                salvos = json.load(f)
        except Exception:
            pass
    if salvos is None:
        return json.loads(json.dumps(_SETORES_PADRAO))
    # Mescla: garante que páginas novas do padrão apareçam nos setores salvos
    for setor, cfg_padrao in _SETORES_PADRAO.items():
        if setor not in salvos:
            salvos[setor] = json.loads(json.dumps(cfg_padrao))
        else:
            pags_salvas = set(salvos[setor].get("paginas", []))
            pags_padrao = set(cfg_padrao.get("paginas", []))
            novas = pags_padrao - pags_salvas
            if novas:
                salvos[setor]["paginas"] = list(pags_salvas | novas)
    return salvos

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
    # Tenta arquivo local; se não existe, baixa do GitHub
    if not os.path.exists(SESSOES_FILE):
        _gh_baixar_arquivo("sessoes.json", SESSOES_FILE)
    if os.path.exists(SESSOES_FILE):
        try:
            with open(SESSOES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _salvar_sessoes(s):
    conteudo = json.dumps(s, ensure_ascii=False, indent=2)
    with open(SESSOES_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("sessoes.json", conteudo, "Atualiza sessoes")

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
    ok = _gh_push_arquivo("usuarios.json", conteudo, "Atualiza usuarios")
    if not ok:
        raise RuntimeError("Falha ao salvar usuários no GitHub — alteração NÃO foi persistida.")

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
            time.sleep(0.15)
            r = requests.request(method, url, headers=HEADERS, params=p or None, json=body, timeout=45)
            r.raise_for_status()
            if not r.content or not r.text.strip():
                return {"code": r.status_code, "data": {}}
            return r.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # Falhas de rede transitórias (comuns em nuvem) — tenta de novo com backoff
            if i == tentativas - 1:
                raise Exception(f"API não respondeu após {tentativas} tentativas. Tente novamente.")
            time.sleep(2 ** i)
        except requests.exceptions.HTTPError:
            # 5xx geralmente é transitório — tenta de novo; 4xx falha imediato
            if r.status_code >= 500 and i < tentativas - 1:
                time.sleep(2 ** i)
                continue
            raise Exception(f"Erro HTTP {r.status_code}: {r.text[:300]}")
        except ValueError:
            # CakePHP mistura PHP notices antes do JSON — busca {"code" diretamente
            _idx = r.text.find('{"code"')
            if _idx >= 0:
                try:
                    _parsed = json.loads(r.text[_idx:])
                    # Aceita qualquer JSON com "code" e "data" (not just status:success)
                    if "data" in _parsed or _parsed.get("status") == "success":
                        return _parsed
                except Exception:
                    pass
            raise Exception(f"Resposta inválida da API ({r.status_code}): {r.text[:2000]}")


def _get(endpoint, params=None, loja_id=None):
    return _request("GET", endpoint, params=params, loja_id=loja_id)


def _put(endpoint, body, loja_id=None):
    return _request("PUT", endpoint, body=body, loja_id=loja_id)


def _post(endpoint, body, loja_id=None):
    return _request("POST", endpoint, body=body, loja_id=loja_id)


def _delete(endpoint, loja_id=None):
    return _request("DELETE", endpoint, loja_id=loja_id)


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


def sincronizar_estoque_loja(loja_id=None, max_paginas=None):
    """
    Atualiza só o estoque das variações no cache da loja, buscando ao vivo
    na GestãoClick (mais rápido que o sync completo). Devolve quantas
    variações foram atualizadas.
    """
    cache = carregar_cache(loja_id)
    if not cache:
        cache = sincronizar_produtos(loja_id)
    dados = buscar_estoque_ao_vivo(loja_id=loja_id, max_paginas=max_paginas)
    estoque_map = {}
    for p in dados.get("produtos", []):
        pid = str(p.get("id", ""))
        for v in p.get("variacoes", []):
            vd = v.get("variacao", {})
            estoque_map[f"{pid}_{vd.get('id','')}"] = vd.get("estoque", 0)
    n = 0
    for p in cache.get("produtos", []):
        pid = str(p.get("id", ""))
        for v in p.get("variacoes", []):
            vd = v.get("variacao", {})
            k = f"{pid}_{vd.get('id','')}"
            if k in estoque_map:
                vd["estoque"] = estoque_map[k]
                n += 1
    cache["sincronizado_em"] = datetime.now().isoformat()
    with open(cache_path(loja_id), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return {"atualizadas": n, "loja_id": loja_id, "sincronizado_em": cache["sincronizado_em"]}


def carregar_cache(loja_id=None):
    p = cache_path(loja_id)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def buscar_estoque_ao_vivo(loja_id=None, nome=None, codigo=None, limite=100, max_paginas=None):
    """Busca produtos direto na API (estoque em tempo real).

    Busca página 1 sequencialmente para descobrir o total de páginas,
    depois busca as demais em paralelo (até 8 threads).
    """
    import concurrent.futures as _cf

    _max = max_paginas if max_paginas is not None else (5 if (nome or codigo) else 20)

    def _fetch(pagina):
        params = {"pagina": pagina, "limite": limite}
        if nome:   params["nome"]   = nome
        if codigo: params["codigo"] = codigo
        data = _get("produtos", params, loja_id=loja_id)
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        prods = data.get("data", []) if isinstance(data, dict) else []
        total_pgs = meta.get("total_paginas", 1)
        return prods, total_pgs

    # Página 1 primeiro — descobre quantas páginas existem
    prods1, total_paginas = _fetch(1)
    todos = list(prods1)

    paginas_restantes = list(range(2, min(total_paginas, _max) + 1))
    if paginas_restantes and prods1:
        with _cf.ThreadPoolExecutor(max_workers=8) as ex:
            for prods, _ in ex.map(_fetch, paginas_restantes):
                todos.extend(prods)

    return {
        "produtos": todos,
        "loja_id": loja_id,
        "total": len(todos),
        "sincronizado_em": datetime.now().isoformat(),
        "ao_vivo": True,
    }


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


def acerto_estoque_produto(produto_id, variacoes_novas: dict, loja_id=None):
    """Substitui TODO o estoque do produto em um único PUT.
    variacoes_novas: {variacao_id: quantidade}
    Variações não listadas ficam com estoque=0.
    """
    produto = _get(f"produtos/{produto_id}", loja_id=loja_id)
    dados = produto.get("data", produto)
    novas_variacoes = []
    for v in dados.get("variacoes", []):
        vd = v["variacao"]
        novo_estoque = variacoes_novas.get(vd["id"], 0)
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


def acerto_estoque_lote(entradas, loja_id=None, progress_callback=None):
    """Acerto completo por produto: zera todas as variações não listadas,
    define as listadas com a quantidade especificada. Um PUT por produto."""
    from collections import defaultdict
    por_produto = defaultdict(dict)  # produto_id → {variacao_id: quantidade}
    for e in entradas:
        por_produto[e["produto_id"]][e["variacao_id"]] = e["quantidade"]
    produtos = list(por_produto.keys())
    resultados = []
    for i, pid in enumerate(produtos):
        try:
            acerto_estoque_produto(pid, por_produto[pid], loja_id=loja_id)
            for e in entradas:
                if e["produto_id"] == pid:
                    resultados.append({"ok": True, **e})
        except Exception as ex:
            for e in entradas:
                if e["produto_id"] == pid:
                    resultados.append({"ok": False, "erro": str(ex), **e})
        if progress_callback:
            progress_callback(i + 1, len(produtos))
    return resultados


def listar_fornecedores():
    data = _get("fornecedores", {"limite": 100})
    return data.get("data", [])


def listar_formas_pagamentos():
    data = _get("formas_pagamentos")
    return data.get("data", [])


def listar_situacoes_compras():
    data = _get("situacoes_compras")
    return data.get("data", [])


def _resolver_variacao_id_loja(produto_id, variacao_cod, variacao_nome, loja_id):
    """Retorna o variacao_id correto para a loja de destino.

    O ID interno da variação é ESPECÍFICO de cada loja (muda por loja),
    enquanto o código da variação (ex.: 'A010002') é estável. Como a
    compra é lançada numa loja específica, precisamos enviar o variacao_id
    daquela loja — senão o gestãoclick não acha a variação e joga tudo na
    primeira (ex.: Preto). Casa primeiro pelo código, depois pelo nome.
    """
    if not loja_id:
        return None
    cache = carregar_cache(loja_id)
    if not cache:
        return None
    for p in cache.get("produtos", []):
        if str(p.get("id")) != str(produto_id):
            continue
        if variacao_cod:
            for v in p.get("variacoes", []):
                vd = v["variacao"]
                if str(vd.get("codigo", "")) == str(variacao_cod):
                    return vd["id"]
        if variacao_nome:
            for v in p.get("variacoes", []):
                vd = v["variacao"]
                if str(vd.get("nome", "")) == str(variacao_nome):
                    return vd["id"]
        break
    return None


def criar_compra_acerto(itens, fornecedor_id, situacao_id, forma_pagamento_id=None, loja_id=None):
    """Cria uma Compra para lançar estoque (acerto).
    itens: lista de dicts com produto_id, variacao_id, produto_nome,
           possui_variacao, quantidade, valor_custo.
    Envia cada item separadamente conforme a API espera.
    """
    from datetime import date as _date

    hoje = _date.today().strftime("%Y-%m-%d")

    _total = 0.0
    produtos = []
    for it in itens:
        _qtd    = int(it.get("quantidade", 1))
        _custo  = float(it.get("valor_custo") or 0)
        if _custo <= 0:
            _custo = 0.01
        _total += _qtd * _custo
        _vid    = it.get("variacao_id") or ""
        # Re-resolve o variacao_id para a LOJA de destino (o ID é por loja).
        if _vid:
            _vid_loja = _resolver_variacao_id_loja(
                it.get("produto_id"), it.get("variacao_cod"),
                it.get("variacao_nome"), loja_id
            )
            if _vid_loja:
                _vid = _vid_loja
        _qtd_str = f"{_qtd:.2f}"          # formato "5.00" como o blueprint
        # nome_produto: usa SEMPRE o nome real do produto (sem a variação),
        # limpando qualquer sufixo que a API/cache tenha grudado.
        _nome = (it.get("produto_nome") or "").strip()
        if " (" in _nome:
            _nome = _nome.split(" (")[0].strip()
        # detalhes: usa o nome REAL da variação (ex.: "Branco / Aveludada")
        # para que cada linha da compra seja identificável no gestãoclick.
        _det = (it.get("variacao_nome") or "").strip()
        produtos.append({
            "produto": {
                "produto_id":       str(it["produto_id"]),
                "variacao_id":      str(_vid),
                "nome_produto":     _nome,
                "possui_variacao":  1 if _vid else 0,
                "quantidade":       _qtd_str,
                "quantidade_saida": _qtd_str,   # entra TODA a quantidade no estoque
                "valor_custo":      f"{_custo:.2f}",
                "detalhes":         _det,
                "unidade":          "UND",
                "largura":          0,
                "altura":           0,
            }
        })

    body = {
        "fornecedor_id": str(fornecedor_id),
        "data_emissao":  hoje,
        "situacao_id":   str(situacao_id),
        "observacoes":   f"Acerto de estoque — {hoje}",
        "valor_frete":   "0.00",
        "produtos":      produtos,
        "pagamentos": [
            {
                "pagamento": {
                    "data_vencimento":    hoje,
                    "valor":             f"{_total:.2f}",
                    "forma_pagamento_id": str(forma_pagamento_id) if forma_pagamento_id else "",
                    "plano_contas_id":   "17129225",
                    "observacao":        "Acerto de estoque",
                }
            }
        ],
    }
    _resp = _post("compras", body, loja_id=loja_id)
    # Anexa o body enviado para depuração (não afeta a API)
    if isinstance(_resp, dict):
        _resp["_body_enviado"] = body
    return _resp


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


# ── Formatos de etiqueta Pimaco ────────────────────────────────────────────
# Medidas em mm (A4 = 210 × 297 mm)
FORMATOS_ETIQUETA = {
    "pimaco_a4351": {
        "label": "Pimaco A4351 (3×10, 63,5×29,7mm — 30/folha)",
        "cols": 3, "rows": 10,
        "larg": 63.5, "alt": 29.7,
        "ml": 5.0, "mt": 13.0,   # margem esquerda / topo
        "gh": 3.0, "gv": 0.0,    # gap horizontal / vertical entre etiquetas
    },
    "pimaco_a4362": {
        "label": "Pimaco A4362 (2×7, 99×42mm — 14/folha)",
        "cols": 2, "rows": 7,
        "larg": 99.0, "alt": 42.0,
        "ml": 5.0, "mt": 5.0,
        "gh": 2.0, "gv": 0.0,
    },
    "pimaco_a4356": {
        "label": "Pimaco A4356 (4×10, 45×25,4mm — 40/folha)",
        "cols": 4, "rows": 10,
        "larg": 45.0, "alt": 25.4,
        "ml": 10.0, "mt": 21.5,
        "gh": 2.5, "gv": 0.0,
    },
}


def gerar_pdf_etiquetas(itens: list, formato: str = "pimaco_a4351") -> bytes:
    """
    Gera PDF de etiquetas com barcode Code 128.
    Cada item da lista é expandido pela quantidade.
    """
    from PIL import Image as _PIL, ImageDraw as _ID, ImageFont as _IF
    import io as _io

    cfg = FORMATOS_ETIQUETA.get(formato, FORMATOS_ETIQUETA["pimaco_a4351"])

    DPI      = 200
    MM2PX    = DPI / 25.4
    def _mm(v): return int(v * MM2PX)

    A4W, A4H = _mm(210), _mm(297)
    larg_px  = _mm(cfg["larg"])
    alt_px   = _mm(cfg["alt"])
    ml_px    = _mm(cfg["ml"])
    mt_px    = _mm(cfg["mt"])
    gh_px    = _mm(cfg["gh"])
    gv_px    = _mm(cfg["gv"])
    per_page = cfg["cols"] * cfg["rows"]

    # Expande itens pela quantidade
    labels = []
    for it in itens:
        for _ in range(max(1, int(it.get("quantidade", 1)))):
            labels.append(it)

    def _barcode_img(text: str, w_px: int, h_px: int):
        try:
            import barcode as _bc
            from barcode.writer import ImageWriter as _IW
            buf = _io.BytesIO()
            # Calcula module_width a partir da largura disponível
            mw = max(0.2, (w_px / DPI * 25.4) / (len(text) * 11 + 20))
            _bc.Code128(text, writer=_IW()).write(buf, options={
                "module_width": mw, "module_height": h_px / DPI * 25.4 - 2,
                "quiet_zone": 2.0, "text_distance": 1.0,
                "font_size": 5, "dpi": DPI, "write_text": True,
            })
            buf.seek(0)
            img = _PIL.open(buf).convert("RGB")
            return img.resize((w_px, h_px), _PIL.LANCZOS)
        except Exception:
            # Fallback: retorna imagem em branco com texto
            img = _PIL.new("RGB", (w_px, h_px), "white")
            _ID.Draw(img).text((4, h_px // 3), text, fill="black")
            return img

    try:
        font_b = _IF.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", _mm(3.2))
        font_n = _IF.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", _mm(2.6))
        font_s = _IF.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", _mm(2.2))
    except Exception:
        font_b = font_n = font_s = _IF.load_default()

    pages = []
    for page_start in range(0, max(1, len(labels)), per_page):
        page_labels = labels[page_start: page_start + per_page]
        page = _PIL.new("RGB", (A4W, A4H), "white")
        draw = _ID.Draw(page)

        for i, it in enumerate(page_labels):
            col = i % cfg["cols"]
            row = i // cfg["cols"]
            x = ml_px + col * (larg_px + gh_px)
            y = mt_px + row * (alt_px + gv_px)

            # Borda da etiqueta (linha cinza fina)
            draw.rectangle([x, y, x + larg_px - 1, y + alt_px - 1],
                           outline=(200, 200, 200), width=1)

            pad = _mm(1.0)
            # Linha 1: nome do produto (negrito)
            nome = (it.get("produto_nome") or "")[:40]
            draw.text((x + pad, y + pad), nome, font=font_b, fill="black")

            # Linha 2: variação
            var = (it.get("variacao_nome") or "")[:45]
            draw.text((x + pad, y + pad + _mm(3.6)), var, font=font_n, fill=(60, 60, 60))

            # Barcode: usa variacao_cod ou variacao_id como fallback
            bc_text = (it.get("variacao_cod") or str(it.get("variacao_id", ""))).strip()
            if bc_text:
                bc_h = alt_px - _mm(10.0)
                bc_y = y + alt_px - bc_h - pad
                bc_w = larg_px - pad * 2
                bc_img = _barcode_img(bc_text, bc_w, bc_h)
                page.paste(bc_img, (x + pad, bc_y))

        pages.append(page)

    buf = _io.BytesIO()
    if pages:
        pages[0].save(buf, format="PDF", resolution=DPI,
                      save_all=True, append_images=pages[1:])
    buf.seek(0)
    return buf.read()


# ──────────────────────────────────────────────
# GitHub sync para listas
# ──────────────────────────────────────────────

import base64

_GH_REPO   = "MacFranzoi/Sistema"
_GH_BRANCH = "main"
_GH_API    = "https://api.github.com"

def _gh_token() -> str:
    """GITHUB_TOKEN: env var primeiro (Railway), depois st.secrets (dev local)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            import streamlit as _st
            token = _st.secrets.get("GITHUB_TOKEN", "")
        except Exception:
            pass
    return token

def _gh_headers():
    token = _gh_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

_GH_HEADERS = None  # legacy alias — use _gh_headers() instead

def diagnostico_config():
    """Verifica se as credenciais necessárias estão configuradas (Railway env vars).

    Retorna dict com status de cada integração. Sem GITHUB_TOKEN a persistência
    (sessões, usuários, listas) NÃO sobrevive a reinícios do container.
    """
    status = {
        "github_token": bool(_gh_token()),
        "anthropic_key": bool(_get_anthropic_key()),
        "openai_key": bool(_get_openai_key()),
        "github_ok": False,
    }
    # Testa de fato o acesso ao GitHub (token válido + repo acessível)
    if status["github_token"]:
        try:
            r = requests.get(f"{_GH_API}/repos/{_GH_REPO}",
                             headers=_gh_headers(), timeout=8)
            status["github_ok"] = (r.status_code == 200)
        except Exception:
            status["github_ok"] = False
    return status

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
    # Descobre a maior ordem atual para esse tipo
    max_ordem = 0
    try:
        for arq in os.listdir(DIR_LISTAS):
            if not arq.endswith(".json"):
                continue
            with open(os.path.join(DIR_LISTAS, arq), encoding="utf-8") as f:
                d = json.load(f)
            if d.get("tipo") == tipo and d.get("ordem") is not None:
                try:
                    max_ordem = max(max_ordem, int(d["ordem"]))
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass

    dados = {
        "nome": nome,
        "tipo": tipo,
        "loja_id": loja_id,
        "loja_nome": loja_nome,
        "criado_em": datetime.now().isoformat(),
        "ordem": max_ordem + 1,
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
        try:
            with open(os.path.join(DIR_LISTAS, arq), encoding="utf-8") as f:
                dados = json.load(f)
            # Filtra por tipo via campo JSON (não mais pelo prefixo do nome)
            if tipo and dados.get("tipo") != tipo:
                continue
            dados["_arquivo"] = arq
            listas.append(dados)
        except Exception:
            pass
    # Ordena: listas com `ordem` primeiro (ascendente), depois por data desc
    com_ordem = sorted([l for l in listas if "ordem" in l], key=lambda l: l["ordem"])
    sem_ordem = sorted([l for l in listas if "ordem" not in l], key=lambda l: l.get("criado_em", ""), reverse=True)
    return com_ordem + sem_ordem


def carregar_lista(arquivo):
    with open(os.path.join(DIR_LISTAS, arquivo), encoding="utf-8") as f:
        return json.load(f)


def excluir_lista(arquivo):
    """Remove lista local e do GitHub."""
    caminho = os.path.join(DIR_LISTAS, arquivo)
    if os.path.exists(caminho):
        os.remove(caminho)
    _gh_delete_arquivo(f"listas/{arquivo}")


def mover_lista_na_ordem(arquivo, tipo, direcao):
    """Move a lista uma posição para cima ou para baixo na ordem de exibição."""
    # Carrega todas as listas do tipo sem chamar sincronizar (evita rede desnecessária)
    arquivos = sorted([f for f in os.listdir(DIR_LISTAS) if f.endswith(".json")], reverse=True)
    listas = []
    for arq in arquivos:
        try:
            with open(os.path.join(DIR_LISTAS, arq), encoding="utf-8") as f:
                d = json.load(f)
            if d.get("tipo") == tipo:
                listas.append([arq, d])
        except Exception:
            pass

    # Ordena igual ao listar_listas_salvas: com ordem asc, depois sem ordem por data desc
    com_ordem = sorted([x for x in listas if "ordem" in x[1]], key=lambda x: x[1]["ordem"])
    sem_ordem = sorted([x for x in listas if "ordem" not in x[1]], key=lambda x: x[1].get("criado_em", ""), reverse=True)
    listas_ord = com_ordem + sem_ordem

    idx = next((i for i, (arq, _) in enumerate(listas_ord) if arq == arquivo), None)
    if idx is None:
        return False

    outro_idx = idx - 1 if direcao == "cima" else idx + 1
    if outro_idx < 0 or outro_idx >= len(listas_ord):
        return False

    # Atribui ordens sequenciais em memória e faz o swap
    for i, (_, d) in enumerate(listas_ord):
        d["_ord_tmp"] = i + 1

    ordem_nova_a = listas_ord[outro_idx][1]["_ord_tmp"]
    ordem_nova_b = listas_ord[idx][1]["_ord_tmp"]

    def _salvar_ordem(arq, d, nova_ordem):
        d["ordem"] = nova_ordem
        d_clean = {k: v for k, v in d.items() if not k.startswith("_")}
        conteudo = json.dumps(d_clean, ensure_ascii=False, indent=2)
        with open(os.path.join(DIR_LISTAS, arq), "w", encoding="utf-8") as f:
            f.write(conteudo)
        _gh_push_arquivo(f"listas/{arq}", conteudo, f"Reordena lista: {d.get('nome', '')}")

    _salvar_ordem(listas_ord[idx][0], listas_ord[idx][1], ordem_nova_a)
    _salvar_ordem(listas_ord[outro_idx][0], listas_ord[outro_idx][1], ordem_nova_b)
    return True


def mudar_tipo_lista(arquivo, novo_tipo):
    """Muda o tipo de uma lista (ex: pedido → entrada)."""
    cam = os.path.join(DIR_LISTAS, arquivo)
    with open(cam, encoding="utf-8") as f:
        d = json.load(f)
    d["tipo"] = novo_tipo
    d.pop("ordem", None)  # reseta ordem para a nova categoria
    conteudo = json.dumps(d, ensure_ascii=False, indent=2)
    with open(cam, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo(f"listas/{arquivo}", conteudo, f"Muda tipo lista: {d.get('nome', '')}")
    return True


def acrescentar_itens_lista(arquivo_destino, novos_itens):
    """Adiciona itens ao final de uma lista existente."""
    cam = os.path.join(DIR_LISTAS, arquivo_destino)
    with open(cam, encoding="utf-8") as f:
        d = json.load(f)
    d["itens"] = d.get("itens", []) + novos_itens
    d["atualizado_em"] = datetime.now().isoformat()
    conteudo = json.dumps(d, ensure_ascii=False, indent=2)
    with open(cam, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo(f"listas/{arquivo_destino}", conteudo, f"Adiciona itens: {d.get('nome', '')}")
    return True


def mesclar_listas(arquivo_a, arquivo_b, nome_nova):
    """Cria uma nova lista com a união dos itens de A e B (mantém tipo de A)."""
    with open(os.path.join(DIR_LISTAS, arquivo_a), encoding="utf-8") as f:
        da = json.load(f)
    with open(os.path.join(DIR_LISTAS, arquivo_b), encoding="utf-8") as f:
        db = json.load(f)
    itens = da.get("itens", []) + db.get("itens", [])
    return salvar_lista(nome_nova, da.get("tipo", "pedido"), itens, da.get("loja_id"), da.get("loja_nome"))


def exportar_todas_listas_excel():
    """Gera um Excel com aba Resumo + uma aba por lista com metadados e itens."""
    import io
    import pandas as pd

    _TIPOS_NOMES = {
        "pedido": "Pedido de Compra", "entrada": "Entrada",
        "acerto": "Acerto", "etiquetas": "Etiquetas"
    }
    _COLS_POR_TIPO = {
        "pedido":    [("fornecedor","Fornecedor"), ("produto_nome","Produto"), ("variacao_nome","Variação"),
                      ("quantidade","Qtd"), ("valor_custo","Custo Unit."), ("observacao","Obs.")],
        "entrada":   [("produto_nome","Produto"), ("variacao_nome","Variação"),
                      ("estoque_atual","Estoque Atual"), ("quantidade","Qtd")],
        "acerto":    [("produto_nome","Produto"), ("variacao_nome","Variação"),
                      ("estoque_atual","Estoque Atual"), ("quantidade","Qtd")],
        "etiquetas": [("nome","Nome"), ("quantidade","Qtd")],
    }
    _DEFAULT_COLS = [("produto_nome","Produto"), ("variacao_nome","Variação"), ("quantidade","Qtd")]

    def _safe_sheet_name(nome, used):
        safe = "".join(c for c in str(nome) if c not in r'\/:*?[]')[:31].strip() or "Lista"
        base, i = safe, 1
        while safe in used:
            safe = f"{base[:28]}_{i}"
            i += 1
        used.add(safe)
        return safe

    listas = listar_listas_salvas()
    buf = io.BytesIO()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # ── Aba Resumo ────────────────────────────────────────────────────
        rows_res = []
        for lst in listas:
            atualizado = lst.get("atualizado_em", "")
            rows_res.append({
                "Nome":         lst.get("nome", ""),
                "Tipo":         _TIPOS_NOMES.get(lst.get("tipo", ""), lst.get("tipo", "")),
                "Loja":         lst.get("loja_nome", ""),
                "Itens":        len(lst.get("itens", [])),
                "Criado em":    lst.get("criado_em", "")[:16].replace("T", " "),
                "Atualizado em": atualizado[:16].replace("T", " ") if atualizado else "—",
                "Criado por":   lst.get("criado_por", "—") or "—",
                "Arquivo":      lst.get("_arquivo", ""),
            })
        pd.DataFrame(rows_res).to_excel(writer, sheet_name="Resumo", index=False)

        # ── Uma aba por lista ─────────────────────────────────────────────
        used_names = {"Resumo"}
        for lst in listas:
            sheet_name = _safe_sheet_name(lst.get("nome", "Lista"), used_names)
            tipo = lst.get("tipo", "")
            cols_def = _COLS_POR_TIPO.get(tipo, _DEFAULT_COLS)
            atualizado = lst.get("atualizado_em", "")

            # Metadados como DataFrame de 2 colunas
            meta_rows = [
                {"Campo": "Nome",          "Valor": lst.get("nome", "")},
                {"Campo": "Tipo",          "Valor": _TIPOS_NOMES.get(tipo, tipo)},
                {"Campo": "Loja",          "Valor": lst.get("loja_nome", "")},
                {"Campo": "Criado em",     "Valor": lst.get("criado_em", "")[:16].replace("T", " ")},
                {"Campo": "Atualizado em", "Valor": atualizado[:16].replace("T", " ") if atualizado else "—"},
                {"Campo": "Criado por",    "Valor": lst.get("criado_por", "—") or "—"},
                {"Campo": "Total de itens","Valor": len(lst.get("itens", []))},
            ]
            df_meta = pd.DataFrame(meta_rows)

            # Itens
            itens = lst.get("itens", [])
            fields = [f for f, _ in cols_def]
            labels = [l for _, l in cols_def]
            if itens:
                df_itens = pd.DataFrame([{f: it.get(f, "") for f in fields} for it in itens])
                df_itens.columns = labels
            else:
                df_itens = pd.DataFrame(columns=labels)

            # Escreve metadados na linha 1, itens a partir da linha len(meta)+3
            startrow_itens = len(meta_rows) + 2
            df_meta.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
            df_itens.to_excel(writer, sheet_name=sheet_name, index=False, startrow=startrow_itens)

    buf.seek(0)
    return buf


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


# ──────────────────────────────────────────────
# Importação / exportação de planilhas
# ──────────────────────────────────────────────

def gerar_template_excel(tipo):
    """Retorna BytesIO com planilha-modelo para importação (tipo='pedido'|'etiquetas')."""
    import io, pandas as pd

    if tipo == "pedido":
        cols = ["Produto", "Variação", "Quantidade", "Fornecedor", "Custo Unit.", "Observação"]
        exemplos = [
            ["Capinha iPhone 15", "Preta", 10, "Distribuidora XYZ", 5.50, ""],
            ["Capinha Samsung A55", "Azul", 5, "Distribuidora XYZ", 4.80, "urgente"],
        ]
    else:  # etiquetas
        cols = ["Produto", "Variação", "Quantidade"]
        exemplos = [
            ["Capinha iPhone 15", "Preta", 10],
            ["Capinha Samsung A55", "Azul", 5],
        ]

    df = pd.DataFrame(exemplos, columns=cols)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Importação")
        ws = writer.sheets["Importação"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                len(str(col[0].value or "")), max(len(str(c.value or "")) for c in col)
            ) + 4
    buf.seek(0)
    return buf


def importar_excel_itens(arquivo_bytes, tipo, cache):
    """
    Lê uma planilha Excel e tenta casar cada linha com produtos do cache.
    Retorna (itens_ok, itens_sem_match).
    itens_ok: lista de dicts prontos para uso em pedido_itens/etiq_itens.
    itens_sem_match: lista de dicts com os dados originais da planilha.
    """
    import io, pandas as pd

    df = pd.read_excel(io.BytesIO(arquivo_bytes))
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Mapeamento flexível de nomes de coluna
    _alias = {
        "produto": ["produto", "product", "nome", "name", "modelo"],
        "variacao": ["variação", "variacao", "variation", "cor", "color", "tamanho", "size"],
        "quantidade": ["quantidade", "qtd", "qty", "quantity", "qntd"],
        "fornecedor": ["fornecedor", "supplier", "vendor", "forncedor"],
        "custo": ["custo unit.", "custo", "valor_custo", "cost", "price", "preco", "preço"],
        "observacao": ["observação", "observacao", "obs", "observation", "note", "notas"],
    }

    def _col(chave):
        for alias in _alias[chave]:
            if alias in df.columns:
                return alias
        return None

    col_prod = _col("produto")
    col_var = _col("variacao")
    col_qtd = _col("quantidade")

    if not col_prod or not col_qtd:
        raise ValueError("Planilha deve ter colunas 'Produto' e 'Quantidade'.")

    produtos_cache = cache.get("produtos", [])

    def _buscar(nome_prod, nome_var):
        nome_prod_l = (nome_prod or "").lower().strip()
        nome_var_l = (nome_var or "").lower().strip()
        # Tokenização: todos os tokens do nome do produto devem aparecer
        tokens = [t for t in nome_prod_l.split() if len(t) > 2]
        candidatos = []
        for p in produtos_cache:
            p_nome_l = (p.get("nome") or "").lower()
            if not all(t in p_nome_l for t in tokens):
                continue
            for v in p.get("variacoes", []):
                vd = v["variacao"]
                v_nome_l = (vd.get("nome") or "").lower()
                score = sum(t in p_nome_l for t in tokens)
                if nome_var_l:
                    var_tokens = [t for t in nome_var_l.split() if len(t) > 1]
                    score += sum(t in v_nome_l for t in var_tokens) * 2
                candidatos.append((score, p, vd))
        if not candidatos:
            return None, None
        candidatos.sort(key=lambda x: -x[0])
        _, p_best, v_best = candidatos[0]
        return p_best, v_best

    itens_ok = []
    itens_sem_match = []

    col_forn = _col("fornecedor")
    col_custo = _col("custo")
    col_obs = _col("observacao")

    for _, row in df.iterrows():
        nome_prod = str(row.get(col_prod, "") or "").strip()
        nome_var = str(row.get(col_var, "") or "").strip() if col_var else ""
        try:
            qtd = int(float(row[col_qtd]))
        except (TypeError, ValueError):
            qtd = 0
        if not nome_prod or qtd <= 0:
            continue

        prod, var = _buscar(nome_prod, nome_var)

        base = {
            "_prod_original": nome_prod,
            "_var_original": nome_var,
            "quantidade": qtd,
            "fornecedor": str(row.get(col_forn, "") or "").strip() if col_forn else "",
            "valor_custo": str(row.get(col_custo, "") or "").strip() if col_custo else "",
            "observacao": str(row.get(col_obs, "") or "").strip() if col_obs else "",
        }

        if prod and var:
            item = {
                "produto_id": prod["id"],
                "produto_nome": prod["nome"],
                "cod_interno": prod.get("codigo_interno", ""),
                "variacao_id": var["id"],
                "variacao_nome": var.get("nome", ""),
                "variacao_cod": var.get("codigo", ""),
                "nome": f"{prod['nome']} / {var.get('nome','')}",
                **base,
            }
            itens_ok.append(item)
        else:
            itens_sem_match.append({**base, "produto_nome": nome_prod, "variacao_nome": nome_var})

    return itens_ok, itens_sem_match


def calcular_capas_restantes(pedido_itens, recebidos_itens):
    """
    Subtrai as quantidades recebidas do pedido original.
    Retorna lista de itens com quantidade > 0 após subtração.
    """
    # Indexa recebidos por variacao_id (prioritário) e por nome normalizado
    recebidos_por_id = {}
    recebidos_por_nome = {}
    for r in recebidos_itens:
        vid = str(r.get("variacao_id", "")).strip()
        nome = (r.get("variacao_nome") or r.get("nome") or "").lower().strip()
        qtd = int(r.get("quantidade", 0))
        if vid:
            recebidos_por_id[vid] = recebidos_por_id.get(vid, 0) + qtd
        if nome:
            recebidos_por_nome[nome] = recebidos_por_nome.get(nome, 0) + qtd

    restantes = []
    for item in pedido_itens:
        vid = str(item.get("variacao_id", "")).strip()
        nome = (item.get("variacao_nome") or item.get("nome") or "").lower().strip()
        qtd_pedido = int(item.get("quantidade", 0))

        qtd_rec = 0
        if vid and vid in recebidos_por_id:
            qtd_rec = recebidos_por_id[vid]
        elif nome and nome in recebidos_por_nome:
            qtd_rec = recebidos_por_nome[nome]

        qtd_restante = max(0, qtd_pedido - qtd_rec)
        if qtd_restante > 0:
            restantes.append({**item, "quantidade": qtd_restante})

    return restantes


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
def buscar_vendas(data_ini=None, data_fim=None, loja_id=None, pagina=1, limite=50,
                  situacao_id=None, tipo=None):
    params = {"limite": limite, "pagina": pagina}
    if data_ini: params["data_inicio"] = data_ini
    if data_fim:  params["data_fim"]    = data_fim
    if situacao_id: params["situacao_id"] = situacao_id
    if tipo: params["tipo"] = tipo
    r = _get("vendas", params=params, loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else []

def buscar_venda(pedido_id, loja_id=None):
    r = _get(f"vendas/{pedido_id}", loja_id=loja_id)
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
# Sugestão automática de pedido (reposição por grupo/variação)
# ──────────────────────────────────────────────
def _extrair_cor_tipo(nome_variacao):
    """'Preto / Aveludada' -> ('preto', 'aveludada'). Sem '/' -> (nome, '')."""
    partes = [x.strip() for x in (nome_variacao or "").split("/") if x.strip()]
    if len(partes) >= 2:
        return partes[0].lower(), partes[-1].lower()
    return (nome_variacao or "").strip().lower(), ""


# Palavras que marcam um GRUPO como acessório/filme (não é capa de celular).
_GRUPOS_NAO_CAPA = (
    "cabo", "fone", "carregador", "suporte", "caixa de som", "fonte",
    "adaptador", "powerbank", "power bank", "microfone", "teclado",
    "localizador", "pulseira", "relógio", "relogio", "smartwatch", "watch",
    "controle", "indução", "inducao", "fotografia", "acessório", "acessorio",
    "adicionai", "adicional", "fivela", "umidificador", "car  bt", "car bt",
    "audio", "áudio", "pelicula", "película", "hidrogel", "vidro",
    "tc fonte", "tc carregador", "indução", "velcro",  # velcro de suporte
)


def grupos_de_aparelhos(loja_id=None, limiar=0.5):
    """
    Devolve os grupos que representam CAPAS de celular — tanto os nomeados por
    modelo (Apple, Galaxy A, Moto G...) quanto os nomeados por tipo de capa
    (Aveludada, Aveludada Linha A, Metalizada, Tecido, Luxo, Space Silk...).

    Critério: o grupo tem variações E o nome NÃO contém palavra de acessório/
    filme (_GRUPOS_NAO_CAPA). Como reforço, grupos com a maioria das variações
    no padrão 'Cor / Tipo' também entram.
    """
    cache = carregar_cache(loja_id) or {}
    stats = {}
    for p in cache.get("produtos", []) or []:
        g = (p.get("nome_grupo", "") or "").strip()
        if not g:
            continue
        tot, combar = stats.get(g, (0, 0))
        for v in p.get("variacoes", []) or []:
            vd = v.get("variacao", v) if isinstance(v, dict) else {}
            tot += 1
            if "/" in (vd.get("nome", "") or ""):
                combar += 1
        stats[g] = (tot, combar)

    aparelhos = []
    for g, (tot, comb) in stats.items():
        if tot <= 0:
            continue
        gl = g.lower()
        if any(kw in gl for kw in _GRUPOS_NAO_CAPA):
            continue  # acessório ou filme
        # É capa: nomeado por modelo (tem '/') ou por tipo de capa (sem '/').
        aparelhos.append(g)
    return sorted(aparelhos)


# Tipos de variação que NÃO são capa (películas, vidros, etc.) — excluídos
# quando o usuário não escolhe um tipo específico.
_TIPOS_NAO_CAPA = {
    "pelicula", "película", "peli", "hidrogel", "vidro", "vidro 3d", "3d",
    "fch", "full", "privacidade", "fosca", "ceramica", "cerâmica",
    "nano", "gel", "cabo", "fone", "carregador", "suporte",
}


def coletar_variacoes_catalogo(loja_id=None, grupo=None, tipo=None, somente_ativos=True,
                               apenas_capas=True):
    """
    Varre o cache de produtos e devolve a lista achatada de variações,
    filtrada por grupo (nome_grupo) e/ou tipo de capa (ex.: 'Aveludada').

    - Sem `grupo` específico, restringe aos grupos de APARELHOS (capinhas),
      nunca acessórios.
    - Com `apenas_capas=True` e sem `tipo` específico, exclui variações cujo
      tipo não seja capa (película, vidro, hidrogel...).
    """
    cache = carregar_cache(loja_id) or {}
    grupo_l = (grupo or "").strip().lower()
    tipo_l = (tipo or "").strip().lower()
    grupos_validos = None
    if not grupo_l:
        grupos_validos = {g.lower() for g in grupos_de_aparelhos(loja_id)}
    out = []
    for p in cache.get("produtos", []) or []:
        if somente_ativos and str(p.get("ativo", "1")) not in ("1", "True", "true"):
            continue
        g_nome = (p.get("nome_grupo", "") or "")
        if grupo_l and grupo_l not in g_nome.lower():
            continue
        if grupos_validos is not None and g_nome.lower() not in grupos_validos:
            continue
        for v in p.get("variacoes", []) or []:
            vd = v.get("variacao", v) if isinstance(v, dict) else {}
            nome = vd.get("nome", "") or ""
            if tipo_l and tipo_l not in nome.lower():
                continue
            cor, vtipo = _extrair_cor_tipo(nome)
            # Sem tipo escolhido: descarta o que não for capa.
            if apenas_capas and not tipo_l and vtipo in _TIPOS_NAO_CAPA:
                continue
            try:
                est = int(float(vd.get("estoque", 0) or 0))
            except (TypeError, ValueError):
                est = 0
            valores = vd.get("valores") or p.get("valores") or []
            custo = (valores[0].get("valor_custo") if valores else None) or p.get("valor_custo", "")
            out.append({
                "produto_id": str(p.get("id", "")),
                "produto_nome": p.get("nome", ""),
                "nome_grupo": p.get("nome_grupo", ""),
                "cod_interno": p.get("codigo_interno", ""),
                "variacao_id": str(vd.get("id", "")),
                "variacao_cod": vd.get("codigo", ""),
                "variacao_nome": nome,
                "cor": cor,
                "tipo": vtipo,
                "estoque": est,
                "valor_custo": custo,
            })
    return out


def cache_vendas_path(loja_id=None):
    sufixo = f"_{loja_id}" if loja_id else "_todas"
    return os.path.join(DIR, f"cache_vendas{sufixo}.json")


def carregar_cache_vendas(loja_id=None):
    p = cache_vendas_path(loja_id)
    if not os.path.exists(p):
        # Cold start: tenta recuperar do GitHub (persistido pelo scheduler).
        if _gh_token():
            try:
                r = requests.get(
                    f"{_GH_API}/repos/{_GH_REPO}/contents/{os.path.basename(p)}",
                    headers=_gh_headers(), params={"ref": _GH_BRANCH}, timeout=10)
                if r.status_code == 200:
                    import base64 as _b64
                    conteudo = _b64.b64decode(r.json().get("content", "")).decode()
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(conteudo)
                    return json.loads(conteudo)
            except Exception:
                pass
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def sincronizar_vendas(loja_id=None, dias=180, situacao_id=None, progress_callback=None,
                       push_github=False):
    """
    Baixa as vendas dos últimos `dias` (padrão ~6 meses) da loja, agrega a
    quantidade vendida por variação e por cor, e salva em cache_vendas_{loja}.
    Alimenta o gerador de pedidos sem precisar bater na API toda hora.
    Com push_github=True, persiste o cache (pequeno) no repositório para
    sobreviver a reinícios do container.
    """
    from datetime import date as _date, timedelta as _td
    hoje = _date.today()
    data_ini = str(hoje - _td(days=dias))
    ontem = str(hoje - _td(days=1))
    data_fim = str(hoje)
    # Base congelada (até ontem) + tail do dia (hoje). Assim a atualização
    # incremental só precisa re-baixar o dia de hoje.
    base = vendas_por_variacao(loja_id=loja_id, data_ini=data_ini, data_fim=ontem,
                               situacao_id=situacao_id, max_paginas=200,
                               progress_callback=progress_callback, coletar_lista=True)
    tail = vendas_por_variacao(loja_id=loja_id, data_ini=data_fim, data_fim=data_fim,
                               situacao_id=situacao_id, max_paginas=50, coletar_lista=True)
    cache = _montar_cache_vendas(loja_id, dias, data_ini, data_fim, base, tail, situacao_id)
    _salvar_cache_vendas(loja_id, cache, push_github)
    # Lista crua de vendas (cabeçalhos) em arquivo separado, para a página Vendas.
    _salvar_vendas_lista(loja_id, (base.get("lista", []) + tail.get("lista", [])))
    return cache


def cache_vendas_lista_path(loja_id=None):
    sufixo = f"_{loja_id}" if loja_id else "_todas"
    return os.path.join(DIR, f"cache_vendas_lista{sufixo}.json")


def _salvar_vendas_lista(loja_id, lista):
    try:
        with open(cache_vendas_lista_path(loja_id), "w", encoding="utf-8") as f:
            json.dump({"sincronizado_em": datetime.now().isoformat(), "lista": lista},
                      f, ensure_ascii=False)
    except Exception:
        pass


def carregar_vendas_lista(loja_id=None):
    p = cache_vendas_lista_path(loja_id)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def vendas_cacheadas(loja_id=None, data_ini=None, data_fim=None):
    """Lista de vendas do cache (rápida), filtrada por período. None se não há cache."""
    cache = carregar_vendas_lista(loja_id)
    if not cache:
        return None
    lista = cache.get("lista", [])
    if data_ini:
        lista = [v for v in lista if (v.get("data") or "") >= data_ini]
    if data_fim:
        lista = [v for v in lista if (v.get("data") or "") <= data_fim]
    return {"lista": sorted(lista, key=lambda v: v.get("data", ""), reverse=True),
            "sincronizado_em": cache.get("sincronizado_em", "")}


def _somar_contagens(a, b):
    out = dict(a or {})
    for k, v in (b or {}).items():
        out[k] = out.get(k, 0) + v
    return out


def _montar_cache_vendas(loja_id, dias, data_ini, data_fim, base, tail, situacao_id=None):
    por_var = _somar_contagens(base.get("por_variacao"), tail.get("por_variacao"))
    por_cor = _somar_contagens(base.get("por_cor"), tail.get("por_cor"))
    return {
        "sincronizado_em": datetime.now().isoformat(),
        "loja_id": loja_id,
        "loja_nome": LOJAS.get(str(loja_id), "Todas") if loja_id else "Todas",
        "data_ini": data_ini,
        "data_fim": data_fim,
        "dias": dias,
        "situacao_id": situacao_id,
        "tail_dia": data_fim,  # dia coberto pelo 'tail' (recarregado no incremental)
        "base_por_variacao": base.get("por_variacao", {}),
        "base_por_cor": base.get("por_cor", {}),
        "base_pedidos": base.get("pedidos", 0),
        "pedidos": base.get("pedidos", 0) + tail.get("pedidos", 0),
        "itens": base.get("itens", 0) + tail.get("itens", 0),
        "por_variacao": por_var,
        "por_cor": por_cor,
    }


def _salvar_cache_vendas(loja_id, cache, push_github=False):
    conteudo = json.dumps(cache, ensure_ascii=False)
    with open(cache_vendas_path(loja_id), "w", encoding="utf-8") as f:
        f.write(conteudo)
    if push_github and _gh_token():
        try:
            _gh_push_arquivo(os.path.basename(cache_vendas_path(loja_id)), conteudo,
                             f"sync vendas {cache['loja_nome']} {cache['sincronizado_em'][:16]}")
        except Exception:
            pass


def atualizar_vendas_incremental(loja_id=None, push_github=False):
    """
    Monitora SÓ as vendas novas do dia: recarrega apenas o dia de hoje e
    recombina com a base congelada (até ontem). Muito mais leve que refazer
    os 6 meses — ideal para rodar de minuto em minuto.

    Se não houver cache ainda, ou se o dia virou (tail_dia != hoje), faz o
    sync completo para refreezar a base.
    """
    from datetime import date as _date
    hoje = str(_date.today())
    cv = carregar_cache_vendas(loja_id)
    if not cv or "base_por_variacao" not in cv or cv.get("tail_dia") != hoje:
        return sincronizar_vendas(loja_id, dias=(cv or {}).get("dias", 180),
                                  push_github=push_github)
    tail = vendas_por_variacao(loja_id=loja_id, data_ini=hoje, data_fim=hoje,
                               max_paginas=50, coletar_lista=True)
    base = {"por_variacao": cv["base_por_variacao"], "por_cor": cv["base_por_cor"],
            "pedidos": cv.get("base_pedidos", 0), "itens": 0}
    cache = _montar_cache_vendas(loja_id, cv.get("dias", 180), cv.get("data_ini", ""),
                                 hoje, base, tail, cv.get("situacao_id"))
    cache["itens"] = cv.get("itens", 0)  # itens é informativo; mantém o da base
    _salvar_cache_vendas(loja_id, cache, push_github)
    # Atualiza a lista crua: troca as vendas de HOJE pelas recém-buscadas.
    _lista_cache = carregar_vendas_lista(loja_id) or {"lista": []}
    nova = [v for v in _lista_cache.get("lista", []) if (v.get("data") or "") != hoje]
    nova += tail.get("lista", [])
    _salvar_vendas_lista(loja_id, nova)
    return cache


def status_sincronizacao(loja_id=None):
    """
    Timestamps das últimas sincronizações relevantes para estoque/vendas,
    para exibir 'última atualização' nas telas.
    """
    cprod = carregar_cache(loja_id) or {}
    cven = carregar_cache_vendas(loja_id) or {}
    return {
        "produtos_em": cprod.get("sincronizado_em", ""),
        "produtos_total": cprod.get("total", 0),
        "vendas_em": cven.get("sincronizado_em", ""),
        "vendas_pedidos": cven.get("pedidos", 0),
        "vendas_periodo": (cven.get("data_ini", ""), cven.get("data_fim", "")),
    }


def _mapa_variacao_nome(loja_id=None):
    """variacao_id -> nome da variação ('Cor / Tipo'), a partir do cache."""
    cache = carregar_cache(loja_id) or {}
    mapa = {}
    for p in cache.get("produtos", []) or []:
        for v in p.get("variacoes", []) or []:
            vd = v.get("variacao", v) if isinstance(v, dict) else {}
            vid = str(vd.get("id", ""))
            if vid:
                mapa[vid] = vd.get("nome", "") or ""
    return mapa


def vendas_por_variacao(dias=30, loja_id=None, max_paginas=20, limite=100,
                        data_ini=None, data_fim=None, situacao_id=None,
                        progress_callback=None, coletar_lista=False):
    """
    Agrega a quantidade vendida por variação e por cor no período, SEMPRE
    filtrando por loja (`loja_id`). Lê os produtos direto da listagem de
    /vendas (que já traz `produtos[]`), paginando via `meta` — sem precisar
    buscar o detalhe de cada venda.

    Devolve {por_variacao: {id: qtd}, por_cor: {cor: qtd}, pedidos, itens}.
    Com coletar_lista=True inclui 'lista' (cabeçalhos enxutos de cada venda)
    para alimentar a página de Vendas sem nova chamada à API.
    """
    from datetime import date as _date, timedelta as _td
    if not data_fim:
        data_fim = str(_date.today())
    if not data_ini:
        data_ini = str(_date.today() - _td(days=dias))

    nome_por_vid = _mapa_variacao_nome(loja_id)
    por_var, por_cor = {}, {}
    lista = []
    n_pedidos = n_itens = 0

    # A GestãoClick separa vendas normais (tipo=produto, o padrão) das vendas
    # de balcão (tipo=vendas_balcao). Varremos os dois para não perder nada.
    for vtipo in (None, "vendas_balcao"):
        pagina = 1
        while pagina <= max_paginas:
            params = {"limite": limite, "pagina": pagina,
                      "data_inicio": data_ini, "data_fim": data_fim}
            if situacao_id:
                params["situacao_id"] = situacao_id
            if vtipo:
                params["tipo"] = vtipo
            try:
                r = _get("vendas", params=params, loja_id=loja_id)
            except Exception:
                break
            data = r.get("data", []) if isinstance(r, dict) else (r or [])
            if not data:
                break
            for v in data:
                n_pedidos += 1
                if coletar_lista:
                    lista.append({
                        "id": v.get("id", ""),
                        "codigo": v.get("codigo", ""),
                        "data": (v.get("data") or "")[:10],
                        "cliente": v.get("nome_cliente", "") or v.get("cliente_nome", ""),
                        "vendedor": v.get("nome_vendedor", ""),
                        "valor_total": float(v.get("valor_total") or 0),
                        "situacao": v.get("nome_situacao", ""),
                        "loja": v.get("nome_loja", ""),
                        "qtd_itens": len(v.get("produtos") or []),
                        "tipo": vtipo or "produto",
                    })
                for it in (v.get("produtos") or []):
                    prod = it.get("produto", it) if isinstance(it, dict) else {}
                    try:
                        qtd = float(prod.get("quantidade") or 0)
                    except (TypeError, ValueError):
                        qtd = 0.0
                    if qtd <= 0:
                        continue
                    vid = str(prod.get("variacao_id") or "")
                    # A cor vem do catálogo ('Cor / Tipo'); nas vendas o
                    # nome_produto é só o modelo (ex.: 'iPhone 16 Plus').
                    nome_cat = nome_por_vid.get(vid, "") or prod.get("nome_produto") or ""
                    n_itens += 1
                    if vid:
                        por_var[vid] = por_var.get(vid, 0) + qtd
                    cor, _ = _extrair_cor_tipo(nome_cat)
                    if cor:
                        por_cor[cor] = por_cor.get(cor, 0) + qtd
            if progress_callback:
                try:
                    progress_callback(vtipo or "produto", pagina, n_pedidos)
                except Exception:
                    pass
            meta = r.get("meta", {}) if isinstance(r, dict) else {}
            if not meta.get("proxima_pagina"):
                break
            pagina += 1

    out = {"por_variacao": por_var, "por_cor": por_cor,
           "pedidos": n_pedidos, "itens": n_itens}
    if coletar_lista:
        out["lista"] = lista
    return out


def diagnostico_vendas(dias=30, loja_id=None):
    """
    Diagnóstico rápido: quantas vendas/itens a API retornou no período para a
    loja, e amostra dos campos. Útil para depurar 'não pegou as vendas'.
    """
    from datetime import date as _date, timedelta as _td
    d_ini = str(_date.today() - _td(days=dias))
    d_fim = str(_date.today())
    out = {"loja_id": loja_id, "data_ini": d_ini, "data_fim": d_fim, "por_tipo": {}}
    nome_por_vid = _mapa_variacao_nome(loja_id)
    out["variacoes_no_catalogo_da_loja"] = len(nome_por_vid)
    for vtipo in (None, "vendas_balcao"):
        try:
            params = {"limite": 50, "pagina": 1, "data_inicio": d_ini, "data_fim": d_fim}
            if vtipo:
                params["tipo"] = vtipo
            r = _get("vendas", params=params, loja_id=loja_id)
            data = r.get("data", []) if isinstance(r, dict) else (r or [])
            meta = r.get("meta", {}) if isinstance(r, dict) else {}
            amostra = {}
            if data:
                prods = data[0].get("produtos") or []
                ex = prods[0].get("produto") if prods else None
                vid_ex = str((ex or {}).get("variacao_id") or "")
                amostra = {
                    "nome_loja": data[0].get("nome_loja"),
                    "situacao": data[0].get("nome_situacao"),
                    "qtd_produtos_na_venda": len(prods),
                    "exemplo_produto": ex,
                    "variacao_id_exemplo": vid_ex,
                    "casa_com_catalogo": vid_ex in nome_por_vid,
                    "variacao_no_catalogo": nome_por_vid.get(vid_ex, "(não encontrada — selecione a loja correta)"),
                }
            out["por_tipo"][vtipo or "produto"] = {
                "total_registros": meta.get("total_registros", len(data)),
                "amostra": amostra,
            }
        except Exception as e:
            out["por_tipo"][vtipo or "produto"] = {"erro": str(e)}
    return out


def _distribuir_quantidade(itens, total, chave="score"):
    """
    Distribui `total` unidades inteiras entre `itens` proporcionalmente a
    item[chave], usando o método do maior resto (a soma fecha exatamente em
    `total`). Itens com peso 0 só recebem sobra se ninguém mais tiver peso.
    """
    total = int(total)
    if total <= 0 or not itens:
        for it in itens:
            it["quantidade"] = 0
        return itens

    pesos = [max(0.0, float(it.get(chave, 0) or 0)) for it in itens]
    soma = sum(pesos)
    if soma <= 0:
        # Sem sinal de demanda: prioriza quem tem menor estoque POSITIVO
        # (negativo é falso, vira 0).
        ordem = sorted(range(len(itens)), key=lambda i: max(0, itens[i].get("estoque", 0)))
        base = [0] * len(itens)
        for k in range(total):
            base[ordem[k % len(ordem)]] += 1
        for it, q in zip(itens, base):
            it["quantidade"] = q
        return itens

    brutos = [total * peso / soma for peso in pesos]
    base = [int(b) for b in brutos]
    resto = total - sum(base)
    # Distribui a sobra para os maiores restos fracionários.
    ordem = sorted(range(len(itens)), key=lambda i: brutos[i] - base[i], reverse=True)
    for k in range(resto):
        base[ordem[k % len(ordem)]] += 1
    for it, q in zip(itens, base):
        it["quantidade"] = q
    return itens


def _parse_valor(v):
    """Converte '8,00' / '8.00' / 8 -> float. Inválido -> 0.0."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    if not s:
        return 0.0
    # '1.234,56' -> '1234.56' ; '8,00' -> '8.00'
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _distribuir_por_cor(itens, total):
    """
    Distribui `total` em dois níveis para garantir VARIEDADE DE CORES:
      1) reparte o total entre as CORES, proporcional às vendas de cada cor
         (cores que vendem mais levam mais — mas todas as que vendem aparecem);
      2) dentro de cada cor, reparte a cota entre os modelos pelo score.
    Cai para a distribuição simples se não houver sinal de vendas por cor.
    """
    total = int(total)
    for it in itens:
        it["quantidade"] = 0
    if total <= 0 or not itens:
        return itens

    # Agrupa por cor. O peso de cada cor é a sua POPULARIDADE no histórico
    # (vendas_cor, somando todos os modelos), com fallback para a soma das
    # vendas das variações daquela cor.
    por_cor = {}
    for it in itens:
        por_cor.setdefault(it.get("cor", ""), []).append(it)
    vendas_cor = {}
    for c, g in por_cor.items():
        pop = max((float(i.get("vendas_cor", 0) or 0) for i in g), default=0.0)
        if pop <= 0:
            pop = sum(float(i.get("vendas", 0) or 0) for i in g)
        vendas_cor[c] = pop

    if sum(vendas_cor.values()) <= 0:
        return _distribuir_quantidade(itens, total, chave="score")

    # Nível 1: cotas por cor (maior resto), ponderado pelas vendas da cor.
    cores = list(por_cor.keys())
    pesos = [vendas_cor[c] for c in cores]
    soma = sum(pesos)
    brutos = [total * p / soma for p in pesos]
    cotas = [int(b) for b in brutos]
    resto = total - sum(cotas)
    ordem = sorted(range(len(cores)), key=lambda i: brutos[i] - cotas[i], reverse=True)
    for k in range(resto):
        cotas[ordem[k % len(ordem)]] += 1

    # Nível 2: dentro de cada cor, reparte pelo score entre os modelos.
    for c, cota in zip(cores, cotas):
        if cota > 0:
            _distribuir_quantidade(por_cor[c], cota, chave="score")
    return itens


def sugerir_pedido_reposicao(quantidade_total=0, grupo=None, tipo=None, loja_id=None,
                             dias_vendas=30, usar_vendas=True, estoque_alvo=0,
                             peso_vendas=2.0, incluir_sem_pedido=False,
                             custo_base=None, orcamento=None, usar_cache_vendas=True,
                             max_por_variacao=2):
    """
    Gera uma sugestão de ordem de compra: distribui unidades de um grupo/tipo
    (ex.: 'Aveludada') entre as cores/variações, priorizando as mais vendidas
    recentemente e as que estão faltando no estoque.

    A quantidade pode ser informada diretamente (`quantidade_total`) OU
    derivada de um `orcamento` (R$) dividido pelo `custo_base` (R$/un).

    score = vendas_recentes * peso_vendas
          + deficit_para_o_alvo
          + (urgência por estoque negativo)

    Retorna {ok, itens, resumo, ...}. Cada item traz a quantidade sugerida,
    o estoque atual, as vendas no período, o custo e o estoque projetado.
    """
    custo_base = _parse_valor(custo_base)
    orcamento = _parse_valor(orcamento)
    quantidade_total = int(quantidade_total or 0)
    # Orçamento define a quantidade quando ela não foi informada diretamente.
    if quantidade_total <= 0 and orcamento > 0 and custo_base > 0:
        quantidade_total = int(orcamento // custo_base)

    variacoes = coletar_variacoes_catalogo(loja_id, grupo, tipo)
    if not variacoes:
        return {"ok": False, "erro": "Nenhuma variação encontrada para o filtro informado.",
                "itens": [], "resumo": {}}
    if quantidade_total <= 0:
        return {"ok": False, "erro": "Informe uma quantidade total ou um orçamento + custo base.",
                "itens": [], "resumo": {}}

    vendas = {"por_variacao": {}, "por_cor": {}, "pedidos": 0}
    vendas_ok = False
    vendas_fonte = ""
    if usar_vendas and quantidade_total > 0:
        # 1) Prefere o cache de vendas já sincronizado (rápido, sem bater na API).
        if usar_cache_vendas:
            cv = carregar_cache_vendas(loja_id)
            if cv and (cv.get("por_variacao") or cv.get("por_cor")):
                vendas = cv
                vendas_ok = True
                vendas_fonte = f"cache ({cv.get('sincronizado_em', '')[:10]})"
        # 2) Sem cache: consulta ao vivo.
        if not vendas_ok:
            try:
                vendas = vendas_por_variacao(dias_vendas, loja_id)
                vendas_ok = bool(vendas["por_variacao"] or vendas["por_cor"])
                vendas_fonte = "ao vivo"
            except Exception as e:
                vendas = {"por_variacao": {}, "por_cor": {}, "pedidos": 0, "erro": str(e)}

    # Quantas variações tiveram venda real pelo ID — diagnóstico de qualidade do cache.
    _por_var_cache = vendas.get("por_variacao", {})
    _por_cor_cache = vendas.get("por_cor", {})
    _matches = 0
    for it in variacoes:
        vid = it["variacao_id"]
        # Vendas REAIS desta variação específica (modelo+cor) no período.
        # Não usa fallback do agregado de cor — isso causava todas as linhas
        # mostrarem o mesmo número.
        v_var = float(_por_var_cache.get(vid, 0) or _por_var_cache.get(int(vid) if vid.isdigit() else vid, 0) or 0)
        if v_var > 0:
            _matches += 1
        # Popularidade da COR no histórico (todos os modelos) — sinal secundário
        # para sugerir cores que vendem bem nos outros modelos.
        v_cor = float(_por_cor_cache.get(it["cor"], 0) or 0)
        it["vendas"] = round(v_var, 2)
        it["vendas_cor"] = round(v_cor, 2)
        # Estoque negativo é acumulado falso de anos → trata como 0.
        est_real = max(0, it["estoque"])
        it["estoque"] = est_real
        it["deficit"] = max(0, int(estoque_alvo) - est_real)
        # Score: venda da variação (peso principal) + popularidade da cor (sinal
        # de tendência) + déficit (urgência de reposição).
        it["score"] = (v_var * float(peso_vendas)
                       + v_cor * 0.3
                       + it["deficit"])

    # Distribuição com variedade de cores quando há sinal de vendas; senão,
    # cai para a repartição simples por score (estoque/déficit).
    if vendas_ok:
        _distribuir_por_cor(variacoes, quantidade_total)
    else:
        _distribuir_quantidade(variacoes, quantidade_total, chave="score")

    # Aplica teto máximo por variação (padrão: 3 unidades), redistribuindo o
    # excesso para as próximas mais pontuadas.
    if max_por_variacao and max_por_variacao > 0:
        sobra = 0
        for it in variacoes:
            if it["quantidade"] > max_por_variacao:
                sobra += it["quantidade"] - max_por_variacao
                it["quantidade"] = max_por_variacao
        if sobra > 0:
            # Redistribui sobra em rodadas, pulando quem já atingiu o teto.
            candidatos = sorted(
                [it for it in variacoes if it["quantidade"] < max_por_variacao],
                key=lambda x: x["score"], reverse=True,
            )
            idx = 0
            while sobra > 0 and candidatos:
                it = candidatos[idx % len(candidatos)]
                if it["quantidade"] < max_por_variacao:
                    it["quantidade"] += 1
                    sobra -= 1
                idx += 1
                if idx >= len(candidatos) * max_por_variacao:
                    break  # evita loop infinito se não há mais espaço

    for it in variacoes:
        it["estoque_atual"] = it["estoque"]
        it["estoque_apos"] = it["estoque"] + it["quantidade"]
        unit = custo_base if custo_base > 0 else _parse_valor(it.get("valor_custo"))
        it["custo_unit"] = round(unit, 2)
        it["custo_total"] = round(unit * it["quantidade"], 2)
        if custo_base > 0:
            it["valor_custo"] = f"{custo_base:.2f}"

    itens = sorted(
        variacoes,
        key=lambda x: (x["quantidade"], x["score"], -x["estoque"]),
        reverse=True,
    )
    if not incluir_sem_pedido:
        itens = [it for it in itens if it["quantidade"] > 0]

    # Ranking de cores: agrega vendas por cor entre todas as variações,
    # usando a venda real por variação como base primária e a popularidade
    # de cor (por_cor do cache) como sinal de tendência geral.
    _rank_cor = {}
    for it in variacoes:
        c = it["cor"]
        if c not in _rank_cor:
            _rank_cor[c] = {"cor": c, "vendas": 0.0, "vendas_cor": it.get("vendas_cor", 0), "qtd_sugerida": 0}
        _rank_cor[c]["vendas"] += it["vendas"]
        _rank_cor[c]["qtd_sugerida"] += it["quantidade"]
    # Ordena: primeiro por vendas reais das variações, depois pela popularidade global da cor.
    ranking_cores = sorted(
        _rank_cor.values(),
        key=lambda x: (x["vendas"], x["vendas_cor"]),
        reverse=True,
    )

    aviso_match = ""
    if vendas_ok and _matches == 0:
        aviso_match = (f" ⚠️ Nenhuma variação casou com o cache de vendas "
                       f"(loja_id={loja_id}). Verifique se o cache foi sincronizado para esta loja.")

    resumo = {
        "quantidade_total": quantidade_total,
        "quantidade_distribuida": sum(it["quantidade"] for it in variacoes),
        "grupo": grupo or "",
        "tipo": tipo or "",
        "variacoes_consideradas": len(variacoes),
        "variacoes_no_pedido": len([it for it in variacoes if it["quantidade"] > 0]),
        "vendas_usadas": vendas_ok,
        "vendas_fonte": vendas_fonte,
        "pedidos_analisados": vendas.get("pedidos", 0),
        "dias_vendas": dias_vendas,
        "estoque_alvo": int(estoque_alvo),
        "custo_base": round(custo_base, 2),
        "orcamento": round(orcamento, 2),
        "custo_total": round(sum(it.get("custo_total", 0) for it in variacoes), 2),
        "matches_por_variacao": _matches,
        "ranking_cores": ranking_cores,
    }
    aviso_base = None if (vendas_ok or not usar_vendas) else \
        "Sem dados de vendas no período — a sugestão usou estoque/déficit como critério."
    return {"ok": True, "itens": itens, "resumo": resumo,
            "aviso": (aviso_base or "") + aviso_match or None}


def sugerir_pedido_ia(quantidade_total=0, grupo=None, tipo=None, loja_id=None,
                      dias_vendas=30, estoque_alvo=0, custo_base=None, orcamento=None,
                      instrucao_extra="", max_candidatos=120, max_por_variacao=2):
    """
    Versão por IA: a Claude monta a lista de compra escolhendo os MODELOS que
    mais saem e as melhores cores, respeitando a quantidade/orçamento.

    Reaproveita o motor determinístico para levantar candidatos (estoque +
    vendas) e pede à IA a alocação final. Sem ANTHROPIC_API_KEY ou em caso de
    erro, faz fallback automático para `sugerir_pedido_reposicao`.
    """
    base = sugerir_pedido_reposicao(
        quantidade_total=quantidade_total, grupo=grupo, tipo=tipo, loja_id=loja_id,
        dias_vendas=dias_vendas, usar_vendas=True, estoque_alvo=estoque_alvo,
        custo_base=custo_base, orcamento=orcamento, incluir_sem_pedido=True,
        max_por_variacao=0,  # sem cap aqui — a IA faz a distribuição final
    )
    if not base.get("ok"):
        return base

    qtd_total = base["resumo"]["quantidade_total"]
    # Candidatos: os de maior score (mais vendidos / mais em falta).
    candidatos = sorted(base["itens"], key=lambda x: x["score"], reverse=True)[:max_candidatos]

    key = _get_anthropic_key()
    if not key or not candidatos:
        base["itens"] = [it for it in base["itens"] if it["quantidade"] > 0]
        base["modo"] = "determinístico (sem chave de IA)"
        return base

    linhas = [
        f'{i}|{it["variacao_id"]}|{it["produto_nome"]} / {it["variacao_nome"]}|'
        f'estoque={it["estoque_atual"]}|vendas={it["vendas"]}'
        for i, it in enumerate(candidatos)
    ]
    prompt = (
        "Você é um comprador de uma loja de capinhas de celular. Monte a lista de "
        f"compra alocando EXATAMENTE {qtd_total} unidades no total entre as variações "
        "abaixo. Regras OBRIGATÓRIAS:\n"
        f"1. Máximo {max_por_variacao} unidades por variação (cor+modelo). NUNCA coloque mais que {max_por_variacao} na mesma variação.\n"
        "2. Priorize os MODELOS que mais saem (maior 'vendas') e as cores com menor estoque.\n"
        "3. Distribua entre MUITAS variações diferentes para ter variedade de cores — "
        "não concentre em poucas. Para vender capas é preciso ter várias opções de cor.\n"
        "4. Pode deixar variações com 0 se necessário.\n"
        + (f"Instrução adicional do usuário: {instrucao_extra}\n" if instrucao_extra else "")
        + "\nVariações (idx|variacao_id|nome|estoque|vendas):\n" + "\n".join(linhas)
        + '\n\nResponda APENAS com JSON: {"itens":[{"variacao_id":"...","quantidade":N}, ...]}. '
        f"A soma das quantidades deve ser exatamente {qtd_total}."
    )
    try:
        import anthropic as _ant
        import json as _json, re as _re
        client = _ant.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-opus-4-8", max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        m = _re.search(r"\{.*\}", txt, _re.S)
        aloc = _json.loads(m.group(0))["itens"] if m else []
    except Exception as e:
        base["itens"] = [it for it in base["itens"] if it["quantidade"] > 0]
        base["modo"] = "determinístico (IA indisponível)"
        base["aviso"] = (base.get("aviso") or "") + f" IA indisponível: {e}".strip()
        return base

    por_id = {it["variacao_id"]: it for it in base["itens"]}
    for it in base["itens"]:
        it["quantidade"] = 0
    for a in aloc:
        vid = str(a.get("variacao_id", ""))
        try:
            q = int(a.get("quantidade", 0) or 0)
        except (TypeError, ValueError):
            q = 0
        if vid in por_id and q > 0:
            por_id[vid]["quantidade"] = q

    cb = base["resumo"].get("custo_base", 0) or 0
    for it in base["itens"]:
        it["estoque_apos"] = it["estoque_atual"] + it["quantidade"]
        unit = cb if cb > 0 else _parse_valor(it.get("valor_custo"))
        it["custo_unit"] = round(unit, 2)
        it["custo_total"] = round(unit * it["quantidade"], 2)

    # Garante teto máximo mesmo que a IA ignore a instrução.
    if max_por_variacao and max_por_variacao > 0:
        sobra = 0
        for it in base["itens"]:
            if it["quantidade"] > max_por_variacao:
                sobra += it["quantidade"] - max_por_variacao
                it["quantidade"] = max_por_variacao
        if sobra > 0:
            candidatos_cap = sorted(
                [it for it in base["itens"] if it["quantidade"] < max_por_variacao],
                key=lambda x: x["score"], reverse=True,
            )
            idx = 0
            while sobra > 0 and candidatos_cap:
                it = candidatos_cap[idx % len(candidatos_cap)]
                if it["quantidade"] < max_por_variacao:
                    it["quantidade"] += 1
                    sobra -= 1
                idx += 1
                if idx >= len(candidatos_cap) * max_por_variacao:
                    break

    itens = sorted([it for it in base["itens"] if it["quantidade"] > 0],
                   key=lambda x: (x["quantidade"], x["score"]), reverse=True)
    dist = sum(it["quantidade"] for it in itens)
    base["itens"] = itens
    base["modo"] = "IA"
    base["resumo"]["quantidade_distribuida"] = dist
    base["resumo"]["variacoes_no_pedido"] = len(itens)
    base["resumo"]["custo_total"] = round(sum(it["custo_total"] for it in itens), 2)
    if dist != qtd_total:
        base["aviso"] = (f"A IA alocou {dist} de {qtd_total} un. "
                         "Ajuste as quantidades na tabela se necessário.")
    return base


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
# Helpers de chave de API
# ──────────────────────────────────────────────
def _get_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        try:
            import streamlit as _st
            key = _st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
    return key


# ──────────────────────────────────────────────
# Parse de pedido via IA (Claude)
# ──────────────────────────────────────────────
def parse_pedido_whatsapp(texto: str, catalogo_resumo: str) -> list[dict]:
    """
    Envia o texto colado do WhatsApp para o Claude e retorna
    lista de dicts: [{modelo, variacao, quantidade, observacao}]
    """
    import anthropic as _ant
    client = _ant.Anthropic(api_key=_get_anthropic_key())

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


# ──────────────────────────────────────────────
# Armazenamento de fotos de entrada (90 dias)
# ──────────────────────────────────────────────
_FOTOS_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_entrada")
_FOTOS_INDEX = os.path.join(_FOTOS_DIR, "index.json")
_FOTOS_DIAS  = 90


def _fotos_index_load() -> list:
    if not os.path.exists(_FOTOS_INDEX):
        return []
    with open(_FOTOS_INDEX, encoding="utf-8") as f:
        return json.load(f)


def _fotos_index_save(index: list):
    os.makedirs(_FOTOS_DIR, exist_ok=True)
    with open(_FOTOS_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def salvar_foto_entrada(img_bytes: bytes, usuario: str, nome_usuario: str,
                        loja_id: str, loja_nome: str, itens_detectados: list) -> str:
    """Salva foto em disco e registra no índice. Remove entradas com +90 dias.
    Retorna o nome do arquivo salvo."""
    import uuid as _uuid
    os.makedirs(_FOTOS_DIR, exist_ok=True)
    ts       = datetime.now()
    filename = f"{ts.strftime('%Y%m%d_%H%M%S')}_{usuario}_{_uuid.uuid4().hex[:6]}.jpg"
    with open(os.path.join(_FOTOS_DIR, filename), "wb") as f:
        f.write(img_bytes)

    index  = _fotos_index_load()
    cutoff = (datetime.now() - timedelta(days=_FOTOS_DIAS)).isoformat()
    validas = []
    for e in index:
        if e.get("timestamp", "") >= cutoff:
            validas.append(e)
        else:
            try:
                os.remove(os.path.join(_FOTOS_DIR, e["filename"]))
            except OSError:
                pass
    validas.append({
        "filename":        filename,
        "timestamp":       ts.isoformat(),
        "usuario":         usuario,
        "nome_usuario":    nome_usuario,
        "loja_id":         loja_id,
        "loja_nome":       loja_nome,
        "itens_detectados": itens_detectados,
    })
    _fotos_index_save(validas)
    return filename


def listar_fotos_entrada() -> list:
    """Retorna fotos dos últimos 90 dias, mais recentes primeiro."""
    cutoff = (datetime.now() - timedelta(days=_FOTOS_DIAS)).isoformat()
    return sorted(
        [e for e in _fotos_index_load() if e.get("timestamp","") >= cutoff],
        key=lambda x: x.get("timestamp",""), reverse=True
    )


def carregar_foto_entrada(filename: str) -> bytes | None:
    """Retorna bytes da foto ou None se não encontrada."""
    path = os.path.join(_FOTOS_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def ler_codigo_barras_foto(img_bytes: bytes, media_type: str = "image/jpeg") -> str | None:
    """
    Usa Claude Opus 4.8 Vision para ler o código de barras de uma etiqueta.
    Retorna o código como string ou None se não encontrado.
    """
    import anthropic as _ant, base64 as _b64
    key = _get_anthropic_key()
    if not key:
        raise ValueError("ANTHROPIC_API_KEY não configurado em .streamlit/secrets.toml")
    client = _ant.Anthropic(api_key=key)
    img_b64 = _b64.b64encode(img_bytes).decode()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                {"type": "text", "text": (
                    "Look at this product label image. "
                    "Extract the barcode number (EAN, Code128, or any numeric code on the label). "
                    "Return ONLY the code digits/characters, nothing else. "
                    "If no barcode or readable code is visible, return exactly: null"
                )},
            ]
        }]
    )
    result = msg.content[0].text.strip()
    if result.lower() in ("null", "none", ""):
        return None
    # strip any stray whitespace/punctuation the model might add
    import re as _re
    m = _re.search(r"[A-Za-z0-9\-]{4,}", result)
    return m.group() if m else None


def decodificar_barcodes_foto(img_bytes: bytes) -> list[str]:
    """Decodifica códigos de barras (Code 128 alfanumérico e outros) via pyzbar/libzbar."""
    from PIL import Image as _PILImage, ImageEnhance as _IE, ImageFilter as _IF
    import io as _io

    base = _PILImage.open(_io.BytesIO(img_bytes)).convert("RGB")

    def _pyzbar(img):
        try:
            from pyzbar.pyzbar import decode as _pyz_decode
            results = _pyz_decode(img)
            return [r.data.decode("utf-8", errors="ignore") for r in results if r.data]
        except Exception:
            return []

    def _zxing(img):
        try:
            import zxingcpp as _zx
            import numpy as _np
            results = _zx.read_barcodes(_np.array(img))
            return [x.text for x in results if x.text]
        except Exception:
            return []

    def _try(img):
        found = _pyzbar(img)
        if found:
            return found
        return _zxing(img)

    # 1. Original
    found = _try(base)
    if found: return found

    # 2. Escala de cinza + contraste alto (ajuda barcodes impressos)
    gray = base.convert("L")
    hi   = _IE.Contrast(gray).enhance(2.5).convert("RGB")
    found = _try(hi)
    if found: return found

    # 3. Nitidez + contraste
    sharp = _IE.Contrast(gray).enhance(2.0).filter(_IF.SHARPEN).convert("RGB")
    found = _try(sharp)
    if found: return found

    # 4. Upscale 2× (ajuda barcodes pequenos na foto)
    big = base.resize((base.width * 2, base.height * 2), _PILImage.LANCZOS)
    found = _try(big)
    if found: return found

    # 5. Crop central horizontal (foca a área onde geralmente está o barcode)
    w, h = base.width, base.height
    crop = base.crop((int(w * 0.05), int(h * 0.3), int(w * 0.95), int(h * 0.7)))
    found = _try(crop)
    if found: return found

    return []


# ──────────────────────────────────────────────
# Leitura de etiquetas por foto (Claude Vision)
# ──────────────────────────────────────────────
def ler_etiquetas_foto(img_bytes: bytes, catalogo_resumo: str,
                       media_type: str = "image/jpeg") -> list[dict]:
    """
    Envia foto de capas ao Claude Vision e retorna as etiquetas lidas.
    Retorna lista de dicts:
      [{cod_interno, variacao_nome, variacao_cod, codigo_barras, quantidade, confianca}]
    """
    import anthropic as _ant, base64 as _b64, json, re
    _key = _get_anthropic_key()
    client = _ant.Anthropic(api_key=_key)

    prompt = f"""Você é assistente de uma loja de capinhas para celular no Brasil.
Nesta foto há uma ou mais capas de celular com etiquetas coladas.

Catálogo disponível (cod_interno | nome do produto):
{catalogo_resumo}

Para CADA etiqueta visível na foto extraia:
- cod_interno: código do produto (ex: G54, A54, EDGE70FUSION, iPhone16). Busque o mais próximo no catálogo.
- variacao_nome: a variação/cor escrita na etiqueta (ex: "Preto / Aveludada", "Roxo / Aveludada", "Preto / Space 2")
- variacao_cod: código alfanumérico da variação se houver (campo separado do produto)
- codigo_barras: o número do código de barras se legível na etiqueta
- quantidade: 1 por padrão, a menos que a etiqueta indique outra quantidade
- confianca: "alta" se leu claramente, "media" se aproximou, "baixa" se incerto

Retorne SOMENTE um JSON válido, sem markdown, sem explicações:
[{{"cod_interno":"...","variacao_nome":"...","variacao_cod":null,"codigo_barras":null,"quantidade":1,"confianca":"alta"}}]"""

    img_b64 = _b64.b64encode(img_bytes).decode()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                {"type": "text", "text": prompt},
            ]
        }]
    )
    raw = msg.content[0].text.strip()
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if m:
        return json.loads(m.group())
    return json.loads(raw)


# ──────────────────────────────────────────────
# Transcrição de áudio via OpenAI Whisper
# ──────────────────────────────────────────────
def _get_openai_key() -> str:
    """Lê OPENAI_API_KEY de os.environ ou, se rodando no Streamlit, de st.secrets."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        try:
            import streamlit as _st
            key = _st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass
    return key


def transcrever_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcreve áudio usando OpenAI Whisper API.
    Requer OPENAI_API_KEY em os.environ ou .streamlit/secrets.toml.
    Retorna o texto transcrito.
    """
    import requests as _req, re as _re
    api_key = _get_openai_key()
    if not api_key or api_key.startswith("sk-..."):
        raise ValueError("OPENAI_API_KEY não configurado. Preencha .streamlit/secrets.toml.")

    # Prompt de domínio reduz alucinações do Whisper
    _prompt_dominio = (
        "Samsung, iPhone, Motorola, Xiaomi, Poco, Redmi, Edge, Aveludada, Silicone, "
        "Masculino, Feminino, Brilho, Diversos, MagSafe, Space 2, Preta, Branca, "
        "Roxa, Amarela, Azul Marinho, Cinza Chumbo, Lilás, Marsala, Vinho, Nude, "
        "Very Rio, Carteira, Película, Transparente, pacote, quantidade"
    )

    resp = _req.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (filename, audio_bytes, "audio/webm")},
        data={"model": "whisper-1", "language": "pt", "prompt": _prompt_dominio},
        timeout=60,
    )
    resp.raise_for_status()
    texto = resp.json().get("text", "").strip()

    # Detecta alucinações comuns do Whisper (silêncio / ruído)
    _alucinacoes = [
        r"intervoices", r"legendas", r"subtitle", r"subtitles",
        r"www\.", r"http", r"\.com", r"transcri\w+ por",
        r"amara\.org", r"dotsub", r"subsvip",
    ]
    if not texto or any(_re.search(p, texto, _re.I) for p in _alucinacoes):
        raise ValueError(
            "Whisper não detectou fala clara no áudio. "
            "Verifique se o microfone está funcionando e tente novamente."
        )
    return texto


# ──────────────────────────────────────────────
# Situações
# ──────────────────────────────────────────────

def buscar_situacoes_compras():
    r = _get("situacoescompras")
    dados = r.get("data", r) if isinstance(r, dict) else r
    return dados if isinstance(dados, list) else []

def buscar_situacoes_vendas():
    r = _get("situacoesvendas")
    dados = r.get("data", r) if isinstance(r, dict) else r
    return dados if isinstance(dados, list) else []

def buscar_situacoes_orcamentos():
    r = _get("situacoesorcamentos")
    dados = r.get("data", r) if isinstance(r, dict) else r
    return dados if isinstance(dados, list) else []


# ──────────────────────────────────────────────
# Funcionários
# ──────────────────────────────────────────────

def buscar_funcionarios(termo="", limite=100):
    params = {"limite": limite}
    if termo:
        params["nome"] = termo
    r = _get("funcionarios", params=params)
    dados = r.get("data", r) if isinstance(r, dict) else r
    return dados if isinstance(dados, list) else []


# ──────────────────────────────────────────────
# CRUD Clientes
# ──────────────────────────────────────────────

def criar_cliente(dados):
    return _post("clientes", dados)

def atualizar_cliente(cliente_id, dados):
    return _put(f"clientes/{cliente_id}", dados)

def excluir_cliente(cliente_id):
    return _delete(f"clientes/{cliente_id}")


# ──────────────────────────────────────────────
# CRUD Fornecedores
# ──────────────────────────────────────────────

def criar_fornecedor(dados):
    return _post("fornecedores", dados)

def atualizar_fornecedor(fornecedor_id, dados):
    return _put(f"fornecedores/{fornecedor_id}", dados)

def excluir_fornecedor(fornecedor_id):
    return _delete(f"fornecedores/{fornecedor_id}")


# ──────────────────────────────────────────────
# Detalhes de compra
# ──────────────────────────────────────────────

def buscar_compra(compra_id, loja_id=None):
    r = _get(f"pedidoscompras/{compra_id}", loja_id=loja_id)
    return r.get("data", r) if isinstance(r, dict) else r


def get_compra(compra_id, loja_id=None):
    """GET /compras/{id} — retorna a resposta crua da API (para conferência)."""
    return _get(f"compras/{compra_id}", loja_id=loja_id)


def buscar_compra_por_codigo(codigo, loja_id=None):
    """GET /compras?codigo=X — busca pelo número visível no sistema (campo codigo).
    Retorna o primeiro resultado ou None.
    """
    r = _get("compras", params={"codigo": str(codigo)}, loja_id=loja_id)
    data = r.get("data", []) if isinstance(r, dict) else []
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    return None


# ──────────────────────────────────────────────
# Registrar compra no GestãoClick
# ──────────────────────────────────────────────

def registrar_compra_gestaoclick(itens, fornecedor_id, data_emissao, situacao_id,
                                  observacoes="", loja_id=None):
    """
    Cria um pedido de compra no GestãoClick a partir de itens do pedido local.
    Apenas itens com produto_id + variacao_id são incluídos.
    """
    import time as _t
    codigo = str(int(_t.time()) % 100000)

    produtos = []
    for item in itens:
        if not item.get("produto_id") or not item.get("variacao_id"):
            continue
        custo_raw = item.get("valor_custo", "") or "0.00"
        try:
            custo = f"{float(str(custo_raw).replace(',', '.')):.2f}"
        except (TypeError, ValueError):
            custo = "0.00"
        produtos.append({
            "produto_id": str(item["produto_id"]),
            "variacao_id": str(item["variacao_id"]),
            "nome_produto": item.get("produto_nome", ""),
            "quantidade": str(int(item.get("quantidade", 1))),
            "valor_custo": custo,
        })

    if not produtos:
        raise ValueError("Nenhum item cadastrado no sistema (com produto_id/variacao_id) para registrar.")

    body = {
        "codigo": codigo,
        "fornecedor_id": str(fornecedor_id),
        "situacao_id": str(situacao_id),
        "data_emissao": str(data_emissao),
        "observacoes": observacoes,
        "produtos": produtos,
    }

    return _post("pedidoscompras", body, loja_id=loja_id)


# ──────────────────────────────────────────────
# Aprovação de entradas
# ──────────────────────────────────────────────
APROVACOES_FILE = os.path.join(DIR, "entradas_aprovacao.json")

def _aprovacoes_load() -> list:
    if not os.path.exists(APROVACOES_FILE):
        _gh_baixar_arquivo("entradas_aprovacao.json", APROVACOES_FILE)
    if not os.path.exists(APROVACOES_FILE):
        return []
    with open(APROVACOES_FILE, encoding="utf-8") as f:
        return json.load(f)

def _aprovacoes_save(dados: list):
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(APROVACOES_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("entradas_aprovacao.json", conteudo, "Atualiza aprovações de entrada")

def salvar_entrada_para_aprovacao(itens: list, usuario: str, nome_usuario: str,
                                   loja_id: str, loja_nome: str, obs: str = "") -> str:
    import uuid as _uuid
    entrada_id = f"ent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_uuid.uuid4().hex[:6]}"
    dados = _aprovacoes_load()
    dados.append({
        "id": entrada_id,
        "criado_em": datetime.now().isoformat(),
        "criado_por": usuario,
        "nome_criador": nome_usuario,
        "loja_id": loja_id,
        "loja_nome": loja_nome,
        "itens": itens,
        "status": "aguardando",
        "obs_envio": obs,
        "aprovado_por": None,
        "nome_aprovador": None,
        "aprovado_em": None,
        "obs_aprovacao": "",
        "lido_por": [],
    })
    _aprovacoes_save(dados)
    return entrada_id

def listar_entradas_aprovacao(status: str = None) -> list:
    dados = _aprovacoes_load()
    if status:
        return [d for d in dados if d.get("status") == status]
    return sorted(dados, key=lambda x: x.get("criado_em",""), reverse=True)

def marcar_entrada_lida(entrada_id: str, usuario: str):
    dados = _aprovacoes_load()
    for d in dados:
        if d["id"] == entrada_id:
            lidos = d.get("lido_por") or []
            if usuario not in lidos:
                lidos.append({"usuario": usuario, "em": datetime.now().isoformat()})
                d["lido_por"] = lidos
            break
    _aprovacoes_save(dados)

def aprovar_entrada_pendente(entrada_id: str, aprovador: str, nome_aprovador: str,
                              aprovado: bool, obs: str = "") -> dict:
    dados = _aprovacoes_load()
    for d in dados:
        if d["id"] == entrada_id:
            d["status"]         = "aprovado" if aprovado else "rejeitado"
            d["aprovado_por"]   = aprovador
            d["nome_aprovador"] = nome_aprovador
            d["aprovado_em"]    = datetime.now().isoformat()
            d["obs_aprovacao"]  = obs
            _aprovacoes_save(dados)
            return d
    return {}

def verificar_api_gestaoclick() -> dict:
    try:
        import time as _t
        t0 = _t.time()
        _get("produtos", params={"limite": 1, "pagina": 1})
        ms = int((_t.time() - t0) * 1000)
        return {"ok": True, "ms": ms, "msg": f"API respondeu em {ms}ms"}
    except Exception as ex:
        return {"ok": False, "ms": None, "msg": str(ex)}

def importar_nfe_xml(xml_bytes: bytes, cache: dict) -> list:
    import xml.etree.ElementTree as _ET
    import re as _re
    try:
        root = _ET.fromstring(xml_bytes)
    except Exception as ex:
        raise ValueError(f"XML inválido: {ex}")
    _NS = "http://www.portalfiscal.inf.br/nfe"
    def _txt(el, tag):
        v = el.find(f"{{{_NS}}}{tag}")
        return v.text.strip() if v is not None and v.text else ""
    produtos_cache = cache.get("produtos", [])
    def _buscar(desc):
        desc_l = desc.lower()
        tokens = [t for t in _re.split(r'\s+', desc_l) if len(t) > 2]
        melhor, melhor_score, melhor_var = None, 0, None
        for p in produtos_cache:
            p_nome_l = (p.get("nome") or "").lower()
            score = sum(t in p_nome_l for t in tokens)
            if score > melhor_score:
                melhor_score = score
                melhor = p
                melhor_var = None
                for v in p.get("variacoes", []):
                    vd = v["variacao"]
                    if sum(t in (vd.get("nome","")).lower() for t in tokens) > 0:
                        melhor_var = vd
                        break
        return (melhor, melhor_var) if melhor_score >= 2 else (None, None)
    itens = []
    for det in root.iter(f"{{{_NS}}}det"):
        prod_el = det.find(f"{{{_NS}}}prod")
        if prod_el is None:
            continue
        desc = _txt(prod_el, "xProd")
        try:
            qtd = int(float(_txt(prod_el, "qCom").replace(",",".")))
        except ValueError:
            qtd = 1
        try:
            vunit = float(_txt(prod_el, "vUnCom").replace(",","."))
        except ValueError:
            vunit = 0.0
        prod, var = _buscar(desc)
        itens.append({
            "produto_id":    prod["id"] if prod else "",
            "produto_nome":  prod["nome"] if prod else desc,
            "cod_interno":   prod.get("codigo_interno","") if prod else "",
            "variacao_id":   var["id"] if var else "",
            "variacao_cod":  var.get("codigo","") if var else "",
            "variacao_nome": var.get("nome","") if var else "",
            "quantidade":    qtd,
            "valor_custo":   f"{vunit:.2f}",
            "_nfe_desc":     desc,
            "_matched":      prod is not None,
        })
    return itens

def parse_entrada_whatsapp(texto: str, catalogo_resumo: str) -> list:
    import anthropic as _ant
    client = _ant.Anthropic(api_key=_get_anthropic_key())
    prompt = f"""Você é assistente de estoque de uma loja de capinhas para celular no Brasil.
O usuário descreve produtos que CHEGARAM (entrada de mercadoria).
Para cada produto/variação identificado, retorne o código do catálogo, variação e quantidade.

Catálogo (cod_interno | nome):
{catalogo_resumo}

Mensagem recebida:
{texto}

Retorne APENAS JSON válido:
[{{"cod_interno":"G54","variacao_nome":"Aveludada Preta","quantidade":3,"confianca":"alta"}}]
- quantidade padrão = 1
- se não encontrar no catálogo, use cod_interno null
- retorne só o JSON, sem explicações"""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role":"user","content":prompt}]
    )
    import json as _j, re as _re
    raw = msg.content[0].text
    m = _re.search(r'\[.*\]', raw, _re.DOTALL)
    if m:
        return _j.loads(m.group())
    return _j.loads(raw)


# ──────────────────────────────────────────────
# Sistema de Notificações
# ──────────────────────────────────────────────

NOTIFICACOES_FILE = os.path.join(DIR, "notificacoes.json")

def _notif_load() -> list:
    if not os.path.exists(NOTIFICACOES_FILE):
        _gh_baixar_arquivo("notificacoes.json", NOTIFICACOES_FILE)
    if not os.path.exists(NOTIFICACOES_FILE):
        return []
    with open(NOTIFICACOES_FILE, encoding="utf-8") as f:
        return json.load(f)

def _notif_save(dados: list):
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(NOTIFICACOES_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _gh_push_arquivo("notificacoes.json", conteudo, "Atualiza notificações")

def criar_notificacao(para_usuarios: list, tipo: str, titulo: str, corpo: str,
                       pagina: str = "", de_usuario: str = "sistema") -> list:
    import uuid as _uuid_notif
    dados = _notif_load()
    ids = []
    for u in para_usuarios:
        nid = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_uuid_notif.uuid4().hex[:4]}"
        dados.append({
            "id": nid,
            "para": u,
            "de": de_usuario,
            "tipo": tipo,
            "titulo": titulo,
            "corpo": corpo,
            "pagina": pagina,
            "lida": False,
            "criada_em": datetime.now().isoformat(),
        })
        ids.append(nid)
    _notif_save(dados)
    return ids

def listar_notificacoes(usuario: str) -> list:
    dados = _notif_load()
    return sorted(
        [d for d in dados if d.get("para") == usuario],
        key=lambda x: x.get("criada_em", ""), reverse=True
    )

def marcar_notificacao_lida(notif_id: str, usuario: str):
    dados = _notif_load()
    for d in dados:
        if d["id"] == notif_id and d.get("para") == usuario:
            d["lida"] = True
            break
    _notif_save(dados)

def marcar_todas_lidas(usuario: str):
    dados = _notif_load()
    for d in dados:
        if d.get("para") == usuario:
            d["lida"] = True
    _notif_save(dados)

def contar_nao_lidas(usuario: str) -> int:
    dados = _notif_load()
    return sum(1 for d in dados if d.get("para") == usuario and not d.get("lida"))

def usuarios_com_permissao(permissao: str, usuarios_db: dict, setores_db: dict) -> list:
    result = []
    for login, ud in usuarios_db.items():
        setor = ud.get("setor", "vendas")
        if setor == "admin":
            result.append(login)
            continue
        setor_cfg = setores_db.get(setor, {})
        if permissao in setor_cfg.get("paginas", []):
            result.append(login)
    return result


# ──────────────────────────────────────────────
# Importar funcionários como usuários
# ──────────────────────────────────────────────

def _normalizar_login(nome: str) -> str:
    import unicodedata as _ud
    nome_norm = _ud.normalize("NFD", nome).encode("ascii", "ignore").decode()
    return nome_norm.strip().lower().split()[0] if nome_norm.strip() else "usuario"

# ──────────────────────────────────────────────
# Rascunho de Pedido (persiste entre sessões)
# ──────────────────────────────────────────────

def _rascunho_ped_path(user: str) -> str:
    return os.path.join(DIR, f"pedido_rascunho_{user}.json")

def salvar_rascunho_pedido(user: str, dados: dict):
    import threading
    path = _rascunho_ped_path(user)
    payload = {"user": user, "salvo_em": datetime.now().isoformat(), **dados}
    conteudo = json.dumps(payload, ensure_ascii=False, default=str)
    with open(path, "w", encoding="utf-8") as f:
        f.write(conteudo)
    def _push():
        _gh_push_arquivo(f"pedido_rascunho_{user}.json", conteudo, f"Rascunho pedido {user}")
    threading.Thread(target=_push, daemon=True).start()

def carregar_rascunho_pedido(user: str) -> dict | None:
    path = _rascunho_ped_path(user)
    if not os.path.exists(path):
        _gh_baixar_arquivo(f"pedido_rascunho_{user}.json", path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def limpar_rascunho_pedido(user: str):
    import threading
    path = _rascunho_ped_path(user)
    if os.path.exists(path):
        os.remove(path)
    threading.Thread(target=lambda: _gh_delete_arquivo(f"pedido_rascunho_{user}.json"), daemon=True).start()


def criar_usuarios_funcionarios(usuarios_db: dict) -> dict:
    funcs = buscar_funcionarios(limite=200)
    criados = []
    ja_existem = []
    for f in funcs:
        nome = f.get("nome") or f.get("fantasia") or ""
        if not nome:
            continue
        login = _normalizar_login(nome)
        primeiro_nome = nome.strip().split()[0]
        senha = _normalizar_login(primeiro_nome) + "123"
        if login in usuarios_db:
            ja_existem.append(login)
        else:
            usuarios_db[login] = {
                "nome": nome,
                "senha": senha,
                "setor": "vendas",
                "primeiro_acesso": True,
            }
            criados.append({"login": login, "nome": nome, "senha": senha})
    return {"criados": criados, "ja_existem": ja_existem}
