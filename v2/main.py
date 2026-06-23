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
    def _simplificar_venda(v):
        if isinstance(v, dict) and "pedido" in v:
            v = v["pedido"]
        return {
            "id": v.get("id", ""),
            "numero": v.get("numero", "") or v.get("id", ""),
            "data": (v.get("data_emissao", "") or v.get("data", ""))[:10],
            "cliente": v.get("nome_cliente", "") or v.get("cliente", ""),
            "total": v.get("valor_total", 0) or v.get("total", 0),
            "status": v.get("situacao", "") or v.get("status", ""),
        }
    return {"vendas": [_simplificar_venda(v) for v in items if isinstance(v, dict)], "pagina": pagina}


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
    def _simplificar_orcamento(o):
        if isinstance(o, dict) and "orcamento" in o:
            o = o["orcamento"]
        return {
            "id": o.get("id", ""),
            "numero": o.get("numero", "") or o.get("id", ""),
            "data": (o.get("data_emissao", "") or o.get("data", ""))[:10],
            "cliente": o.get("nome_cliente", "") or o.get("cliente", ""),
            "total": o.get("valor_total", 0) or o.get("total", 0),
            "status": o.get("situacao", "") or o.get("status", ""),
        }
    return {"orcamentos": [_simplificar_orcamento(o) for o in items if isinstance(o, dict)], "pagina": pagina}


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
