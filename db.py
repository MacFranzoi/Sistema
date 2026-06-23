"""
Camada de persistência com Supabase.
Se SUPABASE_URL e SUPABASE_KEY estiverem definidos, usa Supabase.
Caso contrário, todas as funções retornam None/False e o api.py
cai no fallback GitHub normalmente — zero quebra de compatibilidade.

SQL para criar a tabela no Supabase (cole no SQL Editor):
--------------------------------------------------------------
create table if not exists documentos (
    chave        text primary key,
    dados        jsonb not null default '{}',
    atualizado_em timestamptz default now()
);
create index if not exists idx_doc_chave on documentos (chave text_pattern_ops);
--------------------------------------------------------------
"""
import os

try:
    from supabase import create_client
    _url = os.environ.get("SUPABASE_URL", "")
    _key = os.environ.get("SUPABASE_KEY", "")
    _sb  = create_client(_url, _key) if (_url and _key) else None
except Exception:
    _sb = None


def ativo() -> bool:
    return _sb is not None


def ler(chave: str):
    """Retorna o objeto JSON ou None se não encontrado."""
    if not _sb:
        return None
    try:
        r = _sb.table("documentos").select("dados").eq("chave", chave).maybe_single().execute()
        return r.data["dados"] if r.data else None
    except Exception:
        return None


def salvar(chave: str, dados) -> bool:
    """Cria ou substitui o documento."""
    if not _sb:
        return False
    try:
        _sb.table("documentos").upsert({"chave": chave, "dados": dados}).execute()
        return True
    except Exception:
        return False


def deletar(chave: str) -> bool:
    """Remove o documento."""
    if not _sb:
        return False
    try:
        _sb.table("documentos").delete().eq("chave", chave).execute()
        return True
    except Exception:
        return False


def listar(prefixo: str) -> list:
    """Lista chaves com determinado prefixo."""
    if not _sb:
        return []
    try:
        r = _sb.table("documentos").select("chave").like("chave", f"{prefixo}%").execute()
        return [row["chave"] for row in (r.data or [])]
    except Exception:
        return []
