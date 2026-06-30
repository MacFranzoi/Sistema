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

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query, BackgroundTasks  # noqa: E402
from fastapi.responses import JSONResponse, FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402
import uuid, threading  # noqa: E402

# ── Store em memória para jobs de IA em background ───────────────────────────
_ia_jobs: dict = {}  # job_id → {"status": "running"|"done"|"error", "result": ...}
_ia_jobs_lock = threading.Lock()

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


# ── Diagnóstico (mostra se as credenciais estão configuradas) ────────────────
@app.get("/api/diagnostico")
def diagnostico(request: Request):
    usuario_atual(request)
    return api.diagnostico_config()


# ── IA Balanço em background ─────────────────────────────────────────────────
class _BalancoIAReq(BaseModel):
    loja_ids: list
    grupos: list = []
    modelos: list = []
    regra: str


def _rodar_ia_background(job_id: str, loja_ids, grupos, modelos, regra):
    try:
        full = api.comparar_estoque_lojas(
            loja_ids,
            grupos=grupos or None,
            modelos=modelos or None,
            somente_divergentes=False,
            incluir_vendas=True,
        )
        res = api.balancear_lojas_ia(full["lojas"], full["linhas"], regra)
        cod_map = {ln["codigo"]: ln for ln in full["linhas"]}
        id_por_nome = {l["nome"]: l["id"] for l in full["lojas"]}
        for mv in res.get("movimentos", []):
            info = cod_map.get(mv["codigo"], {})
            mv["produto"] = info.get("produto", "")
            mv["variacao"] = info.get("variacao", "")
            est = info.get("estoque", {})
            mv["est_de"] = est.get(id_por_nome.get(mv["de"]), 0)
            mv["est_para"] = est.get(id_por_nome.get(mv["para"]), 0)
        # Ranking de vendas do cache (rápido)
        modelos_rk = list({ln["produto"] for ln in full["linhas"] if ln.get("produto")}) or modelos or None
        ranking = api.ranking_vendas_lojas(loja_ids, grupos=grupos or None, modelos=modelos_rk, dias=90, top=50)
        with _ia_jobs_lock:
            _ia_jobs[job_id] = {"status": "done", "result": res, "ranking": ranking}
    except Exception as e:
        with _ia_jobs_lock:
            _ia_jobs[job_id] = {"status": "error", "result": {"erro": str(e)}}


def _autenticar_interno(request: Request):
    """Aceita cookie de sessão normal OU header X-Internal-Token (chamadas server-to-server)."""
    token_interno = os.environ.get("INTERNAL_TOKEN", "")
    header_token = request.headers.get("x-internal-token", "")
    if token_interno and header_token == token_interno:
        return  # autenticado via token interno
    usuario_atual(request)  # fallback: cookie normal


@app.post("/api/balanco/ia")
def balanco_ia_start(req: _BalancoIAReq, request: Request, background_tasks: BackgroundTasks):
    _autenticar_interno(request)
    job_id = str(uuid.uuid4())
    with _ia_jobs_lock:
        _ia_jobs[job_id] = {"status": "running", "result": None}
    background_tasks.add_task(_rodar_ia_background, job_id, req.loja_ids, req.grupos, req.modelos, req.regra)
    return {"job_id": job_id}


@app.get("/api/balanco/ia/{job_id}")
def balanco_ia_status(job_id: str, request: Request):
    _autenticar_interno(request)
    with _ia_jobs_lock:
        job = _ia_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    return job


# ── Voz / Whisper ────────────────────────────────────────────────────────────
@app.post("/api/voz/transcrever")
async def voz_transcrever(request: Request):
    from fastapi import UploadFile, File
    import tempfile, os as _os_voz
    openai_key = _os_voz.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        raise HTTPException(400, "OPENAI_API_KEY não configurada")
    form = await request.form()
    audio_file = form.get("audio")
    if not audio_file:
        raise HTTPException(400, "Campo 'audio' ausente")
    data = await audio_file.read()
    suffix = ".webm"
    fname = getattr(audio_file, "filename", "audio.webm") or "audio.webm"
    if "." in fname:
        suffix = "." + fname.rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        import openai as _openai
        client = _openai.OpenAI(api_key=openai_key)
        with open(tmp_path, "rb") as f:
            resp = client.audio.transcriptions.create(model="whisper-1", file=f)
        return {"texto": resp.text}
    finally:
        _os_voz.unlink(tmp_path)


# ── Frontend estático (SPA) ───────────────────────────────────────────────────
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
