import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
import api
from fpdf import FPDF


def gerar_pdf_pedido(df_ped, fornecedor, data_ped, simplificado=False):
    import os
    FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
    USE_UNICODE = os.path.exists(FONT_PATH)

    def _s(v):
        text = str(v or "").replace("—", "-").replace("–", "-").replace("—", "-")
        if not USE_UNICODE:
            return text.encode("latin-1", errors="replace").decode("latin-1")
        return text

    pdf = FPDF()
    if USE_UNICODE:
        pdf.add_font("Arial", "", FONT_PATH)
        pdf.add_font("Arial", "B", FONT_PATH)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    FNORM = "Arial" if USE_UNICODE else "Helvetica"
    titulo = "PEDIDO SIMPLIFICADO" if simplificado else "PEDIDO DE COMPRA"
    pdf.set_font(FNORM, "B", 14)
    pdf.cell(0, 8, titulo, ln=True, align="C")
    pdf.set_font(FNORM, "", 10)
    pdf.cell(0, 6, f"Fornecedor: {_s(fornecedor)}    Data: {data_ped}", ln=True, align="C")
    pdf.ln(4)

    if simplificado:
        cols   = ["produto_nome", "variacao_nome", "observacao", "quantidade"]
        heads  = ["Produto", "Variacao", "Obs.", "Qtd"]
        widths = [70, 55, 35, 20]
    else:
        cols   = ["fornecedor", "produto_nome", "variacao_nome", "observacao", "quantidade", "valor_custo", "total"]
        heads  = ["Fornecedor", "Produto", "Variacao", "Obs.", "Qtd", "Custo", "Total"]
        widths = [28, 48, 38, 28, 12, 18, 18]

    pdf.set_font(FNORM, "B", 9)
    pdf.set_fill_color(220, 220, 220)
    for h, w in zip(heads, widths):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font(FNORM, "", 8)
    fill = False
    pdf.set_fill_color(245, 245, 245)
    for _, row in df_ped.iterrows():
        for col, w in zip(cols, widths):
            val = _s(row.get(col, ""))
            if col in ("valor_custo", "total"):
                try:
                    val = f"R${float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    pass
            pdf.cell(w, 6, val[:35], border=1, fill=fill)
        pdf.ln()
        fill = not fill

    if not simplificado:
        total_geral = df_ped["total"].sum()
        pdf.set_font(FNORM, "B", 9)
        pdf.cell(0, 7,
                 f"TOTAL ESTIMADO: R${total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                 ln=True, align="R")

    return bytes(pdf.output())

st.set_page_config(page_title="Plug ERP", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ── Tema ──
if "tema" not in st.session_state:
    st.session_state.tema = "dark"
_dark = st.session_state.tema == "dark"

BG      = "#111111" if _dark else "#f2f3f5"
SB      = "#0a0a0a" if _dark else "#ffffff"
SB2     = "#1a1a1a" if _dark else "#f8f8f8"
CARD    = "#1a1a1a" if _dark else "#ffffff"
BOR     = "#2a2a2a" if _dark else "#e3e3e3"
TXT     = "#f0f0f0" if _dark else "#1a1a1a"
TXT2    = "#999999"
YEL     = "#FFD600"
YEL_BG  = "rgba(255,214,0,0.10)"
TOPBAR  = "#000000" if _dark else "#000000"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* RESET */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    font-size: 13px;
    background: {BG} !important;
    color: {TXT} !important;
}}
.main .block-container {{ padding: 0 !important; max-width: 100% !important; }}

/* ── TOPBAR preta ── */
[data-testid="stHeader"] {{
    background: {TOPBAR} !important;
    height: 52px !important;
    border-bottom: 1px solid #222 !important;
}}
[data-testid="stHeader"] button {{ color: #fff !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: {SB} !important;
    border-right: 1px solid {BOR} !important;
    width: 220px !important;
    min-width: 220px !important;
    padding: 0 !important;
}}
[data-testid="stSidebar"] > div:first-child {{ padding: 0 !important; }}

/* ── Topbar da sidebar: logo ── */
.sb-logo {{
    display: flex; align-items: center; gap: 10px;
    padding: 0 14px;
    height: 52px;
    background: #000;
    border-bottom: 1px solid #222;
    position: sticky; top: 0; z-index: 10;
}}
.sb-logo-mark {{
    background: {YEL}; color: #000;
    width: 30px; height: 30px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 1rem; letter-spacing: -1px;
    flex-shrink: 0;
}}
.sb-logo-text {{ font-size: 1rem; font-weight: 700; color: {YEL}; letter-spacing: 0.3px; }}

/* ── empresa selecionada ── */
.sb-empresa {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px;
    background: {SB2};
    border-bottom: 1px solid {BOR};
    cursor: pointer;
}}
.sb-empresa-name {{ font-size: 0.78rem; font-weight: 600; }}
.sb-empresa-cnpj {{ font-size: 0.62rem; color: {TXT2}; margin-top: 1px; }}
.sb-empresa-arrow {{ color: {TXT2}; font-size: 0.65rem; }}

/* ── nav group label ── */
.nav-group {{
    font-size: 0.58rem; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; color: {TXT2};
    padding: 14px 14px 4px;
}}

/* ── nav item ── */
[data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    text-align: left !important;
    padding: 8px 14px 8px 16px !important;
    font-size: 0.8rem !important;
    color: {TXT} !important;
    margin: 0 !important;
    display: flex; align-items: center; gap: 8px;
    transition: background 0.1s, color 0.1s;
    border-left: 3px solid transparent !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {YEL_BG} !important;
    color: {YEL} !important;
    border-left-color: {YEL}88 !important;
}}
.nav-active [data-testid="stSidebar"] .stButton > button,
.nav-active .stButton > button {{
    background: {YEL_BG} !important;
    color: {YEL} !important;
    font-weight: 600 !important;
    border-left: 3px solid {YEL} !important;
}}

/* ── user footer ── */
.sb-footer {{
    padding: 10px 14px;
    border-top: 1px solid {BOR};
    background: {SB};
    display: flex; gap: 8px; align-items: center;
}}
.sb-avatar {{
    width: 30px; height: 30px; border-radius: 50%;
    background: {YEL}; color: #000;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.8rem; flex-shrink: 0;
}}
.sb-user-name  {{ font-size: 0.76rem; font-weight: 600; line-height: 1.2; }}
.sb-user-role  {{ font-size: 0.62rem; color: {TXT2}; }}

/* ── PAGE wrapper ── */
.page-wrap {{
    padding: 20px 24px;
    background: {BG};
    min-height: calc(100vh - 52px);
}}

/* ── page header ── */
.page-header {{
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid {BOR};
}}
.page-title {{ font-size: 1.25rem; font-weight: 700; color: {TXT}; }}
.page-breadcrumb {{
    font-size: 0.68rem; color: {TXT2};
    margin-bottom: 3px;
    display: flex; align-items: center; gap: 4px;
}}
.page-breadcrumb span {{ color: {YEL}; }}

/* ── CARDS ── */
.card {{
    background: {CARD};
    border: 1px solid {BOR};
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 14px;
}}
.card-header {{
    font-size: 0.82rem; font-weight: 600;
    color: {TXT};
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid {BOR};
    display: flex; align-items: center; gap: 6px;
}}

/* ── STAT CARDS ── */
.stat-grid {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }}
.stat-box {{
    flex: 1; min-width: 120px;
    background: {CARD};
    border: 1px solid {BOR};
    border-radius: 8px;
    padding: 14px 16px;
    border-top: 3px solid {YEL};
}}
.stat-val {{ font-size: 1.5rem; font-weight: 700; color: {YEL}; line-height: 1.1; }}
.stat-lbl {{ font-size: 0.68rem; color: {TXT2}; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }}

/* ── BADGE ── */
.badge {{
    display: inline-flex; align-items: center; gap: 3px;
    background: {YEL_BG}; color: {YEL};
    border: 1px solid {YEL}55;
    border-radius: 4px;
    font-size: 0.62rem; font-weight: 600;
    padding: 2px 7px;
}}
.badge-green {{ background: rgba(76,175,80,0.12); color: #66bb6a; border-color: #66bb6a55; }}
.badge-red   {{ background: rgba(244,67,54,0.12); color: #ef5350; border-color: #ef535055; }}

/* ── TABELA ── */
.stDataFrame {{ border-radius: 8px !important; overflow: hidden; }}
.stDataFrame [data-testid="stDataFrameResizable"] {{ border: 1px solid {BOR} !important; border-radius: 8px !important; }}
.stDataFrame th {{ background: {SB2} !important; font-size: 0.7rem !important; font-weight: 600 !important; color: {TXT2} !important; text-transform: uppercase; letter-spacing: 0.5px; }}
.stDataFrame td {{ font-size: 0.76rem !important; color: {TXT} !important; }}

/* ── INPUTS ── */
.stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label {{
    font-size: 0.75rem !important; font-weight: 500 !important; color: {TXT2} !important;
    text-transform: uppercase; letter-spacing: 0.4px;
}}
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: {CARD} !important; border: 1px solid {BOR} !important;
    color: {TXT} !important; border-radius: 6px !important; font-size: 0.82rem !important;
    padding: 7px 10px !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{ border-color: {YEL} !important; box-shadow: 0 0 0 2px {YEL}22 !important; }}
.stSelectbox > div > div {{ background: {CARD} !important; border-color: {BOR} !important; font-size: 0.82rem !important; border-radius: 6px !important; }}

/* ── BUTTONS ── */
.main .stButton > button, .stFormSubmitButton > button {{
    font-size: 0.78rem !important; padding: 0.38rem 1rem !important;
    border-radius: 6px !important; border: 1px solid {BOR} !important;
    background: {CARD} !important; color: {TXT} !important;
    font-weight: 500 !important; transition: all 0.15s !important;
}}
.main .stButton > button[kind="primary"], .stFormSubmitButton > button {{
    background: {YEL} !important; color: #000 !important;
    border-color: {YEL} !important; font-weight: 600 !important;
}}
.main .stButton > button:hover {{ border-color: {YEL} !important; color: {YEL} !important; }}
.main .stButton > button[kind="primary"]:hover {{ background: #ffe033 !important; color: #000 !important; }}

/* ── EXPANDER ── */
.stExpander {{ border: 1px solid {BOR} !important; border-radius: 8px !important; background: {CARD} !important; }}
.stExpander summary {{ font-size: 0.8rem !important; color: {TXT} !important; }}

/* ── TABS internas ── */
.stTabs [data-baseweb="tab-list"] {{ border-bottom: 1px solid {BOR}; background: transparent; gap: 0; }}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.78rem !important; padding: 8px 16px !important;
    color: {TXT2} !important; border-radius: 0 !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
}}
.stTabs [aria-selected="true"] {{ color: {YEL} !important; border-bottom-color: {YEL} !important; font-weight: 600 !important; }}

/* ── DIVIDER ── */
hr {{ border-color: {BOR} !important; margin: 12px 0 !important; }}

/* ── LOGIN ── */
.login-page {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 100vh; margin-top: -4rem;
}}
.login-card {{
    background: {CARD}; border: 1px solid {BOR};
    border-top: 3px solid {YEL};
    border-radius: 10px; padding: 2.2rem 2rem 1.6rem;
    width: 100%; max-width: 340px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4);
}}
.login-logo {{ display: flex; align-items: center; gap: 10px; margin-bottom: 1.6rem; }}
.login-logo-mark {{
    width: 44px; height: 44px; border-radius: 10px;
    background: {YEL}; color: #000;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 1.3rem;
}}
.login-brand {{ font-size: 1.1rem; font-weight: 800; color: {YEL}; }}
.login-sub   {{ font-size: 0.68rem; color: {TXT2}; }}
/* Formulário de login: remove gap entre logo e form */
div[data-testid="stForm"] {{ background: transparent !important; border: none !important; padding: 0 !important; }}
div[data-testid="stForm"] > div {{ gap: 0.5rem !important; }}
/* Labels uppercase */
div[data-testid="stForm"] label p {{ font-size: 0.65rem !important; font-weight: 700 !important; letter-spacing: .08em !important; color: {TXT2} !important; }}
/* Submit button amarelo */
div[data-testid="stForm"] button[type="submit"] {{
    background: {YEL} !important; color: #000 !important;
    font-weight: 700 !important; border-radius: 6px !important;
    border: none !important; margin-top: 0.4rem !important;
}}

/* ── MISC ── */
.stAlert {{ border-radius: 6px !important; font-size: 0.8rem !important; }}
[data-testid="stMetric"] {{ background: {CARD}; border: 1px solid {BOR}; border-radius: 8px; padding: 10px 14px !important; }}
p {{ color: {TXT} !important; font-size: 0.82rem !important; }}
caption {{ color: {TXT2} !important; font-size: 0.72rem !important; }}
small {{ color: {TXT2} !important; }}

/* MOBILE */
@media (max-width: 640px) {{
    .page-wrap {{ padding: 12px 14px; }}
    .page-title {{ font-size: 1rem; }}
    .stat-val {{ font-size: 1.1rem; }}
    .stButton > button {{ font-size: 0.72rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────
TODAS_ABAS = [
    "📦 Entrada de Mercadoria", "📊 Acerto de Estoque", "🏷️ Etiquetas",
    "🛒 Pedido de Compra", "🏪 Estoque por Loja", "🔘 Disponibilidade por Loja",
    "💰 Preços", "➕ Novo Modelo", "🔁 Clonar Modelo",
]

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    # CSS extra: centraliza a coluna do meio verticalmente
    st.markdown("""
    <style>
    [data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    section[data-testid="stMain"] { display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    </style>
    """, unsafe_allow_html=True)

    _, col_login, _ = st.columns([1, 1.1, 1])
    with col_login:
        # Logo no topo do card
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BOR};border-top:3px solid {YEL};
                    border-radius:10px 10px 0 0;padding:1.8rem 1.8rem 1rem;
                    box-shadow:0 4px 32px rgba(0,0,0,.4)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:44px;height:44px;border-radius:10px;background:{YEL};
                        color:#000;display:flex;align-items:center;justify-content:center;
                        font-weight:900;font-size:1.4rem">⚡</div>
            <div>
              <div style="font-size:1.1rem;font-weight:800;color:{YEL}">PLUG ERP</div>
              <div style="font-size:0.68rem;color:{TXT2}">Sistema de Gestão</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Form colado abaixo do logo (sem borda superior)
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BOR};border-top:none;
                    border-radius:0 0 10px 10px;padding:0 1.8rem 1.6rem;
                    box-shadow:0 4px 32px rgba(0,0,0,.4)">
        </div>
        <style>
        /* posiciona o form dentro do card visual */
        [data-testid="stForm"] {{
            background:{CARD} !important;
            border:1px solid {BOR} !important;
            border-top:none !important;
            border-radius:0 0 10px 10px !important;
            padding:0 1.8rem 1.6rem !important;
            margin-top:-8px !important;
            box-shadow:0 4px 32px rgba(0,0,0,.4);
        }}
        [data-testid="stForm"] button[type="submit"] {{
            background:{YEL} !important;color:#000 !important;
            font-weight:700 !important;border:none !important;
            border-radius:6px !important;margin-top:0.6rem !important;
        }}
        [data-testid="stForm"] label p {{
            font-size:0.65rem !important;font-weight:700 !important;
            letter-spacing:.08em !important;color:{TXT2} !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            usuario_input = st.text_input("USUÁRIO")
            senha_input   = st.text_input("SENHA", type="password")
            entrar = st.form_submit_button("Entrar →", use_container_width=True)

        if entrar:
            u = usuario_input.strip().lower()
            _udb = api.carregar_usuarios()
            if u in _udb and _udb[u]["senha"] == senha_input:
                st.session_state.usuario_logado = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# ── Dados do usuário ──
_user        = st.session_state.usuario_logado
_usuarios_db = api.carregar_usuarios()
_user_data   = _usuarios_db.get(_user, {})
_setor       = _user_data.get("setor", "vendas")
_abas_perm   = api.SETORES.get(_setor, api.SETORES["vendas"])["abas"]
_nome_usr    = _user_data.get("nome", _user)
_is_admin    = _setor == "admin"
_setor_lbl   = api.SETORES.get(_setor, {}).get("label", _setor)

# ── Menu estruturado (como GestaoClick) ──
# (id, icon, label, grupo, aba_idx_ou_None, placeholder)
_MENU_FULL = [
    # GERAL
    ("dashboard",       "🏠", "Dashboard",           "GERAL",       None,  False),
    # CADASTROS
    ("clientes",        "👥", "Clientes",             "CADASTROS",   None,  True),
    ("fornecedores",    "🏭", "Fornecedores",         "CADASTROS",   None,  True),
    # ITENS
    ("novo_modelo",     "➕", "Novo Produto",         "ITENS",       7,     False),
    ("clonar_modelo",   "🔁", "Clonar Produto",       "ITENS",       8,     False),
    ("precos",          "💰", "Tabela de Preços",     "ITENS",       6,     False),
    # VENDAS
    ("vendas",          "🧾", "Vendas",               "VENDAS",      None,  True),
    ("orcamentos",      "📋", "Orçamentos",           "VENDAS",      None,  True),
    # ESTOQUE
    ("entrada",         "📥", "Entrada",              "ESTOQUE",     0,     False),
    ("acerto",          "🔧", "Acerto",               "ESTOQUE",     1,     False),
    ("estoque_loja",    "🏪", "Por Loja",             "ESTOQUE",     4,     False),
    ("disponibilidade", "🔘", "Disponibilidade",      "ESTOQUE",     5,     False),
    ("etiquetas",       "🏷️", "Etiquetas",            "ESTOQUE",     2,     False),
    # COMPRAS
    ("pedido",          "🛒", "Pedido de Compra",     "COMPRAS",     3,     False),
    ("compras_hist",    "📦", "Histórico de Compras", "COMPRAS",     None,  True),
    # FINANCEIRO
    ("financeiro",      "💳", "Financeiro",           "FINANCEIRO",  None,  True),
    # RELATÓRIOS
    ("relatorios",      "📊", "Relatórios",           "RELATÓRIOS",  None,  True),
    # CONFIG
    ("sincronizacao",   "🔄", "Sincronização",        "CONFIGURAÇÕES",None, False),
    ("usuarios",        "👤", "Usuários",             "CONFIGURAÇÕES",None, False),
]

def _pode_ver(aba_idx, is_placeholder):
    if is_placeholder: return False   # futuro
    if aba_idx is None: return True
    return aba_idx in _abas_perm

_MENU_VISIVEL = [
    m for m in _MENU_FULL
    if _pode_ver(m[4], m[5])
    and (m[0] not in ("usuarios","sincronizacao") or _is_admin)
]

if "pagina" not in st.session_state or st.session_state.pagina not in [m[0] for m in _MENU_VISIVEL]:
    st.session_state.pagina = _MENU_VISIVEL[0][0]

# ────────────────────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────────────────────
with st.sidebar:
    # 1) Logo fixa no topo
    st.markdown(f"""
    <div class="sb-logo">
      <div class="sb-logo-mark">⚡</div>
      <div class="sb-logo-text">PLUG ERP</div>
    </div>
    """, unsafe_allow_html=True)

    # 2) Seletor de loja (escondido visualmente, funcional)
    loja_opcoes = {"Todas as lojas": None, **{nome: lid for lid, nome in api.LOJAS.items()}}
    loja_sel_nome = st.selectbox("loja", list(loja_opcoes.keys()), key="loja_ativa", label_visibility="collapsed")
    loja_id = loja_opcoes[loja_sel_nome]

    # CSS para remover margens do selectbox e fazer parecer com o card do GestaoClick
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [data-testid="stSelectbox"] {
        margin: -12px 0 0 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
        border: none !important;
        border-radius: 0 !important;
        border-bottom: 1px solid var(--bor) !important;
        background: var(--sb2) !important;
        padding: 8px 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }
    /* remove gap entre botões do menu */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { margin: 0 !important; padding: 0 !important; }
    [data-testid="stSidebar"] .stButton { margin: 0 !important; }
    [data-testid="stSidebar"] .stButton > button { border-radius: 0 !important; margin: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # 3) Menu de navegação
    _grp = None
    _pg_ativo = st.session_state.pagina
    for pid, icon, label, grupo, aba_idx, _ in _MENU_VISIVEL:
        if grupo != _grp:
            st.markdown(f'<div class="nav-group">{grupo}</div>', unsafe_allow_html=True)
            _grp = grupo
        ativo = _pg_ativo == pid
        # Injetar CSS dinâmico para o item ativo via key única
        if ativo:
            st.markdown(f"""
            <style>
            [data-testid="stSidebar"] button[kind="secondary"][data-testid="baseButton-secondary"]:has(+ *) {{}}
            div[data-key="nav_{pid}"] button,
            [data-testid="stSidebar"] div:has(button:contains("{label}")) button {{
                background: {YEL_BG} !important;
                color: {YEL} !important;
                font-weight: 600 !important;
                border-left: 3px solid {YEL} !important;
                padding-left: 13px !important;
            }}
            </style>
            """, unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.pagina = pid
            st.rerun()

    # 4) Tema + Sair
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("☀️ Tema" if _dark else "🌙 Tema", use_container_width=True, key="btn_tema"):
        st.session_state.tema = "light" if _dark else "dark"
        st.rerun()
    if c2.button("🚪 Sair", use_container_width=True, key="btn_sair"):
        st.session_state.usuario_logado = None
        st.rerun()

    # 5) User footer
    ini = (_nome_usr[0] if _nome_usr else "U").upper()
    st.markdown(f"""
    <div class="sb-footer">
      <div class="sb-avatar">{ini}</div>
      <div>
        <div class="sb-user-name">{_nome_usr}</div>
        <div class="sb-user-role">{_setor_lbl}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Carrega cache e clip ──
cache = api.carregar_cache(loja_id)
clip  = st.session_state.get("clipboard")

# ── Cabeçalho da página ──
_pg_info = next((m for m in _MENU_VISIVEL if m[0] == st.session_state.pagina), _MENU_VISIVEL[0])
st.markdown(f"""
<div class="page-breadcrumb" style="margin-top:4px">{_pg_info[3]} <span>›</span> {_pg_info[2]}</div>
<div class="page-title">{_pg_info[1]}  {_pg_info[2]}</div>
<hr style="margin:6px 0 12px;border:none;border-top:1px solid var(--bor)">
""", unsafe_allow_html=True)

_pg = st.session_state.pagina




# ──────────────────────────────────────────────
# Helpers globais
# ──────────────────────────────────────────────

def variacoes_ordenadas(produto):
    return sorted(produto.get("variacoes", []), key=lambda v: v["variacao"].get("codigo", "") or "")


def montar_df_variacoes(produto, col_qtd="Quantidade"):
    dados = []
    for v in variacoes_ordenadas(produto):
        vd = v["variacao"]
        dados.append({
            "_variacao_id": vd["id"],
            "Código Var.": vd.get("codigo", ""),
            "Variação": vd["nome"] or "(sem nome)",
            "Estoque Atual": float(vd["estoque"]),
            col_qtd: 0,
        })
    return pd.DataFrame(dados)


def busca_produto_ui(key_prefix, cache_local, col_qtd="Quantidade"):
    termo = st.text_input("🔍 Buscar produto (nome ou código)", key=f"{key_prefix}_termo",
                          placeholder="ex: iPhone 15, S24, Aveludada...")
    prods = sorted(api.buscar_produtos(termo, cache_local) if termo else [],
                   key=lambda p: p.get("codigo_interno", "") or "")
    if termo and not prods:
        st.info("Nenhum produto encontrado.")
        return None, None
    if not prods:
        return None, None

    nomes = [f"{p['codigo_interno']} — {p['nome']}" for p in prods]
    esc = st.selectbox("Produto:", nomes, key=f"{key_prefix}_sel")
    produto = prods[nomes.index(esc)]

    variacoes = produto.get("variacoes", [])
    if not variacoes:
        st.warning("Produto sem variações.")
        return produto, None

    df = montar_df_variacoes(produto, col_qtd=col_qtd)

    filtro_var = st.text_input("🎨 Filtrar variação (cor, código...)",
                               key=f"{key_prefix}_filtro_var",
                               placeholder="ex: preto, azul, 001...")
    if filtro_var:
        mask = df["Variação"].str.lower().str.contains(filtro_var.lower(), na=False) | \
               df["Código Var."].str.lower().str.contains(filtro_var.lower(), na=False)
        df_view = df[mask].copy()
    else:
        df_view = df.copy()

    st.caption(f"{len(df_view)} de {len(df)} variação(ões) — preencha a quantidade nas que deseja incluir")

    # Cabeçalho fora do frame
    h1, h2, h3, h4 = st.columns([2, 4, 1, 2])
    h1.markdown("**Código**"); h2.markdown("**Variação**")
    h3.markdown("**Atual**"); h4.markdown(f"**{col_qtd}**")

    # Frame scrollável com as linhas
    qtds = {}
    frame = st.container(height=280)
    for _, row in df_view.iterrows():
        c1, c2, c3, c4 = frame.columns([2, 4, 1, 2])
        c1.write(row["Código Var."])
        c2.write(row["Variação"])
        c3.write(int(row["Estoque Atual"]))
        qtds[row.name] = c4.number_input(
            label="qtd", label_visibility="collapsed",
            min_value=0, step=1, value=int(row[col_qtd]),
            key=f"{key_prefix}_qtd_{produto['id']}_{row.name}_{filtro_var}"
        )

    # Reconstruir df completo com quantidades editadas
    for idx, qtd in qtds.items():
        df.loc[idx, col_qtd] = qtd
    edited = df.copy()
    edited["_variacao_id"] = df["_variacao_id"].values
    return produto, edited


def painel_etiquetas(itens, key_suffix=""):
    """Bloco de geração de etiquetas reutilizável."""
    st.divider()
    st.subheader("🏷️ Etiquetas")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏷️ Gerar URL de etiquetas", type="primary", use_container_width=True, key=f"etiq_url_{key_suffix}"):
            url = api.gerar_url_etiquetas(itens)
            st.markdown(f"### [👉 Abrir gerador de etiquetas]({url})")
            st.code(url, language=None)
    with col2:
        if st.button("📋 Enviar para aba Etiquetas", use_container_width=True, key=f"etiq_envia_{key_suffix}"):
            st.session_state.clipboard = {
                "tipo": "etiquetas",
                "origem": key_suffix,
                "itens": [
                    {"variacao_id": it["variacao_id"], "nome": it.get("produto_nome", "") + " / " + it.get("variacao_nome", ""), "quantidade": it["quantidade"]}
                    for it in itens
                ]
            }
            st.success("Lista enviada para a área de transferência! Vá para a aba **Etiquetas**.")


def painel_salvar(itens, tipo, key_suffix=""):
    """Bloco de salvar lista."""
    with st.expander("💾 Salvar esta lista"):
        nome_lista = st.text_input("Nome da lista", placeholder="ex: Entrada 14/06 - Plaza",
                                    key=f"nome_lista_{key_suffix}")
        if st.button("💾 Salvar", use_container_width=True, key=f"btn_salvar_{key_suffix}"):
            if not nome_lista:
                st.error("Digite um nome para a lista.")
            else:
                caminho = api.salvar_lista(nome_lista, tipo, itens, loja_id=loja_id, loja_nome=loja_sel_nome)
                st.success(f"Lista salva!")


def painel_carregar_lista(tipo, key_suffix="", retornar_arquivo=False):
    """Bloco de carregar lista salva. Se retornar_arquivo=True devolve (itens, arquivo)."""
    listas = api.listar_listas_salvas(tipo)
    _vazio = (None, None) if retornar_arquivo else None
    if not listas:
        return _vazio
    with st.expander(f"📂 Carregar lista salva ({len(listas)} disponíveis)"):
        opcoes = [f"{l['criado_em'][:16]} | {l['nome']} ({l.get('loja_nome','—')})" for l in listas]
        sel = st.selectbox("Lista:", opcoes, key=f"load_lista_{key_suffix}")
        lista_sel = listas[opcoes.index(sel)]
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Carregar", use_container_width=True, key=f"btn_load_{key_suffix}"):
                if retornar_arquivo:
                    return lista_sel["itens"], lista_sel["_arquivo"]
                return lista_sel["itens"]
        with col2:
            st.caption(f"{len(lista_sel['itens'])} itens")
    return _vazio


def df_lista_resumo(itens, colunas_extras=None):
    _df = pd.DataFrame(itens)
    _sort_cols = [c for c in ["cod_interno", "variacao_cod"] if c in _df.columns]
    df = _df.sort_values(_sort_cols) if _sort_cols else _df
    cols = ["cod_interno", "produto_nome", "variacao_cod", "variacao_nome", "quantidade"]
    if colunas_extras:
        cols += colunas_extras
    cols = [c for c in cols if c in df.columns]
    rename = {
        "cod_interno": "Cód.", "produto_nome": "Produto",
        "variacao_cod": "Cód. Var.", "variacao_nome": "Variação", "quantidade": "Qtd"
    }
    return df[cols].rename(columns=rename)


# ──────────────────────────────────────────────
# Roteador de páginas
# ──────────────────────────────────────────────
class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False

_NULL = _NullCtx()

def _guard(pg_name):
    return st.container() if _pg == pg_name else _NULL

aba1          = _guard("entrada")
aba2          = _guard("acerto")
aba3          = _guard("etiquetas")
aba4          = _guard("pedido")
aba5          = _guard("estoque_loja")
aba6          = _guard("disponibilidade")
aba7          = _guard("precos")
aba8          = _guard("novo_modelo")
aba9          = _guard("clonar_modelo")
aba_usuarios  = _guard("usuarios")

# ══════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════
if _pg == "dashboard":
    total_cache = cache.get("total", 0) if cache else 0
    sync_em = cache.get("sincronizado_em", "")[:10] if cache else "—"
    hora_nm = _nome_usr.split()[0] if _nome_usr else "você"
    st.markdown(f"<p style='font-size:1rem;margin-bottom:16px'>Olá, <b>{hora_nm}</b> 👋</p>", unsafe_allow_html=True)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, total_cache,        "Produtos no catálogo"),
        (c2, len(api.LOJAS),     "Lojas ativas"),
        (c3, len(_usuarios_db),  "Usuários"),
        (c4, sync_em,            "Última sincronização"),
    ]:
        col.markdown(f'<div class="stat-box"><div class="stat-val">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Status das lojas
    cols_lojas = st.columns(len(api.LOJAS))
    for col, (lid, lnome) in zip(cols_lojas, api.LOJAS.items()):
        c = api.carregar_cache(lid)
        t = c.get("total", 0) if c else 0
        s = c.get("sincronizado_em", "")[:10] if c else "—"
        badge = '<span class="badge badge-green">● Online</span>' if c else '<span class="badge badge-red">● Sem cache</span>'
        col.markdown(f"""
        <div class="card">
          <div class="card-header">🏪 {lnome}</div>
          <div class="stat-val" style="font-size:1.3rem">{t}</div>
          <div class="stat-lbl">produtos</div>
          <div style="margin-top:8px">{badge}</div>
          <div class="stat-lbl" style="margin-top:4px">sync {s}</div>
        </div>""", unsafe_allow_html=True)

    if clip:
        st.info(f"📋 Área de transferência: **{clip['tipo']}** — {len(clip['itens'])} itens · de: {clip.get('origem','—')}")
        if st.button("🗑️ Limpar transferência", key="dash_clip"):
            del st.session_state["clipboard"]
            st.rerun()

# ── páginas futuras (placeholder) ──
for _pid in ("clientes", "fornecedores", "vendas", "orcamentos", "compras_hist", "financeiro", "relatorios"):
    if _pg == _pid:
        st.markdown(f"""
        <div class="card" style="text-align:center;padding:3rem 2rem">
          <div style="font-size:3rem;margin-bottom:1rem">🚧</div>
          <div style="font-size:1rem;font-weight:600;margin-bottom:6px">Em desenvolvimento</div>
          <div style="color:{TXT2};font-size:0.82rem">Esta seção será integrada em breve com a API do GestaoClick.</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SINCRONIZAÇÃO
# ══════════════════════════════════════════════
if _pg == "sincronizacao":
    if cache:
        sincronizado = cache.get("sincronizado_em", "")[:16].replace("T", " às ")
        st.success(f"Cache atual: **{cache['total']}** produtos — {cache.get('loja_nome','—')} — sync {sincronizado}")
    else:
        st.warning("Nenhum cache para esta loja.")

    if st.button("🔄 Sincronizar Todas as Lojas", type="primary"):
        lojas_list = list(api.LOJAS.items())
        barra = st.progress(0)
        status_txt = st.empty()
        erros_sync = []
        for idx, (lid, lnome) in enumerate(lojas_list):
            status_txt.info(f"Sincronizando **{lnome}**… ({idx+1}/{len(lojas_list)})")
            def prog(pag, total, _lnome=lnome, _idx=idx, _n=len(lojas_list)):
                frac = (_idx + pag / max(total, 1)) / _n
                barra.progress(frac, text=f"{_lnome}: página {pag}/{total}")
            try:
                resultado = api.sincronizar_produtos(loja_id=lid, progress_callback=prog)
                if lid == loja_id:
                    cache = resultado
            except Exception as e:
                erros_sync.append(f"{lnome}: {e}")
        barra.progress(1.0)
        if erros_sync:
            status_txt.warning("Concluído com erros:\n" + "\n".join(erros_sync))
        else:
            status_txt.success(f"✅ {len(lojas_list)} lojas sincronizadas!")
        st.rerun()

    st.markdown('<div class="erp-card">', unsafe_allow_html=True)
    st.markdown("**Status por loja**")
    for lid, lnome in api.LOJAS.items():
        c = api.carregar_cache(lid)
        if c:
            s = c.get("sincronizado_em", "")[:16].replace("T", " às ")
            st.markdown(f"✅ **{lnome}** — {c['total']} produtos — {s}")
        else:
            st.markdown(f"⚠️ **{lnome}** — sem cache")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ABA 1 — ENTRADA DE MERCADORIA (SOMA)
# ══════════════════════════════════════════════
if _pg == "entrada":
    st.subheader("Entrada de Mercadoria")
    st.caption("Soma as quantidades ao estoque atual.")

    if loja_id:
        st.info(f"🏪 Loja: **{loja_sel_nome}**")
    else:
        st.warning("Selecione uma loja na barra lateral antes de confirmar a entrada.")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
        st.stop()

    if "itens_entrada" not in st.session_state:
        st.session_state.itens_entrada = []

    # Carregar da área de transferência
    clip = st.session_state.get("clipboard")
    if clip and clip.get("tipo") == "entrada":
        st.info(f"📋 Transferência disponível: **{len(clip['itens'])} itens** de '{clip.get('origem','—')}'")
        if st.button("📥 Importar transferência para esta lista", use_container_width=True):
            st.session_state.itens_entrada.extend(clip["itens"])
            del st.session_state["clipboard"]
            st.rerun()

    # Carregar lista salva
    itens_carregados = painel_carregar_lista("entrada", key_suffix="ent")
    if itens_carregados:
        st.session_state.itens_entrada = itens_carregados
        st.rerun()

    # Busca e adição
    produto_sel, edited = busca_produto_ui("ent", cache, col_qtd="Qtd Entrada")

    if produto_sel and edited is not None:
        selecionadas = edited[edited["Qtd Entrada"] > 0]
        st.caption(f"{len(selecionadas)} variação(ões) com quantidade.")

        if st.button("➕ Adicionar à lista", use_container_width=True):
            if len(selecionadas) == 0:
                st.warning("Preencha a quantidade em pelo menos uma variação.")
            else:
                for _, row in selecionadas.iterrows():
                    st.session_state.itens_entrada.append({
                        "produto_id": produto_sel["id"],
                        "produto_nome": produto_sel["nome"],
                        "cod_interno": produto_sel.get("codigo_interno", ""),
                        "variacao_id": row["_variacao_id"],
                        "variacao_cod": row["Código Var."],
                        "variacao_nome": row["Variação"],
                        "quantidade": int(row["Qtd Entrada"])
                    })
                st.success(f"{len(selecionadas)} adicionada(s)!")

    # Lista acumulada
    st.divider()
    st.subheader(f"📝 Lista de entrada ({len(st.session_state.itens_entrada)} itens)")

    if st.session_state.itens_entrada:
        st.dataframe(df_lista_resumo(st.session_state.itens_entrada), use_container_width=True, hide_index=True)

        painel_salvar(st.session_state.itens_entrada, "entrada", key_suffix="ent")

        col_x, col_y, col_z = st.columns(3)
        with col_x:
            if st.button("🗑️ Limpar lista", use_container_width=True):
                st.session_state.itens_entrada = []
                st.rerun()
        with col_y:
            if st.button("📊 Confirmar entrada no sistema", type="primary", use_container_width=True):
                if not loja_id:
                    st.error("Selecione uma loja antes de confirmar.")
                else:
                    barra = st.progress(0)
                    def prog_ent(atual, total):
                        barra.progress(atual / total, text=f"{atual}/{total}...")
                    resultados = api.atualizar_estoque_lote(
                        st.session_state.itens_entrada, loja_id=loja_id, modo="soma",
                        progress_callback=prog_ent
                    )
                    ok = [r for r in resultados if r["ok"]]
                    erros = [r for r in resultados if not r["ok"]]
                    if ok:
                        st.success(f"✅ {len(ok)} variação(ões) com estoque somado em **{loja_sel_nome}**!")
                        st.session_state.itens_entrada_ok = [r for r in resultados if r["ok"]]
                    for e in erros:
                        st.error(f"❌ {e['produto_nome']} / {e['variacao_nome']}: {e['erro']}")
                    if not erros:
                        st.session_state.itens_entrada = []
        with col_z:
            # Transferir para acerto
            if st.button("↗️ Enviar para Acerto de Estoque", use_container_width=True):
                st.session_state.clipboard = {
                    "tipo": "acerto",
                    "origem": "Entrada de Mercadoria",
                    "itens": list(st.session_state.itens_entrada)
                }
                st.success("Enviado para área de transferência! Vá para **Acerto de Estoque**.")

        # Etiquetas após entrada
        if st.session_state.get("itens_entrada_ok"):
            painel_etiquetas(st.session_state.itens_entrada_ok, key_suffix="ent_ok")
            if st.button("✅ Concluído", key="concluido_ent"):
                del st.session_state["itens_entrada_ok"]
                st.rerun()
    else:
        st.info("Adicione produtos à lista acima.")


# ══════════════════════════════════════════════
# ABA 2 — ACERTO DE ESTOQUE (SET ABSOLUTO)
# ══════════════════════════════════════════════
if _pg == "acerto":
    st.subheader("Acerto de Estoque")
    st.caption("Define o valor absoluto do estoque (substitui o atual). Use para inventário ou correção.")

    if loja_id:
        st.info(f"🏪 Loja: **{loja_sel_nome}**")
    else:
        st.warning("Selecione uma loja antes de confirmar o acerto.")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
        st.stop()

    if "itens_acerto" not in st.session_state:
        st.session_state.itens_acerto = []

    # Importar da transferência
    clip = st.session_state.get("clipboard")
    if clip and clip.get("tipo") == "acerto":
        st.info(f"📋 Transferência: **{len(clip['itens'])} itens** de '{clip.get('origem','—')}'")
        if st.button("📥 Importar para Acerto de Estoque", use_container_width=True):
            st.session_state.itens_acerto.extend(clip["itens"])
            del st.session_state["clipboard"]
            st.rerun()

    itens_carregados2 = painel_carregar_lista("acerto", key_suffix="ac")
    if itens_carregados2:
        st.session_state.itens_acerto = itens_carregados2
        st.rerun()

    produto_ac, edited_ac = busca_produto_ui("ac", cache, col_qtd="Qtd Correta")

    if produto_ac and edited_ac is not None:
        selecionadas_ac = edited_ac[edited_ac["Qtd Correta"] > 0]
        st.caption(f"{len(selecionadas_ac)} variação(ões) com quantidade.")

        if st.button("➕ Adicionar à lista", use_container_width=True, key="add_acerto"):
            if len(selecionadas_ac) == 0:
                st.warning("Preencha a quantidade em pelo menos uma variação.")
            else:
                for _, row in selecionadas_ac.iterrows():
                    st.session_state.itens_acerto.append({
                        "produto_id": produto_ac["id"],
                        "produto_nome": produto_ac["nome"],
                        "cod_interno": produto_ac.get("codigo_interno", ""),
                        "variacao_id": row["_variacao_id"],
                        "variacao_cod": row["Código Var."],
                        "variacao_nome": row["Variação"],
                        "quantidade": int(row["Qtd Correta"])
                    })
                st.success(f"{len(selecionadas_ac)} adicionada(s)!")

    st.divider()
    st.subheader(f"📝 Lista de acerto ({len(st.session_state.itens_acerto)} itens)")

    if st.session_state.itens_acerto:
        st.dataframe(df_lista_resumo(st.session_state.itens_acerto), use_container_width=True, hide_index=True)

        painel_salvar(st.session_state.itens_acerto, "acerto", key_suffix="ac")

        col_x, col_y, col_z = st.columns(3)
        with col_x:
            if st.button("🗑️ Limpar lista", use_container_width=True, key="limpar_acerto"):
                st.session_state.itens_acerto = []
                st.rerun()
        with col_y:
            if st.button("📊 Confirmar acerto no sistema", type="primary", use_container_width=True):
                if not loja_id:
                    st.error("Selecione uma loja.")
                else:
                    barra = st.progress(0)
                    def prog_ac(atual, total):
                        barra.progress(atual / total, text=f"{atual}/{total}...")
                    resultados = api.atualizar_estoque_lote(
                        st.session_state.itens_acerto, loja_id=loja_id, modo="set",
                        progress_callback=prog_ac
                    )
                    ok = [r for r in resultados if r["ok"]]
                    erros = [r for r in resultados if not r["ok"]]
                    if ok:
                        st.success(f"✅ {len(ok)} estoque(s) definido(s) em **{loja_sel_nome}**!")
                        st.session_state.itens_acerto_ok = [r for r in resultados if r["ok"]]
                    for e in erros:
                        st.error(f"❌ {e['produto_nome']} / {e['variacao_nome']}: {e['erro']}")
                    if not erros:
                        st.session_state.itens_acerto = []
        with col_z:
            if st.button("↗️ Enviar para Entrada", use_container_width=True, key="ac_para_entrada"):
                st.session_state.clipboard = {
                    "tipo": "entrada",
                    "origem": "Acerto de Estoque",
                    "itens": list(st.session_state.itens_acerto)
                }
                st.success("Enviado! Vá para **Entrada de Mercadoria**.")

        if st.session_state.get("itens_acerto_ok"):
            painel_etiquetas(st.session_state.itens_acerto_ok, key_suffix="ac_ok")
            if st.button("✅ Concluído", key="concluido_ac"):
                del st.session_state["itens_acerto_ok"]
                st.rerun()
    else:
        st.info("Adicione produtos à lista acima.")


# ══════════════════════════════════════════════
# ABA 3 — ETIQUETAS
# ══════════════════════════════════════════════
if _pg == "etiquetas":
    st.subheader("Gerar Etiquetas")
    st.caption("Monte uma lista de variações + quantidades e gere o link de impressão.")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
    else:
        if "etiq_itens" not in st.session_state:
            st.session_state.etiq_itens = []

        # Importar da transferência
        clip = st.session_state.get("clipboard")
        if clip and clip.get("tipo") == "etiquetas":
            st.info(f"📋 Transferência: **{len(clip['itens'])} itens** de '{clip.get('origem','—')}'")
            if st.button("📥 Importar para Etiquetas", use_container_width=True):
                st.session_state.etiq_itens.extend(clip["itens"])
                del st.session_state["clipboard"]
                st.rerun()

        itens_etiq_load = painel_carregar_lista("etiquetas", key_suffix="etiq")
        if itens_etiq_load:
            st.session_state.etiq_itens = itens_etiq_load
            st.rerun()

        prod2, ed2 = busca_produto_ui("etiq", cache, col_qtd="Quantidade")

        if prod2 and ed2 is not None:
            sel2 = ed2[ed2["Quantidade"] > 0]
            st.caption(f"{len(sel2)} variação(ões) com quantidade.")
            if st.button("➕ Adicionar à lista", use_container_width=True, key="add_etiq"):
                if len(sel2) == 0:
                    st.warning("Preencha a quantidade em pelo menos uma variação.")
                else:
                    for _, row in sel2.iterrows():
                        st.session_state.etiq_itens.append({
                            "variacao_id": row["_variacao_id"],
                            "produto_nome": prod2["nome"],
                            "variacao_nome": row["Variação"],
                            "cod_interno": prod2.get("codigo_interno", ""),
                            "variacao_cod": row["Código Var."],
                            "nome": f"{prod2['nome']} / {row['Variação']}",
                            "quantidade": int(row["Quantidade"])
                        })
                    st.success(f"{len(sel2)} adicionado(s)!")

        if st.session_state.etiq_itens:
            st.divider()
            df_etiq = pd.DataFrame(st.session_state.etiq_itens)
            st.dataframe(
                df_etiq[["nome", "quantidade"]].rename(columns={"nome": "Produto / Variação", "quantidade": "Qtd"}),
                use_container_width=True, hide_index=True
            )

            painel_salvar(st.session_state.etiq_itens, "etiquetas", key_suffix="etiq")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Limpar", key="limpar_etiq", use_container_width=True):
                    st.session_state.etiq_itens = []
                    st.rerun()
            with col2:
                if st.button("🏷️ Gerar URL de etiquetas", type="primary", use_container_width=True):
                    url = api.gerar_url_etiquetas(st.session_state.etiq_itens)
                    st.markdown(f"### [👉 Imprimir etiquetas]({url})")
                    st.code(url, language=None)
        else:
            st.info("Adicione produtos ou importe de outra aba.")


# ══════════════════════════════════════════════
# ABA 4 — PEDIDO DE COMPRA
# ══════════════════════════════════════════════
if _pg == "pedido":
    st.subheader("Pedido de Compra ao Fornecedor")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
    else:
        if "pedido_itens" not in st.session_state:
            st.session_state.pedido_itens = []
        if "pedido_undo" not in st.session_state:
            st.session_state.pedido_undo = []

        def _pedido_snapshot():
            import copy
            st.session_state.pedido_undo.append((
                copy.deepcopy(st.session_state.pedido_itens),
                copy.deepcopy(st.session_state.get("pedido_avulsos", []))
            ))
            if len(st.session_state.pedido_undo) > 20:
                st.session_state.pedido_undo.pop(0)

        # Importar da transferência
        clip = st.session_state.get("clipboard")
        if clip and clip.get("tipo") == "pedido":
            st.info(f"📋 Transferência: **{len(clip['itens'])} itens**")
            if st.button("📥 Importar para Pedido", use_container_width=True):
                st.session_state.pedido_itens.extend(clip["itens"])
                del st.session_state["clipboard"]
                st.rerun()

        if "pedido_lista_arquivo" not in st.session_state:
            st.session_state.pedido_lista_arquivo = None

        itens_ped_load, arq_ped_load = painel_carregar_lista("pedido", key_suffix="ped", retornar_arquivo=True)
        if itens_ped_load:
            st.session_state.pedido_itens = itens_ped_load
            st.session_state.pedido_lista_arquivo = arq_ped_load
            st.rerun()

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fornecedor_global = st.text_input("🏭 Fornecedor", placeholder="ex: Distribuidora ABC",
                                               key="fornecedor_global")
        with col_f2:
            data_pedido = st.date_input("📅 Data", value=date.today(), key="data_pedido")
        with col_f3:
            obs_pedido = st.text_input("📝 Observações", placeholder="ex: entrega até sexta", key="obs_pedido")

        # ── Custos por tipo ──

        st.divider()
        st.markdown("**Produtos cadastrados no sistema**")
        prod_p, ed_p = busca_produto_ui("pedido", cache, col_qtd="Qtd a Pedir")

        if prod_p and ed_p is not None:
            forn_item = st.text_input("Fornecedor deste produto (em branco = usar global)", key="forn_item",
                                       placeholder=fornecedor_global or "Fornecedor")
            sel_p = ed_p[ed_p["Qtd a Pedir"] > 0]
            st.caption(f"{len(sel_p)} variação(ões) com quantidade.")

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("➕ Adicionar ao pedido", use_container_width=True):
                    if len(sel_p) == 0:
                        st.warning("Preencha a quantidade em pelo menos uma variação.")
                    else:
                        _pedido_snapshot()
                        forn_usado = forn_item.strip() or fornecedor_global or "—"
                        for _, row in sel_p.iterrows():
                            st.session_state.pedido_itens.append({
                                "fornecedor": forn_usado,
                                "produto_id": prod_p["id"],
                                "produto_nome": prod_p["nome"],
                                "cod_interno": prod_p.get("codigo_interno", ""),
                                "variacao_id": row["_variacao_id"],
                                "variacao_cod": row["Código Var."],
                                "variacao_nome": row["Variação"],
                                "estoque_atual": int(row["Estoque Atual"]),
                                "quantidade": int(row["Qtd a Pedir"]),
                                "valor_custo": prod_p.get("valor_custo", "0.00"),
                            })
                        st.success(f"{len(sel_p)} adicionada(s)!")

            # Kits pré-definidos por gênero
            CORES_MASC        = [("preto", 2), ("marrom", 1), ("azul marinho", 1), ("cinza chumbo", 1)]
            CORES_FEM         = [("lilás", 1), ("marsala", 1), ("marrom", 1)]
            CORES_MASC_PACOTE = [("preto", 3), ("azul marinho", 2), ("verde militar", 1),
                                  ("marrom", 1), ("cinza chumbo", 2)]
            CORES_FEM_PACOTE  = [("lilás", 2), ("pink", 1), ("rosa", 1), ("marsala", 2),
                                  ("vinho", 1), ("roxo", 1), ("marrom", 1), ("nude", 1)]

            def _sl(lista, extra="silicone"):
                return [([cor, extra], qtd) for cor, qtd in lista]

            SL_MASC        = _sl(CORES_MASC)
            SL_FEM         = _sl(CORES_FEM)
            SL_MASC_PACOTE = _sl(CORES_MASC_PACOTE)
            SL_FEM_PACOTE  = _sl(CORES_FEM_PACOTE)

            VR_MASC        = _sl(CORES_MASC)
            VR_FEM         = _sl(CORES_FEM)
            VR_MASC_PACOTE = _sl(CORES_MASC_PACOTE)
            VR_FEM_PACOTE  = _sl(CORES_FEM_PACOTE)

            def _adicionar_kit(cores_qtds, label_kit, observacao=""):
                _pedido_snapshot()
                forn_usado = forn_item.strip() or fornecedor_global or "—"
                adicionados, nao_encontrados = [], []
                for cor, qtd in cores_qtds:
                    # cor pode ser string simples ou lista de termos (todos devem estar presentes)
                    termos = [cor] if isinstance(cor, str) else cor
                    mask = ed_p["Variação"].str.lower().apply(
                        lambda v: all(t.lower() in (v or "") for t in termos)
                    )
                    match = ed_p[mask]
                    if match.empty:
                        nao_encontrados.append(cor)
                    else:
                        row = match.iloc[0]
                        st.session_state.pedido_itens.append({
                            "fornecedor": forn_usado,
                            "produto_id": prod_p["id"],
                            "produto_nome": prod_p["nome"],
                            "cod_interno": prod_p.get("codigo_interno", ""),
                            "variacao_id": row["_variacao_id"],
                            "variacao_cod": row["Código Var."],
                            "variacao_nome": row["Variação"],
                            "estoque_atual": int(row["Estoque Atual"]),
                            "quantidade": qtd,
                            "valor_custo": prod_p.get("valor_custo", "0.00"),
                            "observacao": observacao,
                        })
                        adicionados.append(f"{row['Variação']} ×{qtd}")
                if adicionados:
                    st.success(f"Kit {label_kit}: " + ", ".join(adicionados))
                if nao_encontrados:
                    labels = ["+".join(t) if isinstance(t, list) else t for t in nao_encontrados]
                    st.warning(f"Cores não encontradas: {', '.join(labels)}")

            with col_btn2:
                if st.button("👔 Masculino", use_container_width=True, key="kit_masc"):
                    _adicionar_kit(CORES_MASC, "Masculino")
            with col_btn3:
                if st.button("👗 Feminino", use_container_width=True, key="kit_fem"):
                    _adicionar_kit(CORES_FEM, "Feminino")

            col_btn4, col_btn5 = st.columns(2)
            with col_btn4:
                if st.button("📦 Pacote Masculino", use_container_width=True, key="kit_masc_pac"):
                    _adicionar_kit(CORES_MASC_PACOTE, "Pacote Masculino")
            with col_btn5:
                if st.button("📦 Pacote Feminino", use_container_width=True, key="kit_fem_pac"):
                    _adicionar_kit(CORES_FEM_PACOTE, "Pacote Feminino")

            _e_iphone = "iphone" in (prod_p.get("nome", "") + prod_p.get("nome_grupo", "")).lower()

            def _blocos_sl_vr_magsafe():
                st.caption("**Silicone Líquido**")
                col_sl1, col_sl2 = st.columns(2)
                with col_sl1:
                    if st.button("💧 SL Masculino", use_container_width=True, key="kit_sl_masc"):
                        _adicionar_kit(SL_MASC, "SL Masculino")
                with col_sl2:
                    if st.button("💧 SL Feminino", use_container_width=True, key="kit_sl_fem"):
                        _adicionar_kit(SL_FEM, "SL Feminino")
                col_sl3, col_sl4 = st.columns(2)
                with col_sl3:
                    if st.button("📦 SL Pacote Masculino", use_container_width=True, key="kit_sl_masc_pac"):
                        _adicionar_kit(SL_MASC_PACOTE, "SL Pacote Masculino")
                with col_sl4:
                    if st.button("📦 SL Pacote Feminino", use_container_width=True, key="kit_sl_fem_pac"):
                        _adicionar_kit(SL_FEM_PACOTE, "SL Pacote Feminino")

                st.caption("**Very Rio**")
                col_vr1, col_vr2 = st.columns(2)
                with col_vr1:
                    if st.button("🌊 VR Masculino", use_container_width=True, key="kit_vr_masc"):
                        _adicionar_kit(VR_MASC, "VR Masculino", observacao="Very Rio")
                with col_vr2:
                    if st.button("🌊 VR Feminino", use_container_width=True, key="kit_vr_fem"):
                        _adicionar_kit(VR_FEM, "VR Feminino", observacao="Very Rio")
                col_vr3, col_vr4 = st.columns(2)
                with col_vr3:
                    if st.button("📦 VR Pacote Masculino", use_container_width=True, key="kit_vr_masc_pac"):
                        _adicionar_kit(VR_MASC_PACOTE, "VR Pacote Masculino", observacao="Very Rio")
                with col_vr4:
                    if st.button("📦 VR Pacote Feminino", use_container_width=True, key="kit_vr_fem_pac"):
                        _adicionar_kit(VR_FEM_PACOTE, "VR Pacote Feminino", observacao="Very Rio")

                st.caption("**MagSafe**")

                @st.dialog("🔮 MagSafe — tipo")
                def _dialog_magsafe():
                    with st.form("form_magsafe", clear_on_submit=True):
                        tipo_ms = st.text_input("Tipo do MagSafe", placeholder="ex: Silicone, Couro, Clear...")
                        col_ok, col_cancel = st.columns(2)
                        with col_ok:
                            submitted_ms = st.form_submit_button("✅ Adicionar", use_container_width=True)
                        with col_cancel:
                            cancelado_ms = st.form_submit_button("Cancelar", use_container_width=True)
                    if submitted_ms:
                        obs = f"MagSafe {tipo_ms}".strip() if tipo_ms else "MagSafe"
                        _adicionar_kit([(["119,99", "magsafe"], 3)], "MagSafe", observacao=obs)
                        st.rerun()
                    if cancelado_ms:
                        st.rerun()

                if st.button("🔮 MagSafe ×3", use_container_width=True, key="kit_magsafe"):
                    _dialog_magsafe()

            if _e_iphone:
                _blocos_sl_vr_magsafe()
            else:
                with st.expander("➕ Mais opções (Silicone Líquido / Very Rio / MagSafe)"):
                    _blocos_sl_vr_magsafe()

            st.caption("**Diversos**")
            col_btn6, col_btn7 = st.columns(2)
            with col_btn6:
                if st.button("✨ Diversos Brilho ×3", use_container_width=True, key="kit_div_brilho"):
                    _adicionar_kit([(["59,99", "diversos"], 3)], "Diversos Brilho", observacao="Diversos Brilho")
            with col_btn7:
                if st.button("💪 Diversos Masculino ×3", use_container_width=True, key="kit_div_masc"):
                    _adicionar_kit([(["39,99", "diversos"], 3)], "Diversos Masculino", observacao="Diversos Masculino")

        if "pedido_avulsos" not in st.session_state:
            st.session_state.pedido_avulsos = []

        with st.form("form_avulso", clear_on_submit=True):
            col_av1, col_av2, col_av3, col_av4, col_av5 = st.columns([3, 2, 1, 1, 1])
            with col_av1:
                av_desc = st.text_input("Descrição do produto", placeholder="ex: Capa iPhone 18 Pro Aveludada Preta")
            with col_av2:
                av_forn = st.text_input("Fornecedor", placeholder=fornecedor_global or "—")
            with col_av3:
                av_qtd = st.number_input("Qtd", min_value=1, value=1, step=1)
            with col_av4:
                av_custo = st.text_input("Custo unit.", value="0.00")
            with col_av5:
                st.write("")
                st.write("")
                submitted_av = st.form_submit_button("➕", use_container_width=True)
            if submitted_av and av_desc:
                _pedido_snapshot()
                st.session_state.pedido_avulsos.append({
                    "fornecedor": av_forn.strip() or fornecedor_global or "—",
                    "cod_interno": "NOVO",
                    "produto_nome": av_desc,
                    "variacao_cod": "",
                    "variacao_nome": "",
                    "estoque_atual": 0,
                    "quantidade": int(av_qtd),
                    "valor_custo": av_custo,
                    "_avulso": True,
                })
                st.rerun()

        if st.session_state.pedido_avulsos:
            df_av = pd.DataFrame(st.session_state.pedido_avulsos)
            df_av["total"] = df_av["quantidade"] * pd.to_numeric(df_av["valor_custo"], errors="coerce").fillna(0)
            st.dataframe(
                df_av[["fornecedor", "produto_nome", "quantidade", "valor_custo", "total"]].rename(columns={
                    "fornecedor": "Fornecedor", "produto_nome": "Descrição",
                    "quantidade": "Qtd", "valor_custo": "Custo Unit.", "total": "Total"
                }),
                use_container_width=True, hide_index=True
            )
            if st.button("🗑️ Limpar produtos avulsos", use_container_width=True, key="limpar_avulsos"):
                st.session_state.pedido_avulsos = []
                st.rerun()

        st.divider()
        st.subheader(f"🛒 Pedido ({len(st.session_state.pedido_itens) + len(st.session_state.get('pedido_avulsos', []))} itens)")

        todos_itens_ped = st.session_state.pedido_itens + st.session_state.get("pedido_avulsos", [])

        if todos_itens_ped:
            _df_ped_raw = pd.DataFrame(todos_itens_ped)
            _sort_cols = [c for c in ["produto_nome", "variacao_nome"] if c in _df_ped_raw.columns]
            df_ped = _df_ped_raw.sort_values(_sort_cols, key=lambda s: s.str.lower()) if _sort_cols else _df_ped_raw
            if "observacao" not in df_ped.columns:
                df_ped["observacao"] = ""
            df_ped["observacao"] = df_ped["observacao"].fillna("")
            df_ped["total"] = df_ped["quantidade"] * pd.to_numeric(df_ped["valor_custo"], errors="coerce").fillna(0)
            total_est = df_ped["total"].sum()

            # Destacar avulsos com cor diferente via caption
            n_cad = len(st.session_state.pedido_itens)
            n_av = len(st.session_state.get("pedido_avulsos", []))
            st.caption(f"✅ {n_cad} cadastrado(s) no sistema  |  🆕 {n_av} novo(s) / não cadastrado(s)")

            # Diálogo de edição de linha
            @st.dialog("✏️ Editar item do pedido")
            def _dialog_editar_item(lista_key, idx):
                lst = st.session_state[lista_key]
                it = lst[idx]
                novo_forn = st.text_input("Fornecedor", value=it.get("fornecedor", ""), key="ded_forn")
                novo_prod = st.text_input("Produto", value=it.get("produto_nome", ""), key="ded_prod",
                                          disabled=not it.get("_avulso"))
                novo_var  = st.text_input("Variação", value=it.get("variacao_nome", ""), key="ded_var",
                                          disabled=not it.get("_avulso"))
                novo_qtd  = st.number_input("Quantidade", min_value=1, value=int(it.get("quantidade", 1)),
                                             step=1, key="ded_qtd")
                novo_custo = st.text_input("Custo unit.", value=str(it.get("valor_custo", "0.00")), key="ded_custo")
                novo_obs  = st.text_input("Observação", value=it.get("observacao", ""), key="ded_obs")
                col_ok, col_cancel = st.columns(2)
                def _fechar_dialog():
                    st.session_state.pop("_editar_lista", None)
                    st.session_state.pop("_editar_idx", None)

                with col_ok:
                    if st.button("💾 Salvar", use_container_width=True, key="ded_save"):
                        lst[idx]["fornecedor"]   = novo_forn
                        lst[idx]["quantidade"]   = int(novo_qtd)
                        lst[idx]["valor_custo"]  = novo_custo
                        lst[idx]["observacao"]   = novo_obs
                        if it.get("_avulso"):
                            lst[idx]["produto_nome"]  = novo_prod
                            lst[idx]["variacao_nome"] = novo_var
                        st.session_state[lista_key] = lst
                        _fechar_dialog()
                        st.rerun()
                with col_cancel:
                    if st.button("Cancelar", use_container_width=True, key="ded_cancel"):
                        _fechar_dialog()
                        st.rerun()

            # Gatilho do diálogo via session_state
            if st.session_state.get("_editar_lista"):
                _dialog_editar_item(
                    st.session_state["_editar_lista"],
                    st.session_state["_editar_idx"]
                )

            # Tabela com botões por linha
            hdr = st.columns([2, 3, 3, 2, 1, 1, 0.7, 0.7])
            for txt, col in zip(["Fornecedor","Produto","Variação","Obs.","Qtd","Custo","✏️","🗑️"], hdr):
                col.markdown(f"**{txt}**")

            def _fmt_brl(v):
                try:
                    return f"R$ {float(str(v).replace(',', '.')):.2f}".replace(".", ",", 1) if float(str(v).replace(",", ".")) < 1000 else f"R$ {float(str(v).replace(',', '.')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v)

            # itera sobre pedido_itens depois pedido_avulsos
            total_calculado = 0.0
            for lista_key, lista in [("pedido_itens", st.session_state.pedido_itens),
                                      ("pedido_avulsos", st.session_state.get("pedido_avulsos", []))]:
                for idx, it in enumerate(lista):
                    cols = st.columns([2, 3, 3, 2, 1, 1, 0.7, 0.7])
                    tag = "🆕 " if it.get("_avulso") else ""
                    cols[0].write(it.get("fornecedor", "—"))
                    cols[1].write(tag + it.get("produto_nome", ""))
                    cols[2].write(it.get("variacao_nome", ""))
                    cols[3].write(it.get("observacao", ""))
                    nova_qtd = cols[4].number_input(
                        label="qtd", label_visibility="collapsed",
                        min_value=0, step=1, value=int(it.get("quantidade", 0)),
                        key=f"ped_qtd_{lista_key}_{idx}"
                    )
                    lista[idx]["quantidade"] = nova_qtd
                    try:
                        custo_f = float(str(it.get("valor_custo", "0")).replace(",", "."))
                    except Exception:
                        custo_f = 0.0
                    total_calculado += nova_qtd * custo_f
                    cols[5].write(_fmt_brl(it.get("valor_custo", "0")))
                    if cols[6].button("✏️", key=f"edit_{lista_key}_{idx}"):
                        st.session_state["_editar_lista"] = lista_key
                        st.session_state["_editar_idx"]   = idx
                        st.rerun()
                    if cols[7].button("🗑️", key=f"del_{lista_key}_{idx}"):
                        lista.pop(idx)
                        st.session_state[lista_key] = lista
                        st.rerun()
            st.divider()
            st.metric("💰 Total estimado",
                      f"R$ {total_calculado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            arq_atual = st.session_state.get("pedido_lista_arquivo")
            if arq_atual:
                if st.button(f"💾 Salvar na lista atual", use_container_width=True, key="ped_salvar_atual"):
                    import json as _json
                    caminho = os.path.join(api.DIR_LISTAS, arq_atual)
                    with open(caminho, encoding="utf-8") as _f:
                        dados_arq = _json.load(_f)
                    dados_arq["itens"] = todos_itens_ped
                    dados_arq["atualizado_em"] = datetime.now().isoformat()
                    with open(caminho, "w", encoding="utf-8") as _f:
                        _json.dump(dados_arq, _f, ensure_ascii=False, indent=2)
                    st.success(f"✅ Lista atualizada!")
            painel_salvar(todos_itens_ped, "pedido", key_suffix="ped")

            col_a, col_b, col_c, col_d, col_e = st.columns(5)
            # linha de exportação simplificada (produto / variação / qtd)
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                buf_simples = io.BytesIO()
                df_simples = df_ped[["produto_nome", "variacao_nome", "observacao", "quantidade"]].copy()
                df_simples.columns = ["Produto", "Variação", "Obs.", "Qtd"]
                with pd.ExcelWriter(buf_simples, engine="openpyxl") as wr:
                    df_simples.to_excel(wr, index=False, sheet_name="Pedido")
                buf_simples.seek(0)
                st.download_button("📄 Excel simplificado",
                                   data=buf_simples,
                                   file_name=f"pedido_simples_{data_pedido}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with col_s2:
                if st.button("📋 Texto simplificado", use_container_width=True, key="txt_simples"):
                    linhas_s = [f"PEDIDO — {fornecedor_global or '—'} — {data_pedido}", "=" * 50]
                    for _, r in df_ped.iterrows():
                        obs = str(r["observacao"]).strip() if r["observacao"] else ""
                        obs_s = f" | {obs}" if obs else ""
                        linhas_s.append(f"{r['produto_nome']} | {r['variacao_nome']}{obs_s} | {int(r['quantidade'])} un")
                    st.text_area("Copie:", "\n".join(linhas_s), height=220, key="txt_simples_area")
            with col_s3:
                pdf_simples = gerar_pdf_pedido(df_ped, fornecedor_global or "—", str(data_pedido), simplificado=True)
                st.download_button("📑 PDF simplificado (fornecedor)",
                                   data=pdf_simples,
                                   file_name=f"pedido_simples_{data_pedido}.pdf",
                                   mime="application/pdf",
                                   use_container_width=True)
            with col_s4:
                pdf_completo = gerar_pdf_pedido(df_ped, fornecedor_global or "—", str(data_pedido), simplificado=False)
                st.download_button("📑 PDF completo",
                                   data=pdf_completo,
                                   file_name=f"pedido_{data_pedido}.pdf",
                                   mime="application/pdf",
                                   use_container_width=True)
            with col_a:
                if st.button("🗑️ Limpar tudo", use_container_width=True, key="limpar_ped"):
                    _pedido_snapshot()
                    st.session_state.pedido_itens = []
                    st.session_state.pedido_avulsos = []
                    st.rerun()
            with col_e:
                n_undo = len(st.session_state.get("pedido_undo", []))
                if st.button(f"↩️ Desfazer ({n_undo})", use_container_width=True,
                             key="ped_undo", disabled=n_undo == 0):
                    itens_ant, avulsos_ant = st.session_state.pedido_undo.pop()
                    st.session_state.pedido_itens   = itens_ant
                    st.session_state.pedido_avulsos = avulsos_ant
                    st.rerun()
            with col_b:
                buffer = io.BytesIO()
                df_exp = df_ped[["fornecedor", "cod_interno", "produto_nome", "variacao_nome",
                                  "observacao", "estoque_atual", "quantidade", "valor_custo", "total"]].copy()
                df_exp.columns = ["Fornecedor", "Cód.", "Produto", "Variação",
                                   "Obs.", "Estoque", "Pedir", "Custo Unit.", "Total Est."]
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_exp.to_excel(writer, index=False, sheet_name="Pedido")
                buffer.seek(0)
                st.download_button("📥 Excel", data=buffer,
                                   file_name=f"pedido_{fornecedor_global or 'forn'}_{data_pedido}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with col_c:
                if st.button("↗️ Enviar cadastrados p/ Entrada", use_container_width=True, key="ped_para_entrada"):
                    itens_entrada = [
                        {k: v for k, v in it.items() if k not in ("estoque_atual", "_avulso")}
                        for it in st.session_state.pedido_itens
                    ]
                    st.session_state.clipboard = {
                        "tipo": "entrada",
                        "origem": f"Pedido ({fornecedor_global or '—'})",
                        "itens": itens_entrada
                    }
                    st.success("Enviado! Vá para **Entrada de Mercadoria** quando a mercadoria chegar.")
            with col_d:
                if st.button("📋 Texto do pedido", use_container_width=True):
                    linhas = [f"PEDIDO — {fornecedor_global or '—'} — {data_pedido}", "=" * 60]
                    forn_at = None
                    for _, r in df_ped.iterrows():
                        if r["fornecedor"] != forn_at:
                            forn_at = r["fornecedor"]
                            linhas.append(f"\n[ {forn_at} ]")
                        novo_tag = " 🆕 NOVO" if r.get("cod_interno") == "NOVO" else ""
                        linhas.append(
                            f"  {r['cod_interno']} | {r['produto_nome']} | {r['variacao_nome']} "
                            f"| Pedir: {r['quantidade']}{novo_tag}"
                        )
                    linhas += ["=" * 60, f"TOTAL: R$ {total_est:,.2f}"]
                    if obs_pedido:
                        linhas.append(f"OBS: {obs_pedido}")
                    st.text_area("Copie:", "\n".join(linhas), height=250)

            # Etiquetas só dos cadastrados (têm variacao_id)
            itens_com_id = [it for it in todos_itens_ped if it.get("variacao_id")]
            if itens_com_id:
                painel_etiquetas(
                    [{"variacao_id": it["variacao_id"], "produto_nome": it["produto_nome"],
                      "variacao_nome": it["variacao_nome"], "quantidade": it["quantidade"]}
                     for it in itens_com_id],
                    key_suffix="ped"
                )
        else:
            st.info("Adicione produtos ao pedido acima.")


# ══════════════════════════════════════════════
# ABA 5 — ESTOQUE POR LOJA
# ══════════════════════════════════════════════
if _pg == "estoque_loja":

    st.subheader("Estoque por Loja")
    st.caption("Consulte e edite o estoque de um produto em todas as lojas.")

    cache_any = cache or api.carregar_cache(None)
    if not cache_any:
        st.warning("Sincronize os produtos primeiro.")
    else:
        termo4 = st.text_input("🔍 Buscar produto", key="busca_lojas", placeholder="ex: iPhone 15, S24...")
        prods4 = sorted(api.buscar_produtos(termo4, cache_any) if termo4 else [],
                        key=lambda p: p.get("codigo_interno", "") or "")

        if prods4:
            nomes4 = [f"{p['codigo_interno']} — {p['nome']}" for p in prods4]
            esc4 = st.selectbox("Produto:", nomes4, key="sel_lojas")
            prod4 = prods4[nomes4.index(esc4)]

            if st.button("🔍 Consultar em todas as lojas", use_container_width=True):
                with st.spinner("Consultando todas as lojas..."):
                    try:
                        st.session_state.estoques_lojas = api.estoque_produto_por_loja(prod4["id"])
                        st.session_state.prod_lojas = prod4
                    except Exception as e:
                        st.error(f"Erro: {e}")

        if "estoques_lojas" in st.session_state and st.session_state.get("prod_lojas"):
            prod_viz = st.session_state.prod_lojas
            estoques = st.session_state.estoques_lojas
            st.divider()
            st.markdown(f"**{prod_viz['nome']}** ({prod_viz['codigo_interno']})")

            todas_vars = sorted({v for lv in estoques.values() for v in lv.keys()})
            rows = []
            for var in todas_vars:
                row = {"Variação": var}
                total = 0
                for loja_nome in api.LOJAS.values():
                    est = estoques.get(loja_nome, {}).get(var, {})
                    val = est.get("estoque", 0) if isinstance(est, dict) else 0
                    row[loja_nome] = int(val)
                    total += val
                row["Total"] = int(total)
                rows.append(row)

            df_lojas = pd.DataFrame(rows)
            st.dataframe(df_lojas, use_container_width=True, hide_index=True)

            cols_tot = st.columns(len(api.LOJAS) + 1)
            for i, loja_nome in enumerate(api.LOJAS.values()):
                total_loja = sum(
                    v.get("estoque", 0) if isinstance(v, dict) else 0
                    for v in estoques.get(loja_nome, {}).values()
                )
                cols_tot[i].metric(loja_nome, int(total_loja))
            total_geral = sum(
                v.get("estoque", 0) if isinstance(v, dict) else 0
                for lv in estoques.values() for v in lv.values()
            )
            cols_tot[-1].metric("Total Geral", int(total_geral))

            st.divider()
            st.subheader("✏️ Atualizar estoque em uma loja")
            col_l1, col_l2, col_l3 = st.columns(3)
            with col_l1:
                loja_upd_nome = st.selectbox("Loja:", list(api.LOJAS.values()), key="loja_upd")
                loja_upd_id = {v: k for k, v in api.LOJAS.items()}[loja_upd_nome]
            with col_l2:
                var_upd = st.selectbox("Variação:", todas_vars, key="var_upd")
            with col_l3:
                modo_upd = st.radio("Modo:", ["Definir valor", "Somar ao atual"], key="modo_upd", horizontal=True)

            var_id_upd = None
            qtd_atual = 0
            for v in prod_viz.get("variacoes", []):
                vd = v["variacao"]
                nome_v = vd["nome"] or "(sem nome)"
                if nome_v == var_upd:
                    var_id_upd = vd["id"]
                    est_info = estoques.get(loja_upd_nome, {}).get(var_upd, {})
                    qtd_atual = est_info.get("estoque", 0) if isinstance(est_info, dict) else 0
                    break

            nova_qtd_upd = st.number_input(
                f"{'Nova quantidade' if 'Definir' in modo_upd else 'Quantidade a somar'} (atual: {int(qtd_atual)})",
                min_value=0, value=0, step=1, key="qtd_upd"
            )

            if st.button(f"✅ Atualizar", type="primary", use_container_width=True):
                if not var_id_upd:
                    st.error("Variação não encontrada.")
                else:
                    with st.spinner("Atualizando..."):
                        try:
                            modo_api = "set" if "Definir" in modo_upd else "soma"
                            api.atualizar_estoque_variacao(
                                prod_viz["id"], var_id_upd, nova_qtd_upd,
                                loja_id=loja_upd_id, modo=modo_api
                            )
                            novo_val = nova_qtd_upd if modo_api == "set" else qtd_atual + nova_qtd_upd
                            st.success(f"✅ '{var_upd}' em {loja_upd_nome} → {int(novo_val)}")
                            if isinstance(estoques.get(loja_upd_nome, {}).get(var_upd), dict):
                                st.session_state.estoques_lojas[loja_upd_nome][var_upd]["estoque"] = novo_val
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")



# ══════════════════════════════════════════════
# ABA 6 — DISPONIBILIDADE POR LOJA
# ══════════════════════════════════════════════
if _pg == "disponibilidade":
    st.subheader("Disponibilidade por Loja")
    st.caption("Controle em quais lojas cada produto está ativo. Selecionar um grupo pai inclui todos os subgrupos.")

    # Carrega caches de todas as lojas para comparar ativo real por loja
    caches_por_loja = {lid: api.carregar_cache(lid) for lid in api.LOJAS}
    cache_any = cache or next((c for c in caches_por_loja.values() if c), None)

    if not cache_any:
        st.warning("Sincronize os produtos primeiro.")
    else:
        disp_override = api.carregar_disponibilidade()  # overrides manuais feitos no app
        arvore = api.grupos_arvore()
        nomes_lojas = list(api.LOJAS.values())

        # Índice: {loja_id: {produto_id_str: ativo_bool}} a partir dos caches
        ativo_por_loja = {}
        for lid, c in caches_por_loja.items():
            if c:
                ativo_por_loja[lid] = {
                    str(p["id"]): (str(p.get("ativo", "1")) == "1")
                    for p in c.get("produtos", [])
                }
            else:
                ativo_por_loja[lid] = {}

        col_d1, col_d2, col_d3 = st.columns([2, 2, 1])
        with col_d1:
            termo_disp = st.text_input("🔍 Filtrar por nome/código", key="busca_disp",
                                        placeholder="ex: iPhone, Samsung A...")
        with col_d2:
            opcoes_grupo = ["(Todos)"] + [g["label"] for g in arvore]
            grupo_disp_label = st.selectbox("Grupo (pai inclui filhos)", opcoes_grupo, key="grupo_disp")
        with col_d3:
            so_inconsistentes = st.checkbox("Só divergentes", key="disp_incons",
                                             help="Mostrar apenas produtos com disponibilidade diferente entre lojas")

        # Resolver IDs dos grupos selecionados (pai + filhos)
        grupo_ids_filtro = None
        if grupo_disp_label != "(Todos)":
            grupo_sel_obj = next((g for g in arvore if g["label"] == grupo_disp_label), None)
            if grupo_sel_obj:
                grupo_ids_filtro = api.grupos_filhos_ids(grupo_sel_obj["id"])

        prods_disp = cache_any.get("produtos", [])
        if termo_disp:
            t = termo_disp.lower()
            prods_disp = [p for p in prods_disp
                          if t in (p.get("nome") or "").lower() or t in (p.get("codigo_interno") or "").lower()]
        if grupo_ids_filtro:
            prods_disp = [p for p in prods_disp if str(p.get("grupo_id", "")) in grupo_ids_filtro]

        # Montar dados de disponibilidade
        rows_disp = []
        for p in sorted(prods_disp, key=lambda p: p.get("codigo_interno") or ""):
            pid = str(p["id"])
            status = {}
            for loja_id_k in api.LOJAS:
                if pid in disp_override.get(loja_id_k, {}):
                    # override manual prevalece
                    status[loja_id_k] = disp_override[loja_id_k][pid]
                else:
                    # usa valor real do cache da loja
                    status[loja_id_k] = ativo_por_loja.get(loja_id_k, {}).get(pid, True)
            valores = list(status.values())
            divergente = len(set(valores)) > 1

            if so_inconsistentes and not divergente:
                continue

            row = {
                "_produto_id": p["id"],
                "Cód.": p.get("codigo_interno", ""),
                "Produto": p.get("nome", ""),
                "Grupo": p.get("nome_grupo", ""),
                "⚠️": "⚠️" if divergente else "",
            }
            for loja_id_k, loja_nome_k in api.LOJAS.items():
                row[loja_nome_k] = status[loja_id_k]
            rows_disp.append(row)

        rows_disp = rows_disp[:150]

        if not rows_disp:
            st.info("Nenhum produto encontrado com os filtros aplicados.")
        else:
            n_div = sum(1 for r in rows_disp if r["⚠️"])
            st.caption(f"{len(rows_disp)} produto(s) exibido(s) — {n_div} com disponibilidade divergente entre lojas ⚠️")

            df_disp = pd.DataFrame(rows_disp)

            edited_disp = st.data_editor(
                df_disp[["⚠️", "Cód.", "Produto", "Grupo"] + nomes_lojas],
                column_config={
                    "⚠️": st.column_config.TextColumn("⚠️", width="small", disabled=True),
                    **{n: st.column_config.CheckboxColumn(n, width="small") for n in nomes_lojas}
                },
                hide_index=True, use_container_width=True, key="editor_disp"
            )

            col_ds1, col_ds2, col_ds3 = st.columns(3)
            with col_ds1:
                if st.button("✅ Marcar todos visíveis em todas as lojas", use_container_width=True):
                    for i in range(len(edited_disp)):
                        for n in nomes_lojas:
                            edited_disp.at[i, n] = True
                    st.rerun()
            with col_ds2:
                loja_toggle = st.selectbox("Loja para toggle rápido:", nomes_lojas, key="loja_toggle")
                if st.button(f"🔄 Inverter {loja_toggle}", use_container_width=True):
                    for i in range(len(edited_disp)):
                        edited_disp.at[i, loja_toggle] = not edited_disp.at[i, loja_toggle]
                    st.rerun()
            with col_ds3:
                st.write("")
                if st.button("💾 Salvar disponibilidade", type="primary", use_container_width=True):
                    with st.spinner("Salvando..."):
                        erros_disp = []
                        for i, row in edited_disp.iterrows():
                            prod_id = df_disp.loc[i, "_produto_id"]
                            for loja_id_k, loja_nome_k in api.LOJAS.items():
                                novo_val = bool(row[loja_nome_k])
                                pid_s = str(prod_id)
                                if pid_s in disp_override.get(loja_id_k, {}):
                                    antigo_val = disp_override[loja_id_k][pid_s]
                                else:
                                    antigo_val = ativo_por_loja.get(loja_id_k, {}).get(pid_s, True)
                                if novo_val != antigo_val:
                                    try:
                                        api.toggle_produto_loja(prod_id, loja_id_k, novo_val)
                                    except Exception as e:
                                        erros_disp.append(f"{row['Produto']} / {loja_nome_k}: {e}")
                        disp_override = api.carregar_disponibilidade()
                        if erros_disp:
                            for er in erros_disp:
                                st.warning(f"⚠️ {er}")
                        st.success("✅ Salvo!")


# ══════════════════════════════════════════════
# ABA 7 — PREÇOS
# ══════════════════════════════════════════════
if _pg == "precos":
    st.subheader("Atualização de Preços")
    st.caption("Edite em lote, reajuste por %, copie um preço e aplique a toda a categoria.")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
    else:
        arvore_p = api.grupos_arvore()

        col_p1, col_p2 = st.columns([3, 2])
        with col_p1:
            termo_preco = st.text_input("🔍 Buscar produtos", key="busca_preco",
                                         placeholder="ex: iPhone, Samsung, Aveludada...")
        with col_p2:
            opcoes_grupo_p = ["(Todos)"] + [g["label"] for g in arvore_p]
            grupo_preco_label = st.selectbox("Grupo (pai inclui filhos)", opcoes_grupo_p, key="grupo_preco")

        grupo_ids_preco = None
        if grupo_preco_label != "(Todos)":
            gobj = next((g for g in arvore_p if g["label"] == grupo_preco_label), None)
            if gobj:
                grupo_ids_preco = api.grupos_filhos_ids(gobj["id"])

        prods_preco = cache.get("produtos", [])
        if termo_preco:
            t = termo_preco.lower()
            prods_preco = [p for p in prods_preco
                           if t in (p.get("nome") or "").lower() or t in (p.get("codigo_interno") or "").lower()]
        if grupo_ids_preco:
            prods_preco = [p for p in prods_preco if str(p.get("grupo_id", "")) in grupo_ids_preco]
        prods_preco = sorted(prods_preco[:150], key=lambda p: p.get("codigo_interno") or "")

        # ── Ferramentas de aplicação em lote ──
        with st.expander("⚡ Ferramentas de aplicação em lote"):
            st.markdown("**Reajuste por percentual**")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                pct_custo = st.number_input("% custo", value=0.0, step=0.5, key="pct_custo",
                                             help="10 = +10%,  -5 = -5%")
            with col_r2:
                pct_venda = st.number_input("% venda", value=0.0, step=0.5, key="pct_venda")
            with col_r3:
                st.write("")
                aplicar_pct = st.button("⚡ Aplicar %", use_container_width=True, key="btn_pct")

            st.divider()
            st.markdown("**Copiar preço de um produto e colar em toda a lista**")
            st.caption("Busque o produto de referência, defina custo e venda, e aplique a todos da lista atual.")
            col_cp1, col_cp2, col_cp3 = st.columns(3)
            with col_cp1:
                ref_busca = st.text_input("Produto de referência", placeholder="ex: Samsung A55",
                                           key="ref_busca_preco")
                prods_ref = sorted(api.buscar_produtos(ref_busca, cache) if ref_busca else [],
                                   key=lambda p: p.get("codigo_interno") or "")
                if prods_ref:
                    nomes_ref = [f"{p['codigo_interno']} — {p['nome']}" for p in prods_ref]
                    esc_ref = st.selectbox("Referência:", nomes_ref, key="sel_ref_preco")
                    prod_ref = prods_ref[nomes_ref.index(esc_ref)]
                    st.caption(f"Custo atual: R$ {float(prod_ref.get('valor_custo') or 0):.2f} | "
                               f"Venda: R$ {float(prod_ref.get('valor_venda') or 0):.2f}")
                else:
                    prod_ref = None
            with col_cp2:
                colar_custo = st.number_input("Custo a colar (R$)", min_value=0.0, step=0.01,
                                               value=float(prod_ref.get("valor_custo") or 0) if prod_ref else 0.0,
                                               key="colar_custo")
                colar_venda = st.number_input("Venda a colar (R$)", min_value=0.0, step=0.01,
                                               value=float(prod_ref.get("valor_venda") or 0) if prod_ref else 0.0,
                                               key="colar_venda")
            with col_cp3:
                aplicar_custo_ref = st.checkbox("Aplicar custo", value=True, key="aplicar_custo_ref")
                aplicar_venda_ref = st.checkbox("Aplicar venda", value=True, key="aplicar_venda_ref")
                st.write("")
                aplicar_colar = st.button("📋 Colar em toda a lista", type="primary",
                                           use_container_width=True, key="btn_colar")

        if prods_preco:
            rows_preco = []
            for p in prods_preco:
                custo = float(p.get("valor_custo") or 0)
                venda = float(p.get("valor_venda") or 0)
                # Aplicar reajuste %
                if aplicar_pct:
                    if pct_custo != 0:
                        custo = round(custo * (1 + pct_custo / 100), 2)
                    if pct_venda != 0:
                        venda = round(venda * (1 + pct_venda / 100), 2)
                # Aplicar colar
                if aplicar_colar:
                    if aplicar_custo_ref:
                        custo = colar_custo
                    if aplicar_venda_ref:
                        venda = colar_venda
                margem = round((venda - custo) / custo * 100, 1) if custo > 0 else 0.0
                rows_preco.append({
                    "_produto_id": p["id"],
                    "Cód.": p.get("codigo_interno", ""),
                    "Produto": p.get("nome", ""),
                    "Grupo": p.get("nome_grupo", ""),
                    "Custo (R$)": custo,
                    "Venda (R$)": venda,
                    "Margem %": margem,
                })

            df_preco = pd.DataFrame(rows_preco)

            edited_preco = st.data_editor(
                df_preco[["Cód.", "Produto", "Grupo", "Custo (R$)", "Venda (R$)", "Margem %"]],
                column_config={
                    "Custo (R$)": st.column_config.NumberColumn("Custo (R$)", min_value=0, step=0.01, format="R$ %.2f"),
                    "Venda (R$)": st.column_config.NumberColumn("Venda (R$)", min_value=0, step=0.01, format="R$ %.2f"),
                    "Margem %": st.column_config.NumberColumn("Margem %", format="%.1f%%", disabled=True),
                },
                hide_index=True, use_container_width=True, key="editor_preco"
            )

            n_alt = sum(
                1 for i, row in edited_preco.iterrows()
                if row["Custo (R$)"] != df_preco.loc[i, "Custo (R$)"]
                or row["Venda (R$)"] != df_preco.loc[i, "Venda (R$)"]
            )
            if n_alt:
                st.info(f"✏️ {n_alt} produto(s) com preço alterado em relação ao cache")

            col_pv1, col_pv2 = st.columns(2)
            with col_pv1:
                if st.button("💾 Salvar preços no sistema", type="primary", use_container_width=True):
                    entradas_preco = [
                        {"produto_id": df_preco.loc[i, "_produto_id"],
                         "produto_nome": row["Produto"],
                         "valor_custo": row["Custo (R$)"],
                         "valor_venda": row["Venda (R$)"]}
                        for i, row in edited_preco.iterrows()
                    ]
                    barra_p = st.progress(0)
                    def prog_preco(atual, total):
                        barra_p.progress(atual / total, text=f"{atual}/{total}...")
                    res_p = api.atualizar_precos_lote(entradas_preco, loja_id=loja_id,
                                                       progress_callback=prog_preco)
                    ok_p = [r for r in res_p if r["ok"]]
                    err_p = [r for r in res_p if not r["ok"]]
                    if ok_p:
                        st.success(f"✅ {len(ok_p)} preço(s) atualizado(s)!")
                    for e in err_p:
                        st.error(f"❌ {e['produto_nome']}: {e['erro']}")
            with col_pv2:
                buf_p = io.BytesIO()
                with pd.ExcelWriter(buf_p, engine="openpyxl") as w:
                    edited_preco[["Cód.", "Produto", "Grupo", "Custo (R$)", "Venda (R$)", "Margem %"]].to_excel(
                        w, index=False, sheet_name="Preços")
                buf_p.seek(0)
                st.download_button("📥 Exportar Excel", data=buf_p,
                                   file_name=f"precos_{date.today()}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
        else:
            st.info("Busque produtos ou selecione um grupo acima.")


# ══════════════════════════════════════════════
# ABA 8 — NOVO MODELO
# ══════════════════════════════════════════════
if _pg == "novo_modelo":
    st.subheader("Novo Modelo")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
    else:
        grupos_cache = {p.get("grupo_id"): p.get("nome_grupo")
                        for p in cache.get("produtos", []) if p.get("grupo_id")}
        grupos_lista = sorted(grupos_cache.items(), key=lambda x: x[1] or "")

        col1, col2 = st.columns(2)
        with col1:
            novo_nome = st.text_input("Nome do produto *", placeholder="ex: iPhone 18 Pro Max")
            novo_cod = st.text_input("Código interno *", placeholder="ex: IP18PM")
            grupo_opcoes = [f"{nome} ({gid})" for gid, nome in grupos_lista]
            grupo_sel = st.selectbox("Grupo", grupo_opcoes)
            grupo_id_novo = grupos_lista[grupo_opcoes.index(grupo_sel)][0] if grupo_opcoes else ""
        with col2:
            valor_custo = st.text_input("Valor de custo (R$)", value="0.00")
            valor_venda = st.text_input("Valor de venda (R$)", value="0.00")
            ativo = st.checkbox("Produto ativo", value=True)

        st.divider()
        st.markdown("**Variações**")

        if "novas_variacoes" not in st.session_state:
            st.session_state.novas_variacoes = []

        with st.expander("📥 Importar variações de outro produto"):
            termo_imp = st.text_input("Buscar produto", key="imp_var_busca", placeholder="ex: iPhone 17 Pro Max")
            prods_imp = sorted(api.buscar_produtos(termo_imp, cache) if termo_imp else [],
                                key=lambda p: p.get("codigo_interno", "") or "")
            if prods_imp:
                nomes_imp = [f"{p['codigo_interno']} — {p['nome']}" for p in prods_imp]
                esc_imp = st.selectbox("Produto de origem:", nomes_imp, key="imp_var_sel")
                prod_imp = prods_imp[nomes_imp.index(esc_imp)]
                st.info(f"{len(prod_imp.get('variacoes', []))} variação(ões)")
                if st.button("📥 Importar variações", use_container_width=True):
                    st.session_state.novas_variacoes = [
                        {"nome": v["variacao"]["nome"] or "", "codigo": "", "estoque": "0"}
                        for v in variacoes_ordenadas(prod_imp)
                    ]
                    st.success(f"{len(st.session_state.novas_variacoes)} importadas! Ajuste os códigos abaixo.")
                    st.rerun()

        col_va, col_vb, col_vc = st.columns([3, 2, 1])
        with col_va:
            var_nome = st.text_input("Nome da variação", placeholder="ex: Preto / Aveludada", key="var_nome_inp")
        with col_vb:
            var_cod = st.text_input("Código", placeholder="ex: IP18PM0001", key="var_cod_inp")
        with col_vc:
            st.write("")
            st.write("")
            if st.button("➕", use_container_width=True, key="add_var"):
                if var_nome:
                    st.session_state.novas_variacoes.append({"nome": var_nome, "codigo": var_cod, "estoque": "0"})
                    st.rerun()

        if st.session_state.novas_variacoes:
            df_nv = pd.DataFrame(st.session_state.novas_variacoes)
            df_nv_edit = st.data_editor(
                df_nv[["nome", "codigo"]].rename(columns={"nome": "Variação", "codigo": "Código"}),
                hide_index=True, use_container_width=True, key="ed_novas_var", num_rows="dynamic"
            )
            if st.button("🗑️ Limpar todas", use_container_width=True):
                st.session_state.novas_variacoes = []
                st.rerun()
            if df_nv_edit is not None:
                st.session_state.novas_variacoes = [
                    {"nome": r["Variação"], "codigo": r["Código"], "estoque": "0"}
                    for _, r in df_nv_edit.iterrows()
                ]

        st.divider()
        if st.button("✅ Cadastrar produto", type="primary", use_container_width=True):
            if not novo_nome or not novo_cod:
                st.error("Nome e código interno são obrigatórios.")
            elif not st.session_state.novas_variacoes:
                st.error("Adicione pelo menos uma variação.")
            else:
                with st.spinner("Cadastrando..."):
                    try:
                        res = api.criar_produto(
                            nome=novo_nome, codigo_interno=novo_cod, grupo_id=grupo_id_novo,
                            valor_custo=valor_custo, valor_venda=valor_venda,
                            ativo="1" if ativo else "0",
                            variacoes=st.session_state.novas_variacoes, loja_id=loja_id
                        )
                        st.success(f"✅ Produto '{novo_nome}' cadastrado!")
                        st.json(res)
                        st.session_state.novas_variacoes = []
                        st.info("Sincronize os produtos na barra lateral.")
                    except Exception as e:
                        st.error(f"Erro: {e}")


# ══════════════════════════════════════════════
# ABA 9 — CLONAR MODELO
# ══════════════════════════════════════════════
if _pg == "clonar_modelo":
    st.subheader("Clonar Modelo")

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
    else:
        termo3 = st.text_input("🔍 Buscar modelo de origem", placeholder="ex: iPhone 17", key="busca_clone")
        prods3 = sorted(api.buscar_produtos(termo3, cache) if termo3 else [],
                        key=lambda p: p.get("codigo_interno", "") or "")

        if prods3:
            nomes3 = [f"{p['codigo_interno']} — {p['nome']}" for p in prods3]
            esc3 = st.selectbox("Modelo de origem:", nomes3, key="sel_clone")
            prod3 = prods3[nomes3.index(esc3)]

            st.info(f"Variações a copiar: **{len(prod3.get('variacoes', []))}**")
            with st.expander("Ver variações"):
                for v in variacoes_ordenadas(prod3):
                    vd = v["variacao"]
                    st.write(f"- `{vd['codigo']}` {vd['nome'] or '(sem nome)'}")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                novo_nome3 = st.text_input("Nome do novo modelo", placeholder="ex: iPhone 18")
            with col2:
                novo_cod3 = st.text_input("Código interno", placeholder="ex: IP18")

            if st.button("🔁 Clonar produto", type="primary", use_container_width=True):
                if not novo_nome3 or not novo_cod3:
                    st.error("Preencha o nome e o código.")
                else:
                    with st.spinner(f"Clonando {prod3['nome']} → {novo_nome3}..."):
                        try:
                            res = api.clonar_produto(prod3["id"], novo_nome3, novo_cod3, loja_id=loja_id)
                            st.success(f"✅ Produto '{novo_nome3}' criado!")
                            st.json(res)
                            st.info("Sincronize os produtos na barra lateral.")
                        except Exception as e:
                            st.error(f"Erro ao clonar: {e}")


# ══════════════════════════════════════════════
# ABA USUÁRIOS — somente admin
# ══════════════════════════════════════════════
if _pg == "usuarios":
    st.subheader("👥 Gerenciamento de Usuários")

    _usuarios_db = api.carregar_usuarios()
    setores_opcoes = {v["label"]: k for k, v in api.SETORES.items()}

    # ── Tabela de usuários existentes ──────────
    st.markdown("### Usuários cadastrados")
    rows = []
    for login, ud in _usuarios_db.items():
        setor_k = ud.get("setor", "vendas")
        rows.append({
            "Login": login,
            "Nome": ud.get("nome", ""),
            "Setor": api.SETORES.get(setor_k, {}).get("label", setor_k),
            "Abas permitidas": ", ".join(
                TODAS_ABAS[i].split(" ", 1)[-1]
                for i in api.SETORES.get(setor_k, {}).get("abas", [])
            ),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    col_add, col_edit = st.columns(2)

    # ── Adicionar / Editar usuário ─────────────
    with col_add:
        st.markdown("### ➕ Adicionar usuário")
        with st.form("form_add_usuario", clear_on_submit=True):
            nu_login = st.text_input("Login (único, sem espaços)").strip().lower()
            nu_nome  = st.text_input("Nome completo")
            nu_setor = st.selectbox("Setor", list(setores_opcoes.keys()))
            nu_senha = st.text_input("Senha inicial")
            salvar_novo = st.form_submit_button("Salvar", use_container_width=True)
        if salvar_novo:
            if not nu_login or not nu_senha:
                st.error("Login e senha são obrigatórios.")
            elif nu_login in _usuarios_db:
                st.error(f"Login '{nu_login}' já existe. Use Editar.")
            else:
                _usuarios_db[nu_login] = {
                    "nome": nu_nome or nu_login,
                    "senha": nu_senha,
                    "setor": setores_opcoes[nu_setor],
                }
                api.salvar_usuarios(_usuarios_db)
                st.success(f"Usuário '{nu_login}' criado!")
                st.rerun()

    # ── Editar usuário existente ───────────────
    with col_edit:
        st.markdown("### ✏️ Editar usuário")
        login_sel = st.selectbox("Selecionar usuário", list(_usuarios_db.keys()), key="sel_editar_usr")
        ud_sel = _usuarios_db.get(login_sel, {})
        setor_atual_label = api.SETORES.get(ud_sel.get("setor","vendas"), {}).get("label","Vendas")
        with st.form("form_edit_usuario"):
            ed_nome  = st.text_input("Nome", value=ud_sel.get("nome",""))
            ed_setor = st.selectbox("Setor", list(setores_opcoes.keys()),
                                    index=list(setores_opcoes.keys()).index(setor_atual_label)
                                    if setor_atual_label in setores_opcoes else 0)
            ed_senha = st.text_input("Nova senha (deixe em branco para manter)", value="")
            col_s, col_d = st.columns(2)
            salvar_edit = col_s.form_submit_button("💾 Salvar", use_container_width=True)
            excluir     = col_d.form_submit_button("🗑️ Excluir", use_container_width=True)
        if salvar_edit:
            if login_sel == _user and setores_opcoes[ed_setor] != "admin":
                st.error("Você não pode remover seu próprio acesso admin.")
            else:
                _usuarios_db[login_sel]["nome"]  = ed_nome
                _usuarios_db[login_sel]["setor"] = setores_opcoes[ed_setor]
                if ed_senha:
                    _usuarios_db[login_sel]["senha"] = ed_senha
                api.salvar_usuarios(_usuarios_db)
                st.success("Usuário atualizado!")
                st.rerun()
        if excluir:
            if login_sel == _user:
                st.error("Você não pode excluir seu próprio usuário.")
            else:
                del _usuarios_db[login_sel]
                api.salvar_usuarios(_usuarios_db)
                st.success(f"Usuário '{login_sel}' removido.")
                st.rerun()

    # ── Referência de setores ──────────────────
    st.divider()
    st.markdown("### 📋 Setores e permissões")
    setor_rows = []
    for k, v in api.SETORES.items():
        setor_rows.append({
            "Setor": v["label"],
            "Abas": ", ".join(TODAS_ABAS[i].split(" ", 1)[-1] for i in v["abas"]),
        })
    st.dataframe(setor_rows, use_container_width=True, hide_index=True)
