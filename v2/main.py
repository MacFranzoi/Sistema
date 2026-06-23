"""
Sistema Plug 2.0 — Backend FastAPI
===================================
Camada REST fina que expõe o api.py existente como endpoints JSON.
NÃO contém lógica de negócio — só recebe pedidos, chama o api.py e devolve JSON.

Roda em paralelo ao sistema Streamlit atual, reaproveitando 100% do api.py,
os mesmos caches e a mesma persistência via GitHub.
"""
import os
import sys

# Reaproveita o api.py da raiz do repositório (uma pasta acima)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import api  # noqa: E402

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query  # noqa: E402
from fastapi.responses import JSONResponse, FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="Plug ERP 2.0", docs_url="/api/docs")

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_COOKIE = "plug_sessao"

# ── Estrutura do menu (espelha o sistema atual) ──────────────────────────────
# (id, ícone, rótulo, categoria)
MENU = [
    ("dashboard",       "🏠", "Dashboard",            "GERAL"),
    ("clientes",        "👥", "Clientes",             "CADASTROS"),
    ("fornecedores",    "🏭", "Fornecedores",         "CADASTROS"),
    ("novo_modelo",     "➕", "Novo Produto",         "ITENS"),
    ("clonar_modelo",   "🔁", "Clonar Produto",       "ITENS"),
    ("precos",          "💰", "Tabela de Preços",     "ITENS"),
    ("vendas",          "🧾", "Vendas",               "VENDAS"),
    ("orcamentos",      "📋", "Orçamentos",           "VENDAS"),
    ("entrada",         "📥", "Entrada",              "ESTOQUE"),
    ("acerto",          "🔧", "Acerto",               "ESTOQUE"),
    ("estoque_loja",    "🏪", "Por Loja",             "ESTOQUE"),
    ("disponibilidade", "🔘", "Disponibilidade",      "ESTOQUE"),
    ("etiquetas",       "🏷️", "Etiquetas",            "ESTOQUE"),
    ("aprovacoes",      "✅", "Aprovações",           "ESTOQUE"),
    ("pedido",          "🛒", "Pedido de Compra",     "COMPRAS"),
    ("compras_hist",    "📦", "Histórico de Compras", "COMPRAS"),
    ("financeiro",      "💳", "Financeiro",           "FINANCEIRO"),
    ("relatorios",      "📊", "Relatórios",           "RELATÓRIOS"),
    ("rel_estoque",     "📦", "Rel. Estoque",         "RELATÓRIOS"),
    ("sincronizacao",   "🔄", "Sincronização",        "CONFIGURAÇÕES"),
    ("listas",          "📋", "Listas",               "CONFIGURAÇÕES"),
    ("usuarios",        "👤", "Usuários",             "CONFIGURAÇÕES"),
]

CAT_ICONS = {
    "GERAL": "🏠", "CADASTROS": "👥", "ITENS": "🏷️", "VENDAS": "🧾",
    "ESTOQUE": "📦", "COMPRAS": "🛒", "FINANCEIRO": "💳",
    "RELATÓRIOS": "📊", "CONFIGURAÇÕES": "⚙️",
}


# ── Autenticação por cookie ──────────────────────────────────────────────────
def usuario_atual(request: Request) -> str:
    """Lê o cookie de sessão e valida. Lança 401 se inválido."""
    token = request.cookies.get(_COOKIE, "")
    user = api.validar_sessao(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def paginas_do_usuario(user: str) -> list:
    """Retorna a lista de páginas que o usuário (pelo seu setor) pode ver."""
    usuarios = api.carregar_usuarios()
    setor = usuarios.get(user, {}).get("setor", "vendas")
    setores = api.carregar_setores()
    return setores.get(setor, {}).get("paginas", [])


def admin_atual(request: Request) -> str:
    """Como usuario_atual, mas exige que o usuário seja do setor admin."""
    user = usuario_atual(request)
    usuarios = api.carregar_usuarios()
    if usuarios.get(user, {}).get("setor") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return user


# ── Modelos de entrada ───────────────────────────────────────────────────────
class LoginIn(BaseModel):
    usuario: str
    senha: str


# ── Rotas de autenticação ────────────────────────────────────────────────────
@app.post("/api/login")
def login(dados: LoginIn, response: Response):
    u = (dados.usuario or "").strip().lower()
    usuarios = api.carregar_usuarios()
    if u in usuarios and usuarios[u].get("senha") == dados.senha:
        token = api.criar_sessao(u)
        response.set_cookie(
            _COOKIE, token,
            httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30, path="/",
        )
        return {"ok": True, "usuario": u, "nome": usuarios[u].get("nome", u)}
    raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")


@app.post("/api/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(_COOKIE, "")
    if token:
        api.revogar_sessao(token)
    response.delete_cookie(_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/me")
def me(request: Request):
    user = usuario_atual(request)
    usuarios = api.carregar_usuarios()
    info = usuarios.get(user, {})
    paginas = paginas_do_usuario(user)
    menu = [
        {"id": m[0], "icone": m[1], "rotulo": m[2], "categoria": m[3]}
        for m in MENU if m[0] in paginas
    ]
    return {
        "usuario": user,
        "nome": info.get("nome", user),
        "setor": info.get("setor", "vendas"),
        "paginas": paginas,
        "menu": menu,
        "cat_icones": CAT_ICONS,
    }


# ── Rotas de dados ───────────────────────────────────────────────────────────
@app.get("/api/lojas")
def lojas(request: Request):
    usuario_atual(request)
    return {"lojas": [{"id": lid, "nome": nome} for lid, nome in api.LOJAS.items()]}


@app.get("/api/dashboard")
def dashboard(request: Request):
    usuario_atual(request)
    cards = []
    for lid, nome in api.LOJAS.items():
        cache = api.carregar_cache(lid)
        cards.append({
            "loja_id": lid,
            "nome": nome,
            "total": (cache or {}).get("total", 0),
            "sincronizado_em": (cache or {}).get("sincronizado_em", ""),
            "online": bool(cache),
        })
    cache_geral = api.carregar_cache(None)
    return {
        "lojas": cards,
        "total_catalogo": (cache_geral or {}).get("total", 0),
        "qtd_lojas": len(api.LOJAS),
    }


def _simplificar_produto(p: dict) -> dict:
    """Reduz um produto da GestãoClick ao essencial para a tela de estoque."""
    variacoes = []
    for v in p.get("variacoes", []) or []:
        vd = v.get("variacao", {}) if isinstance(v, dict) else {}
        if vd:
            variacoes.append({
                "id": vd.get("id", ""),
                "codigo": vd.get("codigo", ""),
                "nome": vd.get("nome", ""),
                "estoque": vd.get("estoque", 0),
            })
    return {
        "id": p.get("id", ""),
        "nome": p.get("nome", ""),
        "codigo_interno": p.get("codigo_interno", ""),
        "grupo": p.get("nome_grupo", ""),
        "estoque": p.get("estoque", 0),
        "valor_venda": p.get("valor_venda", ""),
        "variacoes": variacoes,
    }


@app.get("/api/estoque")
def estoque(
    request: Request,
    loja: str = Query(default=""),
    nome: str = Query(default=""),
    codigo: str = Query(default=""),
):
    usuario_atual(request)
    loja_id = loja or None
    dados = api.buscar_estoque_ao_vivo(
        loja_id=loja_id,
        nome=nome or None,
        codigo=codigo or None,
    )
    produtos = [_simplificar_produto(p) for p in dados.get("produtos", [])]
    return {"produtos": produtos, "total": len(produtos), "ao_vivo": True}


# ── Clientes ─────────────────────────────────────────────────────────────────
@app.get("/api/clientes")
def clientes(
    request: Request,
    termo: str = Query(default=""),
    pagina: int = Query(default=1),
):
    usuario_atual(request)
    dados = api.buscar_clientes(termo=termo, pagina=pagina, limite=50)
    if isinstance(dados, dict):
        items = dados.get("data", dados.get("clientes", []))
    else:
        items = dados or []
    def _simplificar_cliente(c):
        if isinstance(c, dict) and "cliente" in c:
            c = c["cliente"]
        return {
            "id": c.get("id", ""),
            "nome": c.get("nome", ""),
            "cpf_cnpj": c.get("cpf_cnpj", "") or c.get("cnpj", "") or c.get("cpf", ""),
            "email": c.get("email", ""),
            "telefone": c.get("fone", "") or c.get("celular", ""),
            "cidade": c.get("cidade", ""),
        }
    return {"clientes": [_simplificar_cliente(c) for c in items if isinstance(c, dict)], "pagina": pagina}


# ── Fornecedores ──────────────────────────────────────────────────────────────
@app.get("/api/fornecedores")
def fornecedores(
    request: Request,
    termo: str = Query(default=""),
    pagina: int = Query(default=1),
):
    usuario_atual(request)
    dados = api.buscar_fornecedores(termo=termo, pagina=pagina, limite=50)
    if isinstance(dados, dict):
        items = dados.get("data", dados.get("fornecedores", []))
    else:
        items = dados or []
    def _simplificar_fornecedor(f):
        if isinstance(f, dict) and "fornecedor" in f:
            f = f["fornecedor"]
        return {
            "id": f.get("id", ""),
            "nome": f.get("nome", "") or f.get("razao_social", ""),
            "cpf_cnpj": f.get("cpf_cnpj", "") or f.get("cnpj", "") or f.get("cpf", ""),
            "email": f.get("email", ""),
            "telefone": f.get("fone", "") or f.get("celular", ""),
            "cidade": f.get("cidade", ""),
        }
    return {"fornecedores": [_simplificar_fornecedor(f) for f in items if isinstance(f, dict)], "pagina": pagina}


# ── Vendas ────────────────────────────────────────────────────────────────────
@app.get("/api/vendas")
def vendas(
    request: Request,
    loja: str = Query(default=""),
    data_ini: str = Query(default=""),
    data_fim: str = Query(default=""),
    pagina: int = Query(default=1),
):
    usuario_atual(request)
    loja_id = loja or None
    dados = api.buscar_vendas(
        data_ini=data_ini or None,
        data_fim=data_fim or None,
        loja_id=loja_id,
        pagina=pagina,
        limite=50,
    )
    if isinstance(dados, dict):
        items = dados.get("data", dados.get("pedidos", []))
    else:
        items = dados or []
    return {"vendas": [_simplificar_pedido(v) for v in items if isinstance(v, dict)], "pagina": pagina}


# ── Orçamentos ────────────────────────────────────────────────────────────────
@app.get("/api/orcamentos")
def orcamentos(
    request: Request,
    loja: str = Query(default=""),
    data_ini: str = Query(default=""),
    data_fim: str = Query(default=""),
    pagina: int = Query(default=1),
):
    usuario_atual(request)
    loja_id = loja or None
    dados = api.buscar_orcamentos(
        data_ini=data_ini or None,
        data_fim=data_fim or None,
        loja_id=loja_id,
        pagina=pagina,
        limite=50,
    )
    if isinstance(dados, dict):
        items = dados.get("data", dados.get("orcamentos", []))
    else:
        items = dados or []
    return {"orcamentos": [_simplificar_pedido(o) for o in items if isinstance(o, dict)], "pagina": pagina}


def _nome_de(obj, *chaves):
    """Pega o primeiro campo não-vazio; aceita também sub-dict {'nome': ...}."""
    for k in chaves:
        v = obj.get(k)
        if isinstance(v, dict):
            v = v.get("nome", "")
        if v:
            return v
    return ""


def _simplificar_pedido(v):
    """Vendas e orçamentos compartilham a mesma estrutura na GestãoClick."""
    if isinstance(v, dict) and "pedido" in v and isinstance(v["pedido"], dict):
        v = v["pedido"]
    return {
        "id": v.get("id", ""),
        "numero": v.get("numero", "") or v.get("id", ""),
        "data": (v.get("data_emissao", "") or v.get("data", ""))[:10],
        "cliente": _nome_de(v, "cliente_nome", "nome_cliente", "cliente"),
        "total": v.get("valor_total", 0) or v.get("total", 0),
        "status": v.get("status", "") or v.get("situacao", ""),
    }


# ── Histórico de Compras ──────────────────────────────────────────────────────
@app.get("/api/compras")
def compras(
    request: Request,
    loja: str = Query(default=""),
    data_ini: str = Query(default=""),
    data_fim: str = Query(default=""),
    pagina: int = Query(default=1),
):
    usuario_atual(request)
    dados = api.buscar_compras(
        data_ini=data_ini or None,
        data_fim=data_fim or None,
        loja_id=loja or None,
        pagina=pagina,
        limite=50,
    )
    if isinstance(dados, dict):
        items = dados.get("data", dados.get("pedidos", []))
    else:
        items = dados or []
    def _simplificar_compra(c):
        if isinstance(c, dict) and "pedido" in c and isinstance(c["pedido"], dict):
            c = c["pedido"]
        return {
            "id": c.get("id", ""),
            "numero": c.get("numero", "") or c.get("id", ""),
            "data": (c.get("data_emissao", "") or c.get("data", ""))[:10],
            "fornecedor": _nome_de(c, "fornecedor_nome", "fornecedor"),
            "total": c.get("valor_total", 0) or 0,
            "status": c.get("status", ""),
            "nfe": c.get("numero_nfe", ""),
        }
    lista = [_simplificar_compra(c) for c in items if isinstance(c, dict)]
    total = sum(float(c["total"] or 0) for c in lista)
    return {"compras": lista, "total_valor": total, "pagina": pagina}


# ── Financeiro (contas a receber / a pagar) ──────────────────────────────────
def _simplificar_conta(x, tipo):
    """tipo='receber' usa cliente; 'pagar' usa fornecedor."""
    valor = float(x.get("valor") or x.get("valor_total") or 0)
    pago = float(x.get("valor_pago") or 0)
    quitado = str(x.get("situacao_id", "")) == "2" or str(x.get("pago", "")) == "1"
    nome = _nome_de(x, "cliente_nome", "cliente") if tipo == "receber" else _nome_de(x, "fornecedor_nome", "fornecedor")
    return {
        "descricao": x.get("descricao") or x.get("historico", ""),
        "nome": nome,
        "vencimento": (x.get("data_vencimento") or "")[:10],
        "valor": valor,
        "pago": pago,
        "quitado": quitado,
    }


@app.get("/api/financeiro")
def financeiro(
    request: Request,
    tipo: str = Query(default="receber"),
    data_ini: str = Query(default=""),
    data_fim: str = Query(default=""),
):
    usuario_atual(request)
    if tipo == "pagar":
        dados = api.buscar_contas_pagar(data_ini=data_ini or None, data_fim=data_fim or None, limite=200)
    else:
        dados = api.buscar_contas_receber(data_ini=data_ini or None, data_fim=data_fim or None, limite=200)
    if not isinstance(dados, list):
        dados = dados.get("data", []) if isinstance(dados, dict) else []
    contas = [_simplificar_conta(x, tipo) for x in dados if isinstance(x, dict)]
    total = sum(c["valor"] for c in contas)
    total_pago = sum(c["pago"] for c in contas)
    return {
        "contas": contas,
        "total": total,
        "pago": total_pago,
        "aberto": total - total_pago,
        "tipo": tipo,
    }


# ── Relatório de vendas (resumo por período) ─────────────────────────────────
@app.get("/api/rel_vendas")
def rel_vendas(
    request: Request,
    loja: str = Query(default=""),
    data_ini: str = Query(default=""),
    data_fim: str = Query(default=""),
):
    usuario_atual(request)
    dados = api.buscar_vendas(
        data_ini=data_ini or None,
        data_fim=data_fim or None,
        loja_id=loja or None,
        limite=500,
    )
    if not isinstance(dados, list):
        dados = dados.get("data", []) if isinstance(dados, dict) else []
    vendas_l = [_simplificar_pedido(v) for v in dados if isinstance(v, dict)]
    total = sum(float(v["total"] or 0) for v in vendas_l)
    qtd = len(vendas_l)
    # agrega por dia (para gráfico)
    por_dia = {}
    for v in vendas_l:
        por_dia[v["data"]] = por_dia.get(v["data"], 0) + float(v["total"] or 0)
    serie = [{"data": k, "valor": por_dia[k]} for k in sorted(por_dia)]
    return {
        "vendas": vendas_l,
        "total": total,
        "qtd": qtd,
        "ticket_medio": (total / qtd) if qtd else 0,
        "serie": serie,
    }


# ── Sincronização ─────────────────────────────────────────────────────────────
@app.get("/api/sincronizacao/status")
def sincronizacao_status(request: Request):
    usuario_atual(request)
    status = []
    for lid, nome in api.LOJAS.items():
        c = api.carregar_cache(lid)
        status.append({
            "loja_id": lid,
            "nome": nome,
            "total": (c or {}).get("total", 0),
            "sincronizado_em": (c or {}).get("sincronizado_em", ""),
            "online": bool(c),
        })
    return {"lojas": status}


@app.post("/api/sincronizar")
def sincronizar(request: Request, loja: str = Query(default="")):
    usuario_atual(request)
    resultados = []
    lojas = [(loja, api.LOJAS.get(loja, ""))] if loja else list(api.LOJAS.items())
    for lid, nome in lojas:
        try:
            res = api.sincronizar_produtos(loja_id=lid)
            resultados.append({"loja_id": lid, "nome": nome, "ok": True, "total": (res or {}).get("total", 0)})
        except Exception as e:
            resultados.append({"loja_id": lid, "nome": nome, "ok": False, "erro": str(e)})
    return {"resultados": resultados}


# ── Grupos (para filtros) ─────────────────────────────────────────────────────
@app.get("/api/grupos")
def grupos(request: Request):
    usuario_atual(request)
    return {"grupos": api.grupos_arvore()}


# ── Produtos do cache (preços, disponibilidade) ──────────────────────────────
def _filtrar_produtos_cache(loja_id, termo, grupo):
    cache = api.carregar_cache(loja_id)
    if not cache:
        # se a loja não tem cache, tenta o cache geral
        cache = api.carregar_cache(None)
    prods = (cache or {}).get("produtos", [])
    if termo:
        t = termo.lower()
        prods = [p for p in prods
                 if t in (p.get("nome") or "").lower() or t in (p.get("codigo_interno") or "").lower()]
    if grupo:
        ids = set(api.grupos_filhos_ids(grupo))
        prods = [p for p in prods if str(p.get("grupo_id", "")) in ids]
    return sorted(prods, key=lambda p: p.get("codigo_interno") or "")


@app.get("/api/precos")
def precos_listar(
    request: Request,
    loja: str = Query(default=""),
    termo: str = Query(default=""),
    grupo: str = Query(default=""),
):
    usuario_atual(request)
    prods = _filtrar_produtos_cache(loja or None, termo, grupo)[:150]
    itens = []
    for p in prods:
        custo = float(p.get("valor_custo") or 0)
        venda = float(p.get("valor_venda") or 0)
        margem = round((venda - custo) / custo * 100, 1) if custo > 0 else 0.0
        itens.append({
            "id": p.get("id", ""),
            "codigo": p.get("codigo_interno", ""),
            "nome": p.get("nome", ""),
            "grupo": p.get("nome_grupo", ""),
            "custo": custo,
            "venda": venda,
            "margem": margem,
        })
    return {"produtos": itens, "total": len(itens)}


class PrecoItem(BaseModel):
    produto_id: str
    produto_nome: str = ""
    valor_custo: float
    valor_venda: float


class PrecosIn(BaseModel):
    loja: str = ""
    itens: list[PrecoItem]


@app.post("/api/precos")
def precos_salvar(request: Request, dados: PrecosIn):
    usuario_atual(request)
    entradas = [
        {"produto_id": it.produto_id, "produto_nome": it.produto_nome,
         "valor_custo": it.valor_custo, "valor_venda": it.valor_venda}
        for it in dados.itens
    ]
    res = api.atualizar_precos_lote(entradas, loja_id=dados.loja or None)
    ok = [r for r in res if r.get("ok")]
    erros = [{"nome": r.get("produto_nome", ""), "erro": r.get("erro", "")} for r in res if not r.get("ok")]
    return {"atualizados": len(ok), "erros": erros}


# ── Disponibilidade por loja ──────────────────────────────────────────────────
@app.get("/api/disponibilidade")
def disponibilidade_listar(
    request: Request,
    termo: str = Query(default=""),
    grupo: str = Query(default=""),
    so_divergentes: bool = Query(default=False),
):
    usuario_atual(request)
    caches = {lid: api.carregar_cache(lid) for lid in api.LOJAS}
    cache_any = next((c for c in caches.values() if c), None)
    if not cache_any:
        return {"lojas": [], "produtos": []}
    override = api.carregar_disponibilidade()
    ativo_por_loja = {}
    for lid, c in caches.items():
        ativo_por_loja[lid] = (
            {str(p["id"]): (str(p.get("ativo", "1")) == "1") for p in c.get("produtos", [])}
            if c else {}
        )
    prods = cache_any.get("produtos", [])
    if termo:
        t = termo.lower()
        prods = [p for p in prods
                 if t in (p.get("nome") or "").lower() or t in (p.get("codigo_interno") or "").lower()]
    if grupo:
        ids = set(api.grupos_filhos_ids(grupo))
        prods = [p for p in prods if str(p.get("grupo_id", "")) in ids]
    lista = []
    for p in sorted(prods, key=lambda p: p.get("codigo_interno") or ""):
        pid = str(p["id"])
        status = {}
        for lid in api.LOJAS:
            if pid in override.get(lid, {}):
                status[lid] = bool(override[lid][pid])
            else:
                status[lid] = ativo_por_loja.get(lid, {}).get(pid, True)
        divergente = len(set(status.values())) > 1
        if so_divergentes and not divergente:
            continue
        lista.append({
            "id": p.get("id", ""),
            "codigo": p.get("codigo_interno", ""),
            "nome": p.get("nome", ""),
            "grupo": p.get("nome_grupo", ""),
            "divergente": divergente,
            "lojas": status,
        })
    return {
        "lojas": [{"id": lid, "nome": nome} for lid, nome in api.LOJAS.items()],
        "produtos": lista[:150],
    }


class DispItem(BaseModel):
    produto_id: str
    loja_id: str
    ativo: bool


class DispIn(BaseModel):
    mudancas: list[DispItem]


@app.post("/api/disponibilidade")
def disponibilidade_salvar(request: Request, dados: DispIn):
    usuario_atual(request)
    erros = []
    ok = 0
    for m in dados.mudancas:
        try:
            api.toggle_produto_loja(m.produto_id, m.loja_id, m.ativo)
            ok += 1
        except Exception as e:
            erros.append({"produto_id": m.produto_id, "loja_id": m.loja_id, "erro": str(e)})
    return {"aplicadas": ok, "erros": erros}


# ── Busca de produtos no cache (com variações) — usado por Acerto/Entrada ─────
@app.get("/api/produtos/buscar")
def produtos_buscar(
    request: Request,
    termo: str = Query(default=""),
    loja: str = Query(default=""),
):
    usuario_atual(request)
    cache = api.carregar_cache(loja or None) or api.carregar_cache(None)
    prods = api.buscar_produtos(termo, cache or {})
    out = []
    for p in prods:
        variacoes = []
        for v in sorted(p.get("variacoes", []), key=lambda v: v.get("variacao", {}).get("codigo", "") or ""):
            vd = v.get("variacao", {})
            variacoes.append({
                "id": vd.get("id", ""),
                "codigo": vd.get("codigo", ""),
                "nome": vd.get("nome", "") or "(sem nome)",
                "estoque": float(vd.get("estoque", 0) or 0),
            })
        out.append({
            "id": p.get("id", ""),
            "nome": p.get("nome", ""),
            "codigo_interno": p.get("codigo_interno", ""),
            "variacoes": variacoes,
        })
    return {"produtos": out}


class AjusteItem(BaseModel):
    produto_id: str
    produto_nome: str = ""
    variacao_id: str
    variacao_nome: str = ""
    quantidade: float


class AjusteIn(BaseModel):
    loja: str = ""
    modo: str = "set"          # 'set' = acerto, 'soma' = entrada
    itens: list[AjusteItem]


@app.post("/api/estoque/ajustar")
def estoque_ajustar(request: Request, dados: AjusteIn):
    usuario_atual(request)
    if not dados.loja:
        raise HTTPException(status_code=400, detail="Selecione uma loja antes de confirmar.")
    entradas = [
        {"produto_id": it.produto_id, "produto_nome": it.produto_nome,
         "variacao_id": it.variacao_id, "variacao_nome": it.variacao_nome,
         "quantidade": it.quantidade}
        for it in dados.itens
    ]
    modo = "soma" if dados.modo == "soma" else "set"
    res = api.atualizar_estoque_lote(entradas, loja_id=dados.loja, modo=modo)
    ok = [r for r in res if r.get("ok")]
    erros = [{"produto": r.get("produto_nome", ""), "variacao": r.get("variacao_nome", ""), "erro": r.get("erro", "")}
             for r in res if not r.get("ok")]
    return {"aplicados": len(ok), "erros": erros}


# ── Novo produto ──────────────────────────────────────────────────────────────
class VariacaoNova(BaseModel):
    nome: str
    codigo: str = ""
    estoque: str = "0"


class ProdutoNovoIn(BaseModel):
    nome: str
    codigo_interno: str
    grupo_id: str = ""
    valor_custo: str = "0.00"
    valor_venda: str = "0.00"
    ativo: bool = True
    loja: str = ""
    variacoes: list[VariacaoNova]


@app.post("/api/produtos/criar")
def produtos_criar(request: Request, dados: ProdutoNovoIn):
    usuario_atual(request)
    if not dados.nome or not dados.codigo_interno:
        raise HTTPException(status_code=400, detail="Nome e código interno são obrigatórios.")
    if not dados.variacoes:
        raise HTTPException(status_code=400, detail="Adicione pelo menos uma variação.")
    try:
        res = api.criar_produto(
            nome=dados.nome, codigo_interno=dados.codigo_interno, grupo_id=dados.grupo_id,
            valor_custo=dados.valor_custo, valor_venda=dados.valor_venda,
            ativo="1" if dados.ativo else "0",
            variacoes=[v.model_dump() for v in dados.variacoes],
            loja_id=dados.loja or None,
        )
        return {"ok": True, "resultado": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Clonar produto ────────────────────────────────────────────────────────────
class CloneIn(BaseModel):
    produto_id: str
    novo_nome: str
    novo_codigo: str
    loja: str = ""


@app.post("/api/produtos/clonar")
def produtos_clonar(request: Request, dados: CloneIn):
    usuario_atual(request)
    if not dados.novo_nome or not dados.novo_codigo:
        raise HTTPException(status_code=400, detail="Preencha o nome e o código.")
    try:
        res = api.clonar_produto(dados.produto_id, dados.novo_nome, dados.novo_codigo, loja_id=dados.loja or None)
        return {"ok": True, "resultado": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Usuários (admin) ──────────────────────────────────────────────────────────
@app.get("/api/usuarios")
def usuarios_listar(request: Request):
    admin_atual(request)
    usuarios = api.carregar_usuarios()
    setores = api.carregar_setores()
    lista = []
    for login, ud in usuarios.items():
        sk = ud.get("setor", "vendas")
        lista.append({
            "login": login,
            "nome": ud.get("nome", ""),
            "setor": sk,
            "setor_label": setores.get(sk, {}).get("label", sk),
            "paginas": setores.get(sk, {}).get("paginas", []),
        })
    setores_out = [{"id": k, "label": v.get("label", k)} for k, v in setores.items()]
    return {"usuarios": lista, "setores": setores_out}


class UsuarioIn(BaseModel):
    login: str
    nome: str = ""
    senha: str = ""
    setor: str = "vendas"


@app.post("/api/usuarios")
def usuarios_criar(request: Request, dados: UsuarioIn):
    admin_atual(request)
    login = (dados.login or "").strip().lower()
    usuarios = api.carregar_usuarios()
    if not login or not dados.senha:
        raise HTTPException(status_code=400, detail="Login e senha são obrigatórios.")
    if login in usuarios:
        raise HTTPException(status_code=400, detail=f"Login '{login}' já existe.")
    usuarios[login] = {"nome": dados.nome or login, "senha": dados.senha, "setor": dados.setor}
    api.salvar_usuarios(usuarios)
    return {"ok": True}


class UsuarioEditIn(BaseModel):
    nome: str = ""
    senha: str = ""   # vazio = mantém
    setor: str = "vendas"


@app.put("/api/usuarios/{login}")
def usuarios_editar(request: Request, login: str, dados: UsuarioEditIn):
    me_admin = admin_atual(request)
    usuarios = api.carregar_usuarios()
    if login not in usuarios:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if login == me_admin and dados.setor != "admin":
        raise HTTPException(status_code=400, detail="Você não pode remover seu próprio acesso admin.")
    usuarios[login]["nome"] = dados.nome
    usuarios[login]["setor"] = dados.setor
    if dados.senha:
        usuarios[login]["senha"] = dados.senha
    api.salvar_usuarios(usuarios)
    return {"ok": True}


@app.delete("/api/usuarios/{login}")
def usuarios_excluir(request: Request, login: str):
    me_admin = admin_atual(request)
    if login == me_admin:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário.")
    usuarios = api.carregar_usuarios()
    if login in usuarios:
        del usuarios[login]
        api.salvar_usuarios(usuarios)
    return {"ok": True}


@app.post("/api/usuarios/importar")
def usuarios_importar(request: Request):
    admin_atual(request)
    usuarios = api.carregar_usuarios()
    resultado = api.criar_usuarios_funcionarios(usuarios)
    api.salvar_usuarios(usuarios)
    return resultado


# ── Aprovações de entrada ─────────────────────────────────────────────────────
@app.get("/api/aprovacoes")
def aprovacoes_listar(request: Request):
    user = usuario_atual(request)
    usuarios = api.carregar_usuarios()
    setor = usuarios.get(user, {}).get("setor", "vendas")
    setores = api.carregar_setores()
    pode = setor == "admin" or "aprovacoes" in setores.get(setor, {}).get("paginas", [])
    pendentes = api.listar_entradas_aprovacao(status="aguardando")
    todos = api.listar_entradas_aprovacao()
    historico = [a for a in todos if a.get("status") != "aguardando"]

    def _resumo(a):
        return {
            "id": a.get("id", ""),
            "criado_em": (a.get("criado_em", "") or "")[:16].replace("T", " "),
            "criador": a.get("nome_criador", a.get("criado_por", "")),
            "loja_nome": a.get("loja_nome", ""),
            "obs_envio": a.get("obs_envio", ""),
            "status": a.get("status", ""),
            "aprovador": a.get("nome_aprovador", "") or "—",
            "aprovado_em": (a.get("aprovado_em", "") or "")[:16].replace("T", " ") or "—",
            "obs_aprovacao": a.get("obs_aprovacao", "") or "",
            "itens": [
                {"produto": i.get("produto_nome", ""), "variacao": i.get("variacao_nome", ""), "qtd": i.get("quantidade", 1)}
                for i in a.get("itens", [])
            ],
        }
    return {
        "pode_aprovar": pode,
        "pendentes": [_resumo(a) for a in pendentes],
        "historico": [_resumo(a) for a in historico],
    }


class AprovacaoIn(BaseModel):
    aprovado: bool
    obs: str = ""
    loja: str = ""


@app.post("/api/aprovacoes/{entrada_id}")
def aprovacoes_decidir(request: Request, entrada_id: str, dados: AprovacaoIn):
    user = usuario_atual(request)
    usuarios = api.carregar_usuarios()
    setor = usuarios.get(user, {}).get("setor", "vendas")
    setores = api.carregar_setores()
    if not (setor == "admin" or "aprovacoes" in setores.get(setor, {}).get("paginas", [])):
        raise HTTPException(status_code=403, detail="Você não tem permissão para aprovar.")
    nome = usuarios.get(user, {}).get("nome", user)
    res = api.aprovar_entrada_pendente(entrada_id, user, nome, dados.aprovado, dados.obs or "")
    if not res:
        raise HTTPException(status_code=404, detail="Entrada não encontrada.")
    if dados.aprovado:
        loja_ap = res.get("loja_id") or dados.loja
        if not loja_ap:
            raise HTTPException(status_code=400, detail="Selecione uma loja para aplicar o estoque.")
        api.atualizar_estoque_lote(res["itens"], loja_id=loja_ap, modo="soma")
        try:
            api.criar_notificacao(
                para_usuarios=[res.get("criado_por", "")],
                tipo="aprovacao_resultado",
                titulo="Sua lista foi aprovada ✅",
                corpo=f"{nome} aprovou sua entrada de {len(res.get('itens', []))} item(ns) — loja {res.get('loja_nome', '')}",
                pagina="entrada", de_usuario=user,
            )
        except Exception:
            pass
    else:
        try:
            api.criar_notificacao(
                para_usuarios=[res.get("criado_por", "")],
                tipo="aprovacao_resultado",
                titulo="Sua lista foi rejeitada ❌",
                corpo=f"{nome} rejeitou sua entrada. Obs: {dados.obs or '—'}",
                pagina="entrada", de_usuario=user,
            )
        except Exception:
            pass
    return {"ok": True, "status": res.get("status")}


# ── Listas salvas ─────────────────────────────────────────────────────────────
@app.get("/api/listas")
def listas_listar(request: Request, tipo: str = Query(default="")):
    usuario_atual(request)
    todas = api.listar_listas_salvas(tipo or None)
    out = [{
        "arquivo": l.get("_arquivo", ""),
        "nome": l.get("nome", l.get("_arquivo", "")),
        "tipo": l.get("tipo", ""),
        "loja_nome": l.get("loja_nome", ""),
        "criado_em": (l.get("criado_em", "") or "")[:10],
        "n_itens": len(l.get("itens", [])),
    } for l in todas]
    return {"listas": out}


@app.get("/api/listas/{arquivo}")
def listas_ver(request: Request, arquivo: str):
    usuario_atual(request)
    d = api.carregar_lista(arquivo)
    if not d:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")
    itens = [
        {"produto": i.get("produto_nome", ""), "variacao": i.get("variacao_nome", ""),
         "codigo": i.get("variacao_cod", "") or i.get("cod_interno", ""), "qtd": i.get("quantidade", "")}
        for i in d.get("itens", [])
    ]
    return {
        "nome": d.get("nome", arquivo), "tipo": d.get("tipo", ""),
        "loja_nome": d.get("loja_nome", ""), "itens": itens,
    }


@app.delete("/api/listas/{arquivo}")
def listas_excluir(request: Request, arquivo: str):
    usuario_atual(request)
    api.excluir_lista(arquivo)
    return {"ok": True}


# ── Etiquetas ─────────────────────────────────────────────────────────────────
@app.get("/api/etiquetas/formatos")
def etiquetas_formatos(request: Request):
    usuario_atual(request)
    return {"formatos": [{"id": k, "label": v.get("label", k)} for k, v in api.FORMATOS_ETIQUETA.items()]}


class EtiquetaItem(BaseModel):
    produto_nome: str = ""
    variacao_nome: str = ""
    variacao_cod: str = ""
    variacao_id: str = ""
    quantidade: int = 1


class EtiquetasIn(BaseModel):
    formato: str = "pimaco_a4351"
    itens: list[EtiquetaItem]


@app.post("/api/etiquetas/pdf")
def etiquetas_pdf(request: Request, dados: EtiquetasIn):
    usuario_atual(request)
    if not dados.itens:
        raise HTTPException(status_code=400, detail="Adicione itens antes de gerar.")
    itens = [it.model_dump() for it in dados.itens]
    pdf = api.gerar_pdf_etiquetas(itens, dados.formato)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="etiquetas_{dados.formato}.pdf"'},
    )


# ── Pedido de Compra ──────────────────────────────────────────────────────────
@app.get("/api/situacoes_compras")
def situacoes_compras(request: Request):
    usuario_atual(request)
    dados = api.buscar_situacoes_compras()
    out = []
    for s in dados:
        if isinstance(s, dict) and "situacao" in s:
            s = s["situacao"]
        if isinstance(s, dict):
            out.append({"id": s.get("id", ""), "nome": s.get("nome", "")})
    return {"situacoes": out}


class PedidoItem(BaseModel):
    produto_id: str = ""
    variacao_id: str = ""
    produto_nome: str = ""
    quantidade: int = 1
    valor_custo: str = "0.00"


class PedidoIn(BaseModel):
    fornecedor_id: str
    situacao_id: str
    data_emissao: str
    observacoes: str = ""
    loja: str = ""
    itens: list[PedidoItem]


class PedidoWppIn(BaseModel):
    texto: str = ""
    regras: str = ""
    avulsos: str = ""
    fornecedor: str = ""
    reprocess_base: list = []
    loja: str = ""


@app.post("/api/pedido/whatsapp")
def pedido_whatsapp(request: Request, dados: PedidoWppIn):
    usuario_atual(request)
    cache = api.carregar_cache(dados.loja or None) or api.carregar_cache(None)
    if not cache:
        raise HTTPException(status_code=400, detail="Sincronize os produtos primeiro.")
    try:
        return api.processar_pedido_whatsapp(
            dados.texto, dados.regras, dados.avulsos, cache,
            fornecedor=dados.fornecedor, reprocess_base=dados.reprocess_base,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/pedido/kits")
def pedido_kits(request: Request):
    usuario_atual(request)
    # Botões de kit da página de Pedidos (rótulo → chave do kit em api.WPP_KITS)
    return {"kits": [
        {"label": "👔 Masculino", "kit": "masculino"},
        {"label": "👗 Feminino", "kit": "feminino"},
        {"label": "📦 Pacote Masc.", "kit": "pacote masculino"},
        {"label": "📦 Pacote Fem.", "kit": "pacote feminino"},
        {"label": "SL Masc.", "kit": "sl masculino"},
        {"label": "SL Fem.", "kit": "sl feminino"},
        {"label": "SL Pac. Masc.", "kit": "sl pacote masculino"},
        {"label": "SL Pac. Fem.", "kit": "sl pacote feminino"},
        {"label": "VR Masc.", "kit": "vr masculino"},
        {"label": "VR Fem.", "kit": "vr feminino"},
        {"label": "MagSafe", "kit": "magsafe"},
        {"label": "✨ Brilho", "kit": "brilho"},
        {"label": "Diversos Masc.", "kit": "diversos masculino"},
    ]}


class KitIn(BaseModel):
    produto_id: str
    kit: str
    loja: str = ""


@app.post("/api/pedido/kit")
def pedido_kit(request: Request, dados: KitIn):
    usuario_atual(request)
    cache = api.carregar_cache(dados.loja or None) or api.carregar_cache(None)
    prods = (cache or {}).get("produtos", [])
    produto = next((p for p in prods if str(p.get("id")) == str(dados.produto_id)), None)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado no cache.")
    return api.expandir_kit_em_produto(produto, dados.kit)


@app.post("/api/pedido/registrar")
def pedido_registrar(request: Request, dados: PedidoIn):
    usuario_atual(request)
    if not dados.fornecedor_id:
        raise HTTPException(status_code=400, detail="Selecione um fornecedor.")
    if not dados.situacao_id:
        raise HTTPException(status_code=400, detail="Selecione a situação do pedido.")
    if not dados.itens:
        raise HTTPException(status_code=400, detail="Adicione itens ao pedido.")
    itens = [it.model_dump() for it in dados.itens]
    try:
        res = api.registrar_compra_gestaoclick(
            itens, fornecedor_id=dados.fornecedor_id, data_emissao=dados.data_emissao,
            situacao_id=dados.situacao_id, observacoes=dados.observacoes, loja_id=dados.loja or None,
        )
        return {"ok": True, "resultado": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Diagnóstico (mostra se as credenciais estão configuradas) ────────────────
@app.get("/api/diagnostico")
def diagnostico(request: Request):
    usuario_atual(request)
    return api.diagnostico_config()


# ── Frontend estático (SPA) ──────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


# 401 → o frontend trata mostrando a tela de login
@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Arquivos estáticos (css/js) — montado por último para não cobrir as rotas /api
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
