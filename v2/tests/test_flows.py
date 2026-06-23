"""
Testes dos fluxos críticos do Sistema Plug 2.0.
Cobre: auth, estoque, entrada, pedido, listas.

Rodar:
    cd /home/user/Sistema
    pytest v2/tests/test_flows.py -v
"""
import sys, os
import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from httpx import AsyncClient, ASGITransport
from v2.main import app

TRANSPORT = ASGITransport(app=app)


@pytest_asyncio.fixture
async def anon():
    async with AsyncClient(transport=TRANSPORT, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth():
    async with AsyncClient(transport=TRANSPORT, base_url="http://test") as c:
        r = await c.post("/api/login", json={"usuario": "gustavo", "senha": "admin"})
        assert r.status_code == 200, f"Login falhou: {r.text}"
        yield c


# ── Auth ───────────────────────────────────────────────────────────────────────

async def test_health(anon):
    r = await anon.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_login_invalido(anon):
    r = await anon.post("/api/login", json={"usuario": "naoexiste", "senha": "errado"})
    assert r.status_code == 401


async def test_me_sem_auth(anon):
    r = await anon.get("/api/me")
    assert r.status_code == 401


async def test_login_e_me(auth):
    r = await auth.get("/api/me")
    assert r.status_code == 200
    d = r.json()
    assert d["usuario"] == "gustavo"
    assert "menu" in d


async def test_logout(auth):
    await auth.post("/api/logout")
    r = await auth.get("/api/me")
    assert r.status_code == 401


# ── Endpoints críticos ─────────────────────────────────────────────────────────

async def test_lojas(auth):
    r = await auth.get("/api/lojas")
    assert r.status_code == 200
    lojas = r.json()["lojas"]
    assert len(lojas) > 0
    assert all("id" in l and "nome" in l for l in lojas)


async def test_dashboard(auth):
    r = await auth.get("/api/dashboard")
    assert r.status_code == 200
    assert "lojas" in r.json()


async def test_grupos(auth):
    r = await auth.get("/api/grupos")
    assert r.status_code == 200
    assert "grupos" in r.json()


async def test_estoque_sem_termo_retorna_vazio(auth):
    """Sem nome nem código deve retornar vazio — nunca 500."""
    r = await auth.get("/api/estoque?nome=&codigo=")
    assert r.status_code == 200
    assert r.json()["produtos"] == []


async def test_estoque_com_termo(auth):
    """Com termo deve retornar estrutura válida (lista pode estar vazia sem cache)."""
    r = await auth.get("/api/estoque?nome=iphone")
    assert r.status_code == 200
    d = r.json()
    assert "produtos" in d
    assert isinstance(d["produtos"], list)


async def test_pedido_kits(auth):
    r = await auth.get("/api/pedido/kits")
    assert r.status_code == 200
    assert "kits" in r.json()


async def test_listas_salvas(auth):
    r = await auth.get("/api/listas?tipo=entrada")
    assert r.status_code == 200
    assert "listas" in r.json()


async def test_entrada_whatsapp_texto_vazio(auth):
    """Texto vazio não deve causar 500."""
    r = await auth.post("/api/entrada/whatsapp", json={"texto": "", "loja": ""})
    assert r.status_code in (200, 400, 422)


async def test_produtos_buscar(auth):
    """Busca de produtos no cache local."""
    r = await auth.get("/api/produtos/buscar?termo=iphone")
    assert r.status_code == 200
    assert "produtos" in r.json()
