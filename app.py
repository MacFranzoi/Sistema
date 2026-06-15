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
    st.session_state.tema = "light"
_dark = st.session_state.tema == "dark"

# Light: branco limpo / Dark: grafite com letras bem legíveis
BG    = "#18181b"   if _dark else "#f5f5f7"
SB    = "#111113"   if _dark else "#ffffff"
SB2   = "#1e1e22"   if _dark else "#f0f0f3"
CARD  = "#1e1e22"   if _dark else "#ffffff"
BOR   = "#2e2e34"   if _dark else "#e2e2e7"
TXT   = "#f2f2f5"   if _dark else "#111113"   # letras bem claras no dark
TXT2  = "#a0a0b0"   if _dark else "#6b6b80"   # muted mais legível no dark
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

/* ── TRANSIÇÕES GLOBAIS ── */
*, *::before, *::after {{ transition: background 0.18s ease, border-color 0.18s ease, color 0.12s ease, box-shadow 0.18s ease; }}
a, button {{ transition: all 0.15s ease !important; }}

/* ── FADE-IN de página ── */
.main .block-container > div:first-child {{ animation: fadeSlideIn 0.25s ease both; }}
@keyframes fadeSlideIn {{
  from {{ opacity: 0; transform: translateY(6px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ── TOPBAR ── */
[data-testid="stHeader"] {{
    background: {SB} !important;
    height: 48px !important;
    border-bottom: 1px solid {BOR} !important;
    backdrop-filter: blur(12px);
}}
[data-testid="stHeader"] button, [data-testid="stHeader"] svg {{
    color: {TXT2} !important; fill: {TXT2} !important;
}}
[data-testid="stHeader"] button:hover {{ color: {TXT} !important; fill: {TXT} !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

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
    transition: background 0.12s, color 0.12s !important;
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
    transition: box-shadow 0.2s ease;
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
    transition: box-shadow 0.2s ease, transform 0.2s ease;
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
    padding: 9px 13px !important; transition: border-color 0.15s, box-shadow 0.15s !important;
}}
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
    font-weight: 500 !important; transition: all 0.15s ease !important;
    letter-spacing: 0.1px;
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
    transition: box-shadow 0.2s ease !important;
}}
.stExpander:hover {{ box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important; }}
.stExpander summary {{ font-size: 0.88rem !important; font-weight: 500 !important; color: {TXT} !important; padding: 12px 16px !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ border-bottom: 1px solid {BOR}; background: transparent; gap: 0; padding: 0; }}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.84rem !important; padding: 10px 20px !important;
    color: {TXT2} !important; border-radius: 0 !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
    font-weight: 400 !important; transition: color 0.15s, border-color 0.15s !important;
}}
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
::-webkit-scrollbar-thumb {{ background: {BOR}; border-radius: 99px; transition: background 0.2s; }}
::-webkit-scrollbar-thumb:hover {{ background: {TXT2}; }}

/* ── LOGIN ── */
[data-testid="stMain"] > div:first-child {{ padding-top: 0 !important; }}
section[data-testid="stMain"] {{
    display: flex; align-items: center; justify-content: center; min-height: 100vh;
    background: {"radial-gradient(ellipse at 60% 40%, #1e1033 0%, #18181b 60%)" if _dark else "radial-gradient(ellipse at 60% 40%, #ede9fe 0%, #fafafa 60%)"} !important;
}}

/* MOBILE */
@media (max-width: 640px) {{
    .main .block-container {{ padding: 12px 14px 24px !important; }}
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

if st.session_state.usuario_logado is None:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        # Card único com logo + form
        st.markdown(f"""
        <style>
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
            transition: opacity 0.15s !important;
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
    ("usuarios",        "👤", "Usuários",             "CONFIGURAÇÕES",None,  False),
]

def _pode_ver(aba_idx, is_placeholder):
    if is_placeholder: return False
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
# ── CSS sidebar scroll + page top alignment ──
st.markdown(f"""
<style>
/* Header mínimo — mantém toggle da sidebar */
[data-testid="stHeader"] {{
    background: {SB} !important; height: 40px !important;
    min-height: 40px !important; border-bottom: 1px solid {BOR} !important;
}}
[data-testid="stHeader"] button, [data-testid="stHeader"] svg {{
    color: {TXT2} !important; fill: {TXT2} !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stAppViewContainer"] > section[data-testid="stMain"] {{
    padding-top: 40px !important;
}}
.main .block-container {{
    padding-top: 22px !important; padding-bottom: 40px !important;
    max-width: 100% !important;
}}
</style>
<script>
(function() {{
  function openSidebar() {{
    const sb = document.querySelector('[data-testid="stSidebar"]');
    if (sb && sb.getAttribute('aria-expanded') === 'false') {{
      const btn = document.querySelector('[data-testid="stSidebarNavToggleButton"] button') ||
                  document.querySelector('button[aria-controls*="sidebar"]');
      if (btn) btn.click();
    }}
  }}
  setTimeout(openSidebar, 300);
}})();
</script>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    # Logo — clicável, volta ao dashboard
    if st.button("⚡  PLUG ERP", key="logo_btn", use_container_width=True):
        st.session_state.pagina = "dashboard"
        st.rerun()

    # Seletor de loja — botões inline
    if "loja_ativa_id" not in st.session_state:
        st.session_state.loja_ativa_id = None   # None = todas
    loja_id = st.session_state.loja_ativa_id
    loja_sel_nome = next((n for lid, n in api.LOJAS.items() if lid == loja_id), "Todas as lojas")

    # card da loja atual — abre/fecha o picker
    if "loja_picker" not in st.session_state:
        st.session_state.loja_picker = False

    _icon_loja = "🏪"
    st.markdown(f"""
    <div style="border-bottom:1px solid {BOR};padding:8px 14px 6px">
      <div style="font-size:0.58rem;font-weight:600;letter-spacing:1px;
                  text-transform:uppercase;color:{TXT2};margin-bottom:4px">Loja ativa</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"{_icon_loja}  {loja_sel_nome}  {'▴' if st.session_state.loja_picker else '▾'}",
                 key="loja_toggle", use_container_width=True):
        st.session_state.loja_picker = not st.session_state.loja_picker
        st.rerun()

    if st.session_state.loja_picker:
        opcoes = [("Todas as lojas", None)] + [(n, lid) for lid, n in api.LOJAS.items()]
        for nome_op, lid_op in opcoes:
            ativo_op = loja_id == lid_op
            if st.button(
                f"{'●' if ativo_op else '○'}  {nome_op}",
                key=f"loja_opt_{lid_op or 'all'}",
                use_container_width=True
            ):
                st.session_state.loja_ativa_id = lid_op
                st.session_state.loja_picker = False
                st.rerun()
        st.markdown(f"<hr style='margin:4px 0;border-color:{BOR}'>", unsafe_allow_html=True)

    # ── Menu colapsável ──
    _pg_ativo = st.session_state.pagina
    _grupos_ordem = list(dict.fromkeys(m[3] for m in _MENU_VISIVEL))
    _grp_ativo = next((m[3] for m in _MENU_VISIVEL if m[0] == _pg_ativo), _grupos_ordem[0])

    if "sb_abertos" not in st.session_state:
        st.session_state.sb_abertos = {_grp_ativo}
    st.session_state.sb_abertos.add(_grp_ativo)

    for grupo in _grupos_ordem:
        aberto = grupo in st.session_state.sb_abertos
        seta = "▾" if aberto else "▸"
        if st.button(f"{seta}  {grupo}", key=f"grp_{grupo}", use_container_width=True):
            s = st.session_state.sb_abertos
            s.discard(grupo) if grupo in s else s.add(grupo)
            st.rerun()
        if aberto:
            for pid, icon, label, grp, _, _ in _MENU_VISIVEL:
                if grp != grupo: continue
                if st.button(f"  {icon}  {label}", key=f"nav_{pid}", use_container_width=True):
                    st.session_state.pagina = pid
                    st.rerun()

    # JS — estiliza logo, grupos e item ativo
    _pg_label = next((f"  {m[1]}  {m[2]}" for m in _MENU_VISIVEL if m[0] == _pg_ativo), "")
    st.markdown(f"""<script>
(function() {{
  const ACC='{ACC}', ACC_LT='{ACC_LT}', TXT='{TXT}', TXT2='{TXT2}', SB='{SB}', BOR='{BOR}';
  const activeLabel = {repr(_pg_label.strip())};

  function styleAll() {{
    const sb = document.querySelector('[data-testid="stSidebar"]');
    if (!sb) return;
    sb.querySelectorAll('button').forEach(btn => {{
      const t = btn.innerText.trim();
      // logo
      if (t === '⚡  PLUG ERP') {{
        btn.style.cssText = `font-size:1rem!important;font-weight:800!important;
          color:${{TXT}}!important;background:transparent!important;border:none!important;
          text-align:left!important;padding:0 16px!important;height:52px!important;
          width:100%!important;border-radius:0!important;border-bottom:1px solid ${{BOR}}!important;
          letter-spacing:-0.3px!important;cursor:pointer!important;`;
        return;
      }}
      // header de grupo (começa com ▾ ou ▸)
      if (t[0]==='▾' || t[0]==='▸') {{
        btn.style.cssText = `font-size:0.6rem!important;font-weight:700!important;
          letter-spacing:1.3px!important;text-transform:uppercase!important;
          color:${{TXT2}}!important;padding:13px 16px 4px!important;
          margin:0!important;border-radius:0!important;width:100%!important;
          background:transparent!important;border:none!important;`;
        return;
      }}
      // item ativo
      if (t === activeLabel) {{
        btn.style.cssText = `background:${{ACC_LT}}!important;color:${{ACC}}!important;
          font-weight:600!important;border-left:3px solid ${{ACC}}!important;
          padding-left:9px!important;border-radius:6px!important;`;
        return;
      }}
      // botão loja toggle ou opção — não mexe
      if (t.includes('▴') || t.includes('▾') && t.includes('●') === false && t[0] !== '▾') return;
      if (t.startsWith('●') || t.startsWith('○')) return;
      // item normal — limpa override anterior
      if (btn.style.cssText && !btn.closest('[data-testid="stForm"]')) {{
        btn.style.cssText = '';
      }}
    }});
  }}
  const obs = new MutationObserver(styleAll);
  obs.observe(document.body, {{childList:true, subtree:true}});
  styleAll();
}})();
</script>""", unsafe_allow_html=True)

    # Footer — avatar + tema + sair
    ini = (_nome_usr[0] if _nome_usr else "U").upper()
    st.markdown(f"""
    <div style="border-top:1px solid {BOR};padding:10px 14px;
         display:flex;align-items:center;gap:9px;background:{SB}">
      <div class="sb-avatar">{ini}</div>
      <div style="min-width:0;flex:1">
        <div class="sb-user-name">{_nome_usr}</div>
        <div class="sb-user-role">{_setor_lbl}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    col_t, col_s = st.columns([1, 1])
    if col_t.button("☀️ Tema" if _dark else "🌙 Tema", key="btn_tema", use_container_width=True):
        st.session_state.tema = "light" if _dark else "dark"
        st.rerun()
    if col_s.button("Sair", key="btn_sair", use_container_width=True):
        st.session_state.usuario_logado = None
        st.rerun()

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
        # ── Diversos ── mesmos que os botões Diversos da página
        "brilho":            [(["59,99", "diversos"], 3)],   # ✨ Diversos Brilho ×3
        "diversos masculino":[(["39,99", "diversos"], 3)],   # 💪 Diversos Masculino ×3
    }

    with st.expander("🤖  Importar pedido via WhatsApp (IA)", expanded=False):
        st.markdown(f"<p style='color:{TXT2}'>Cole o texto do WhatsApp. A IA identifica o modelo e aplica os kits de cores exatos (mesmo comportamento dos botões Masculino/Feminino).</p>", unsafe_allow_html=True)
        wpp_texto = st.text_area(
            "Texto do WhatsApp",
            placeholder="Poco x3 - masculino e brilho\nX6- femininas\nNote13pro4g- masculinas e femininas",
            height=160, key="wpp_input", label_visibility="collapsed"
        )
        col_ia1, col_ia2 = st.columns([3, 1])
        fornecedor_wpp = col_ia1.text_input("Fornecedor (opcional)", placeholder="ex: Distribuidora ABC", key="wpp_forn")
        gerar = col_ia2.button("✨ Gerar pré-pedido", type="primary", use_container_width=True, key="wpp_gerar")

        if gerar and wpp_texto.strip():
            if not cache:
                st.warning("Sincronize os produtos primeiro.")
            else:
                with st.spinner("Analisando com IA…"):
                    import json as _json, re as _re, os as _os

                    _prods_all = cache.get("produtos", [])
                    _catalogo_txt = "\n".join(
                        f"{_p.get('codigo_interno','')} | {_p.get('nome','')}"
                        for _p in _prods_all if _p.get("codigo_interno") and _p.get("nome")
                    )[:12000]

                    _kits_disponiveis = list(_WPP_KITS.keys())

                    _prompt = f"""Você é assistente de compras de uma loja de capas para celular no Brasil.
As pessoas anotam os modelos com abreviações e erros de digitação. Seu trabalho é identificar o modelo correto.

Pedido recebido no WhatsApp:
{wpp_texto}

Catálogo de aparelhos (cod_interno | nome):
{_catalogo_txt}

Kits disponíveis: {_kits_disponiveis}

REGRAS DE ABREVIAÇÃO — decodifique ANTES de buscar no catálogo:
- "Ed" ou "ED" = "EDGE" (série Motorola). Ex: Ed20=EDGE 20, Ed30=EDGE 30, Ed30fusion=EDGE 30 Fusion, Ed30neo=EDGE 30 Neo, Ed40neo=EDGE 40 Neo, Ed50=EDGE 50, Ed50neo=EDGE 50 Neo, Ed50fusion=EDGE 50 Fusion, Ed5050=EDGE 50, Ed60=EDGE 60, Ed60pro=EDGE 60 Pro, Ed70=EDGE 70, Ed70ultra=EDGE 70 Ultra
- "pró/pro/pró" = "Pro", "ultra/ul" = "Ultra", "neo" = "Neo", "fusion/fus" = "Fusion"
- Números colados à letra: Ed30neo = EDGE 30 Neo
- Marcas comuns: G23/G32/G53/G54 = Motorola G série; A01/A02/A03... = Samsung A série; Note = Samsung Note; X6/X6pro = Poco X6/X6 Pro; Redmi = Xiaomi Redmi
- Se não tiver certeza do modelo exato, use o nome mais próximo do catálogo

REGRAS DE KIT — mapeie para o nome EXATO abaixo:
Kits disponíveis: {list(_WPP_KITS.keys())}

- "masculinas/masculinos/masc" → "masculino"
- "femininas/femininos/fem" → "feminino"
- "pacote masc/pacote masculino" → "pacote masculino"
- "pacote fem/pacote feminino" → "pacote feminino"
- "sl masc/silicone masc/silicone masculino" → "sl masculino"
- "sl fem/silicone fem/silicone feminino" → "sl feminino"
- "sl pacote masc" → "sl pacote masculino"
- "sl pacote fem" → "sl pacote feminino"
- "brilho/brilhos/glitter/div brilho/diversos brilho" → "brilho"  (= botão ✨ Diversos Brilho ×3, adiciona R$59,99/Diversos × 3)
- "diversos masc/div masc/diversos masculino" → "diversos masculino"
- Se pedir 2 ou mais kits numa linha, gere uma entrada por kit para o mesmo aparelho

EXCLUSÕES: se a linha contiver "menos [cor]" ou "exceto [cor]" ou "sem [cor]", inclua essas cores em "excluir_cores".
Ex: "Ed30 neo- brilho e masculina menos preta" → excluir_cores: ["preto"]

- Encontre o cod_interno exato no catálogo para cada aparelho.
- Retorne SOMENTE JSON válido sem markdown:

[{{"modelo_digitado":"...","cod_interno":"...ou null","nome_produto":"...ou null","kit":"nome_do_kit","excluir_cores":[],"confianca":"alta|media|baixa"}}]"""

                    try:
                        _ant_key = _os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
                        if not _ant_key:
                            st.error("Configure ANTHROPIC_API_KEY nos secrets do Streamlit.")
                        else:
                            import anthropic as _ant
                            _client = _ant.Anthropic(api_key=_ant_key)
                            _msg = _client.messages.create(
                                model="claude-haiku-4-5-20251001",
                                max_tokens=2048,
                                messages=[{"role": "user", "content": _prompt}]
                            )
                            _raw = _msg.content[0].text.strip()
                            _m = _re.search(r'\[.*\]', _raw, _re.DOTALL)
                            _parsed = _json.loads(_m.group() if _m else _raw)

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

                            for _entry in _parsed:
                                _cod  = _entry.get("cod_interno") or ""
                                _nome = _entry.get("nome_produto") or _entry.get("modelo_digitado", "")
                                _kit  = _entry.get("kit", "").lower()
                                _conf = _entry.get("confianca", "baixa")
                                _excluir = [x.lower().strip() for x in _entry.get("excluir_cores", [])]
                                _cores_kit = _WPP_KITS.get(_kit, [])
                                _prod_obj  = _achar_produto(_cod, _nome)
                                # Atualiza cod e nome com o que foi encontrado no cache
                                if _prod_obj:
                                    _cod  = _prod_obj.get("codigo_interno", _cod)
                                    _nome = _prod_obj.get("nome", _nome)

                                for _cor, _qtd in _cores_kit:
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
                                    _linhas_expandidas.append({
                                        "✓":        _encontrado,  # só marca se achou exato
                                        "_cod":     _cod,
                                        "_nome":    _nome,
                                        "_kit":     _kit,
                                        "_conf":    _conf,
                                        "_achado":  _encontrado,
                                        "_var_id":  _var_match.get("id", "") if _var_match else "",
                                        "_var_cod": _var_match.get("codigo", "") if _var_match else "",
                                        "_prod_id": _prod_obj.get("id", "") if _prod_obj else "",
                                        "_custo":   float(_prod_obj.get("valor_custo") or 0) if _prod_obj else 0.0,
                                        "Aparelho": _nome,
                                        "Kit":      _kit.title(),
                                        # nome EXATO do catálogo — nunca o texto do WhatsApp
                                        "Variação": _var_match.get("nome", "") if _var_match else f"⚠ {'/'.join(_termos)} não encontrado",
                                        "Qtd":      _qtd,
                                        "Status":   "✓" if _encontrado else "⚠",
                                    })

                            st.session_state["wpp_expandido"] = _linhas_expandidas
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")

        # ── Tabela de revisão com seleção ──────────────────────────
        if "wpp_expandido" in st.session_state and st.session_state.wpp_expandido:
            import pandas as _pd
            _linhas = st.session_state.wpp_expandido

            st.markdown(f"<div style='font-weight:700;font-size:0.95rem;margin:14px 0 6px'>Pré-pedido gerado — selecione e ajuste</div>", unsafe_allow_html=True)

            _cols_visiveis = ["✓", "Aparelho", "Kit", "Variação", "Qtd", "Status"]
            _df_edit = _pd.DataFrame(_linhas)[_cols_visiveis + ["_cod","_nome","_kit","_achado","_var_id","_var_cod","_prod_id","_custo"]]

            _n_achados  = int(_pd.DataFrame(_linhas)["_achado"].sum())
            _n_falhos   = len(_linhas) - _n_achados
            if _n_falhos:
                st.warning(f"⚠ {_n_falhos} cor(es) não encontradas no catálogo — aparecem desmarcadas na lista.")

            _edited = st.data_editor(
                _df_edit[_cols_visiveis],
                column_config={
                    "✓":        st.column_config.CheckboxColumn("✓", width="small"),
                    "Aparelho": st.column_config.TextColumn("Aparelho", width="medium", disabled=True),
                    "Kit":      st.column_config.TextColumn("Kit", width="small", disabled=True),
                    "Variação": st.column_config.TextColumn("Variação (catálogo)", width="large", disabled=True),
                    "Qtd":      st.column_config.NumberColumn("Qtd", min_value=1, max_value=999, width="small"),
                    "Status":   st.column_config.TextColumn("", width="small", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key="wpp_editor",
            )

            _n_sel = int(_edited["✓"].sum())
            col_wpp1, col_wpp2 = st.columns([2, 1])
            col_wpp1.markdown(f"<div style='color:{TXT2};font-size:0.8rem;padding-top:8px'>{_n_sel} selecionado(s) · {_n_falhos} sem match</div>", unsafe_allow_html=True)
            if col_wpp2.button("🗑 Limpar", key="wpp_clear", use_container_width=True):
                del st.session_state["wpp_expandido"]
                st.rerun()

            if _n_sel and st.button("➕ Adicionar selecionados ao pedido", type="primary", key="wpp_add", use_container_width=True):
                if "pedido_itens" not in st.session_state:
                    st.session_state.pedido_itens = []
                _forn = fornecedor_wpp.strip() or st.session_state.get("fornecedor_global", "") or "—"
                _adicionados = 0
                for _i, _erow in _edited[_edited["✓"] == True].iterrows():
                    _meta = _linhas[_i]
                    if not _meta["_achado"]:
                        continue  # nunca adiciona sem match exato
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
                        "observacao":    "",
                    })
                    _adicionados += 1
                del st.session_state["wpp_expandido"]
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
