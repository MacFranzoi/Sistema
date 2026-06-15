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

# ── Tema fixo claro (ignora preferência do sistema) ──
if "tema" not in st.session_state:
    st.session_state.tema = "light"
_dark = False  # sempre claro

BG   = "#f5f5f7"
SB   = "#ffffff"
SB2  = "#f0f0f3"
CARD = "#ffffff"
BOR  = "#e2e2e7"
TXT  = "#111113"
TXT2 = "#6b6b80"
ACC   = "#7c3aed"
ACC2  = "#a855f7"
ACC_LT= "rgba(124,58,237,0.12)"
GRN   = "#22c55e"
GRN_LT= "rgba(34,197,94,0.10)"
RED   = "#ef4444"
RED_LT= "rgba(239,68,68,0.10)"
SB_W  = "240px"
YEL   = ACC
YEL_BG= ACC_LT

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&display=swap');

/* ── RESET ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; }}
html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    font-size: 14.5px; line-height: 1.55;
    background: {BG} !important;
    color: {TXT} !important;
    -webkit-font-smoothing: antialiased;
}}
.main .block-container {{ padding: 26px 32px 40px !important; max-width: 100% !important; }}

/* ── SEM TRANSIÇÕES / SEM ANIMAÇÕES ── */
*, *::before, *::after {{ animation: none !important; }}
/* força esquema de cores claro independente do sistema */
:root {{ color-scheme: light only; }}

/* ── TOPBAR: esconde header nativo do Streamlit ── */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
header[data-testid="stHeader"] {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: {SB} !important;
    border-right: 1px solid {BOR} !important;
    width: {SB_W} !important; min-width: {SB_W} !important;
    padding: 0 !important;
}}
[data-testid="stSidebar"] > div {{
    padding: 0 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: 100vh !important;
    display: flex !important; flex-direction: column !important;
    background: {SB} !important;
}}
[data-testid="stSidebar"] > div::-webkit-scrollbar {{ width: 3px; }}
[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb {{ background: {BOR}; border-radius: 99px; }}

/* remove padding/gap interno do Streamlit */
[data-testid="stSidebar"] section, [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    padding: 0 !important; gap: 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
    margin: 0 !important; padding: 0 !important; gap: 0 !important;
}}

/* logo */
.sb-logo {{
    display: flex; align-items: center; gap: 10px;
    padding: 0 16px; height: 52px;
    border-bottom: 1px solid {BOR};
    background: {SB}; flex-shrink: 0;
}}
.sb-logo-mark {{
    width: 28px; height: 28px; border-radius: 7px;
    background: linear-gradient(135deg, {ACC}, {ACC2});
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; font-weight: 800; color: #fff;
    box-shadow: 0 2px 8px {ACC}55; flex-shrink: 0;
}}
.sb-logo-text {{ font-size: 0.9rem; font-weight: 700; color: {TXT}; }}

/* botão toggle da loja ativa */
[data-testid="stSidebar"] button[data-testid="baseButton-secondary"][key="loja_toggle"] {{
    background: {SB2} !important;
    border: none !important; border-bottom: 1px solid {BOR} !important;
    border-radius: 0 !important; width: 100% !important;
    padding: 9px 14px !important; text-align: left !important;
    font-size: 0.84rem !important; font-weight: 600 !important;
    color: {TXT} !important;
}}
/* opções da loja — levemente indentadas */
[data-testid="stSidebar"] button[key^="loja_opt_"] {{
    font-size: 0.82rem !important; font-weight: 500 !important;
    color: {TXT2} !important; padding: 6px 20px !important;
    border-radius: 6px !important; margin: 1px 6px !important;
    width: calc(100% - 12px) !important;
}}

/* todos os botões da sidebar */
[data-testid="stSidebar"] .stButton > button {{
    width: calc(100% - 12px) !important;
    background: transparent !important; border: none !important;
    border-radius: 6px !important; text-align: left !important;
    padding: 7px 12px !important; margin: 1px 6px !important;
    font-size: 0.84rem !important; font-weight: 600 !important;
    color: {TXT2} !important;
    }}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {SB2} !important; color: {TXT} !important;
}}

/* botão de grupo (header colapsável) — sobrescreve o padrão */
[data-testid="stSidebar"] button[data-sb-group="1"] {{
    font-size: 0.6rem !important; font-weight: 700 !important;
    letter-spacing: 1.4px !important; text-transform: uppercase !important;
    color: {TXT2} !important; padding: 14px 16px 5px !important;
    margin: 0 !important; border-radius: 0 !important; width: 100% !important;
    background: transparent !important;
}}

/* avatar */
.sb-avatar {{
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, {ACC}, {ACC2});
    color: #fff; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.75rem; flex-shrink: 0;
}}
.sb-user-name {{ font-size: 0.8rem; font-weight: 600; color: {TXT}; line-height: 1.2; }}
.sb-user-role {{ font-size: 0.65rem; color: {TXT2}; }}

/* botões tema/sair no sidebar */
[data-testid="stSidebar"] .stButton > button[data-testid*="btn_tema"],
[data-testid="stSidebar"] .stButton > button[data-testid*="btn_sair"] {{
    font-size: 0.72rem !important; padding: 4px 8px !important;
    border: 1px solid {BOR} !important; border-radius: 5px !important;
    margin: 2px 4px !important; width: auto !important;
    background: {CARD} !important; color: {TXT2} !important;
}}

/* ── PAGE ── */
.page-breadcrumb {{
    font-size: 0.68rem; color: {TXT2};
    display: flex; align-items: center; gap: 5px;
    margin-bottom: 2px;
}}
.page-breadcrumb span {{ color: {ACC}; }}
.page-title {{
    font-size: 1.3rem; font-weight: 700; color: {TXT};
    letter-spacing: -0.4px; line-height: 1.2;
}}

/* ── CARDS ── */
.card {{
    background: {CARD}; border: 1px solid {BOR};
    border-radius: 10px; padding: 16px 18px; margin-bottom: 14px;
}}
.card-header {{
    font-size: 0.8rem; font-weight: 600; color: {TXT};
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 1px solid {BOR};
    display: flex; align-items: center; gap: 6px;
}}

/* ── PAGE HEADER ── */
.page-breadcrumb {{
    font-size: 0.75rem; color: {TXT2};
    display: flex; align-items: center; gap: 5px; margin-bottom: 4px;
}}
.page-breadcrumb span {{ color: {ACC}; }}
.page-title {{
    font-size: 1.5rem; font-weight: 700; color: {TXT};
    letter-spacing: -0.5px; line-height: 1.2; margin-bottom: 20px;
}}

/* ── CARDS ── */
.card {{
    background: {CARD}; border: 1px solid {BOR};
    border-radius: 12px; padding: 20px 22px; margin-bottom: 16px;
    }}
.card:hover {{ box-shadow: 0 4px 24px rgba(0,0,0,{"0.25" if _dark else "0.07"}); }}
.card-header {{
    font-size: 0.88rem; font-weight: 600; color: {TXT};
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid {BOR};
    display: flex; align-items: center; gap: 7px;
}}

/* ── STAT CARDS ── */
.stat-grid {{ display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 24px; }}
.stat-box {{
    flex: 1; min-width: 140px;
    background: {CARD}; border: 1px solid {BOR};
    border-radius: 12px; padding: 18px 20px;
    position: relative; overflow: hidden;
    }}
.stat-box::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {ACC} 0%, {ACC2} 100%);
}}
.stat-box:hover {{ box-shadow: 0 6px 28px rgba(0,0,0,{"0.3" if _dark else "0.09"}); transform: translateY(-1px); }}
.stat-val {{ font-size: 1.85rem; font-weight: 700; color: {TXT}; line-height: 1; letter-spacing: -1.5px; }}
.stat-lbl {{ font-size: 0.7rem; color: {TXT2}; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 500; }}
.stat-icon {{ position: absolute; right: 16px; top: 16px; font-size: 1.3rem; opacity: 0.35; }}

/* ── BADGES ── */
.badge {{
    display: inline-flex; align-items: center; gap: 4px;
    background: {ACC_LT}; color: {ACC};
    border: 1px solid {ACC}30; border-radius: 5px;
    font-size: 0.68rem; font-weight: 600; padding: 3px 8px;
    letter-spacing: 0.2px;
}}
.badge-green {{ background: {GRN_LT}; color: {GRN}; border-color: {GRN}30; }}
.badge-red   {{ background: {RED_LT}; color: {RED}; border-color: {RED}30; }}
.badge-gray  {{ background: {SB2}; color: {TXT2}; border-color: {BOR}; }}

/* ── TABELA ── */
.stDataFrame {{ border-radius: 12px !important; overflow: hidden; }}
.stDataFrame [data-testid="stDataFrameResizable"] {{ border: 1px solid {BOR} !important; border-radius: 12px !important; }}
.stDataFrame th {{ background: {SB2} !important; font-size: 0.7rem !important; font-weight: 600 !important; color: {TXT2} !important; text-transform: uppercase; letter-spacing: 0.6px; padding: 10px 12px !important; }}
.stDataFrame td {{ font-size: 0.82rem !important; color: {TXT} !important; padding: 9px 12px !important; }}

/* ── INPUTS ── */
.stTextInput label p, .stSelectbox label p, .stNumberInput label p, .stTextArea label p {{
    font-size: 0.78rem !important; font-weight: 500 !important; color: {TXT2} !important;
    letter-spacing: 0.1px; margin-bottom: 4px !important;
}}
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: {CARD} !important; border: 1px solid {BOR} !important;
    color: {TXT} !important; border-radius: 8px !important; font-size: 0.88rem !important;
    padding: 9px 13px !important; }}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
    border-color: {ACC} !important; box-shadow: 0 0 0 3px {ACC}18 !important; outline: none !important;
}}
.stSelectbox > div > div {{
    background: {CARD} !important; border-color: {BOR} !important;
    font-size: 0.88rem !important; border-radius: 8px !important; color: {TXT} !important;
    padding: 1px 4px !important;
}}
.stSelectbox > div > div:focus-within {{ border-color: {ACC} !important; box-shadow: 0 0 0 3px {ACC}18 !important; }}

/* ── BUTTONS ── */
.main .stButton > button, .stFormSubmitButton > button {{
    font-size: 0.84rem !important; padding: 0.45rem 1.1rem !important;
    border-radius: 8px !important; border: 1px solid {BOR} !important;
    background: {CARD} !important; color: {TXT} !important;
    font-weight: 500 !important; letter-spacing: 0.1px;
}}
.main .stButton > button:hover {{
    background: {SB2} !important; border-color: {TXT2}66 !important;
    transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}}
.main .stButton > button[kind="primary"], .stFormSubmitButton > button {{
    background: {ACC} !important; color: #fff !important;
    border-color: {ACC} !important; font-weight: 600 !important;
    box-shadow: 0 2px 8px {ACC}44 !important;
}}
.main .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {{
    background: {ACC2} !important; border-color: {ACC2} !important;
    box-shadow: 0 4px 16px {ACC}55 !important; transform: translateY(-1px);
}}

/* ── EXPANDER ── */
.stExpander {{
    border: 1px solid {BOR} !important; border-radius: 12px !important;
    background: {CARD} !important; overflow: hidden;
    }}
.stExpander:hover {{ box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important; }}
.stExpander summary {{ font-size: 0.88rem !important; font-weight: 500 !important; color: {TXT} !important; padding: 12px 16px !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ border-bottom: 1px solid {BOR}; background: transparent; gap: 0; padding: 0; }}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.84rem !important; padding: 10px 20px !important;
    color: {TXT2} !important; border-radius: 0 !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
    font-weight: 400 !important; }}
.stTabs [aria-selected="true"] {{
    color: {TXT} !important; border-bottom-color: {ACC} !important; font-weight: 600 !important;
}}

/* ── ALERTS ── */
.stAlert {{ border-radius: 10px !important; font-size: 0.84rem !important; border: 1px solid {BOR} !important; }}

/* ── METRIC ── */
[data-testid="stMetric"] {{
    background: {CARD} !important; border: 1px solid {BOR} !important;
    border-radius: 12px !important; padding: 14px 18px !important;
}}
[data-testid="stMetricValue"] {{ font-size: 1.6rem !important; font-weight: 700 !important; color: {TXT} !important; }}
[data-testid="stMetricLabel"] {{ font-size: 0.72rem !important; color: {TXT2} !important; text-transform: uppercase; letter-spacing: 0.5px; }}

/* ── MISC ── */
hr {{ border: none !important; border-top: 1px solid {BOR} !important; margin: 14px 0 !important; }}
p {{ color: {TXT} !important; font-size: 0.88rem !important; line-height: 1.6; }}
caption, small {{ color: {TXT2} !important; font-size: 0.75rem !important; }}

/* scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {BOR}; border-radius: 99px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TXT2}; }}

/* ── LOGIN (background e centralização aplicados via CSS local no bloco de login) ── */

/* MOBILE */
@media (max-width: 640px) {{
    .main .block-container {{
        padding-left: 10px !important;
        padding-right: 10px !important;
        padding-bottom: max(24px, env(safe-area-inset-bottom)) !important;
    }}
    .page-title {{ font-size: 1.05rem; }}
    .stat-val {{ font-size: 1.2rem; }}
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

# ── Auto-login por token salvo na URL ──
if st.session_state.usuario_logado is None:
    _token_url = st.query_params.get("t", "")
    if _token_url:
        _usr_token = api.validar_sessao(_token_url)
        if _usr_token:
            st.session_state.usuario_logado = _usr_token
            st.session_state["_sessao_token"] = _token_url

if st.session_state.usuario_logado is None:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        # Card único com logo + form
        st.markdown(f"""
        <style>
        /* fundo e centralização da tela de login */
        [data-testid="stAppViewContainer"] {{
            background: {"radial-gradient(ellipse at 60% 40%, #1e1033 0%, #18181b 60%)" if _dark else "radial-gradient(ellipse at 60% 40%, #ede9fe 0%, #fafafa 60%)"} !important;
        }}
        section[data-testid="stMain"] {{
            display: flex !important; align-items: center !important;
            justify-content: center !important; min-height: 100dvh !important;
            padding-top: max(12px, env(safe-area-inset-top)) !important;
            padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
        }}
        /* login card */
        [data-testid="stForm"] {{
            background: {CARD} !important;
            border: 1px solid {BOR} !important;
            border-radius: 14px !important;
            padding: 2rem 2rem 1.6rem !important;
            box-shadow: 0 8px 40px rgba(0,0,0,{"0.5" if _dark else "0.10"}) !important;
            margin-top: 0 !important;
        }}
        [data-testid="stForm"] label p {{
            font-size: 0.68rem !important; font-weight: 500 !important;
            color: {TXT2} !important; letter-spacing: 0.1px !important;
        }}
        [data-testid="stForm"] input {{
            background: {BG} !important; border: 1px solid {BOR} !important;
            border-radius: 7px !important; color: {TXT} !important;
            font-size: 0.85rem !important; padding: 8px 12px !important;
        }}
        [data-testid="stForm"] input:focus {{
            border-color: {ACC} !important; box-shadow: 0 0 0 3px {ACC}18 !important;
        }}
        [data-testid="stForm"] button[type="submit"] {{
            background: linear-gradient(135deg, {ACC} 0%, {ACC2} 100%) !important;
            color: #fff !important; font-weight: 600 !important;
            border: none !important; border-radius: 8px !important;
            padding: 0.55rem 1rem !important; margin-top: 0.8rem !important;
            font-size: 0.85rem !important; letter-spacing: 0.2px !important;
            box-shadow: 0 2px 12px {ACC}44 !important;
            }}
        [data-testid="stForm"] button[type="submit"]:hover {{ opacity: 0.88 !important; }}
        </style>
        <div style="text-align:center;margin-bottom:1.4rem;margin-top:0.5rem">
          <div style="display:inline-flex;align-items:center;justify-content:center;
                      width:46px;height:46px;border-radius:12px;
                      background:linear-gradient(135deg,{ACC} 0%,{ACC2} 100%);
                      box-shadow:0 4px 16px {ACC}55;margin-bottom:12px">
            <span style="font-size:1.4rem;line-height:1">⚡</span>
          </div>
          <div style="font-size:1.2rem;font-weight:700;color:{TXT};letter-spacing:-0.3px">Plug ERP</div>
          <div style="font-size:0.72rem;color:{TXT2};margin-top:3px">Bem-vindo de volta</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input   = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            u = usuario_input.strip().lower()
            _udb = api.carregar_usuarios()
            if u in _udb and _udb[u]["senha"] == senha_input:
                st.session_state.usuario_logado = u
                _tok = api.criar_sessao(u)
                st.session_state["_sessao_token"] = _tok
                st.query_params["t"] = _tok
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# ── Dados do usuário ──
_user        = st.session_state.usuario_logado
_usuarios_db = api.carregar_usuarios()
_user_data   = _usuarios_db.get(_user, {})
_setor       = _user_data.get("setor", "vendas")
_setores_db  = api.carregar_setores()
_setor_cfg   = _setores_db.get(_setor, _setores_db.get("vendas", {"label": _setor, "paginas": []}))
_paginas_perm = set(_setor_cfg.get("paginas", []))
_nome_usr    = _user_data.get("nome", _user)
_is_admin    = _setor == "admin"
_setor_lbl   = _setor_cfg.get("label", _setor)

# ── Menu estruturado (como GestaoClick) ──
# (id, icon, label, grupo, aba_idx_ou_None, placeholder)
_MENU_FULL = [
    # GERAL
    ("dashboard",       "🏠", "Dashboard",           "GERAL",        None,  False),
    # CADASTROS
    ("clientes",        "👥", "Clientes",             "CADASTROS",    None,  False),
    ("fornecedores",    "🏭", "Fornecedores",         "CADASTROS",    None,  False),
    # ITENS
    ("novo_modelo",     "➕", "Novo Produto",         "ITENS",        7,     False),
    ("clonar_modelo",   "🔁", "Clonar Produto",       "ITENS",        8,     False),
    ("precos",          "💰", "Tabela de Preços",     "ITENS",        6,     False),
    # VENDAS
    ("vendas",          "🧾", "Vendas",               "VENDAS",       None,  False),
    ("orcamentos",      "📋", "Orçamentos",           "VENDAS",       None,  False),
    # ESTOQUE
    ("entrada",         "📥", "Entrada",              "ESTOQUE",      0,     False),
    ("acerto",          "🔧", "Acerto",               "ESTOQUE",      1,     False),
    ("estoque_loja",    "🏪", "Por Loja",             "ESTOQUE",      4,     False),
    ("disponibilidade", "🔘", "Disponibilidade",      "ESTOQUE",      5,     False),
    ("etiquetas",       "🏷️", "Etiquetas",            "ESTOQUE",      2,     False),
    # COMPRAS
    ("pedido",          "🛒", "Pedido de Compra",     "COMPRAS",      3,     False),
    ("compras_hist",    "📦", "Histórico de Compras", "COMPRAS",      None,  False),
    # FINANCEIRO
    ("financeiro",      "💳", "Financeiro",           "FINANCEIRO",   None,  False),
    # RELATÓRIOS
    ("relatorios",      "📊", "Relatórios",           "RELATÓRIOS",   None,  False),
    # CONFIG
    ("sincronizacao",   "🔄", "Sincronização",        "CONFIGURAÇÕES",None,  False),
    ("listas",          "📋", "Listas",               "CONFIGURAÇÕES",None,  False),
    ("usuarios",        "👤", "Usuários",             "CONFIGURAÇÕES",None,  False),
]

_MENU_VISIVEL = [
    m for m in _MENU_FULL
    if not m[5]  # não é placeholder
    and m[0] in _paginas_perm
]

if "pagina" not in st.session_state or st.session_state.pagina not in [m[0] for m in _MENU_VISIVEL]:
    st.session_state.pagina = _MENU_VISIVEL[0][0]

# ────────────────────────────────────────────────────────────
# SIDEBAR
# ── CSS sidebar scroll + page top alignment ──
st.markdown(f"""
<style>
/* esconde tudo do Streamlit que não é conteúdo */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stSidebar"],
header[data-testid="stHeader"] {{
    display: none !important;
    height: 0 !important; min-height: 0 !important;
    visibility: hidden !important; pointer-events: none !important;
}}

/* remove padding interno do main que o Streamlit injeta pra compensar o header */
[data-testid="stAppViewContainer"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
[data-testid="stAppViewContainer"] > section[data-testid="stMain"],
section[data-testid="stMain"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
.main .block-container {{
    padding-top: 0 !important;
    padding-left: clamp(8px, 3vw, 32px) !important;
    padding-right: clamp(8px, 3vw, 32px) !important;
    padding-bottom: max(40px, env(safe-area-inset-bottom)) !important;
    max-width: 100% !important;
}}

/* Barra de navegação horizontal */
.plug-nav {{
    position: sticky; top: 0; z-index: 999;
    background: {SB}; border-bottom: 1px solid {BOR};
    display: flex; align-items: center; gap: 4px;
    padding: 0 clamp(6px, 2vw, 12px);
    padding-left: max(clamp(6px, 2vw, 12px), env(safe-area-inset-left));
    padding-right: max(clamp(6px, 2vw, 12px), env(safe-area-inset-right));
    height: 48px; overflow-x: auto;
    scrollbar-width: none;
}}
.plug-nav::-webkit-scrollbar {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# Variáveis de loja necessárias antes do menu
if "loja_ativa_id" not in st.session_state:
    st.session_state.loja_ativa_id = None
loja_id = st.session_state.loja_ativa_id
loja_sel_nome = next((n for lid, n in api.LOJAS.items() if lid == loja_id), "Todas")

# ── Barra de navegação horizontal ──
_pg_ativo = st.session_state.pagina
_todas_pids    = [m[0] for m in _MENU_VISIVEL]
_todas_labels  = [f"{m[1]} {m[2]}" for m in _MENU_VISIVEL]
_idx_pg = _todas_pids.index(_pg_ativo) if _pg_ativo in _todas_pids else 0

_lojas_nomes = ["Todas"] + [n for _, n in api.LOJAS.items()]
_lojas_ids   = [None]    + [lid for lid, _ in api.LOJAS.items()]
_loja_idx    = _lojas_ids.index(loja_id) if loja_id in _lojas_ids else 0

def _on_nav_change():
    _lbl = st.session_state["nav_pagina"]
    if _lbl in _todas_labels:
        st.session_state.pagina = _todas_pids[_todas_labels.index(_lbl)]

def _on_loja_change():
    _n = st.session_state["nav_loja"]
    if _n in _lojas_nomes:
        st.session_state.loja_ativa_id = _lojas_ids[_lojas_nomes.index(_n)]

_c1, _c2, _c3, _c4 = st.columns([4, 2, 1, 1])

with _c1:
    st.selectbox("Página", _todas_labels, index=_idx_pg,
                 key="nav_pagina", label_visibility="collapsed",
                 on_change=_on_nav_change)

with _c2:
    st.selectbox("Loja", _lojas_nomes, index=_loja_idx,
                 key="nav_loja", label_visibility="collapsed",
                 on_change=_on_loja_change)

with _c3:
    if st.button("☀️" if _dark else "🌙", key="btn_tema", use_container_width=True):
        st.session_state.tema = "light" if _dark else "dark"
        st.rerun()

with _c4:
    if st.button("Sair", key="btn_sair", use_container_width=True):
        api.revogar_sessao(st.session_state.get("_sessao_token", ""))
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.rerun()

# ── Scroll restore: salva posição e restaura após rerun ──
st.markdown("""<script>
(function(){
  const KEY = 'plugerp_scroll_' + (window.location.pathname || '');
  // restaura posição salva
  const saved = sessionStorage.getItem(KEY);
  if (saved) {
    window.scrollTo(0, parseInt(saved));
    sessionStorage.removeItem(KEY);
  }
  // salva posição antes de qualquer navegação/rerun
  window.addEventListener('beforeunload', function() {
    sessionStorage.setItem(KEY, window.scrollY);
  });
  // Streamlit faz rerun sem beforeunload — salva também no visibilitychange
  document.addEventListener('visibilitychange', function() {
    sessionStorage.setItem(KEY, window.scrollY);
  });
})();
</script>""", unsafe_allow_html=True)

# ── Carrega cache e clip ──
cache = api.carregar_cache(loja_id)
clip  = st.session_state.get("clipboard")

# ── Cabeçalho da página ──
_pg_info = next((m for m in _MENU_VISIVEL if m[0] == st.session_state.pagina), _MENU_VISIVEL[0])
st.markdown(f"""
<div style="margin-top:0;padding-top:0">
  <div class="page-breadcrumb">{_pg_info[3]} <span>›</span> {_pg_info[2]}</div>
  <div class="page-title">{_pg_info[1]}  {_pg_info[2]}</div>
  <hr style="margin:8px 0 16px;border:none;border-top:1px solid {BOR}">
</div>
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

    st.caption(f"{len(df_view)} de {len(df)} variação(ões)")

    # Cabeçalho compacto
    h1, h2, h3, h4 = st.columns([1, 4, 1, 2])
    h1.caption("**Cód.**"); h2.caption("**Variação**")
    h3.caption("**Atual**"); h4.caption(f"**{col_qtd}**")

    # Frame scrollável com altura dinâmica (evita espaço em branco desnecessário)
    _altura_frame = min(220, max(90, len(df_view) * 52))
    qtds = {}
    frame = st.container(height=_altura_frame)
    for _, row in df_view.iterrows():
        c1, c2, c3, c4 = frame.columns([1, 4, 1, 2])
        c1.caption(str(row["Código Var."]))
        c2.caption(str(row["Variação"]))
        c3.caption(str(int(row["Estoque Atual"])))
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
    """Atalho legado — delega ao painel_listas."""
    painel_listas(itens, tipo, key_suffix=key_suffix)


def painel_carregar_lista(tipo, key_suffix="", retornar_arquivo=False):
    """Atalho legado — mantém compatibilidade com páginas que chamam diretamente."""
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


def painel_listas(itens_atuais, tipo, key_suffix=""):
    """Painel completo de gerenciamento de listas: salvar, carregar, renomear, excluir."""
    import json as _pj, os as _pos

    listas = api.listar_listas_salvas(tipo)
    arq_atual = st.session_state.get(f"lista_arq_{key_suffix}")

    with st.expander(f"📋 Listas salvas ({len(listas)})", expanded=False):
        # ── Salvar ───────────────────────────────────────────────────────
        st.markdown("**Salvar**")
        _c1, _c2, _c3 = st.columns([3, 1, 1])
        _nome_novo = _c1.text_input("Nome", placeholder="ex: Pedido 15/06 — Fornecedor X",
                                     key=f"ls_nome_{key_suffix}", label_visibility="collapsed")
        if _c2.button("💾 Salvar novo", use_container_width=True, key=f"ls_salvar_{key_suffix}"):
            if not _nome_novo.strip():
                st.error("Digite um nome.")
            else:
                _cam = api.salvar_lista(_nome_novo.strip(), tipo, itens_atuais,
                                        loja_id=loja_id, loja_nome=loja_sel_nome)
                st.session_state[f"lista_arq_{key_suffix}"] = os.path.basename(_cam)
                st.success("✅ Lista salva!")
                st.rerun()
        if arq_atual and _c3.button("🔄 Atualizar atual", use_container_width=True, key=f"ls_atual_{key_suffix}"):
            _cam = os.path.join(api.DIR_LISTAS, arq_atual)
            if os.path.exists(_cam):
                with open(_cam, encoding="utf-8") as _f:
                    _d = _pj.load(_f)
                _d["itens"] = itens_atuais
                _d["atualizado_em"] = datetime.now().isoformat()
                with open(_cam, "w", encoding="utf-8") as _f:
                    _pj.dump(_d, _f, ensure_ascii=False, indent=2)
                st.success("✅ Lista atualizada!")
                st.rerun()

        if arq_atual:
            st.caption(f"Lista aberta: **{arq_atual}**")

        if not listas:
            st.info("Nenhuma lista salva ainda.")
            return

        st.divider()
        st.markdown("**Listas salvas**")

        # Selectbox para escolher qual lista operar
        _opcoes = [
            f"{l['criado_em'][:16].replace('T',' ')} — {l['nome']} ({l.get('loja_nome','—')}) [{len(l['itens'])} itens]"
            for l in listas
        ]
        _idx = st.selectbox("Selecione:", range(len(_opcoes)),
                             format_func=lambda i: _opcoes[i],
                             key=f"ls_sel_{key_suffix}")
        _lst = listas[_idx]

        # Preview resumido
        if _lst["itens"]:
            _prev_cols = ["produto_nome", "variacao_nome", "quantidade"]
            _prev_cols = [c for c in _prev_cols if c in (_lst["itens"][0] if _lst["itens"] else {})]
            _df_prev = pd.DataFrame(_lst["itens"])[_prev_cols].head(6) if _prev_cols else pd.DataFrame(_lst["itens"]).head(6)
            _df_prev.columns = [c.replace("produto_nome","Produto").replace("variacao_nome","Variação").replace("quantidade","Qtd") for c in _df_prev.columns]
            st.dataframe(_df_prev, use_container_width=True, hide_index=True)
            if len(_lst["itens"]) > 6:
                st.caption(f"… e mais {len(_lst['itens'])-6} itens")

        _ca, _cb, _cc = st.columns(3)

        # Carregar
        if _ca.button("📂 Carregar", use_container_width=True, key=f"ls_load_{key_suffix}"):
            st.session_state[f"lista_arq_{key_suffix}"] = _lst["_arquivo"]
            st.session_state[f"ls_carregar_{key_suffix}"] = _lst["itens"]
            st.rerun()

        # Renomear
        with _cb.popover("✏️ Renomear"):
            _novo_nome = st.text_input("Novo nome:", value=_lst["nome"], key=f"ls_rename_txt_{key_suffix}")
            if st.button("Salvar nome", key=f"ls_rename_btn_{key_suffix}"):
                _cam = os.path.join(api.DIR_LISTAS, _lst["_arquivo"])
                with open(_cam, encoding="utf-8") as _f:
                    _d = _pj.load(_f)
                _d["nome"] = _novo_nome.strip()
                _conteudo = _pj.dumps(_d, ensure_ascii=False, indent=2)
                with open(_cam, "w", encoding="utf-8") as _f:
                    _f.write(_conteudo)
                api._gh_push_arquivo(f"listas/{_lst['_arquivo']}", _conteudo, f"Renomeia lista: {_novo_nome.strip()}")
                st.success("Renomeado!")
                st.rerun()

        # Excluir
        with _cc.popover("🗑️ Excluir"):
            st.warning(f"Excluir **{_lst['nome']}**?")
            if st.button("Confirmar exclusão", key=f"ls_del_{key_suffix}", type="primary"):
                api.excluir_lista(_lst["_arquivo"])
                if arq_atual == _lst["_arquivo"]:
                    st.session_state.pop(f"lista_arq_{key_suffix}", None)
                st.success("Excluído.")
                st.rerun()

        # ── Segunda linha: reordenar / mudar tipo / mover itens ──────────
        _cd, _ce, _cf, _cg = st.columns(4)

        # Mover para cima
        if _cd.button("⬆️ Para cima", use_container_width=True, key=f"ls_up_{key_suffix}"):
            api.mover_lista_na_ordem(_lst["_arquivo"], tipo, "cima")
            st.rerun()

        # Mover para baixo
        if _ce.button("⬇️ Para baixo", use_container_width=True, key=f"ls_down_{key_suffix}"):
            api.mover_lista_na_ordem(_lst["_arquivo"], tipo, "baixo")
            st.rerun()

        # Mudar tipo
        _TIPOS_LISTA = {"pedido": "Pedido de Compra", "entrada": "Entrada", "acerto": "Acerto", "etiquetas": "Etiquetas"}
        with _cf.popover("🔀 Mudar tipo"):
            _tipos_opcoes = [t for t in _TIPOS_LISTA if t != tipo]
            _novo_tipo = st.selectbox(
                "Novo tipo:",
                _tipos_opcoes,
                format_func=lambda t: _TIPOS_LISTA[t],
                key=f"ls_tipo_sel_{key_suffix}"
            )
            st.caption(f"A lista sairá de **{_TIPOS_LISTA.get(tipo, tipo)}** e irá para **{_TIPOS_LISTA.get(_novo_tipo, _novo_tipo)}**.")
            if st.button("Confirmar mudança", key=f"ls_tipo_btn_{key_suffix}", type="primary"):
                api.mudar_tipo_lista(_lst["_arquivo"], _novo_tipo)
                st.success(f"Tipo alterado para {_TIPOS_LISTA.get(_novo_tipo, _novo_tipo)}!")
                st.rerun()

        # Mover itens para outra lista
        with _cg.popover("➡️ Mover itens"):
            _outras = [l for l in listas if l["_arquivo"] != _lst["_arquivo"]]
            if not _outras:
                st.info("Nenhuma outra lista disponível.")
            else:
                _dest_opcoes = [l["_arquivo"] for l in _outras]
                _dest_idx = st.selectbox(
                    "Destino:",
                    range(len(_outras)),
                    format_func=lambda i: f"{_outras[i]['nome']} ({_outras[i].get('loja_nome','—')})",
                    key=f"ls_mv_sel_{key_suffix}"
                )
                _dest = _outras[_dest_idx]
                st.caption(f"Adiciona **{len(_lst['itens'])} itens** ao final de **{_dest['nome']}**.")
                if st.button("Mover itens", key=f"ls_mv_btn_{key_suffix}", type="primary"):
                    api.acrescentar_itens_lista(_dest["_arquivo"], _lst["itens"])
                    st.success(f"Itens adicionados a **{_dest['nome']}**!")
                    st.rerun()

    # Retorna itens carregados via botão (fora do expander para o caller processar)
    _carregados = st.session_state.pop(f"ls_carregar_{key_suffix}", None)
    return _carregados


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

# ─────────────────────────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────────────────────────
if _pg == "clientes":
    sc1, sc2 = st.columns([3, 1])
    termo_cli = sc1.text_input("Buscar cliente", placeholder="Nome, CPF/CNPJ, e-mail…", key="cli_busca", label_visibility="collapsed")
    if sc2.button("🔍 Buscar", use_container_width=True, key="cli_btn"):
        st.session_state["cli_dados"] = None

    if "cli_dados" not in st.session_state or st.session_state.cli_dados is None:
        with st.spinner("Carregando clientes…"):
            try:
                st.session_state["cli_dados"] = api.buscar_clientes(termo_cli, limite=100)
            except Exception as e:
                st.error(f"Erro ao buscar clientes: {e}")
                st.session_state["cli_dados"] = []

    clientes = st.session_state.get("cli_dados") or []
    if not isinstance(clientes, list):
        clientes = []

    st.markdown(f"<div style='color:{TXT2};font-size:0.8rem;margin-bottom:12px'>{len(clientes)} cliente(s) encontrado(s)</div>", unsafe_allow_html=True)

    if clientes:
        import pandas as pd
        rows = []
        for c in clientes:
            rows.append({
                "Nome": c.get("nome") or c.get("razao_social", ""),
                "CPF/CNPJ": c.get("cpf_cnpj", ""),
                "Telefone": c.get("telefone", "") or c.get("celular", ""),
                "E-mail": c.get("email", ""),
                "Cidade": c.get("cidade", ""),
                "UF": c.get("uf", ""),
            })
        df_cli = pd.DataFrame(rows)
        st.dataframe(df_cli, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum cliente encontrado. Use a busca acima.")

# ─────────────────────────────────────────────────────────────────
# FORNECEDORES
# ─────────────────────────────────────────────────────────────────
if _pg == "fornecedores":
    sf1, sf2 = st.columns([3, 1])
    termo_forn = sf1.text_input("Buscar fornecedor", placeholder="Nome, CNPJ…", key="forn_busca", label_visibility="collapsed")
    if sf2.button("🔍 Buscar", use_container_width=True, key="forn_btn"):
        st.session_state["forn_dados"] = None

    if "forn_dados" not in st.session_state or st.session_state.forn_dados is None:
        with st.spinner("Carregando fornecedores…"):
            try:
                st.session_state["forn_dados"] = api.buscar_fornecedores(termo_forn, limite=100)
            except Exception as e:
                st.error(f"Erro: {e}")
                st.session_state["forn_dados"] = []

    fornecedores = st.session_state.get("forn_dados") or []
    if not isinstance(fornecedores, list):
        fornecedores = []

    st.markdown(f"<div style='color:{TXT2};font-size:0.8rem;margin-bottom:12px'>{len(fornecedores)} fornecedor(es)</div>", unsafe_allow_html=True)

    if fornecedores:
        import pandas as pd
        rows = []
        for f in fornecedores:
            rows.append({
                "Nome / Razão Social": f.get("razao_social") or f.get("nome", ""),
                "CNPJ": f.get("cnpj") or f.get("cpf_cnpj", ""),
                "Telefone": f.get("telefone", "") or f.get("celular", ""),
                "E-mail": f.get("email", ""),
                "Cidade": f.get("cidade", ""),
                "UF": f.get("uf", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum fornecedor encontrado.")

# ─────────────────────────────────────────────────────────────────
# VENDAS
# ─────────────────────────────────────────────────────────────────
if _pg == "vendas":
    import pandas as pd
    from datetime import date, timedelta

    vf1, vf2, vf3 = st.columns([1, 1, 1])
    d_ini_v = vf1.date_input("De", value=date.today() - timedelta(days=30), key="v_ini")
    d_fim_v = vf2.date_input("Até", value=date.today(), key="v_fim")
    if vf3.button("🔄 Carregar", use_container_width=True, key="v_load"):
        st.session_state["vendas_dados"] = None

    if "vendas_dados" not in st.session_state or st.session_state.vendas_dados is None:
        with st.spinner("Buscando vendas…"):
            try:
                st.session_state["vendas_dados"] = api.buscar_vendas(
                    data_ini=str(d_ini_v), data_fim=str(d_fim_v),
                    loja_id=loja_id, limite=200)
            except Exception as e:
                st.error(f"Erro: {e}")
                st.session_state["vendas_dados"] = []

    vendas = st.session_state.get("vendas_dados") or []
    if not isinstance(vendas, list): vendas = []

    # KPIs
    total_v = sum(float(v.get("valor_total") or 0) for v in vendas)
    cv1, cv2, cv3 = st.columns(3)
    cv1.markdown(f'<div class="stat-box"><div class="stat-val">{len(vendas)}</div><div class="stat-lbl">Pedidos</div></div>', unsafe_allow_html=True)
    cv2.markdown(f'<div class="stat-box"><div class="stat-val">R$ {total_v:,.0f}</div><div class="stat-lbl">Total vendido</div></div>', unsafe_allow_html=True)
    cv3.markdown(f'<div class="stat-box"><div class="stat-val">R$ {(total_v/len(vendas) if vendas else 0):,.0f}</div><div class="stat-lbl">Ticket médio</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if vendas:
        STATUS_MAP = {"1":"Aberto","2":"Aprovado","3":"Faturado","4":"Cancelado","5":"Em andamento","6":"Entregue"}
        rows = []
        for v in vendas:
            rows.append({
                "Nº": v.get("numero", ""),
                "Data": (v.get("data_emissao") or v.get("data", ""))[:10],
                "Cliente": v.get("cliente_nome") or v.get("cliente", {}).get("nome", ""),
                "Valor": f"R$ {float(v.get('valor_total') or 0):,.2f}",
                "Status": STATUS_MAP.get(str(v.get("status_id", "")), v.get("status", "")),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda encontrada no período.")

# ─────────────────────────────────────────────────────────────────
# ORÇAMENTOS
# ─────────────────────────────────────────────────────────────────
if _pg == "orcamentos":
    import pandas as pd
    from datetime import date, timedelta

    of1, of2, of3 = st.columns([1, 1, 1])
    d_ini_o = of1.date_input("De", value=date.today() - timedelta(days=30), key="o_ini")
    d_fim_o = of2.date_input("Até", value=date.today(), key="o_fim")
    if of3.button("🔄 Carregar", use_container_width=True, key="o_load"):
        st.session_state["orc_dados"] = None

    if "orc_dados" not in st.session_state or st.session_state.orc_dados is None:
        with st.spinner("Buscando orçamentos…"):
            try:
                st.session_state["orc_dados"] = api.buscar_orcamentos(
                    data_ini=str(d_ini_o), data_fim=str(d_fim_o),
                    loja_id=loja_id, limite=200)
            except Exception as e:
                st.error(f"Erro: {e}")
                st.session_state["orc_dados"] = []

    orc = st.session_state.get("orc_dados") or []
    if not isinstance(orc, list): orc = []

    total_o = sum(float(o.get("valor_total") or 0) for o in orc)
    co1, co2 = st.columns(2)
    co1.markdown(f'<div class="stat-box"><div class="stat-val">{len(orc)}</div><div class="stat-lbl">Orçamentos</div></div>', unsafe_allow_html=True)
    co2.markdown(f'<div class="stat-box"><div class="stat-val">R$ {total_o:,.0f}</div><div class="stat-lbl">Valor total</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if orc:
        rows = []
        for o in orc:
            rows.append({
                "Nº": o.get("numero", ""),
                "Data": (o.get("data_emissao") or o.get("data", ""))[:10],
                "Cliente": o.get("cliente_nome") or o.get("cliente", {}).get("nome", ""),
                "Valor": f"R$ {float(o.get('valor_total') or 0):,.2f}",
                "Validade": (o.get("data_validade") or "")[:10],
                "Status": o.get("status", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum orçamento encontrado no período.")

# ─────────────────────────────────────────────────────────────────
# HISTÓRICO DE COMPRAS
# ─────────────────────────────────────────────────────────────────
if _pg == "compras_hist":
    import pandas as pd
    from datetime import date, timedelta

    hf1, hf2, hf3 = st.columns([1, 1, 1])
    d_ini_h = hf1.date_input("De", value=date.today() - timedelta(days=60), key="h_ini")
    d_fim_h = hf2.date_input("Até", value=date.today(), key="h_fim")
    if hf3.button("🔄 Carregar", use_container_width=True, key="h_load"):
        st.session_state["comp_dados"] = None

    if "comp_dados" not in st.session_state or st.session_state.comp_dados is None:
        with st.spinner("Buscando pedidos de compra…"):
            try:
                st.session_state["comp_dados"] = api.buscar_compras(
                    data_ini=str(d_ini_h), data_fim=str(d_fim_h),
                    loja_id=loja_id, limite=200)
            except Exception as e:
                st.error(f"Erro: {e}")
                st.session_state["comp_dados"] = []

    compras = st.session_state.get("comp_dados") or []
    if not isinstance(compras, list): compras = []

    total_c = sum(float(c.get("valor_total") or 0) for c in compras)
    ch1, ch2 = st.columns(2)
    ch1.markdown(f'<div class="stat-box"><div class="stat-val">{len(compras)}</div><div class="stat-lbl">Pedidos de compra</div></div>', unsafe_allow_html=True)
    ch2.markdown(f'<div class="stat-box"><div class="stat-val">R$ {total_c:,.0f}</div><div class="stat-lbl">Total em compras</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if compras:
        rows = []
        for c in compras:
            rows.append({
                "Nº": c.get("numero", ""),
                "Data": (c.get("data_emissao") or c.get("data", ""))[:10],
                "Fornecedor": c.get("fornecedor_nome") or c.get("fornecedor", {}).get("nome", ""),
                "Valor": f"R$ {float(c.get('valor_total') or 0):,.2f}",
                "Status": c.get("status", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum pedido de compra encontrado no período.")

# ─────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────
if _pg == "financeiro":
    import pandas as pd
    from datetime import date, timedelta

    tab_rec, tab_pag = st.tabs(["💰 Contas a Receber", "💸 Contas a Pagar"])

    with tab_rec:
        fr1, fr2, fr3 = st.columns([1, 1, 1])
        d_ini_fr = fr1.date_input("De", value=date.today() - timedelta(days=30), key="fr_ini")
        d_fim_fr = fr2.date_input("Até", value=date.today() + timedelta(days=30), key="fr_fim")
        if fr3.button("🔄 Carregar", use_container_width=True, key="fr_load"):
            st.session_state["rec_dados"] = None

        if "rec_dados" not in st.session_state or st.session_state.rec_dados is None:
            with st.spinner("Carregando contas a receber…"):
                try:
                    st.session_state["rec_dados"] = api.buscar_contas_receber(
                        data_ini=str(d_ini_fr), data_fim=str(d_fim_fr), limite=200)
                except Exception as e:
                    st.error(f"Erro: {e}")
                    st.session_state["rec_dados"] = []

        receber = st.session_state.get("rec_dados") or []
        if not isinstance(receber, list): receber = []

        total_r = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in receber)
        total_r_pago = sum(float(r.get("valor_pago") or 0) for r in receber)
        total_r_ab = total_r - total_r_pago

        crr1, crr2, crr3 = st.columns(3)
        crr1.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{ACC}">R$ {total_r:,.0f}</div><div class="stat-lbl">Total a receber</div></div>', unsafe_allow_html=True)
        crr2.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{GRN}">R$ {total_r_pago:,.0f}</div><div class="stat-lbl">Recebido</div></div>', unsafe_allow_html=True)
        crr3.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{RED}">R$ {total_r_ab:,.0f}</div><div class="stat-lbl">Em aberto</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if receber:
            rows = []
            for r in receber:
                rows.append({
                    "Descrição": r.get("descricao") or r.get("historico", ""),
                    "Cliente": r.get("cliente_nome") or r.get("cliente", {}).get("nome", ""),
                    "Vencimento": (r.get("data_vencimento") or "")[:10],
                    "Valor": f"R$ {float(r.get('valor') or r.get('valor_total') or 0):,.2f}",
                    "Pago": f"R$ {float(r.get('valor_pago') or 0):,.2f}",
                    "Situação": "✅ Pago" if str(r.get("situacao_id","")) == "2" or str(r.get("pago","")) == "1" else "⏳ Aberto",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta a receber no período.")

    with tab_pag:
        fp1, fp2, fp3 = st.columns([1, 1, 1])
        d_ini_fp = fp1.date_input("De", value=date.today() - timedelta(days=30), key="fp_ini")
        d_fim_fp = fp2.date_input("Até", value=date.today() + timedelta(days=30), key="fp_fim")
        if fp3.button("🔄 Carregar", use_container_width=True, key="fp_load"):
            st.session_state["pag_dados"] = None

        if "pag_dados" not in st.session_state or st.session_state.pag_dados is None:
            with st.spinner("Carregando contas a pagar…"):
                try:
                    st.session_state["pag_dados"] = api.buscar_contas_pagar(
                        data_ini=str(d_ini_fp), data_fim=str(d_fim_fp), limite=200)
                except Exception as e:
                    st.error(f"Erro: {e}")
                    st.session_state["pag_dados"] = []

        pagar = st.session_state.get("pag_dados") or []
        if not isinstance(pagar, list): pagar = []

        total_p = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in pagar)
        total_p_pago = sum(float(p.get("valor_pago") or 0) for p in pagar)
        total_p_ab = total_p - total_p_pago

        cpp1, cpp2, cpp3 = st.columns(3)
        cpp1.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{ACC}">R$ {total_p:,.0f}</div><div class="stat-lbl">Total a pagar</div></div>', unsafe_allow_html=True)
        cpp2.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{GRN}">R$ {total_p_pago:,.0f}</div><div class="stat-lbl">Pago</div></div>', unsafe_allow_html=True)
        cpp3.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{RED}">R$ {total_p_ab:,.0f}</div><div class="stat-lbl">Em aberto</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if pagar:
            rows = []
            for p in pagar:
                rows.append({
                    "Descrição": p.get("descricao") or p.get("historico", ""),
                    "Fornecedor": p.get("fornecedor_nome") or p.get("fornecedor", {}).get("nome", ""),
                    "Vencimento": (p.get("data_vencimento") or "")[:10],
                    "Valor": f"R$ {float(p.get('valor') or p.get('valor_total') or 0):,.2f}",
                    "Pago": f"R$ {float(p.get('valor_pago') or 0):,.2f}",
                    "Situação": "✅ Pago" if str(p.get("situacao_id","")) == "2" or str(p.get("pago","")) == "1" else "⏳ Aberto",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta a pagar no período.")

# ─────────────────────────────────────────────────────────────────
# RELATÓRIOS
# ─────────────────────────────────────────────────────────────────
if _pg == "relatorios":
    import pandas as pd
    from datetime import date, timedelta

    st.markdown(f"<p style='color:{TXT2};margin-bottom:18px'>Selecione um relatório abaixo para gerar:</p>", unsafe_allow_html=True)

    tab_rv, tab_rc, tab_re = st.tabs(["📈 Vendas por período", "📦 Estoque atual", "💰 Resultado financeiro"])

    with tab_rv:
        rv1, rv2, rv3 = st.columns([1, 1, 1])
        d_ini_rv = rv1.date_input("De", value=date.today() - timedelta(days=30), key="rv_ini")
        d_fim_rv = rv2.date_input("Até", value=date.today(), key="rv_fim")
        if rv3.button("📊 Gerar relatório", use_container_width=True, key="rv_btn", type="primary"):
            with st.spinner("Gerando…"):
                try:
                    dados_rv = api.buscar_vendas(data_ini=str(d_ini_rv), data_fim=str(d_fim_rv), loja_id=loja_id, limite=500)
                    if not isinstance(dados_rv, list): dados_rv = []
                    if dados_rv:
                        total_rv = sum(float(v.get("valor_total") or 0) for v in dados_rv)
                        st.success(f"**{len(dados_rv)} pedidos** · Total: **R$ {total_rv:,.2f}** · Ticket médio: **R$ {total_rv/len(dados_rv):,.2f}**")
                        rows = []
                        for v in dados_rv:
                            rows.append({
                                "Data": (v.get("data_emissao") or "")[:10],
                                "Nº Pedido": v.get("numero",""),
                                "Cliente": v.get("cliente_nome",""),
                                "Valor (R$)": float(v.get("valor_total") or 0),
                                "Status": v.get("status",""),
                            })
                        df_rv = pd.DataFrame(rows)
                        st.dataframe(df_rv, use_container_width=True, hide_index=True)
                        st.bar_chart(df_rv.groupby("Data")["Valor (R$)"].sum())
                    else:
                        st.info("Nenhuma venda no período.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with tab_rc:
        rc1, rc2 = st.columns([2, 1])
        loja_rel = rc1.selectbox("Loja", ["Todas"] + list(api.LOJAS.values()), key="rc_loja")
        if rc2.button("📊 Gerar", use_container_width=True, key="rc_btn", type="primary"):
            loja_id_rel = None
            if loja_rel != "Todas":
                loja_id_rel = next((lid for lid, ln in api.LOJAS.items() if ln == loja_rel), None)
            c_rel = api.carregar_cache(loja_id_rel)
            if c_rel:
                prods = c_rel.get("produtos", [])
                rows = []
                for p in prods:
                    for v in p.get("variacoes", []):
                        vd = v.get("variacao", v)
                        rows.append({
                            "Produto": p.get("nome",""),
                            "Variação": vd.get("nome",""),
                            "Cód.": vd.get("codigo",""),
                            "Estoque": int(vd.get("estoque", 0) or 0),
                        })
                if rows:
                    df_rc = pd.DataFrame(rows)
                    total_itens = df_rc["Estoque"].sum()
                    st.success(f"**{len(df_rc)} variações** · **{total_itens} unidades** em estoque")
                    df_rc = df_rc.sort_values("Estoque", ascending=True)
                    st.dataframe(df_rc, use_container_width=True, hide_index=True)
                else:
                    st.info("Cache vazio. Sincronize primeiro.")
            else:
                st.info("Cache não encontrado. Sincronize a loja primeiro.")

    with tab_re:
        rfi1, rfi2, rfi3 = st.columns([1, 1, 1])
        d_ini_rf = rfi1.date_input("De", value=date.today() - timedelta(days=30), key="rf_ini")
        d_fim_rf = rfi2.date_input("Até", value=date.today(), key="rf_fim")
        if rfi3.button("📊 Gerar", use_container_width=True, key="rf_btn", type="primary"):
            with st.spinner("Calculando…"):
                try:
                    _rec = api.buscar_contas_receber(data_ini=str(d_ini_rf), data_fim=str(d_fim_rf), limite=500)
                    _pag = api.buscar_contas_pagar(data_ini=str(d_ini_rf), data_fim=str(d_fim_rf), limite=500)
                    if not isinstance(_rec, list): _rec = []
                    if not isinstance(_pag, list): _pag = []
                    tot_rec = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in _rec)
                    tot_pag = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in _pag)
                    resultado = tot_rec - tot_pag
                    cor_res = GRN if resultado >= 0 else RED
                    rfr1, rfr2, rfr3 = st.columns(3)
                    rfr1.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{GRN}">R$ {tot_rec:,.0f}</div><div class="stat-lbl">Total a receber</div></div>', unsafe_allow_html=True)
                    rfr2.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{RED}">R$ {tot_pag:,.0f}</div><div class="stat-lbl">Total a pagar</div></div>', unsafe_allow_html=True)
                    rfr3.markdown(f'<div class="stat-box"><div class="stat-val" style="color:{cor_res}">R$ {resultado:,.0f}</div><div class="stat-lbl">Resultado</div></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro: {e}")

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

    # ── Importação via WhatsApp + IA ──────────────────────────────
    # Kits espelho EXATO dos botões da página de Pedidos
    # Simples = busca a cor no nome da variação (igual ao _adicionar_kit da página)
    # Lista   = todos os termos devem estar presentes (igual ao _sl da página)
    _WPP_KITS = {
        # ── Aveludada ── mesmos que CORES_MASC / CORES_FEM
        "masculino":         [("preto", 2), ("marrom", 1), ("azul marinho", 1), ("cinza chumbo", 1)],
        "feminino":          [("lilás", 1), ("marsala", 1), ("marrom", 1)],
        "pacote masculino":  [("preto", 3), ("azul marinho", 2), ("verde militar", 1),
                              ("marrom", 1), ("cinza chumbo", 2)],
        "pacote feminino":   [("lilás", 2), ("pink", 1), ("rosa", 1), ("marsala", 2),
                              ("vinho", 1), ("roxo", 1), ("marrom", 1), ("nude", 1)],
        # ── Silicone Líquido ── mesmo que SL_MASC / SL_FEM
        "sl masculino":      [(["preto",        "silicone"], 2), (["marrom",      "silicone"], 1),
                              (["azul marinho", "silicone"], 1), (["cinza chumbo","silicone"], 1)],
        "sl feminino":       [(["lilás",    "silicone"], 1), (["marsala","silicone"], 1),
                              (["marrom",   "silicone"], 1)],
        "sl pacote masculino":[(["preto",       "silicone"], 3), (["azul marinho","silicone"], 2),
                               (["verde militar","silicone"],1), (["marrom",      "silicone"], 1),
                               (["cinza chumbo","silicone"], 2)],
        "sl pacote feminino": [(["lilás",  "silicone"], 2), (["pink",   "silicone"], 1),
                               (["rosa",   "silicone"], 1), (["marsala","silicone"], 2),
                               (["vinho",  "silicone"], 1), (["roxo",   "silicone"], 1),
                               (["marrom", "silicone"], 1), (["nude",   "silicone"], 1)],
        # ── Very Rio ── mesmas cores do SL (silicone), observacao="Very Rio"
        "vr masculino":      [(["preto",        "silicone"], 2), (["marrom",      "silicone"], 1),
                              (["azul marinho", "silicone"], 1), (["cinza chumbo","silicone"], 1)],
        "vr feminino":       [(["lilás",  "silicone"], 1), (["marsala","silicone"], 1),
                              (["marrom", "silicone"], 1)],
        "vr pacote masculino":[(["preto",        "silicone"], 3), (["azul marinho","silicone"], 2),
                               (["verde militar","silicone"], 1), (["marrom",      "silicone"], 1),
                               (["cinza chumbo", "silicone"], 2)],
        "vr pacote feminino": [(["lilás",  "silicone"], 2), (["pink",   "silicone"], 1),
                               (["rosa",   "silicone"], 1), (["marsala","silicone"], 2),
                               (["vinho",  "silicone"], 1), (["roxo",   "silicone"], 1),
                               (["marrom", "silicone"], 1), (["nude",   "silicone"], 1)],
        # ── MagSafe ── mesmo que o botão MagSafe ×3 da página
        "magsafe":           [(["119,99", "magsafe"], 3)],
        # ── Diversos ── mesmos que os botões Diversos da página
        "brilho":            [(["59,99", "diversos"], 3)],   # ✨ Diversos Brilho ×3
        "diversos masculino":[(["39,99", "diversos"], 3)],   # 💪 Diversos Masculino ×3
    }
    # Kits que não têm cores predefinidas → viram avulso com descrição "Aparelho / Kit"
    _WPP_KITS_AVULSO = {"carteira", "película", "pelicula", "couro", "clear", "transparente",
                         "vidro", "anti-impacto", "anti impacto", "capinha", "strass",
                         "avulso cor", "outro"}

    with st.expander("🤖  Importar pedido via WhatsApp (IA)", expanded=False):
        st.markdown(f"<p style='color:{TXT2}'>Cole o texto do WhatsApp. A IA identifica o modelo e aplica os kits de cores exatos (mesmo comportamento dos botões Masculino/Feminino).</p>", unsafe_allow_html=True)
        wpp_texto = st.text_area(
            "Texto do WhatsApp",
            placeholder="Poco x3 - masculino e brilho\nX6- femininas\nNote13pro4g- masculinas e femininas",
            height=160, key="wpp_input", label_visibility="collapsed"
        )
        with st.expander("⚙️ Regras personalizadas", expanded=False):
            st.markdown(f"<p style='color:{TXT2};font-size:0.82rem'>Uma regra por linha. Formato: <code>kit [marca/palavra] = kit_substituto</code><br>Exemplos: <code>sl iphone = vr</code> &nbsp;|&nbsp; <code>sl apple = vr</code></p>", unsafe_allow_html=True)
            wpp_regras = st.text_area("Regras", placeholder="sl iphone = vr\nsl apple = vr", height=80, key="wpp_regras", label_visibility="collapsed")
        with st.expander("➕ Itens avulsos diretos", expanded=False):
            st.markdown(f"<p style='color:{TXT2};font-size:0.82rem'>Cada linha vira um item avulso (sem busca no catálogo). Formato: <code>Descrição | Qtd</code> ou só <code>Descrição</code> (qtd=1).<br>Exemplos: <code>iPhone 16 / Carteira | 2</code> &nbsp;|&nbsp; <code>Samsung A15 / Película</code></p>", unsafe_allow_html=True)
            wpp_avulsos_diretos_txt = st.text_area("Avulsos", placeholder="iPhone 16 / Carteira | 2\nSamsung A15 / Película", height=100, key="wpp_avulsos_txt", label_visibility="collapsed")
        col_ia1, col_ia2 = st.columns([3, 1])
        fornecedor_wpp = col_ia1.text_input("Fornecedor (opcional)", placeholder="ex: Distribuidora ABC", key="wpp_forn")
        gerar = col_ia2.button("✨ Gerar pré-pedido", type="primary", use_container_width=True, key="wpp_gerar")

        if gerar and (wpp_texto.strip() or (wpp_avulsos_diretos_txt or "").strip()):
            if not cache:
                st.warning("Sincronize os produtos primeiro.")
            else:
                with st.spinner("Analisando com IA…"):
                    import json as _json, re as _re, os as _os

                    # Parseia regras personalizadas: "sl iphone = vr" → [("sl","iphone","vr"), ...]
                    _regras_kit = []
                    for _rl in (wpp_regras or "").splitlines():
                        _rl = _rl.strip().lower()
                        _rm = _re.match(r'^([a-záéíóúãõ\s]+?)\s+([a-záéíóúãõ\s]+?)\s*=\s*([a-záéíóúãõ\s]+)$', _rl)
                        if _rm:
                            _regras_kit.append((_rm.group(1).strip(), _rm.group(2).strip(), _rm.group(3).strip()))

                    # ── Pré-processamento do texto do WhatsApp ──────────
                    _SECOES_MARCA   = {"motorola","samsung","apple","iphone","xiaomi","poco","realme"}
                    _SECOES_SPACE   = {"space","space 2"}
                    _SECOES_TRANSP  = {"transparente","transparente básica","transparente basica",
                                       "transparente básica pedido","transparente basica pedido"}

                    def _strip_wpp_linha(ln):
                        """Remove timestamp e nome do WhatsApp."""
                        return _re.sub(
                            r'^\[\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}(?::\d{2})?\]\s*[^:]+:\s*',
                            '', ln
                        ).strip()

                    def _expandir_barra(ln, marca=""):
                        """Expande 'A36/56 kits' → ['A36 kits','A56 kits']; 'Edge 60 / 60 fusion...' → duas."""
                        # "Edge 60 / 60 fusion" ou "Edge 60/60fusion"
                        m = _re.match(r'^(Edge\s*\d+)\s*/\s*(\d+\s*\w*)(.*)$', ln, _re.I)
                        if m:
                            e1, e2, rest = m.groups()
                            return [f"{e1.strip()}{rest}", f"Edge {e2.strip()}{rest}"]
                        # "A36/56", "G67/77", "7/8" etc.
                        m = _re.match(r'^([A-Za-z]*)(\d+)/(\d+)(.*)$', ln)
                        if m:
                            pfx, n1, n2, rest = m.groups()
                            p = marca + " " if marca else pfx
                            return [f"{pfx or marca}{n1}{rest}", f"{pfx or marca}{n2}{rest}"]
                        return [ln]

                    # Resultado separado: linhas para IA vs avulsos diretos (space/transparente)
                    _linhas_ia      = []   # vão para o prompt da IA
                    _avulsos_diretos = []  # criados diretamente sem IA

                    # Parseia avulsos digitados manualmente no campo "Itens avulsos diretos"
                    for _av_ln in (wpp_avulsos_diretos_txt or "").splitlines():
                        _av_ln = _av_ln.strip()
                        if not _av_ln:
                            continue
                        if "|" in _av_ln:
                            _av_desc, _av_qtd_s = _av_ln.rsplit("|", 1)
                            try:
                                _av_qtd = int(_av_qtd_s.strip())
                            except ValueError:
                                _av_qtd = 1
                            _av_desc = _av_desc.strip()
                        else:
                            _av_desc = _av_ln.strip()
                            _av_qtd = 1
                        if _av_desc:
                            _avulsos_diretos.append({"desc": _av_desc, "qtd": _av_qtd, "kit": "avulso"})

                    _secao    = ""
                    _marca    = ""  # Samsung / Motorola / Apple etc.

                    for _ln_raw in wpp_texto.splitlines():
                        _ln = _strip_wpp_linha(_ln_raw).strip()
                        if not _ln:
                            continue

                        _ln_low = _ln.lower().strip().rstrip(':').strip()

                        # Detecta seção
                        if _ln_low in _SECOES_MARCA:
                            _secao = "marca"; _marca = _ln_low; continue
                        if _ln_low in _SECOES_SPACE:
                            _secao = "space"; _marca = ""; continue
                        if _ln_low in _SECOES_TRANSP:
                            _secao = "transparente"; _marca = ""; continue
                        # Linha que começa com marca como cabeçalho
                        if _ln_low in ("motorola","samsung","apple","iphone"):
                            _secao = "marca"; _marca = _ln_low; continue

                        # ── Seção SPACE: "modelo +N" → brilho avulso direto ──
                        if _secao == "space":
                            for _exp in _expandir_barra(_ln):
                                _m_sp = _re.match(r'^(.+?)\s*\+\s*(\d+)\s*$', _exp.strip())
                                if _m_sp:
                                    _mod_sp, _qtd_sp = _m_sp.group(1).strip(), int(_m_sp.group(2))
                                    # Infere marca: se não tem letra → iPhone
                                    _nome_sp = _mod_sp if _re.search(r'[A-Za-z]', _mod_sp) else f"iPhone {_mod_sp}"
                                    _avulsos_diretos.append({
                                        "desc": f"{_nome_sp} / Space 2",
                                        "qtd":  _qtd_sp,
                                        "kit":  "space 2",
                                    })
                            continue

                        # ── Seção TRANSPARENTE: "modelo N" → transparente avulso direto ──
                        if _secao == "transparente":
                            for _exp in _expandir_barra(_ln, _marca):
                                _m_tr = _re.match(r'^(.+?)\s+(\d+)\s*$', _exp.strip())
                                if _m_tr:
                                    _mod_tr, _qtd_tr = _m_tr.group(1).strip(), int(_m_tr.group(2))
                                    # Adiciona marca se não tiver
                                    if _marca == "motorola" and not _re.search(r'edge|moto', _mod_tr, _re.I):
                                        _mod_tr = f"Motorola {_mod_tr}"
                                    elif _marca == "apple" and not _re.search(r'ip|iphone', _mod_tr, _re.I):
                                        _mod_tr = f"iPhone {_mod_tr}"
                                    _avulsos_diretos.append({
                                        "desc": f"{_mod_tr} / Transparente",
                                        "qtd":  _qtd_tr,
                                        "kit":  "transparente",
                                    })
                            continue

                        # ── Seção normal: expande barras e envia para IA ──
                        _expandidas = _expandir_barra(_ln)
                        for _exp in _expandidas:
                            if _marca in ("motorola",) and not _re.search(r'edge|moto|motorola', _exp, _re.I):
                                _linhas_ia.append(f"[Motorola] {_exp}")
                            elif _marca in ("apple","iphone") and not _re.search(r'ip|iphone|apple', _exp, _re.I):
                                _linhas_ia.append(f"[Apple] {_exp}")
                            else:
                                _linhas_ia.append(_exp)

                    _texto_proc = "\n".join(_linhas_ia)

                    _prods_all = cache.get("produtos", [])
                    _catalogo_txt = "\n".join(
                        f"{_p.get('codigo_interno','')} | {_p.get('nome','')}"
                        for _p in _prods_all if _p.get("codigo_interno") and _p.get("nome")
                    )[:12000]

                    _kits_disponiveis = list(_WPP_KITS.keys())

                    _prompt = f"""Você é assistente de compras de uma loja de capas para celular no Brasil.
As pessoas anotam os modelos com abreviações e erros de digitação. Seu trabalho é identificar o modelo correto.

Pedido recebido (pré-processado — timestamps e nomes removidos, modelos com barra já expandidos):
{_texto_proc}

Catálogo de aparelhos (cod_interno | nome):
{_catalogo_txt}

Kits disponíveis: {_kits_disponiveis}

SEÇÕES ESPECIAIS — linhas prefixadas pelo pré-processador:
- "[Space] modelo +N" → kit="brilho", quantidade=N (ex: "[Space] 15 +5" = iPhone 15, brilho, qtd 5)
- "[Space] modelo +N" sem marca → iPhone
- "[Transparente] modelo N" → kit="transparente", quantidade=N (ex: "[Transparente] A07 5" = Samsung A07, transparente, qtd 5)
- "[Motorola] modelo kits" → prefixe o modelo com "Motorola" se não tiver marca
- "[Apple] modelo kits" → é iPhone
- "[SEÇÃO: X]" → linha de cabeçalho, ignore (não gere entrada)
- Cores específicas mencionadas isoladas (ex: "laranja", "azul marinho", "branca com prata", "strass") → kit="avulso cor" com a cor na descrição

ABREVIAÇÕES DE MODELOS — decodifique antes de buscar:
Motorola EDGE: "Ed"/"ED"/"edge" + número = EDGE [número]. Exemplos:
  Ed20=EDGE 20, Ed30=EDGE 30, Ed30f/Ed30fus=EDGE 30 Fusion, Ed30n/Ed30neo=EDGE 30 Neo,
  Ed40=EDGE 40, Ed40n/Ed40neo=EDGE 40 Neo, Ed50=EDGE 50, Ed50n=EDGE 50 Neo,
  Ed50f=EDGE 50 Fusion, Ed5050=EDGE 50, Ed60=EDGE 60, Ed60p/Ed60pro=EDGE 60 Pro,
  Ed70=EDGE 70, Ed70u/Ed70ultra=EDGE 70 Ultra, Ed70f=EDGE 70 Fusion
Sufixos: "pro/pró/p" → Pro | "ultra/ul/u" → Ultra | "neo/n" → Neo | "fusion/fus/f" → Fusion | "plus/+" → Plus
Motorola G: "G" + número (G23, G32, G53, G54, G60, G60S...)
Samsung A: "A" + número (A01, A02, A03, A04, A13, A14, A23, A24, A33, A34, A51, A52, A53, A54, A72, A73...)
Samsung Note: "Note" + número
Xiaomi/Poco: "X6"=Poco X6, "X6pro"=Poco X6 Pro, "Redmi"=Redmi [número], "Note13"=Redmi Note 13...
iPhone: "ip"/"iph"/"iphone" + número (ip15=iPhone 15, ip15pm=iPhone 15 Pro Max...)
Outros: ignore acentos e espaços extras, tente o modelo mais próximo do catálogo

ABREVIAÇÕES DE KITS — mapeie para o nome exato:
  "masc/masculina/masculinas/masculinos/m" → "masculino"
  "fem/feminina/femininas/femininos/f" → "feminino"
  "pac masc/pacote masc/pm" → "pacote masculino"
  "pac fem/pacote fem/pf" → "pacote feminino"
  "sl masc/silicone masc/slm/silicone liquido masc/silicone líquido masc" → "sl masculino"
  "sl fem/silicone fem/slf/silicone liquido fem/silicone líquido fem" → "sl feminino"
  "sl pac masc/slpm/silicone liquido pac masc" → "sl pacote masculino"
  "sl pac fem/slpf/silicone liquido pac fem" → "sl pacote feminino"
  "sl/silicone/silicone liquido/silicone líquido" sozinho (sem masc/fem) → gere 2 entradas: "sl pacote masculino" + "sl pacote feminino"
  "very rio masc/vr masc/vrm" → "vr masculino"
  "very rio fem/vr fem/vrf" → "vr feminino"
  "vr pac masc/vrpm" → "vr pacote masculino"
  "vr pac fem/vrpf" → "vr pacote feminino"
  "very rio/vr" sozinho → gere 2 entradas: "vr pacote masculino" + "vr pacote feminino"
  "magsafe/mag safe/ms" → "magsafe"
  "brilho/brilhos/br/bri/glitter/div br/diversos br" → "brilho"
  "div masc/diversos masc/dm" → "diversos masculino"
  "carteira/cart/wallet/porta cartão/porta cartao" → "carteira"  (avulso)
  "película/pelicula/peliculas/pel" → "película"  (avulso)
  "couro/leather" → "couro"  (avulso)
  "clear/transparente/cristal/básica/basica/transparente básica" → "transparente"  (avulso)
  "strass/pedras/brilhinho" → "strass"  (avulso)
  Qualquer tipo de produto não listado acima → use o nome exato como kit (será criado como avulso)
Se a linha pedir 2+ kits, gere uma entrada por kit para o mesmo aparelho.

REGRA SOBRE CORES — válida sempre, inclusive em texto normal:
Palavras de cor (preta, preto, branca, verde, lilás, rosa, vinho, nude, dourada, vermelha, etc.)
NUNCA são kits. São SEMPRE kit="avulso cor" com descricao_avulso=a cor.
Cores NUNCA viram "masculino" ou "feminino". A regra "kit ambíguo → masculino" não se aplica a cores.

TRANSCRIÇÃO DE VOZ / DITADO — quando o texto é fala contínua sem pontuação:
1. MODELO: "a" + número = Samsung A[número] ("a 06"=A06, "a 53"=A53). Nunca artigo.
   Outros: "iphone 15"=iPhone 15, "edge 30"=Edge 30, "g 54"=Moto G54.
2. MÚLTIPLOS MODELOS em sequência: ao detectar novo modelo, inicia entradas para ele.
3. QUANTIDADES por extenso — sempre quantidade, nunca artigo:
   "um/uma"=1, "dois/duas"=2, "três"=3, "quatro"=4, "cinco"=5, "seis"=6, "sete"=7, "oito"=8, "nove"=9, "dez"=10
4. [número] + [cor] → kit="avulso cor", descricao_avulso=cor no singular, quantidade_fixa=número
   Normalize gênero/plural: pretas→"preta", brancos→"branca", vermelhas→"vermelha", lilases→"lilás"
5. [número] + [kit] → kit=nome mapeado, quantidade_fixa=número
6. Kit nomeado (masculino, brilho, sl, vr, etc.) sem número → quantidade_fixa=1
7. Uma entrada JSON por par modelo+cor ou modelo+kit

Exemplo A — kits e cores mistos: "A 07 diversos masculino a 06 brilho a 53 uma preta duas vermelhas uma vinho"
→ A07 | kit="diversos masculino" | qtd=1
→ A06 | kit="brilho" | qtd=1
→ A53 | kit="avulso cor" descricao_avulso="preta" | qtd=1
→ A53 | kit="avulso cor" descricao_avulso="vermelha" | qtd=2
→ A53 | kit="avulso cor" descricao_avulso="vinho" | qtd=1

Exemplo B — só cores: "A 06 duas pretas uma verde militar duas lilás a 07 brilho duas pretas uma branca"
→ A06 | kit="avulso cor" descricao_avulso="preta" | qtd=2
→ A06 | kit="avulso cor" descricao_avulso="verde militar" | qtd=1
→ A06 | kit="avulso cor" descricao_avulso="lilás" | qtd=2
→ A07 | kit="brilho" | qtd=1
→ A07 | kit="avulso cor" descricao_avulso="preta" | qtd=2
→ A07 | kit="avulso cor" descricao_avulso="branca" | qtd=1

EXCLUSÕES: "menos [cor]" / "exceto [cor]" / "sem [cor]" / "tira [cor]" → inclua em excluir_cores.
Ex: "Ed30neo - brilho e masculina menos preta" → excluir_cores: ["preto"]

CASOS ESPECIAIS:
- "não temos nenhuma" / "estoque zerado" / "zeramos" / "acabou" / "sem estoque" na linha → significa pedir TODOS os kits: gere 4 entradas para o modelo: kit="masculino", kit="feminino", kit="brilho", kit="diversos masculino"
- "preta apenas" / "só preta" / "somente preta" JUNTO de um kit (ex: "A54 masculino só preta") → use kit="masculino" com excluir_cores=["marrom","azul marinho","cinza chumbo"]. ATENÇÃO: "duas pretas" ou "uma preta" em ditado NÃO é isso — é avulso cor.
- Linha que fala de AUSÊNCIA mas não pede nada (ex: "Edge 60 estoque zerado") → processe normalmente com os 4 kits

POSTURA — REGRA ABSOLUTA:
- Se o modelo existir no catálogo com nome parecido, use-o com confianca "baixa".
- Se o modelo NÃO existir de jeito nenhum no catálogo (nenhum nome próximo), marque cod_interno: null e nao_compreendido: false — o sistema vai criar como item avulso automaticamente.
- nao_compreendido: true SOMENTE para linhas completamente ilegíveis (emoji puro, linha em branco, texto aleatório sem modelo nem kit).
- Kit ambíguo (texto que pode ser kit mas não é claramente uma cor) → prefira "masculino". Cores NUNCA são kits.
- Nunca escreva justificativas — apenas processe.

Para seções Space e Transparente, o campo "quantidade_fixa" deve conter a quantidade explícita da linha (ex: +5 → 5, "A07 5" → 5). Para kits normais deixe null.

Retorne SOMENTE JSON válido, sem markdown:
[{{"modelo_digitado":"...","cod_interno":"...ou null","nome_produto":"...ou null","kit":"...ou null","descricao_avulso":"...ou null","excluir_cores":[],"quantidade_fixa":null,"confianca":"alta|media|baixa","nao_compreendido":false,"motivo":""}}]

O campo "descricao_avulso" deve ser preenchido quando kit="avulso cor" com o nome da cor (ex: "preta", "verde militar", "lilás"). Para outros kits, deixe null."""

                    st.session_state.pop("wpp_truncado_resto", None)
                    try:
                        _parsed = []  # preenchido pela IA se houver texto WPP
                        if _texto_proc.strip():
                            _ant_key = _os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
                            if not _ant_key:
                                st.error("Configure ANTHROPIC_API_KEY nos secrets do Streamlit.")
                            else:
                                import anthropic as _ant
                                _client = _ant.Anthropic(api_key=_ant_key)
                                _msg = _client.messages.create(
                                    model="claude-sonnet-4-6",
                                    max_tokens=8192,
                                    messages=[{"role": "user", "content": _prompt}]
                                )
                                _raw = _msg.content[0].text.strip()
                                # Extrai o array JSON — tenta completo primeiro, depois recupera parcial
                                _m = _re.search(r'\[.*\]', _raw, _re.DOTALL)
                                _json_str = _m.group() if _m else _raw
                                try:
                                    _parsed = _json.loads(_json_str)
                                except _json.JSONDecodeError:
                                    # JSON truncado: encontra o último objeto completo e fecha o array
                                    _ultimo_ok = _json_str.rfind('},')
                                    if _ultimo_ok == -1:
                                        _ultimo_ok = _json_str.rfind('}')
                                    if _ultimo_ok > 0:
                                        _json_rec = _json_str[:_ultimo_ok + 1] + ']'
                                        _parsed = _json.loads(_json_rec)
                                        # Descobre quais linhas do texto original NÃO foram processadas
                                        _modelos_proc = {
                                            (e.get("modelo_digitado") or "").strip().lower()
                                            for e in _parsed
                                        }
                                        _linhas_orig = [l for l in _texto_proc.splitlines() if l.strip()]
                                        _resto = []
                                        _encontrados = 0
                                        for _lo in reversed(_linhas_orig):
                                            if _lo.strip().lower() in _modelos_proc and _encontrados < len(_parsed):
                                                _encontrados += 1
                                            else:
                                                _resto.insert(0, _lo)
                                        _resto_txt = "\n".join(_resto) if _resto else ""
                                        st.session_state["wpp_truncado_resto"] = _resto_txt
                                        st.warning(f"⚠ Resposta da IA foi truncada — {len(_parsed)} linha(s) processadas.")
                                    else:
                                        raise

                        # Expande cada entrada nos itens reais (cor × qtd) usando os kits
                        # Mapas case-insensitive para lookup robusto
                        _prods_map_ci   = {p.get("codigo_interno","").lower(): p for p in _prods_all}
                        _prods_map_nome = {p.get("nome","").lower().strip(): p for p in _prods_all}
                        _linhas_expandidas = []

                        def _achar_produto(cod, nome_ai):
                            """Busca produto por cod (case-insensitive) e fallback por nome."""
                            if cod:
                                p = _prods_map_ci.get(cod.lower())
                                if p:
                                    return p
                            # fallback: nome exato
                            if nome_ai:
                                p = _prods_map_nome.get(nome_ai.lower().strip())
                                if p:
                                    return p
                                # fallback: nome contém
                                _nl = nome_ai.lower().strip()
                                for _k, _p in _prods_map_nome.items():
                                    if _nl in _k or _k in _nl:
                                        return _p
                            return None

                        _nao_compreendidos = []
                        for _entry in _parsed:
                            _cod  = _entry.get("cod_interno") or ""
                            _nome = _entry.get("nome_produto") or _entry.get("modelo_digitado", "")
                            _kit  = (_entry.get("kit") or "").lower()
                            _conf = _entry.get("confianca", "baixa")
                            _excluir   = [x.lower().strip() for x in _entry.get("excluir_cores", [])]
                            _qtd_fixa  = _entry.get("quantidade_fixa")
                            _nao_comp  = _entry.get("nao_compreendido", False)
                            _motivo    = _entry.get("motivo", "")
                            _nome_lower = (_entry.get("nome_produto") or _entry.get("modelo_digitado","")).lower()

                            # Aplica regras personalizadas: ex "sl iphone = vr"
                            for _r_kit, _r_palavra, _r_sub in _regras_kit:
                                if _kit.startswith(_r_kit) and _r_palavra in _nome_lower:
                                    # Substitui prefixo do kit: "sl masculino" → "vr masculino"
                                    _kit = _kit.replace(_r_kit, _r_sub, 1)
                                    break

                            if _nao_comp or not _kit:
                                _nao_compreendidos.append(
                                    f"• \"{_entry.get('modelo_digitado','')}\" — {_motivo or 'não identificado'}"
                                )
                                continue

                            # Kit avulso (carteira, película, cor etc.) ou kit desconhecido
                            if _kit in _WPP_KITS_AVULSO or _kit not in _WPP_KITS:
                                _prod_obj_av = _achar_produto(_cod, _nome)
                                _nome_av = _prod_obj_av.get("nome", _nome) if _prod_obj_av else _nome
                                _desc_avulso_extra = _entry.get("descricao_avulso") or ""
                                _qtd_av = int(_qtd_fixa) if _qtd_fixa else 1

                                # Para "avulso cor": tenta achar a variação pelo nome da cor no catálogo
                                # Normaliza gênero: preta→preto, branca→branco, vermelha→vermelho, etc.
                                _var_match_av = None
                                if _kit == "avulso cor" and _desc_avulso_extra and _prod_obj_av:
                                    _cor_busca = _desc_avulso_extra.lower().strip()
                                    # variantes de gênero para busca mais ampla
                                    _cor_variantes = {_cor_busca}
                                    _genero_map = {"preta":"preto","branca":"branco","vermelha":"vermelho",
                                                   "dourada":"dourado","rosada":"rosado","cinza":"cinza",
                                                   "lilás":"lilas","lilas":"lilás"}
                                    if _cor_busca in _genero_map:
                                        _cor_variantes.add(_genero_map[_cor_busca])
                                    # remove plural simples
                                    if _cor_busca.endswith("s") and len(_cor_busca) > 3:
                                        _cor_variantes.add(_cor_busca[:-1])
                                    for _v in _prod_obj_av.get("variacoes", []):
                                        _vn = _v.get("variacao", {}).get("nome", "").lower()
                                        if any(c in _vn for c in _cor_variantes):
                                            _var_match_av = _v.get("variacao", {})
                                            break

                                if _var_match_av:
                                    # Variação encontrada no catálogo
                                    _desc_av = f"{_nome_av} / {_desc_avulso_extra.title()}"
                                    _linhas_expandidas.append({
                                        "✓": True, "_cod": _prod_obj_av.get("codigo_interno",""),
                                        "_nome": _nome_av, "_kit": _kit, "_conf": _conf,
                                        "_achado": True, "_avulso_auto": False, "_obs": "",
                                        "_var_id":  _var_match_av.get("id", ""),
                                        "_var_cod": _var_match_av.get("codigo", ""),
                                        "_prod_id": _prod_obj_av.get("id", ""),
                                        "_custo":   float(_prod_obj_av.get("valor_custo") or 0),
                                        "Aparelho": _nome_av, "Kit": _desc_avulso_extra.title(),
                                        "Variação": _var_match_av.get("nome", _desc_avulso_extra.title()),
                                        "Qtd": _qtd_av, "Status": "✓",
                                        "_desc_avulso": _desc_av,
                                    })
                                else:
                                    # Não encontrou → avulso
                                    if _kit == "avulso cor" and _desc_avulso_extra:
                                        _desc_av = f"{_nome_av} / {_desc_avulso_extra.title()}"
                                    else:
                                        _desc_av = f"{_nome_av} / {_kit.title()}"
                                        if _desc_avulso_extra:
                                            _desc_av += f" {_desc_avulso_extra.title()}"
                                    _linhas_expandidas.append({
                                        "✓": False, "_cod": _cod, "_nome": _nome_av,
                                        "_kit": _kit, "_conf": _conf, "_achado": False,
                                        "_avulso_auto": True, "_obs": "",
                                        "_var_id": "", "_var_cod": "",
                                        "_prod_id": _prod_obj_av.get("id","") if _prod_obj_av else "",
                                        "_custo": 0.0,
                                        "Aparelho": _nome_av, "Kit": _kit.title(),
                                        "Variação": f"⚠ {_desc_av}",
                                        "Qtd": _qtd_av, "Status": "⚠",
                                        "_desc_avulso": _desc_av,
                                    })
                                continue

                            _cores_kit = _WPP_KITS.get(_kit, [])
                            _prod_obj  = _achar_produto(_cod, _nome)
                            if not _prod_obj:
                                # Modelo não encontrado → avulso automático
                                _desc_av = f"{_nome} / {_kit.title()}"
                                _linhas_expandidas.append({
                                    "✓": False, "_cod": "", "_nome": _nome,
                                    "_kit": _kit, "_conf": _conf, "_achado": False,
                                    "_avulso_auto": True,
                                    "_var_id": "", "_var_cod": "", "_prod_id": "", "_custo": 0.0,
                                    "Aparelho": _nome, "Kit": _kit.title(),
                                    "Variação": f"⚠ {_desc_av}",
                                    "Qtd": 1,
                                    "Status": "⚠",
                                    "_desc_avulso": _desc_av,
                                })
                                continue
                            # Atualiza cod e nome com o que foi encontrado no cache
                            _cod  = _prod_obj.get("codigo_interno", _cod)
                            _nome = _prod_obj.get("nome", _nome)

                            for _cor, _qtd in _cores_kit:
                                # quantidade_fixa sobrepõe a qtd do kit (ex: Space +5)
                                if _qtd_fixa:
                                    _qtd = int(_qtd_fixa)
                                # Aplica exclusões ("menos preta" → pula "preto"/"preta")
                                _cor_lower = (_cor if isinstance(_cor, str) else " ".join(_cor)).lower()
                                if any(_ex in _cor_lower or _cor_lower in _ex for _ex in _excluir):
                                    continue
                                _termos = [_cor] if isinstance(_cor, str) else _cor
                                # Busca a variação EXATA no catálogo pelo nome
                                _var_match = None
                                if _prod_obj:
                                    for _v in _prod_obj.get("variacoes", []):
                                        _vd = _v.get("variacao", {})
                                        _vn = _vd.get("nome", "").lower()
                                        if all(t.lower() in _vn for t in _termos):
                                            _var_match = _vd
                                            break

                                _encontrado = _var_match is not None and bool(_cod) and _prod_obj is not None
                                _obs_kit = ("Very Rio" if _kit.startswith("vr ") else
                                            ("MagSafe" if _kit == "magsafe" else ""))
                                _desc_av_var = f"{_nome} / {_kit.title()} / {'/'.join(_termos)}"
                                _linhas_expandidas.append({
                                    "✓":           _encontrado,
                                    "_cod":        _cod,
                                    "_nome":       _nome,
                                    "_kit":        _kit,
                                    "_conf":       _conf,
                                    "_achado":     _encontrado,
                                    "_avulso_auto": not _encontrado,
                                    "_obs":        _obs_kit,
                                    "_var_id":     _var_match.get("id", "") if _var_match else "",
                                    "_var_cod":    _var_match.get("codigo", "") if _var_match else "",
                                    "_prod_id":    _prod_obj.get("id", "") if _prod_obj else "",
                                    "_custo":      float(_prod_obj.get("valor_custo") or 0) if _prod_obj else 0.0,
                                    "Aparelho":    _nome,
                                    "Kit":         _kit.title(),
                                    "Variação":    _var_match.get("nome", "") if _var_match else f"⚠ {'/'.join(_termos)} não encontrado",
                                    "Qtd":         _qtd,
                                    "Status":      "✓" if _encontrado else "⚠",
                                    "_desc_avulso": _desc_av_var,
                                })

                        # Injeta avulsos diretos (Space / Transparente) parseados sem IA
                        for _av in _avulsos_diretos:
                            _linhas_expandidas.append({
                                "✓": False,
                                "_cod": "", "_nome": _av["desc"],
                                "_kit": _av["kit"], "_conf": "alta",
                                "_achado": False, "_avulso_auto": True, "_obs": "",
                                "_var_id": "", "_var_cod": "", "_prod_id": "", "_custo": 0.0,
                                "Aparelho": _av["desc"],
                                "Kit": _av["kit"].title(),
                                "Variação": f"⚠ {_av['desc']}",
                                "Qtd": _av["qtd"],
                                "Status": "⚠",
                                "_desc_avulso": _av["desc"],
                            })

                        st.session_state["wpp_expandido"]      = _linhas_expandidas
                        st.session_state["wpp_nao_comp"] = _nao_compreendidos
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")

        # ── Resto truncado — cole novamente ───────────────────────
        if st.session_state.get("wpp_truncado_resto"):
            _resto_wpp = st.session_state["wpp_truncado_resto"]
            st.warning(f"⚠ Resposta da IA foi truncada — as linhas abaixo não foram processadas. Copie, cole no campo acima e gere novamente.")
            st.text_area("Resto não processado (copie e cole acima):", value=_resto_wpp, height=120, key="wpp_resto_area")
            if st.button("🗑 Limpar aviso de truncamento", key="wpp_limpar_resto"):
                del st.session_state["wpp_truncado_resto"]
                st.rerun()

        # ── Itens não compreendidos ────────────────────────────────
        if st.session_state.get("wpp_nao_comp"):
            _nc = st.session_state["wpp_nao_comp"]
            st.markdown(f"""
            <div style="background:{RED_LT};border:1px solid {RED}44;border-radius:8px;padding:10px 14px;margin:10px 0">
              <div style="font-weight:700;color:{RED};margin-bottom:4px">⚠ {len(_nc)} linha(s) não compreendida(s) — revise o texto:</div>
              <div style="color:{TXT};font-size:0.83rem;line-height:1.7">{"<br>".join(_nc)}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Tabela de revisão com seleção ──────────────────────────
        if "wpp_expandido" in st.session_state and st.session_state.wpp_expandido:
            import pandas as _pd
            _linhas   = st.session_state.wpp_expandido
            _achados  = [l for l in _linhas if l["_achado"]]
            _falhos   = [l for l in _linhas if not l["_achado"]]
            _forn     = fornecedor_wpp.strip() or st.session_state.get("fornecedor_global", "") or "—"

            st.markdown(f"<div style='font-weight:700;font-size:0.95rem;margin:14px 0 6px'>Pré-pedido gerado — selecione e ajuste</div>", unsafe_allow_html=True)

            # ── Itens encontrados no catálogo ──
            if _achados:
                _df_ok = _pd.DataFrame(_achados)[["✓","Aparelho","Kit","Variação","Qtd"]]
                _edited_ok = st.data_editor(
                    _df_ok,
                    column_config={
                        "✓":        st.column_config.CheckboxColumn("✓", width="small"),
                        "Aparelho": st.column_config.TextColumn("Aparelho", width="medium", disabled=True),
                        "Kit":      st.column_config.TextColumn("Kit", width="small", disabled=True),
                        "Variação": st.column_config.TextColumn("Variação (catálogo)", width="large", disabled=True),
                        "Qtd":      st.column_config.NumberColumn("Qtd", min_value=1, max_value=999, width="small"),
                    },
                    hide_index=True, use_container_width=True, key="wpp_editor_ok",
                )
            else:
                _edited_ok = _pd.DataFrame()

            # ── Itens NÃO encontrados — criar como avulso ──
            if _falhos:
                st.markdown(f"""
                <div style="background:{RED_LT};border:1px solid {RED}44;border-radius:8px;padding:8px 14px;margin:10px 0 4px">
                  <span style="font-weight:700;color:{RED}">⚠ {len(_falhos)} variação(ões) sem match no catálogo</span>
                  <span style="color:{TXT2};font-size:0.8rem;margin-left:8px">— marque para criar como item avulso (sem vínculo com catálogo)</span>
                </div>
                """, unsafe_allow_html=True)

                _rows_falhos = []
                for _l in _falhos:
                    if _l.get("_avulso_auto"):
                        _desc_sugerida = _l.get("_desc_avulso", f"{_l['Aparelho']} / {_l['Kit']}")
                    else:
                        _termos_raw = _l["Variação"].replace("⚠ ", "").replace(" não encontrado", "")
                        _desc_sugerida = f"{_l['Aparelho']} / {_l['Kit']} / {_termos_raw}"
                    _rows_falhos.append({
                        "Criar avulso": _l.get("_avulso_auto", False),  # auto-marca modelo não encontrado
                        "Descrição": _desc_sugerida,
                        "Qtd": _l["Qtd"],
                    })

                _df_falhos = _pd.DataFrame(_rows_falhos)
                _edited_falhos = st.data_editor(
                    _df_falhos[["Criar avulso", "Descrição", "Qtd"]],
                    column_config={
                        "Criar avulso": st.column_config.CheckboxColumn("Criar avulso", width="small"),
                        "Descrição":    st.column_config.TextColumn("Descrição (editável)", width="large"),
                        "Qtd":          st.column_config.NumberColumn("Qtd", min_value=1, max_value=999, width="small"),
                    },
                    hide_index=True, use_container_width=True, key="wpp_editor_falhos",
                )
            else:
                _edited_falhos = _pd.DataFrame()

            # ── Contadores e ações ──
            _n_ok  = int(_edited_ok["✓"].sum()) if not _edited_ok.empty and "✓" in _edited_ok.columns else 0
            _n_av  = int(_edited_falhos["Criar avulso"].sum()) if not _edited_falhos.empty and "Criar avulso" in _edited_falhos.columns else 0
            _total = _n_ok + _n_av

            col_wpp1, col_wpp2 = st.columns([2, 1])
            col_wpp1.markdown(f"<div style='color:{TXT2};font-size:0.8rem;padding-top:8px'>{_n_ok} do catálogo · {_n_av} avulso(s) · {_total} total</div>", unsafe_allow_html=True)
            if col_wpp2.button("🗑 Limpar", key="wpp_clear", use_container_width=True):
                for _k in ["wpp_expandido", "wpp_nao_comp"]:
                    st.session_state.pop(_k, None)
                st.rerun()

            if _total and st.button("➕ Adicionar ao pedido", type="primary", key="wpp_add", use_container_width=True):
                if "pedido_itens" not in st.session_state:
                    st.session_state.pedido_itens = []
                if "pedido_avulsos" not in st.session_state:
                    st.session_state.pedido_avulsos = []

                _adicionados = 0

                # Itens do catálogo
                if not _edited_ok.empty:
                    for _i, _erow in _edited_ok[_edited_ok["✓"] == True].iterrows():
                        _meta = _achados[_i]
                        st.session_state.pedido_itens.append({
                            "fornecedor":    _forn,
                            "produto_id":    _meta["_prod_id"],
                            "produto_nome":  _meta["_nome"],
                            "cod_interno":   _meta["_cod"],
                            "variacao_id":   _meta["_var_id"],
                            "variacao_cod":  _meta["_var_cod"],
                            "variacao_nome": _erow["Variação"],
                            "estoque_atual": 0,
                            "quantidade":    int(_erow["Qtd"]),
                            "Qtd a Pedir":   int(_erow["Qtd"]),
                            "valor_custo":   str(_meta["_custo"]),
                            "observacao":    _meta.get("_obs", ""),
                        })
                        _adicionados += 1

                # Itens avulsos (sem match)
                if not _edited_falhos.empty:
                    for _, _frow in _edited_falhos[_edited_falhos["Criar avulso"] == True].iterrows():
                        st.session_state.pedido_avulsos.append({
                            "fornecedor":    _forn,
                            "cod_interno":   "AVULSO",
                            "produto_nome":  _frow["Descrição"],
                            "variacao_cod":  "",
                            "variacao_nome": "",
                            "estoque_atual": 0,
                            "quantidade":    int(_frow["Qtd"]),
                            "valor_custo":   "0.00",
                            "observacao":    "Criado via WhatsApp — sem vínculo com catálogo",
                            "_avulso":       True,
                        })
                        _adicionados += 1

                for _k in ["wpp_expandido", "wpp_nao_comp"]:
                    st.session_state.pop(_k, None)
                st.success(f"✅ {_adicionados} itens adicionados ao pedido!")
                st.rerun()

    st.divider()

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

        _itens_ped_load = painel_listas(
            st.session_state.get("pedido_itens", []) + st.session_state.get("pedido_avulsos", []),
            "pedido", key_suffix="ped"
        )
        if _itens_ped_load is not None:
            # Separa itens cadastrados de avulsos
            st.session_state.pedido_itens   = [i for i in _itens_ped_load if not i.get("_avulso")]
            st.session_state.pedido_avulsos = [i for i in _itens_ped_load if i.get("_avulso")]
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

            def _fmt_brl(v):
                try:
                    f = float(str(v).replace(",", "."))
                    return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(v)

            # Monta lista flat de todos os itens para indexação única
            _ped_flat = []
            for _lk, _lst in [("pedido_itens", st.session_state.pedido_itens),
                               ("pedido_avulsos", st.session_state.get("pedido_avulsos", []))]:
                for _i, _it in enumerate(_lst):
                    _ped_flat.append({"lk": _lk, "idx": _i, "it": _it})

            total_calculado = sum(
                int(r["it"].get("quantidade", 1)) *
                float(str(r["it"].get("valor_custo", "0")).replace(",", "."))
                for r in _ped_flat
            )

            # Tabela HTML pura — compacta em qualquer dispositivo
            _rows_html = ""
            for _n, _r in enumerate(_ped_flat):
                _it   = _r["it"]
                _qtd  = int(_it.get("quantidade", 1))
                _nome = _it.get("produto_nome", "")
                _var  = _it.get("variacao_nome", "") or ""
                _obs  = _it.get("observacao", "") or ""
                _tag  = "🆕 " if _it.get("_avulso") else ""
                _info = " · ".join(filter(None, [_var, _obs]))
                _bg   = CARD if _n % 2 == 0 else BG
                _rows_html += f"""
                <tr style="background:{_bg}">
                  <td style="padding:5px 6px;font-size:0.73rem;color:{TXT};
                             max-width:0;overflow:hidden;text-overflow:ellipsis;
                             white-space:nowrap">
                    {_tag}{_nome}
                    {"<br><span style='font-size:0.65rem;color:" + TXT2 + "'>" + _info + "</span>" if _info else ""}
                  </td>
                  <td style="padding:5px 6px;text-align:center;font-size:0.8rem;
                             font-weight:700;color:{TXT};white-space:nowrap;width:36px">
                    {_qtd}
                  </td>
                </tr>"""

            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;
                          border:1px solid {BOR};border-radius:8px;overflow:hidden">
              <thead>
                <tr style="background:{SB}">
                  <th style="padding:5px 6px;text-align:left;font-size:0.62rem;
                             font-weight:700;text-transform:uppercase;
                             letter-spacing:.5px;color:{TXT2}">#&nbsp; Produto · Variação</th>
                  <th style="padding:5px 6px;text-align:center;font-size:0.62rem;
                             font-weight:700;text-transform:uppercase;
                             letter-spacing:.5px;color:{TXT2};width:36px">Qtd</th>
                </tr>
              </thead>
              <tbody>{_rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)

            # Controles: seleciona linha → edita qtd / edita item / exclui
            if _ped_flat:
                _fmt_item = lambda n: (
                    f"{n+1}. {_ped_flat[n]['it'].get('produto_nome','')} "
                    f"· {_ped_flat[n]['it'].get('variacao_nome','') or _ped_flat[n]['it'].get('observacao','')}"
                )
                _ca, _cb, _cc, _cd = st.columns([4, 1, 1, 1])
                _sel = _ca.selectbox("Item", range(len(_ped_flat)),
                                     format_func=_fmt_item,
                                     label_visibility="collapsed",
                                     key="ped_sel")
                _it_sel = _ped_flat[_sel]["it"]
                _nova_qtd = _cb.number_input(
                    "Qtd", min_value=0, step=1,
                    value=int(_it_sel.get("quantidade", 1)),
                    key=f"ped_qtd_ctrl_{_sel}",
                    label_visibility="collapsed",
                )
                if _nova_qtd != int(_it_sel.get("quantidade", 1)):
                    st.session_state[_ped_flat[_sel]["lk"]][_ped_flat[_sel]["idx"]]["quantidade"] = _nova_qtd
                    st.rerun()
                if _cc.button("✏️", use_container_width=True, key="ped_edit_btn", help="Editar"):
                    st.session_state["_editar_lista"] = _ped_flat[_sel]["lk"]
                    st.session_state["_editar_idx"]   = _ped_flat[_sel]["idx"]
                    st.rerun()
                if _cd.button("🗑", use_container_width=True, key="ped_del_btn", help="Excluir"):
                    st.session_state[_ped_flat[_sel]["lk"]].pop(_ped_flat[_sel]["idx"])
                    st.rerun()
            st.divider()
            st.metric("💰 Total estimado",
                      f"R$ {total_calculado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


            # ── Exportação filtrada por tipo de variação ───────────────
            with st.expander("🔽 Exportar por tipo de variação", expanded=False):
                # Detecta tipos a partir das variações presentes no pedido
                def _tipo_variacao(nome_var):
                    """Classifica a variação em tipo (para filtro de exportação)."""
                    v = (nome_var or "").lower()
                    if "very rio" in v or ("silicone" in v and "magsafe" not in v and "119" not in v):
                        return "Very Rio / Silicone"
                    if "aveludada" in v:
                        return "Aveludada"
                    if "magsafe" in v or "119" in v:
                        return "MagSafe"
                    if "brilho" in v or ("diversos" in v and "59" in v):
                        return "Brilho / Diversos"
                    if "diversos" in v:
                        return "Diversos"
                    if "carteira" in v:
                        return "Carteira"
                    if "transparente" in v:
                        return "Transparente"
                    if "película" in v or "pelicula" in v or "vidro" in v:
                        return "Película / Vidro"
                    if "strass" in v:
                        return "Strass"
                    if "couro" in v:
                        return "Couro"
                    if "clear" in v:
                        return "Clear"
                    if "space" in v:
                        return "Space"
                    if not nome_var or nome_var.strip() == "":
                        return "Avulso / Sem tipo"
                    return "Outros"

                _df_ped_tipos = df_ped.copy()
                _df_ped_tipos["_tipo_var"] = _df_ped_tipos["variacao_nome"].apply(_tipo_variacao)
                _tipos_presentes = sorted(_df_ped_tipos["_tipo_var"].unique().tolist())

                _tipos_selecionados = st.multiselect(
                    "Tipos de variação para exportar:",
                    options=_tipos_presentes,
                    default=_tipos_presentes,
                    key="export_tipos",
                )

                _df_filtrado = _df_ped_tipos[_df_ped_tipos["_tipo_var"].isin(_tipos_selecionados)].drop(columns=["_tipo_var"])
                st.caption(f"{len(_df_filtrado)} de {len(df_ped)} itens selecionados")

                for _c, _dv in [("estoque_atual", 0), ("observacao", ""), ("fornecedor", "—"),
                                ("variacao_nome", ""), ("valor_custo", "0.00")]:
                    if _c not in _df_filtrado.columns:
                        _df_filtrado[_c] = _dv
                if "total" not in _df_filtrado.columns:
                    _df_filtrado["total"] = _df_filtrado["quantidade"] * pd.to_numeric(_df_filtrado["valor_custo"], errors="coerce").fillna(0)

                _col_ex1, _col_ex2, _col_ex3, _col_ex4 = st.columns(4)
                with _col_ex1:
                    _buf_filt = io.BytesIO()
                    _df_exp_filt = _df_filtrado[["fornecedor", "cod_interno", "produto_nome", "variacao_nome",
                                                  "observacao", "estoque_atual", "quantidade", "valor_custo", "total"]].copy()
                    _df_exp_filt.columns = ["Fornecedor", "Cód.", "Produto", "Variação",
                                             "Obs.", "Estoque", "Pedir", "Custo Unit.", "Total Est."]
                    with pd.ExcelWriter(_buf_filt, engine="openpyxl") as _wr:
                        _df_exp_filt.to_excel(_wr, index=False, sheet_name="Pedido")
                    _buf_filt.seek(0)
                    st.download_button("📥 Excel completo", data=_buf_filt,
                                       file_name=f"pedido_filtrado_{data_pedido}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True, key="dl_filt_excel")
                with _col_ex2:
                    _buf_filt_s = io.BytesIO()
                    _df_simp_filt = _df_filtrado[["produto_nome", "variacao_nome", "observacao", "quantidade"]].copy()
                    _df_simp_filt.columns = ["Produto", "Variação", "Obs.", "Qtd"]
                    with pd.ExcelWriter(_buf_filt_s, engine="openpyxl") as _wr:
                        _df_simp_filt.to_excel(_wr, index=False, sheet_name="Pedido")
                    _buf_filt_s.seek(0)
                    st.download_button("📄 Excel simples", data=_buf_filt_s,
                                       file_name=f"pedido_simples_filtrado_{data_pedido}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True, key="dl_filt_simples")
                with _col_ex3:
                    _pdf_filt = gerar_pdf_pedido(_df_filtrado, fornecedor_global or "—", str(data_pedido), simplificado=True)
                    st.download_button("📑 PDF simples", data=_pdf_filt,
                                       file_name=f"pedido_simples_filtrado_{data_pedido}.pdf",
                                       mime="application/pdf",
                                       use_container_width=True, key="dl_filt_pdf_s")
                with _col_ex4:
                    _pdf_filt_c = gerar_pdf_pedido(_df_filtrado, fornecedor_global or "—", str(data_pedido), simplificado=False)
                    st.download_button("📑 PDF completo", data=_pdf_filt_c,
                                       file_name=f"pedido_completo_filtrado_{data_pedido}.pdf",
                                       mime="application/pdf",
                                       use_container_width=True, key="dl_filt_pdf_c")

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
                for _c, _dv in [("estoque_atual", 0), ("observacao", ""), ("fornecedor", "—"),
                                ("variacao_nome", ""), ("valor_custo", "0.00")]:
                    if _c not in df_ped.columns:
                        df_ped[_c] = _dv
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
# GERENCIAR LISTAS
# ══════════════════════════════════════════════
if _pg == "listas":
    import os as _glos, json as _gljson

    _TIPOS_BADGE = {"pedido": "🛒", "entrada": "📥", "acerto": "🔧", "etiquetas": "🏷️"}
    _TIPOS_NOMES = {"pedido": "Pedido", "entrada": "Entrada", "acerto": "Acerto", "etiquetas": "Etiquetas"}
    _TIPOS_FILTRO = {"todas": "Todas", "pedido": "🛒 Pedido", "entrada": "📥 Entrada", "acerto": "🔧 Acerto", "etiquetas": "🏷️ Etiquetas"}

    st.markdown("## 📋 Gerenciar Listas")

    _gl_tfiltro = st.radio(
        "Tipo:", list(_TIPOS_FILTRO.keys()),
        format_func=lambda t: _TIPOS_FILTRO[t],
        horizontal=True, key="gl_tipo_filtro"
    )

    _gl_todas = api.listar_listas_salvas()
    _tq = None if _gl_tfiltro == "todas" else _gl_tfiltro
    _gl_listas = _gl_todas if _tq is None else [l for l in _gl_todas if l.get("tipo") == _tq]

    st.divider()

    if not _gl_listas:
        st.info("Nenhuma lista encontrada.")
    else:
        st.caption(f"{len(_gl_listas)} lista(s)" + (" · ⬆️/⬇️ reordena dentro do próprio tipo" if _gl_tfiltro == "todas" else ""))

        for _gli, _lst in enumerate(_gl_listas):
            _arq    = _lst["_arquivo"]
            _nome   = _lst.get("nome", _arq)
            _tipo_l = _lst.get("tipo", "—")
            _loja_l = _lst.get("loja_nome", "—")
            _n_it   = len(_lst.get("itens", []))
            _data_l = _lst.get("criado_em", "")[:10]
            _badge  = _TIPOS_BADGE.get(_tipo_l, "📋")
            _tnome  = _TIPOS_NOMES.get(_tipo_l, _tipo_l)

            _listas_tipo = [l for l in _gl_todas if l.get("tipo") == _tipo_l]
            _pos = next((i for i, l in enumerate(_listas_tipo) if l["_arquivo"] == _arq), 0)

            _c1, _c2, _c3, _c4 = st.columns([6, 1, 1, 1])

            _c1.markdown(
                f"**{_nome}**  \n"
                f"<small style='color:#888'>{_badge} {_tnome} · {_loja_l} · {_n_it} itens · {_data_l}</small>",
                unsafe_allow_html=True
            )

            if _c2.button("⬆️", key=f"gl_up_{_arq}", disabled=(_pos == 0), use_container_width=True):
                api.mover_lista_na_ordem(_arq, _tipo_l, "cima")
                st.rerun()

            if _c3.button("⬇️", key=f"gl_down_{_arq}", disabled=(_pos == len(_listas_tipo) - 1), use_container_width=True):
                api.mover_lista_na_ordem(_arq, _tipo_l, "baixo")
                st.rerun()

            with _c4.popover("⚙️", use_container_width=True):
                # Renomear
                st.markdown("**✏️ Renomear**")
                _gl_nn = st.text_input("Nome:", value=_nome, key=f"gl_rn_{_arq}", label_visibility="collapsed")
                if st.button("Salvar nome", key=f"gl_rn_btn_{_arq}"):
                    _gl_cam = _glos.path.join(api.DIR_LISTAS, _arq)
                    with open(_gl_cam, encoding="utf-8") as _ff:
                        _gl_dd = _gljson.load(_ff)
                    _gl_dd["nome"] = _gl_nn.strip()
                    _gl_str = _gljson.dumps(_gl_dd, ensure_ascii=False, indent=2)
                    with open(_gl_cam, "w", encoding="utf-8") as _ff:
                        _ff.write(_gl_str)
                    api._gh_push_arquivo(f"listas/{_arq}", _gl_str, f"Renomeia lista: {_gl_nn.strip()}")
                    st.rerun()

                st.divider()

                # Mudar tipo
                st.markdown("**🔀 Mudar tipo**")
                _gl_tipos_alt = [t for t in _TIPOS_NOMES if t != _tipo_l]
                _gl_nt = st.selectbox(
                    "Novo tipo:", _gl_tipos_alt,
                    format_func=lambda t: f"{_TIPOS_BADGE[t]} {_TIPOS_NOMES[t]}",
                    key=f"gl_tp_{_arq}", label_visibility="collapsed"
                )
                if st.button("Mudar tipo", key=f"gl_tp_btn_{_arq}"):
                    api.mudar_tipo_lista(_arq, _gl_nt)
                    st.rerun()

                st.divider()

                # Mover itens
                st.markdown("**➡️ Mover itens para**")
                _outras_gl = [l for l in _gl_todas if l["_arquivo"] != _arq]
                if _outras_gl:
                    _gl_dst_i = st.selectbox(
                        "Destino:", range(len(_outras_gl)),
                        format_func=lambda i: f"{_TIPOS_BADGE.get(_outras_gl[i].get('tipo',''), '📋')} {_outras_gl[i]['nome']}",
                        key=f"gl_mv_{_arq}", label_visibility="collapsed"
                    )
                    if st.button(f"Mover {_n_it} itens", key=f"gl_mv_btn_{_arq}"):
                        api.acrescentar_itens_lista(_outras_gl[_gl_dst_i]["_arquivo"], _lst["itens"])
                        st.rerun()
                else:
                    st.caption("Nenhuma outra lista.")

                st.divider()

                # Excluir
                st.markdown("**🗑️ Excluir**")
                if st.button(f"Excluir lista", key=f"gl_del_{_arq}", type="primary"):
                    api.excluir_lista(_arq)
                    st.rerun()

    # ── Mesclar ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💥 Criar nova lista a partir de outras")
    if len(_gl_todas) < 2:
        st.info("Precisa de pelo menos 2 listas para mesclar.")
    else:
        _gl_opcoes_mescla = [
            f"{_TIPOS_BADGE.get(l.get('tipo',''), '📋')} {l['nome']} ({len(l.get('itens',[]))} itens)"
            for l in _gl_todas
        ]
        _gl_selecionadas = st.multiselect(
            "Selecione 2 ou mais listas para combinar:",
            options=range(len(_gl_todas)),
            format_func=lambda i: _gl_opcoes_mescla[i],
            key="gl_mescla_sel"
        )
        _gl_nome_mescla = st.text_input("Nome da nova lista:", key="gl_mescla_nome", placeholder="ex: Pedido completo 15/06")
        _total_itens = sum(len(_gl_todas[i].get("itens", [])) for i in _gl_selecionadas)
        if _gl_selecionadas:
            st.caption(f"Total: **{_total_itens} itens** de {len(_gl_selecionadas)} lista(s)")
        if st.button("💥 Criar lista combinada", key="gl_mescla_btn", type="primary"):
            if len(_gl_selecionadas) < 2:
                st.error("Selecione pelo menos 2 listas.")
            elif not _gl_nome_mescla.strip():
                st.error("Digite um nome para a nova lista.")
            else:
                _itens_combinados = []
                for _i in _gl_selecionadas:
                    _itens_combinados += _gl_todas[_i].get("itens", [])
                _tipo_base = _gl_todas[_gl_selecionadas[0]].get("tipo", "pedido")
                api.salvar_lista(_gl_nome_mescla.strip(), _tipo_base, _itens_combinados)
                st.success(f"✅ **{_gl_nome_mescla}** criada com {len(_itens_combinados)} itens!")
                st.rerun()


# ══════════════════════════════════════════════
# ABA USUÁRIOS — somente admin
# ══════════════════════════════════════════════
if _pg == "usuarios":
    st.subheader("👥 Gerenciamento de Usuários")

    _usuarios_db = api.carregar_usuarios()
    _setores_vivos = api.carregar_setores()
    setores_opcoes = {v["label"]: k for k, v in _setores_vivos.items()}

    # ── Tabela de usuários existentes ──────────
    st.markdown("### Usuários cadastrados")
    rows = []
    for login, ud in _usuarios_db.items():
        setor_k = ud.get("setor", "vendas")
        rows.append({
            "Login": login,
            "Nome": ud.get("nome", ""),
            "Setor": _setores_vivos.get(setor_k, {}).get("label", setor_k),
            "Páginas": ", ".join(_setores_vivos.get(setor_k, {}).get("paginas", [])),
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
        setor_atual_label = _setores_vivos.get(ud_sel.get("setor","vendas"), {}).get("label","Vendas")
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

    # ── Gerenciar setores e permissões ────────
    st.divider()
    st.markdown("### 🔐 Setores e permissões")

    _label_por_id = {m[0]: f"{m[1]} {m[2]}" for m in _MENU_FULL}
    _id_por_label = {v: k for k, v in _label_por_id.items()}
    _todas_paginas_labels = [_label_por_id[m[0]] for m in _MENU_FULL if not m[5]]

    _setores_edit = api.carregar_setores()

    # Seletor de setor a editar
    _opcoes_setores = list(_setores_edit.keys())
    _col_sel, _col_novo = st.columns([3, 2])
    _setor_sel_key = _col_sel.selectbox(
        "Setor", _opcoes_setores,
        format_func=lambda k: f"{_setores_edit[k]['label']} ({k})",
        key="setores_sel"
    )

    # Criar novo setor
    with _col_novo.popover("➕ Novo setor"):
        _ns_key   = st.text_input("ID (sem espaços, ex: financeiro)", key="ns_key").strip().lower()
        _ns_label = st.text_input("Nome exibido", key="ns_label").strip()
        if st.button("Criar", key="ns_criar"):
            if not _ns_key or not _ns_label:
                st.error("Preencha ID e nome.")
            elif _ns_key in _setores_edit:
                st.error("ID já existe.")
            elif _ns_key == "admin":
                st.error("Não é possível criar outro admin.")
            else:
                _setores_edit[_ns_key] = {"label": _ns_label, "paginas": []}
                api.salvar_setores(_setores_edit)
                api.SETORES = api.carregar_setores()
                st.success(f"Setor '{_ns_label}' criado.")
                st.rerun()

    if _setor_sel_key:
        _setor_obj = _setores_edit[_setor_sel_key]
        st.markdown(f"**Editando:** {_setor_obj['label']}")

        _c_nome, _c_del = st.columns([4, 1])
        _novo_label = _c_nome.text_input("Nome do setor", value=_setor_obj["label"], key=f"setor_label_{_setor_sel_key}")

        # Excluir setor (não admin)
        if _setor_sel_key != "admin":
            with _c_del.popover("🗑️"):
                st.warning(f"Excluir **{_setor_obj['label']}**?")
                if st.button("Confirmar", key="setor_del_btn", type="primary"):
                    del _setores_edit[_setor_sel_key]
                    # Usuários desse setor vão para 'vendas'
                    _udb = api.carregar_usuarios()
                    for _u in _udb.values():
                        if _u.get("setor") == _setor_sel_key:
                            _u["setor"] = "vendas"
                    api.salvar_usuarios(_udb)
                    api.salvar_setores(_setores_edit)
                    api.SETORES = api.carregar_setores()
                    st.success("Setor removido.")
                    st.rerun()

        # Multiselect de páginas
        _pags_atuais = _setor_obj.get("paginas", [])
        _pags_labels_atuais = [_label_por_id[p] for p in _pags_atuais if p in _label_por_id]
        _pags_novas_labels = st.multiselect(
            "Páginas permitidas",
            options=_todas_paginas_labels,
            default=_pags_labels_atuais,
            key=f"setor_pags_{_setor_sel_key}",
            disabled=(_setor_sel_key == "admin"),
            help="Admin sempre tem acesso a tudo."
        )

        if st.button("💾 Salvar permissões", key="setor_salvar", use_container_width=True,
                     disabled=(_setor_sel_key == "admin")):
            _setores_edit[_setor_sel_key]["label"]   = _novo_label.strip() or _setor_obj["label"]
            _setores_edit[_setor_sel_key]["paginas"]  = [_id_por_label[l] for l in _pags_novas_labels]
            api.salvar_setores(_setores_edit)
            api.SETORES = api.carregar_setores()
            st.success("Permissões salvas! Usuários desse setor verão as mudanças no próximo login.")
            st.rerun()
