"""Sistema Beta v3 — Rich UI, mobile-first, market-ready."""

import json
import streamlit as st
import pandas as pd
import io
from datetime import date, datetime, timedelta
import api

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════

_CSS = """<style>
[data-testid="stHeader"],[data-testid="stSidebar"],
[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f0f2f8!important}

/* ── Top bar ── */
.bh{background:linear-gradient(135deg,#1e1b4b 0%,#4f46e5 60%,#7c3aed 100%);
color:#fff;padding:0 20px;height:56px;display:flex;align-items:center;
justify-content:space-between;position:sticky;top:0;z-index:300;
box-shadow:0 2px 20px rgba(79,70,229,.4)}
.bh-brand{display:flex;align-items:center;gap:10px}
.bh-icon{width:32px;height:32px;border-radius:8px;background:rgba(255,255,255,.18);
display:flex;align-items:center;justify-content:center;font-size:1.1rem}
.bh-name{font-weight:800;font-size:1rem;letter-spacing:-.3px}
.bh-pill{background:rgba(255,255,255,.22);padding:2px 8px;border-radius:20px;
font-size:.55rem;font-weight:700;letter-spacing:1px}
.bh-right{display:flex;align-items:center;gap:10px;font-size:.72rem}
.bh-loja{background:rgba(255,255,255,.15);padding:4px 10px;border-radius:20px;
font-size:.68rem;font-weight:600}

/* ── Nav tabs ── */
[data-testid="stTabs"]>[data-baseweb="tab-list"]{background:#fff!important;
border-bottom:1px solid #e2e8f0!important;padding:0 16px!important;
gap:0!important;overflow-x:auto!important;flex-wrap:nowrap!important;
box-shadow:0 1px 4px rgba(0,0,0,.06)!important}
[data-testid="stTabs"]>[data-baseweb="tab-list"] [data-baseweb="tab"]{
font-size:.78rem!important;font-weight:500!important;padding:12px 16px!important;
color:#64748b!important;background:none!important;border:none!important;
border-bottom:2.5px solid transparent!important;margin-bottom:-1px!important;
white-space:nowrap!important}
[data-testid="stTabs"]>[data-baseweb="tab-list"] [aria-selected="true"]{
color:#4f46e5!important;border-bottom-color:#4f46e5!important;font-weight:700!important}
[data-testid="stTabs"]>[data-baseweb="tab-list"] [data-baseweb="tab"]:hover{
color:#4f46e5!important;background:#f5f3ff!important}

/* ── Nested tabs ── */
[data-testid="stTabs"] [data-testid="stTabs"]>[data-baseweb="tab-list"]{
background:transparent!important;border-bottom:1px solid #dde3ee!important;
padding:0!important;box-shadow:none!important}
[data-testid="stTabs"] [data-testid="stTabs"]>[data-baseweb="tab-list"] [data-baseweb="tab"]{
padding:8px 12px!important;font-size:.75rem!important}

/* ── Page ── */
.pg{padding:20px 24px 60px;max-width:960px;margin:0 auto}
.pg-title{font-size:1.15rem;font-weight:800;color:#0f172a;letter-spacing:-.4px;margin:0}
.pg-sub{font-size:.74rem;color:#94a3b8;margin-top:3px;margin-bottom:16px}

/* ── Cards ── */
.card{background:#fff;border-radius:14px;padding:18px 20px;margin-bottom:14px;
box-shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04)}
.card-sm{background:#fff;border-radius:10px;padding:12px 14px;margin-bottom:8px;
box-shadow:0 1px 3px rgba(0,0,0,.05);border:1px solid #f1f5f9}
.card-grad{border-radius:14px;padding:20px 22px;color:#fff;margin-bottom:14px}
.card-ind{background:linear-gradient(135deg,#4f46e5,#7c3aed)}
.card-grn{background:linear-gradient(135deg,#059669,#10b981)}
.card-amb{background:linear-gradient(135deg,#d97706,#f59e0b)}
.card-red{background:linear-gradient(135deg,#dc2626,#ef4444)}

/* ── KPI ── */
.kpi{background:#fff;border-radius:13px;padding:16px 18px;
box-shadow:0 1px 3px rgba(0,0,0,.07);height:100%;border:1px solid rgba(0,0,0,.04)}
.kpi-lbl{font-size:.63rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px}
.kpi-icon{font-size:1.2rem;float:right;opacity:.6;margin-top:-2px}
.kpi-val{font-size:1.6rem;font-weight:800;color:#0f172a;line-height:1.1;margin-top:6px}
.kpi-sub{font-size:.67rem;color:#94a3b8;margin-top:5px}
.kpi-grn .kpi-val{color:#059669}.kpi-red .kpi-val{color:#dc2626}
.kpi-ind .kpi-val{color:#4f46e5}.kpi-amb .kpi-val{color:#d97706}

/* ── Section label ── */
.sec{font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
letter-spacing:.9px;margin:20px 0 10px;display:flex;align-items:center;gap:8px}
.sec::after{content:'';flex:1;height:1px;background:#e8ecf2}

/* ── Alerts ── */
.alerta{border-left:3px solid #ef4444;background:#fff5f5;border-radius:0 10px 10px 0;
padding:10px 14px;margin-bottom:8px}
.alerta-yel{border-left-color:#f59e0b;background:#fffbeb}
.alerta-grn{border-left-color:#22c55e;background:#f0fdf4}
.alerta-ind{border-left-color:#4f46e5;background:#f5f3ff}
.alerta-t{font-size:.8rem;font-weight:600;color:#0f172a}
.alerta-s{font-size:.69rem;color:#64748b;margin-top:2px}

/* ── Chips ── */
.chip{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;
font-size:.6rem;font-weight:700;letter-spacing:.3px;white-space:nowrap}
.chip-red{background:#fee2e2;color:#b91c1c}.chip-yel{background:#fef3c7;color:#92400e}
.chip-grn{background:#dcfce7;color:#15803d}.chip-ind{background:#ede9fe;color:#4338ca}
.chip-blue{background:#dbeafe;color:#1e40af}.chip-gray{background:#f1f5f9;color:#475569}

/* ── List rows ── */
.li{background:#fff;border-radius:10px;padding:12px 15px;margin-bottom:7px;
border:1px solid #f1f5f9;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.li-name{font-size:.83rem;font-weight:600;color:#0f172a}
.li-sub{font-size:.7rem;color:#64748b;margin-top:2px}

/* ── Buttons ── */
[data-testid="stButton"]>button{border-radius:9px!important;font-weight:600!important;
font-size:.82rem!important;min-height:42px!important}
[data-testid="stButton"]>button[kind="primary"]{
background:linear-gradient(135deg,#4f46e5,#7c3aed)!important;
border:none!important;color:#fff!important;
box-shadow:0 2px 8px rgba(79,70,229,.3)!important}

/* ── Inputs ── */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input{border-radius:9px!important;font-size:.85rem!important}
[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,[data-testid="stTextArea"] label{
font-size:.74rem!important;font-weight:600!important;color:#475569!important}

/* ── DataFrames ── */
[data-testid="stDataFrame"]>div{border-radius:12px!important;overflow:hidden!important;
box-shadow:0 1px 4px rgba(0,0,0,.06)!important;border:1px solid #f1f5f9!important}

/* ── Expanders ── */
[data-testid="stExpander"]{border:1px solid #e2e8f0!important;border-radius:12px!important;
background:#fff!important;margin-bottom:10px!important}
[data-testid="stExpander"] summary{font-size:.84rem!important;font-weight:600!important}

/* ── Mobile ── */
@media(max-width:640px){
.pg{padding:14px 12px 70px!important}
.bh{padding:0 14px!important;height:50px!important}
.bh-loja{display:none!important}
.kpi-val{font-size:1.3rem!important}
[data-testid="stTabs"]>[data-baseweb="tab-list"] [data-baseweb="tab"]{
padding:10px 11px!important;font-size:.7rem!important}}
</style>"""


# ══════════════════════════════════════════════════════════════════
# Visual helpers
# ══════════════════════════════════════════════════════════════════

def _kpi(val, lbl, cls="", icon="", sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    ico_html  = f'<span class="kpi-icon">{icon}</span>' if icon else ""
    st.markdown(
        f'<div class="kpi {cls}">'
        f'<div class="kpi-lbl">{lbl}{ico_html}</div>'
        f'<div class="kpi-val">{val}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )

def _alerta(titulo, sub="", tipo="red"):
    cls = "alerta" + ("" if tipo == "red" else f" alerta-{tipo}")
    sub_html = f'<div class="alerta-s">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="{cls}"><div class="alerta-t">{titulo}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )

def _sec(txt):
    st.markdown(f'<div class="sec">{txt}</div>', unsafe_allow_html=True)

def _chip(txt, cor="ind"):
    return f'<span class="chip chip-{cor}">{txt}</span>'

def _pg_header(title, subtitle=""):
    st.markdown(
        f'<div class="pg-title">{title}</div>'
        f'<div class="pg-sub">{subtitle}</div>' if subtitle else f'<div class="pg-title" style="margin-bottom:16px">{title}</div>',
        unsafe_allow_html=True,
    )

def _empty_state(icon, msg, hint=""):
    hint_html = f'<div style="font-size:.73rem;color:#94a3b8;margin-top:6px">{hint}</div>' if hint else ""
    st.markdown(
        f'<div class="card" style="text-align:center;padding:38px 20px">'
        f'<div style="font-size:2.6rem;margin-bottom:10px">{icon}</div>'
        f'<div style="font-size:.88rem;font-weight:600;color:#475569">{msg}</div>'
        f'{hint_html}</div>',
        unsafe_allow_html=True,
    )

def _copiar_html(texto):
    import html as _h, streamlit.components.v1 as cv
    cv.html(
        f'<textarea id="ct" style="position:fixed;top:-9999px">{_h.escape(texto)}</textarea>'
        f'<p style="margin:0;font:13px sans-serif;color:#059669">✅ Copiado para área de transferência!</p>'
        f'<script>(function(){{var e=document.getElementById("ct");e.focus();e.select();'
        f'try{{navigator.clipboard.writeText(e.value).catch(function(){{document.execCommand("copy")}});'
        f'}}catch(ex){{document.execCommand("copy");}}}})();</script>',
        height=35,
    )

def _stock_bar_html(name, current, ref=20):
    pct = min(100, int(current / max(1, ref) * 100))
    if current <= 3:
        fg, bg = "#ef4444", "#fee2e2"
    elif current <= 10:
        fg, bg = "#f59e0b", "#fef3c7"
    else:
        fg, bg = "#22c55e", "#dcfce7"
    return (
        f'<div style="margin-bottom:9px">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
        f'<span style="font-size:.72rem;font-weight:600;color:#475569">{name[:36]}</span>'
        f'<span style="font-size:.7rem;font-weight:700;color:#0f172a">{current} un</span>'
        f'</div>'
        f'<div style="background:#f1f5f9;border-radius:4px;height:8px;overflow:hidden">'
        f'<div style="width:{pct}%;height:100%;background:{fg};border-radius:4px"></div>'
        f'</div></div>'
    )

def _grad_card(icon, val, lbl, color="ind"):
    st.markdown(
        f'<div class="card-grad card-{color}">'
        f'<div style="font-size:1.5rem;opacity:.75">{icon}</div>'
        f'<div style="font-size:1.8rem;font-weight:800;margin:4px 0;line-height:1">{val}</div>'
        f'<div style="font-size:.67rem;font-weight:700;opacity:.8;text-transform:uppercase;letter-spacing:.5px">{lbl}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════════════

def _check_auth():
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None
    if st.session_state.usuario_logado is None:
        _t = st.query_params.get("t", "")
        if _t:
            _u = api.validar_sessao(_t)
            if _u:
                st.session_state.usuario_logado = _u
                st.session_state["_sessao_token"] = _t
    return st.session_state.usuario_logado is not None


def _tela_login():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"]{
          background:linear-gradient(160deg,#ede9fe 0%,#dbeafe 100%)!important}
        [data-testid="stForm"]{background:#fff!important;border:1px solid #e2e8f0!important;
          border-radius:18px!important;padding:2.2rem 2rem 1.8rem!important;
          box-shadow:0 8px 48px rgba(79,70,229,.14)!important}
        [data-testid="stForm"] button[type="submit"]{
          background:linear-gradient(135deg,#4f46e5,#7c3aed)!important;
          color:#fff!important;font-weight:700!important;border:none!important;
          border-radius:9px!important;min-height:44px!important;
          font-size:.88rem!important;margin-top:.6rem!important;
          box-shadow:0 2px 16px rgba(79,70,229,.35)!important}
        </style>
        <div style="text-align:center;margin-bottom:1.8rem">
          <div style="display:inline-flex;align-items:center;justify-content:center;
            width:56px;height:56px;border-radius:16px;
            background:linear-gradient(135deg,#4f46e5,#7c3aed);
            box-shadow:0 6px 24px rgba(79,70,229,.4);margin-bottom:14px">
            <span style="font-size:1.6rem">⚡</span>
          </div>
          <div style="font-size:1.4rem;font-weight:800;color:#0f172a;letter-spacing:-.5px">
            Plug ERP
            <span style="background:#ede9fe;color:#4338ca;font-size:.52rem;
              padding:3px 8px;border-radius:12px;font-weight:700;
              vertical-align:middle;margin-left:6px">BETA</span>
          </div>
          <div style="font-size:.72rem;color:#94a3b8;margin-top:5px">
            Interface redesenhada · Mobile-first · Mais recursos
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("beta_login"):
            u_in = st.text_input("Usuário", placeholder="seu usuário")
            s_in = st.text_input("Senha", type="password", placeholder="••••••")
            ok   = st.form_submit_button("Entrar →", use_container_width=True)

        if ok:
            u = u_in.strip().lower()
            udb = api.carregar_usuarios()
            if u in udb and udb[u]["senha"] == s_in:
                st.session_state.usuario_logado = u
                tok = api.criar_sessao(u)
                st.session_state["_sessao_token"] = tok
                st.query_params["t"] = tok
                st.query_params["v"] = "beta"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.markdown('<hr style="margin:16px 0 12px;opacity:.12">', unsafe_allow_html=True)
        if st.button("← Usar versão Classic", use_container_width=True, key="beta_login_cls"):
            st.session_state["version"] = "classic"
            st.query_params["v"] = "classic"
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════

def _header(nome, loja_nome):
    st.markdown(
        f'<div class="bh">'
        f'<div class="bh-brand">'
        f'<div class="bh-icon">⚡</div>'
        f'<div class="bh-name">Plug ERP</div>'
        f'<div class="bh-pill">BETA</div>'
        f'</div>'
        f'<div class="bh-right">'
        f'<div class="bh-loja">🏪 {loja_nome}</div>'
        f'<div style="opacity:.75">{nome.split()[0]}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# Stock alerts (cached 5 min)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def _alertas_estoque(loja_id):
    c = api.carregar_cache(loja_id)
    criticos, baixos = [], []
    for p in (c or {}).get("produtos", []):
        for v in p.get("variacoes", []):
            vd  = v.get("variacao", v)
            est = int(vd.get("estoque", 0) or 0)
            item = {"produto": p.get("nome", ""), "variacao": vd.get("nome", ""),
                    "cod": vd.get("codigo", ""), "estoque": est}
            if est <= 3:    criticos.append(item)
            elif est <= 10: baixos.append(item)
    return (sorted(criticos, key=lambda x: x["estoque"]),
            sorted(baixos,   key=lambda x: x["estoque"]))


# ══════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════

def _dashboard(cache, loja_id, loja_nome, nome, is_adm):
    st.markdown('<div class="pg">', unsafe_allow_html=True)

    hora  = datetime.now().hour
    saud  = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")
    hoje  = date.today().strftime("%A, %d de %B de %Y")
    # Translate weekday/month to Portuguese
    _dias = {"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
              "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
    _mes  = {"January":"janeiro","February":"fevereiro","March":"março",
              "April":"abril","May":"maio","June":"junho","July":"julho",
              "August":"agosto","September":"setembro","October":"outubro",
              "November":"novembro","December":"dezembro"}
    for en, pt in {**_dias, **_mes}.items():
        hoje = hoje.replace(en, pt)

    st.markdown(
        f'<div style="margin-bottom:18px">'
        f'<div style="font-size:1.05rem;font-weight:700;color:#0f172a">'
        f'{saud}, {nome.split()[0]} 👋</div>'
        f'<div style="font-size:.72rem;color:#94a3b8;margin-top:2px">{hoje}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPIs principais ──
    _sec("Visão geral")
    total   = cache.get("total", 0) if cache else 0
    n_lojas = len(api.LOJAS)
    sync_em = (cache.get("sincronizado_em", "") or "")[:10] if cache else "—"
    criticos, baixos = _alertas_estoque(loja_id) if cache else ([], [])
    n_crit  = len(criticos)
    alerta_cor = "kpi-red" if n_crit > 0 else "kpi-grn"

    k1, k2, k3, k4 = st.columns(4)
    with k1: _kpi(f"{total:,}",  "Produtos",      "kpi-ind", "📦", f"sync {sync_em}")
    with k2: _kpi(str(n_lojas),  "Lojas ativas",  "",        "🏪")
    with k3: _kpi(str(n_crit),   "Críticos",      alerta_cor,"🚨", f"+ {len(baixos)} baixo(s)")
    with k4:
        _fin_key = f"beta_fin_{loja_id}"
        if _fin_key in st.session_state:
            tr, tp = st.session_state[_fin_key]
            res    = tr - tp
            _kpi(f"R$ {res:,.0f}", "Resultado mês",
                 "kpi-grn" if res >= 0 else "kpi-red", "💰")
        else:
            _kpi("—", "Resultado mês", "", "💰", "clique em Financeiro")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Estoque visual ──
    if cache:
        _sec("⚠️ Saúde do estoque")
        c1, c2 = st.columns([3, 2])
        with c1:
            if criticos or baixos:
                top = (criticos + baixos)[:12]
                bars_html = "".join(_stock_bar_html(
                    f"{it['produto']} / {it['variacao']}", it["estoque"]
                ) for it in top)
                st.markdown(f'<div class="card" style="padding:16px 18px">{bars_html}</div>',
                            unsafe_allow_html=True)
            else:
                _alerta("✅  Todos os produtos com estoque saudável", tipo="grn")

        with c2:
            total_vars = sum(len(p.get("variacoes", [])) for p in cache.get("produtos", []))
            n_ok = total_vars - len(criticos) - len(baixos)
            _kpi(f"{n_crit}", "Críticos (≤3 un)", "kpi-red", "🔴",
                 f"{len(baixos)} baixos · {n_ok} ok")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if criticos:
                # Top 3 mais críticos
                for it in criticos[:3]:
                    st.markdown(
                        f'<div class="card-sm">'
                        f'<div class="li-name">{it["produto"][:28]}</div>'
                        f'<div class="li-sub">{it["variacao"]} · '
                        f'<b style="color:#dc2626">{it["estoque"]} un</b></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        if st.button("🔄 Atualizar alertas", key="dash_refresh_alerta"):
            _alertas_estoque.clear()
            st.rerun()

    # ── Financeiro do mês ──
    _sec("💰 Financeiro — mês atual")
    _fin_key = f"beta_fin_{loja_id}"
    if _fin_key not in st.session_state:
        with st.spinner("Carregando financeiro…"):
            try:
                ini = date.today().replace(day=1)
                fim = date.today()
                rec = api.buscar_contas_receber(str(ini), str(fim), limite=500)
                pag = api.buscar_contas_pagar(str(ini), str(fim), limite=500)
                if not isinstance(rec, list): rec = []
                if not isinstance(pag, list): pag = []
                tr = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in rec)
                tp = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in pag)
                st.session_state[_fin_key] = (tr, tp)
            except Exception:
                st.session_state[_fin_key] = (0.0, 0.0)

    tr, tp = st.session_state.get(_fin_key, (0.0, 0.0))
    res     = tr - tp
    f1, f2, f3 = st.columns(3)
    with f1: _grad_card("💚", f"R$ {tr:,.0f}", "A receber", "grn")
    with f2: _grad_card("❤️",  f"R$ {tp:,.0f}", "A pagar",   "red")
    with f3: _grad_card("⚡", f"R$ {res:,.0f}", "Resultado", "ind" if res >= 0 else "red")

    if tr > 0 or tp > 0:
        df_fin = pd.DataFrame({"Valor": {"Receitas": tr, "Despesas": tp, "Resultado": max(0, res)}})
        st.bar_chart(df_fin)

    if st.button("🔄 Atualizar financeiro", key="dash_refresh_fin"):
        st.session_state.pop(_fin_key, None)
        st.rerun()

    # ── Status das lojas ──
    _sec("🏪 Status das lojas")
    lcols = st.columns(len(api.LOJAS))
    for col, (lid, lnm) in zip(lcols, api.LOJAS.items()):
        c = api.carregar_cache(lid)
        t = c.get("total", 0) if c else 0
        s = (c.get("sincronizado_em", "") or "")[:10] if c else "—"
        cor  = "#16a34a" if c else "#dc2626"
        txt  = "● Online" if c else "● Sem dados"
        col.markdown(
            f'<div class="card" style="text-align:center;padding:13px 8px">'
            f'<div style="font-size:.63rem;font-weight:600;color:#64748b">{lnm}</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:#0f172a;margin:5px 0">{t}</div>'
            f'<div style="font-size:.58rem;font-weight:700;color:{cor}">{txt}</div>'
            f'<div style="font-size:.57rem;color:#94a3b8;margin-top:3px">{s}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Ações rápidas ──
    _sec("⚡ Ações rápidas")
    qa1, qa2, qa3 = st.columns(3)
    if qa1.button("🛒 Novo Pedido", use_container_width=True, key="dash_qa_ped"):
        st.info("Abra a aba **Pedidos** acima para criar um novo pedido.")
    if qa2.button("🔄 Sincronizar", use_container_width=True, key="dash_qa_sync"):
        st.info("Abra **Config → Sincronização** para sincronizar.")
    if qa3.button("📊 Ver Relatórios", use_container_width=True, key="dash_qa_rel"):
        st.info("Abra a aba **Relatórios** para ver análises detalhadas.")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PEDIDOS
# ══════════════════════════════════════════════════════════════════

def _pedidos(cache, loja_id):
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("🛒 Pedidos de Compra", "Crie, gerencie e exporte pedidos")

    if "beta_ped" not in st.session_state:
        st.session_state.beta_ped = []
    itens = st.session_state.beta_ped

    # ── Lista aberta ──
    _arq = st.session_state.get("beta_ped_arq")
    if _arq:
        try:
            import os as _os
            cam = _os.path.join(api.DIR_LISTAS, _arq)
            with open(cam, encoding="utf-8") as f:
                _d = json.load(f)
            _ln = _d.get("nome", _arq)
        except Exception:
            _ln = _arq
        b1, b2, b3 = st.columns([5, 1, 1])
        b1.info(f"📂 Lista aberta: **{_ln}**")
        if b2.button("💾 Salvar", key="ped_sv", use_container_width=True):
            try:
                import os as _os2
                cam = _os2.path.join(api.DIR_LISTAS, _arq)
                with open(cam, encoding="utf-8") as f:
                    _d = json.load(f)
                _d["itens"] = itens
                _d["atualizado_em"] = datetime.now().isoformat()
                _s = json.dumps(_d, ensure_ascii=False, indent=2)
                with open(cam, "w", encoding="utf-8") as f:
                    f.write(_s)
                api._gh_push_arquivo(f"listas/{_arq}", _s, f"Salva: {_ln}")
                st.success("✅ Lista salva!")
            except Exception as ex:
                st.error(f"Erro: {ex}")
        if b3.button("✕", key="ped_fechar", use_container_width=True):
            st.session_state.pop("beta_ped_arq", None)
            st.rerun()

    # ── Tabs de input ──
    tab_wpp, tab_cat, tab_avl, tab_lst = st.tabs([
        "📱 WhatsApp / IA", "🔍 Catálogo", "✏️ Avulso", "📂 Listas"
    ])

    # ─── WhatsApp ───
    with tab_wpp:
        _sec("Cole o pedido do WhatsApp")
        txt_wpp = st.text_area(
            "Texto", height=130, key="beta_wpp_txt",
            placeholder="Ex:\niPhone 15 - masculino 2, feminino 3\nSamsung A55 - brilho 5",
            label_visibility="collapsed",
        )
        if st.button("🤖 Processar com IA", use_container_width=True, type="primary", key="wpp_proc"):
            if not txt_wpp.strip():
                st.warning("Cole o texto do pedido.")
            elif not cache:
                st.warning("Sincronize os produtos primeiro.")
            else:
                with st.spinner("Processando com IA…"):
                    try:
                        cat = "\n".join(
                            f"{p.get('codigo_interno','')} | {p.get('nome','')}"
                            for p in cache.get("produtos", [])[:400]
                        )
                        res = api.parse_pedido_whatsapp(txt_wpp, cat)
                        st.session_state["beta_wpp_res"] = res
                        for i, r in enumerate(res):
                            st.session_state[f"beta_wpp_chk_{i}"] = bool(r.get("nome_produto"))
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erro na IA: {ex}")

        res = st.session_state.get("beta_wpp_res", [])
        if res:
            _sec(f"Resultado IA — {len(res)} item(ns)")
            for i, r in enumerate(res):
                conf = r.get("confianca", "baixa")
                cor  = "grn" if conf == "alta" else ("yel" if conf == "media" else "red")
                c1, c2 = st.columns([5, 1])
                nome_p = r.get("nome_produto") or r.get("modelo_digitado", "—")
                label  = f"{nome_p} · {', '.join(str(v) for v in r.get('variacoes',[]))} · {r.get('quantidade',1)} un"
                st.session_state[f"beta_wpp_chk_{i}"] = c1.checkbox(
                    label,
                    value=st.session_state.get(f"beta_wpp_chk_{i}", bool(r.get("nome_produto"))),
                    key=f"wpp_chk_r_{i}",
                )
                c2.markdown(_chip(conf.upper(), cor), unsafe_allow_html=True)

            ca, cb = st.columns(2)
            if ca.button("➕ Adicionar selecionados", use_container_width=True,
                         type="primary", key="wpp_add"):
                added = 0
                for i, r in enumerate(res):
                    if not st.session_state.get(f"beta_wpp_chk_{i}", False):
                        continue
                    np_ = r.get("nome_produto")
                    if not np_ or not cache:
                        st.session_state.beta_ped.append({
                            "produto_nome": r.get("modelo_digitado", np_ or "—"),
                            "variacao_nome": ", ".join(str(v) for v in r.get("variacoes", [])),
                            "quantidade": int(r.get("quantidade", 1)),
                            "fornecedor": "", "valor_custo": "", "_avulso": True,
                        })
                        added += 1
                        continue
                    prods_m = api.buscar_produtos(r.get("cod_interno") or np_, cache)
                    if prods_m:
                        p = prods_m[0]
                        for vr in (r.get("variacoes") or [""]):
                            vd_m = None
                            for v in p.get("variacoes", []):
                                vd = v.get("variacao", v)
                                if str(vr).lower() in (vd.get("nome", "")).lower():
                                    vd_m = vd; break
                            if vd_m:
                                st.session_state.beta_ped.append({
                                    "produto_id": p["id"], "produto_nome": p["nome"],
                                    "cod_interno": p.get("codigo_interno", ""),
                                    "variacao_id": vd_m["id"],
                                    "variacao_nome": vd_m.get("nome", ""),
                                    "variacao_cod": vd_m.get("codigo", ""),
                                    "quantidade": int(r.get("quantidade", 1)),
                                    "fornecedor": "", "valor_custo": "",
                                })
                            else:
                                st.session_state.beta_ped.append({
                                    "produto_id": p["id"], "produto_nome": p["nome"],
                                    "variacao_nome": str(vr),
                                    "quantidade": int(r.get("quantidade", 1)),
                                    "fornecedor": "", "valor_custo": "",
                                })
                            added += 1
                    else:
                        st.session_state.beta_ped.append({
                            "produto_nome": np_,
                            "variacao_nome": ", ".join(str(v) for v in r.get("variacoes", [])),
                            "quantidade": int(r.get("quantidade", 1)),
                            "fornecedor": "", "valor_custo": "", "_avulso": True,
                        })
                        added += 1
                if added:
                    st.session_state.pop("beta_wpp_res", None)
                    st.success(f"✅ {added} item(ns) adicionado(s)!")
                    st.rerun()
            if cb.button("✕ Descartar", use_container_width=True, key="wpp_clear"):
                st.session_state.pop("beta_wpp_res", None)
                st.rerun()

    # ─── Catálogo ───
    with tab_cat:
        if not cache:
            st.warning("Sincronize os produtos primeiro.")
        else:
            _sec("Buscar no catálogo")
            termo = st.text_input("🔍 Produto", key="cat_busca",
                                   placeholder="Ex: iPhone 15, Samsung A55…",
                                   label_visibility="collapsed")
            prods = api.buscar_produtos(termo, cache) if termo else []
            if prods:
                nomes = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in prods]
                sel   = st.selectbox("Produto", nomes, key="cat_sel", label_visibility="collapsed")
                prod  = prods[nomes.index(sel)]
                vars_ = [v.get("variacao", v) for v in prod.get("variacoes", [])]

                if vars_:
                    _qtds = {}
                    _sec("Variações e quantidades")
                    for vd in vars_:
                        vc1, vc2, vc3 = st.columns([3, 1, 1])
                        vc1.caption(f"**{vd.get('nome','')}** · `{vd.get('codigo','')}`")
                        est_v = int(vd.get("estoque", 0) or 0)
                        est_cor = "🔴" if est_v <= 3 else ("🟡" if est_v <= 10 else "🟢")
                        vc2.caption(f"{est_cor} {est_v} un")
                        _qtds[vd["id"]] = vc3.number_input(
                            "q", min_value=0, value=0, step=1,
                            key=f"cat_qtd_{vd['id']}", label_visibility="collapsed",
                        )

                    cf1, cf2 = st.columns(2)
                    forn  = cf1.text_input("Fornecedor", key="cat_forn")
                    custo = cf2.text_input("Custo unit. (R$)", key="cat_custo")

                    if st.button("➕ Adicionar ao pedido", use_container_width=True,
                                  type="primary", key="cat_add"):
                        added_c = 0
                        for vd in vars_:
                            q = int(_qtds.get(vd["id"], 0))
                            if q > 0:
                                st.session_state.beta_ped.append({
                                    "produto_id": prod["id"], "produto_nome": prod["nome"],
                                    "cod_interno": prod.get("codigo_interno", ""),
                                    "variacao_id": vd["id"],
                                    "variacao_nome": vd.get("nome", ""),
                                    "variacao_cod": vd.get("codigo", ""),
                                    "quantidade": q, "fornecedor": forn,
                                    "valor_custo": custo, "observacao": "",
                                })
                                added_c += 1
                        if added_c:
                            st.success(f"✅ {added_c} variação(ões) adicionada(s)!")
                            st.rerun()
                        else:
                            st.warning("Preencha a quantidade em pelo menos uma variação.")
            elif termo:
                st.info("Nenhum produto encontrado.")

    # ─── Avulso ───
    with tab_avl:
        _sec("Item fora do catálogo")
        a1, a2 = st.columns([3, 1])
        desc  = a1.text_input("Descrição", key="avl_desc",
                               placeholder="Ex: Película Samsung A55 5G")
        qtd_a = a2.number_input("Qtd", min_value=1, value=1, key="avl_qtd")
        b1, b2 = st.columns(2)
        forn_a  = b1.text_input("Fornecedor", key="avl_forn")
        custo_a = b2.text_input("Custo unit. (R$)", key="avl_custo")
        if st.button("➕ Adicionar avulso", use_container_width=True, key="avl_add"):
            if desc.strip():
                st.session_state.beta_ped.append({
                    "produto_nome": desc.strip(), "variacao_nome": "",
                    "quantidade": int(qtd_a), "fornecedor": forn_a,
                    "valor_custo": custo_a, "_avulso": True,
                })
                st.success("✅ Adicionado!")
                st.rerun()
            else:
                st.warning("Digite uma descrição.")

    # ─── Listas salvas ───
    with tab_lst:
        _sec("Listas de pedido salvas")
        listas = api.listar_listas_salvas("pedido")
        if listas:
            for lst in listas[:15]:
                lnm = lst.get("nome", "—")
                lqt = len(lst.get("itens", []))
                ldt = (lst.get("criado_em", "") or "")[:10]
                lc1, lc2 = st.columns([5, 1])
                lc1.markdown(f'<div class="li"><div class="li-name">{lnm}</div>'
                             f'<div class="li-sub">{lqt} itens · {ldt}</div></div>',
                             unsafe_allow_html=True)
                if lc2.button("Abrir", key=f"lst_op_{lst['_arquivo']}", use_container_width=True):
                    st.session_state.beta_ped = list(lst.get("itens", []))
                    st.session_state["beta_ped_arq"] = lst["_arquivo"]
                    st.rerun()
        else:
            _empty_state("📂", "Nenhuma lista salva", "Salve seu pedido abaixo")

        st.divider()
        _sec("Salvar pedido atual")
        nn = st.text_input("Nome da lista", key="ped_novo_nome",
                            placeholder="Ex: Pedido Distribuidora 15/06")
        if st.button("💾 Salvar lista", use_container_width=True, key="ped_salvar"):
            if not itens:
                st.warning("O pedido está vazio.")
            elif not nn.strip():
                st.warning("Digite um nome.")
            else:
                api.salvar_lista(nn.strip(), "pedido", itens)
                st.success(f"✅ Lista '{nn}' salva!")
                st.rerun()

    # ════════════════════════════════════════
    # Pedido atual
    # ════════════════════════════════════════
    if itens:
        st.divider()
        # Total de itens e valor estimado
        total_qtd = sum(int(it.get("quantidade", 0)) for it in itens)
        custos = []
        for it in itens:
            try:
                custos.append(float(str(it.get("valor_custo","0") or "0").replace(",","."))
                              * int(it.get("quantidade", 1)))
            except Exception:
                pass
        total_val = sum(custos)

        h1, h2, h3 = st.columns(3)
        h1.metric("Itens", len(itens))
        h2.metric("Unidades", total_qtd)
        if total_val > 0:
            h3.metric("Custo total", f"R$ {total_val:,.2f}")

        _sec(f"Itens do pedido")
        for i, it in enumerate(list(itens)):
            nome_v   = it.get("variacao_nome", "")
            linha    = it.get("produto_nome", "")
            if nome_v: linha += f" / {nome_v}"
            is_avulso = it.get("_avulso", False)

            pc1, pc2, pc3 = st.columns([5, 1, 1])
            pc1.markdown(
                f'<div class="li"><div class="li-name">{linha[:50]}</div>'
                f'<div class="li-sub">'
                + (f'Fornecedor: {it.get("fornecedor","")} · ' if it.get("fornecedor") else '')
                + (f'Custo: R$ {it.get("valor_custo","")} · ' if it.get("valor_custo") else '')
                + (_chip("avulso", "gray") if is_avulso else '')
                + f'</div></div>',
                unsafe_allow_html=True,
            )
            nova_q = pc2.number_input(
                "q", min_value=1,
                value=max(1, int(it.get("quantidade", 1))),
                step=1, label_visibility="collapsed", key=f"ped_q_{i}",
            )
            if nova_q != it.get("quantidade"):
                st.session_state.beta_ped[i]["quantidade"] = nova_q
            if pc3.button("🗑", key=f"ped_del_{i}", use_container_width=True):
                st.session_state.beta_ped.pop(i)
                st.rerun()

        # ── Exportações ──
        st.divider()
        _sec("Exportar")
        ea, eb, ec = st.columns(3)

        buf = io.BytesIO()
        df_exp = pd.DataFrame([{
            "Produto":     it.get("produto_nome", ""),
            "Variação":    it.get("variacao_nome", ""),
            "Qtd":         it.get("quantidade", 0),
            "Fornecedor":  it.get("fornecedor", ""),
            "Custo Unit.": it.get("valor_custo", ""),
        } for it in itens])
        with pd.ExcelWriter(buf, engine="openpyxl") as wr:
            df_exp.to_excel(wr, index=False, sheet_name="Pedido")
        buf.seek(0)
        ea.download_button(
            "📄 Excel", buf, f"pedido_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        if eb.button("📋 Copiar texto", use_container_width=True, key="ped_txt"):
            linhas = [f"PEDIDO — {date.today()}", "=" * 42]
            for it in itens:
                v = f" / {it['variacao_nome']}" if it.get("variacao_nome") else ""
                linhas.append(f"{it.get('produto_nome','')}{v} — {it.get('quantidade',0)} un")
            _copiar_html("\n".join(linhas))

        if ec.button("🗑️ Limpar tudo", use_container_width=True, key="ped_limpar"):
            st.session_state.beta_ped = []
            st.session_state.pop("beta_ped_arq", None)
            st.rerun()

        # ── Registrar no GestãoClick ──
        with st.expander("📤 Registrar Compra no GestãoClick"):
            itens_cad = [it for it in itens if it.get("produto_id") and it.get("variacao_id")]
            itens_avs = [it for it in itens if not it.get("produto_id")]
            st.info(f"**{len(itens_cad)}** cadastrado(s) serão enviados · **{len(itens_avs)}** avulso(s) ignorado(s).")

            rg1, rg2 = st.columns(2)
            forn_gc = rg1.text_input("Buscar fornecedor", key="gc_forn")
            data_gc = rg2.date_input("Data", value=date.today(), key="gc_data")
            obs_gc  = st.text_input("Observações", key="gc_obs")

            if st.button("🔍 Buscar fornecedor", use_container_width=True, key="gc_buscar"):
                with st.spinner("Buscando…"):
                    try:
                        st.session_state["gc_forns"] = api.buscar_fornecedores(forn_gc, limite=20)
                    except Exception as ex:
                        st.error(f"Erro: {ex}")

            forns = st.session_state.get("gc_forns", [])
            if forns:
                opts = {
                    f"{f.get('razao_social') or f.get('nome','—')} ({f.get('cnpj','')})": f["id"]
                    for f in forns
                }
                fsel = st.selectbox("Fornecedor", list(opts.keys()), key="gc_fsel")
                fid  = opts[fsel]

                if "gc_sits" not in st.session_state:
                    try:
                        sits = api.buscar_situacoes_compras()
                        st.session_state["gc_sits"] = {
                            s.get("nome", "—"): s.get("id", "1")
                            for s in sits if isinstance(s, dict) and s.get("nome")
                        } or {"Aguardando recebimento": "1"}
                    except Exception:
                        st.session_state["gc_sits"] = {"Aguardando recebimento": "1"}

                sit_sel = st.selectbox("Situação", list(st.session_state["gc_sits"].keys()), key="gc_sit")
                sit_id  = st.session_state["gc_sits"][sit_sel]

                if st.button("✅ Confirmar e registrar", type="primary",
                              use_container_width=True, key="gc_confirmar"):
                    if not itens_cad:
                        st.error("Nenhum item cadastrado no pedido.")
                    else:
                        with st.spinner("Enviando…"):
                            try:
                                api.registrar_compra_gestaoclick(
                                    itens_cad, fid, data_gc, sit_id, obs_gc, loja_id,
                                )
                                st.success("✅ Compra registrada no GestãoClick!")
                                st.session_state.pop("gc_forns", None)
                            except Exception as ex:
                                st.error(f"Erro: {ex}")
    else:
        _empty_state("🛒", "Pedido vazio", "Use as abas acima para adicionar produtos")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# ESTOQUE
# ══════════════════════════════════════════════════════════════════

def _estoque(cache, loja_id):
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("📦 Estoque", "Entrada, acerto e etiquetas")

    if not cache:
        _empty_state("📦", "Cache vazio", "Vá em Config → Sincronização para atualizar")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Stats rápidos
    all_vars = [(p, v.get("variacao", v)) for p in cache.get("produtos", [])
                for v in p.get("variacoes", [])]
    n_total = len(all_vars)
    n_crit  = sum(1 for _, vd in all_vars if int(vd.get("estoque", 0) or 0) <= 3)
    n_baixo = sum(1 for _, vd in all_vars if 3 < int(vd.get("estoque", 0) or 0) <= 10)
    n_ok    = n_total - n_crit - n_baixo
    s1, s2, s3, s4 = st.columns(4)
    with s1: _kpi(f"{n_total}", "Variações", "kpi-ind", "📦")
    with s2: _kpi(f"{n_crit}",  "Críticos",  "kpi-red" if n_crit else "", "🔴")
    with s3: _kpi(f"{n_baixo}", "Baixos",    "kpi-amb" if n_baixo else "", "🟡")
    with s4: _kpi(f"{n_ok}",    "Saudáveis", "kpi-grn", "🟢")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    modo = st.radio(
        "Modo", ["📥 Entrada", "📊 Acerto", "🏷️ Etiquetas", "📋 Visão geral"],
        horizontal=True, key="est_modo", label_visibility="collapsed",
    )
    st.divider()

    # ── Visão geral ──
    if modo == "📋 Visão geral":
        _sec("Itens com estoque crítico ou baixo")
        rows_crit = []
        for p, vd in all_vars:
            est = int(vd.get("estoque", 0) or 0)
            if est <= 10:
                status = "🔴 Crítico" if est <= 3 else "🟡 Baixo"
                rows_crit.append({
                    "Status":   status,
                    "Produto":  p.get("nome", "")[:30],
                    "Variação": vd.get("nome", "")[:25],
                    "Cód.":     vd.get("codigo", ""),
                    "Estoque":  est,
                })
        if rows_crit:
            df_crit = pd.DataFrame(rows_crit).sort_values("Estoque")
            st.dataframe(df_crit, use_container_width=True, hide_index=True)
            bars = "".join(
                _stock_bar_html(f"{r['Produto']} / {r['Variação']}", r["Estoque"])
                for r in rows_crit[:15]
            )
            st.markdown(f'<div class="card" style="padding:16px 18px"><b style="font-size:.75rem;color:#94a3b8">VISUALIZAÇÃO GRÁFICA</b><div style="height:10px"></div>{bars}</div>',
                        unsafe_allow_html=True)
        else:
            _alerta("✅ Todos os itens com estoque saudável!", tipo="grn")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Busca de produto ──
    termo = st.text_input("🔍 Buscar produto", key="est_busca",
                           placeholder="Nome ou código interno")
    prods = api.buscar_produtos(termo, cache) if termo else []
    if not prods:
        if termo:
            st.info("Nenhum produto encontrado.")
        elif modo != "🏷️ Etiquetas":
            pass
        if modo != "🏷️ Etiquetas":
            st.markdown('</div>', unsafe_allow_html=True)
            return

    if prods:
        nomes = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in prods]
        sel   = st.selectbox("Produto", nomes, key="est_sel", label_visibility="collapsed")
        prod  = prods[nomes.index(sel)]
        vars_ = [v.get("variacao", v) for v in prod.get("variacoes", [])]

        if not vars_:
            st.warning("Produto sem variações.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        if modo in ("📥 Entrada", "📊 Acerto"):
            modo_api = "soma" if "Entrada" in modo else "set"
            lbl_q    = "Qtd a adicionar" if modo_api == "soma" else "Novo estoque"

            qtds: dict[str, int] = {}
            _sec("Variações")
            for vd in vars_:
                est_atual = int(vd.get("estoque", 0) or 0)
                v1, v2, v3 = st.columns([3, 1, 1])
                v1.markdown(f'<div style="font-size:.83rem;font-weight:600">{vd.get("nome","")}</div>'
                            f'<div style="font-size:.7rem;color:#94a3b8">`{vd.get("codigo","")}`</div>',
                            unsafe_allow_html=True)
                cor_est = "🔴" if est_atual <= 3 else ("🟡" if est_atual <= 10 else "🟢")
                v2.metric("Atual", f"{cor_est} {est_atual}")
                qtds[vd["id"]] = v3.number_input(
                    lbl_q, min_value=0, value=0, step=1,
                    key=f"est_q_{vd['id']}", label_visibility="collapsed",
                )

            obs_e = st.text_input("Observação", key="est_obs")

            if st.button(f"✅ Aplicar {modo}", use_container_width=True,
                          type="primary", key="est_apply"):
                erros, ok = [], 0
                for vd in vars_:
                    q = int(qtds.get(vd["id"], 0))
                    if q > 0:
                        try:
                            api.atualizar_estoque_variacao(
                                prod["id"], vd["id"], q, loja_id=loja_id, modo=modo_api
                            )
                            ok += 1
                        except Exception as ex:
                            erros.append(f"{vd.get('nome','')}: {ex}")
                if ok:
                    st.success(f"✅ {ok} variação(ões) atualizada(s)!")
                    _alertas_estoque.clear()
                for e in erros:
                    st.error(e)

    # ── Etiquetas ──
    if modo == "🏷️ Etiquetas":
        if "beta_etiq" not in st.session_state:
            st.session_state.beta_etiq = []

        if prods and vars_:
            qtds_e: dict[str, int] = {}
            for vd in vars_:
                e1, e2 = st.columns([4, 1])
                e1.write(f"{vd.get('nome','')} · `{vd.get('codigo','')}`")
                qtds_e[vd["id"]] = e2.number_input(
                    "Qtd", min_value=0, value=0, step=1,
                    key=f"etiq_q_{vd['id']}", label_visibility="collapsed",
                )
            if st.button("➕ Adicionar à lista", use_container_width=True, key="etiq_add"):
                added_e = 0
                for vd in vars_:
                    q = int(qtds_e.get(vd["id"], 0))
                    if q > 0:
                        st.session_state.beta_etiq.append({
                            "variacao_id": vd["id"],
                            "produto_nome": prod["nome"],
                            "variacao_nome": vd.get("nome", ""),
                            "variacao_cod": vd.get("codigo", ""),
                            "quantidade": q,
                        })
                        added_e += 1
                if added_e:
                    st.success(f"✅ {added_e} adicionado(s)!")
                    st.rerun()

        etiq_itens = st.session_state.get("beta_etiq", [])
        if etiq_itens:
            _sec(f"Lista de etiquetas — {len(etiq_itens)} item(ns)")
            df_et = pd.DataFrame(etiq_itens)[["produto_nome", "variacao_nome", "quantidade"]]
            df_et.columns = ["Produto", "Variação", "Qtd"]
            st.dataframe(df_et, use_container_width=True, hide_index=True)

            url_et = api.gerar_url_etiquetas([
                {"variacao_id": it["variacao_id"], "quantidade": it["quantidade"]}
                for it in etiq_itens if it.get("variacao_id")
            ])
            if url_et:
                st.link_button("🏷️ Gerar Etiquetas no GestãoClick", url_et, use_container_width=True)
            if st.button("🗑️ Limpar lista", use_container_width=True, key="etiq_clear"):
                st.session_state.beta_etiq = []
                st.rerun()
        else:
            _empty_state("🏷️", "Lista de etiquetas vazia", "Busque um produto e adicione acima")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════

def _clientes():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("👥 Clientes", "Gerencie o cadastro de clientes")

    # ── Novo cliente ──
    with st.expander("➕ Cadastrar novo cliente"):
        nc1, nc2 = st.columns(2)
        nc_nome  = nc1.text_input("Nome / Razão Social *", key="cli_new_nome")
        nc_cpf   = nc2.text_input("CPF / CNPJ", key="cli_new_cpf")
        nc3, nc4 = st.columns(2)
        nc_tel   = nc3.text_input("Telefone", key="cli_new_tel")
        nc_cel   = nc4.text_input("Celular / WhatsApp", key="cli_new_cel")
        nc5, nc6 = st.columns(2)
        nc_email = nc5.text_input("E-mail", key="cli_new_email")
        nc_cid   = nc6.text_input("Cidade", key="cli_new_cid")
        nc_obs   = st.text_area("Observações", key="cli_new_obs", height=70)

        if st.button("✅ Salvar cliente", use_container_width=True,
                     type="primary", key="cli_new_save"):
            if not nc_nome.strip():
                st.warning("Nome/Razão Social é obrigatório.")
            else:
                with st.spinner("Salvando…"):
                    try:
                        dados = {"nome": nc_nome.strip(), "cpf_cnpj": nc_cpf,
                                 "telefone": nc_tel, "celular": nc_cel,
                                 "email": nc_email, "cidade": nc_cid,
                                 "observacoes": nc_obs}
                        api.criar_cliente(dados)
                        st.success(f"✅ Cliente '{nc_nome}' cadastrado!")
                        st.session_state.pop("cli_results", None)
                    except Exception as ex:
                        st.error(f"Erro: {ex}")

    # ── Busca ──
    _sec("Buscar clientes")
    sc1, sc2 = st.columns([4, 1])
    termo_c = sc1.text_input("🔍 Nome ou CPF/CNPJ", key="cli_termo",
                              label_visibility="collapsed",
                              placeholder="Nome ou CPF/CNPJ…")
    if sc2.button("Buscar", use_container_width=True, key="cli_buscar"):
        with st.spinner("Buscando…"):
            try:
                st.session_state["cli_results"] = api.buscar_clientes(termo_c, limite=30)
            except Exception as ex:
                st.error(f"Erro: {ex}")
                st.session_state["cli_results"] = []

    clientes = st.session_state.get("cli_results")
    if clientes is None and not termo_c:
        # Carrega primeiros por padrão
        try:
            clientes = api.buscar_clientes("", limite=20)
            st.session_state["cli_results"] = clientes
        except Exception:
            clientes = []

    clientes = clientes or []
    if clientes:
        st.caption(f"{len(clientes)} cliente(s) encontrado(s)")
        for ci, c in enumerate(clientes):
            nome_c = c.get("nome") or c.get("razao_social") or "—"
            doc    = c.get("cpf") or c.get("cnpj") or ""
            tel    = c.get("telefone") or c.get("celular") or ""
            cidade = c.get("cidade") or ""
            cid_html = (f" · {cidade}" if cidade else "")

            with st.expander(f"👤 {nome_c}" + (f" — {doc}" if doc else "")):
                d1, d2 = st.columns(2)
                d1.write(f"**Nome:** {nome_c}")
                d1.write(f"**Doc.:** {doc or '—'}")
                d1.write(f"**Tel.:** {tel or '—'}")
                d1.write(f"**E-mail:** {c.get('email','—')}")
                d2.write(f"**Cidade:** {cidade or '—'}")
                d2.write(f"**Estado:** {c.get('estado','—')}")
                d2.write(f"**Obs.:** {c.get('observacoes','—')[:60]}")

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                _sec("Editar dados")

                e1, e2 = st.columns(2)
                e_nome  = e1.text_input("Nome", value=nome_c, key=f"cli_e_nome_{ci}")
                e_doc   = e2.text_input("CPF/CNPJ", value=doc, key=f"cli_e_doc_{ci}")
                e3, e4  = st.columns(2)
                e_tel   = e3.text_input("Telefone", value=tel, key=f"cli_e_tel_{ci}")
                e_email = e4.text_input("E-mail", value=c.get("email",""), key=f"cli_e_email_{ci}")
                e_obs   = st.text_area("Observações", value=c.get("observacoes",""),
                                       key=f"cli_e_obs_{ci}", height=60)

                col_save, col_del = st.columns(2)
                if col_save.button("💾 Salvar edição", use_container_width=True,
                                   key=f"cli_save_{ci}"):
                    with st.spinner("Salvando…"):
                        try:
                            api.atualizar_cliente(c["id"], {
                                "nome": e_nome, "cpf_cnpj": e_doc,
                                "telefone": e_tel, "email": e_email,
                                "observacoes": e_obs,
                            })
                            st.success("✅ Cliente atualizado!")
                            st.session_state.pop("cli_results", None)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Erro: {ex}")

                if col_del.button("🗑️ Excluir", use_container_width=True,
                                   key=f"cli_del_{ci}"):
                    with st.spinner("Excluindo…"):
                        try:
                            api.excluir_cliente(c["id"])
                            st.warning(f"Cliente '{nome_c}' excluído.")
                            st.session_state.pop("cli_results", None)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Erro: {ex}")
    elif clientes is not None:
        _empty_state("👥", "Nenhum cliente encontrado", "Use a busca acima ou cadastre um novo")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# FORNECEDORES
# ══════════════════════════════════════════════════════════════════

def _fornecedores():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("🏭 Fornecedores", "Gerencie o cadastro de fornecedores")

    # ── Novo fornecedor ──
    with st.expander("➕ Cadastrar novo fornecedor"):
        nf1, nf2 = st.columns(2)
        nf_nome  = nf1.text_input("Razão Social *", key="forn_new_nome")
        nf_cnpj  = nf2.text_input("CNPJ", key="forn_new_cnpj")
        nf3, nf4 = st.columns(2)
        nf_tel   = nf3.text_input("Telefone", key="forn_new_tel")
        nf_email = nf4.text_input("E-mail", key="forn_new_email")
        nf5, nf6 = st.columns(2)
        nf_rep   = nf5.text_input("Representante / Contato", key="forn_new_rep")
        nf_pz    = nf6.text_input("Prazo de entrega", key="forn_new_pz")
        nf_obs   = st.text_area("Observações", key="forn_new_obs", height=70)

        if st.button("✅ Salvar fornecedor", use_container_width=True,
                     type="primary", key="forn_new_save"):
            if not nf_nome.strip():
                st.warning("Razão Social é obrigatório.")
            else:
                with st.spinner("Salvando…"):
                    try:
                        dados = {"razao_social": nf_nome.strip(), "cnpj": nf_cnpj,
                                 "telefone": nf_tel, "email": nf_email,
                                 "observacoes": nf_obs}
                        api.criar_fornecedor(dados)
                        st.success(f"✅ Fornecedor '{nf_nome}' cadastrado!")
                        st.session_state.pop("forn_results", None)
                    except Exception as ex:
                        st.error(f"Erro: {ex}")

    # ── Busca ──
    _sec("Buscar fornecedores")
    sf1, sf2 = st.columns([4, 1])
    termo_f = sf1.text_input("🔍 Nome ou CNPJ", key="forn_termo",
                              label_visibility="collapsed",
                              placeholder="Nome ou CNPJ…")
    if sf2.button("Buscar", use_container_width=True, key="forn_buscar"):
        with st.spinner("Buscando…"):
            try:
                st.session_state["forn_results"] = api.buscar_fornecedores(termo_f, limite=30)
            except Exception as ex:
                st.error(f"Erro: {ex}")
                st.session_state["forn_results"] = []

    fornecedores = st.session_state.get("forn_results")
    if fornecedores is None and not termo_f:
        try:
            fornecedores = api.buscar_fornecedores("", limite=20)
            st.session_state["forn_results"] = fornecedores
        except Exception:
            fornecedores = []

    fornecedores = fornecedores or []
    if fornecedores:
        st.caption(f"{len(fornecedores)} fornecedor(es) encontrado(s)")
        for fi, f in enumerate(fornecedores):
            nome_f = f.get("razao_social") or f.get("nome") or "—"
            cnpj_f = f.get("cnpj") or ""
            tel_f  = f.get("telefone") or ""

            with st.expander(f"🏭 {nome_f}" + (f" — {cnpj_f}" if cnpj_f else "")):
                d1, d2 = st.columns(2)
                d1.write(f"**Razão Social:** {nome_f}")
                d1.write(f"**CNPJ:** {cnpj_f or '—'}")
                d1.write(f"**Tel.:** {tel_f or '—'}")
                d2.write(f"**E-mail:** {f.get('email','—')}")
                d2.write(f"**Obs.:** {(f.get('observacoes') or '')[:60]}")

                _sec("Editar dados")
                ef1, ef2 = st.columns(2)
                ef_nome  = ef1.text_input("Razão Social", value=nome_f, key=f"forn_e_nome_{fi}")
                ef_cnpj  = ef2.text_input("CNPJ", value=cnpj_f, key=f"forn_e_cnpj_{fi}")
                ef3, ef4 = st.columns(2)
                ef_tel   = ef3.text_input("Telefone", value=tel_f, key=f"forn_e_tel_{fi}")
                ef_email = ef4.text_input("E-mail", value=f.get("email",""), key=f"forn_e_email_{fi}")
                ef_obs   = st.text_area("Observações", value=f.get("observacoes",""),
                                        key=f"forn_e_obs_{fi}", height=60)

                cs, cd = st.columns(2)
                if cs.button("💾 Salvar", use_container_width=True, key=f"forn_save_{fi}"):
                    with st.spinner("Salvando…"):
                        try:
                            api.atualizar_fornecedor(f["id"], {
                                "razao_social": ef_nome, "cnpj": ef_cnpj,
                                "telefone": ef_tel, "email": ef_email,
                                "observacoes": ef_obs,
                            })
                            st.success("✅ Fornecedor atualizado!")
                            st.session_state.pop("forn_results", None)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Erro: {ex}")
                if cd.button("🗑️ Excluir", use_container_width=True, key=f"forn_del_{fi}"):
                    with st.spinner("Excluindo…"):
                        try:
                            api.excluir_fornecedor(f["id"])
                            st.warning(f"Fornecedor '{nome_f}' excluído.")
                            st.session_state.pop("forn_results", None)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Erro: {ex}")
    elif fornecedores is not None:
        _empty_state("🏭", "Nenhum fornecedor encontrado", "Use a busca ou cadastre um novo")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# COMPRAS
# ══════════════════════════════════════════════════════════════════

def _compras(loja_id):
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("🧾 Histórico de Compras", "Consulte e detalhe pedidos de compra")

    c1, c2, c3 = st.columns([1, 1, 1])
    d_ini = c1.date_input("De",  value=date.today() - timedelta(days=30), key="cmp_ini")
    d_fim = c2.date_input("Até", value=date.today(), key="cmp_fim")
    if c3.button("🔄 Carregar", use_container_width=True, type="primary", key="cmp_load"):
        st.session_state.pop("cmp_data", None)

    if "cmp_data" not in st.session_state:
        with st.spinner("Carregando compras…"):
            try:
                res = api.buscar_compras(str(d_ini), str(d_fim), loja_id=loja_id, limite=100)
                st.session_state["cmp_data"] = res if isinstance(res, list) else []
            except Exception as ex:
                st.error(f"Erro ao carregar compras: {ex}")
                st.session_state["cmp_data"] = []

    compras = st.session_state.get("cmp_data", [])

    if compras:
        total_val = sum(float(c.get("valor_total") or 0) for c in compras)
        mk1, mk2, mk3 = st.columns(3)
        with mk1: _kpi(len(compras), "Compras", "kpi-ind", "🧾")
        with mk2: _kpi(f"R$ {total_val:,.0f}", "Total", "kpi-grn", "💰")
        with mk3:
            n_pend = sum(1 for c in compras
                         if str(c.get("situacao_id","")) not in ("2","3","4"))
            _kpi(n_pend, "Pendentes", "kpi-amb" if n_pend else "", "⏳")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        for ci, cmp in enumerate(compras):
            num    = cmp.get("codigo") or cmp.get("numero") or cmp.get("id","")
            forn   = (cmp.get("fornecedor_nome") or cmp.get("fornecedor") or "—")[:30]
            data_c = (cmp.get("data_emissao") or cmp.get("created_at",""))[:10]
            val    = float(cmp.get("valor_total") or 0)
            sit    = cmp.get("situacao") or cmp.get("status") or "—"
            sit_id = str(cmp.get("situacao_id",""))
            sit_cor = "grn" if sit_id in ("3","4") else ("yel" if sit_id == "2" else "gray")

            with st.expander(
                f"#{num} · {forn} · {data_c} · R$ {val:,.2f} "
                + (f"[{sit}]" if sit != "—" else "")
            ):
                d1, d2 = st.columns(2)
                d1.write(f"**Fornecedor:** {forn}")
                d1.write(f"**Data emissão:** {data_c}")
                d1.write(f"**Código:** {num}")
                d2.write(f"**Valor total:** R$ {val:,.2f}")
                d2.markdown(f"**Situação:** {_chip(sit, sit_cor)}", unsafe_allow_html=True)
                obs_c = cmp.get("observacoes") or ""
                if obs_c:
                    d2.write(f"**Obs.:** {obs_c[:60]}")

                if st.button("📋 Ver itens desta compra", key=f"cmp_det_{ci}"):
                    with st.spinner("Carregando itens…"):
                        try:
                            det = api.buscar_compra(cmp["id"], loja_id)
                            prods_det = det.get("produtos", det.get("itens", []))
                            if prods_det:
                                rows_d = [{
                                    "Produto":   (p.get("nome_produto") or p.get("produto_nome",""))[:30],
                                    "Variação":  p.get("variacao_nome",""),
                                    "Qtd":       p.get("quantidade",""),
                                    "Custo un.": f"R$ {float(p.get('valor_custo') or 0):,.2f}",
                                } for p in prods_det]
                                st.dataframe(pd.DataFrame(rows_d), use_container_width=True, hide_index=True)
                            else:
                                st.info("Nenhum item encontrado.")
                        except Exception as ex:
                            st.error(f"Erro: {ex}")
    else:
        _empty_state("🧾", "Nenhuma compra encontrada", "Ajuste o período e clique em Carregar")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# FINANCEIRO
# ══════════════════════════════════════════════════════════════════

def _financeiro():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("💰 Financeiro", "Contas a receber e a pagar")

    tab_r, tab_p = st.tabs(["💚 Contas a Receber", "❤️ Contas a Pagar"])

    def _render_fin(tipo: str):
        key_d = f"beta_fin2_{tipo}"
        f1, f2, f3 = st.columns([1, 1, 1])
        ini = f1.date_input("De",  value=date.today() - timedelta(days=30), key=f"{tipo}_ini")
        fim = f2.date_input("Até", value=date.today() + timedelta(days=30), key=f"{tipo}_fim")
        if f3.button("🔄 Carregar", use_container_width=True, key=f"{tipo}_btn"):
            st.session_state.pop(key_d, None)

        if key_d not in st.session_state:
            with st.spinner("Carregando…"):
                try:
                    fn = api.buscar_contas_receber if tipo == "rec" else api.buscar_contas_pagar
                    dados = fn(str(ini), str(fim), limite=300)
                    st.session_state[key_d] = dados if isinstance(dados, list) else []
                except Exception as ex:
                    st.error(f"Erro: {ex}")
                    st.session_state[key_d] = []

        contas = st.session_state.get(key_d, [])
        if not isinstance(contas, list):
            contas = []

        total  = sum(float(c.get("valor") or c.get("valor_total") or 0) for c in contas)
        pago   = sum(float(c.get("valor_pago") or 0) for c in contas)
        aberto = total - pago

        k1, k2, k3 = st.columns(3)
        cor_tot = "kpi-grn" if tipo == "rec" else "kpi-red"
        with k1: _kpi(f"R$ {total:,.2f}",  "Total",          cor_tot, "💰")
        with k2: _kpi(f"R$ {pago:,.2f}",   "Recebido/Pago",  "kpi-grn", "✅")
        with k3: _kpi(f"R$ {aberto:,.2f}", "Em aberto",      "kpi-amb" if aberto else "", "⏳")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if contas:
            # Chart por vencimento
            by_date: dict[str, float] = {}
            for c in contas:
                venc = (c.get("data_vencimento") or "")[:10]
                v    = float(c.get("valor") or c.get("valor_total") or 0)
                if venc:
                    by_date[venc] = by_date.get(venc, 0) + v
            if len(by_date) > 1:
                df_chart = pd.DataFrame({"Valor": by_date}).sort_index()
                st.bar_chart(df_chart)

            rows = []
            for c in contas:
                pago_c = str(c.get("situacao_id","")) in ("2","3") or str(c.get("pago","")) == "1"
                sit = "✅ Quitado" if pago_c else "⏳ Aberto"
                parte = (c.get("cliente_nome") or c.get("fornecedor_nome") or "")[:22]
                rows.append({
                    "Status":    sit,
                    "Descrição": (c.get("descricao") or c.get("historico",""))[:32],
                    "Parte":     parte,
                    "Vencto":    (c.get("data_vencimento") or "")[:10],
                    "Valor":     f"R$ {float(c.get('valor') or c.get('valor_total') or 0):,.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            buf_fin = io.BytesIO()
            with pd.ExcelWriter(buf_fin, engine="openpyxl") as wr:
                pd.DataFrame(rows).to_excel(wr, index=False)
            buf_fin.seek(0)
            st.download_button(
                "📄 Exportar Excel", buf_fin,
                f"financeiro_{tipo}_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key=f"fin_xls_{tipo}",
            )
        else:
            _empty_state("💰", "Sem lançamentos no período", "Ajuste as datas e clique em Carregar")

    with tab_r: _render_fin("rec")
    with tab_p: _render_fin("pag")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ══════════════════════════════════════════════════════════════════

def _relatorios(cache, loja_id):
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("📊 Relatórios", "Vendas, estoque e resultado financeiro")

    tab_v, tab_e, tab_f = st.tabs(["📈 Vendas", "📦 Estoque", "💰 Resultado"])

    # ── Vendas ──
    with tab_v:
        rv1, rv2, rv3 = st.columns([1, 1, 1])
        d_ini = rv1.date_input("De",  value=date.today() - timedelta(days=30), key="rv_ini")
        d_fim = rv2.date_input("Até", value=date.today(), key="rv_fim")
        if rv3.button("📊 Gerar", use_container_width=True, type="primary", key="rv_btn"):
            with st.spinner("Carregando vendas…"):
                try:
                    vendas = api.buscar_vendas(str(d_ini), str(d_fim), loja_id=loja_id, limite=500)
                    if not isinstance(vendas, list): vendas = []
                    if vendas:
                        tv = sum(float(v.get("valor_total") or 0) for v in vendas)
                        tm = tv / len(vendas)
                        k1, k2, k3 = st.columns(3)
                        with k1: _kpi(len(vendas), "Pedidos", "kpi-ind", "🛒")
                        with k2: _kpi(f"R$ {tv:,.2f}", "Total", "kpi-grn", "💰")
                        with k3: _kpi(f"R$ {tm:,.2f}", "Ticket médio", "", "📊")

                        rows_v = [{
                            "Data":    (v.get("data_emissao", "") or "")[:10],
                            "Nº":      v.get("numero", ""),
                            "Cliente": (v.get("cliente_nome","") or "")[:22],
                            "Valor":   float(v.get("valor_total") or 0),
                            "Status":  v.get("status",""),
                        } for v in vendas]
                        df_v = pd.DataFrame(rows_v)
                        _sec("Vendas por dia")
                        st.bar_chart(df_v.groupby("Data")["Valor"].sum())
                        st.dataframe(df_v, use_container_width=True, hide_index=True)
                    else:
                        _empty_state("📈", "Nenhuma venda no período")
                except Exception as ex:
                    st.error(f"Erro: {ex}")

    # ── Estoque ──
    with tab_e:
        if not cache:
            _empty_state("📦", "Cache vazio", "Sincronize em Config")
        else:
            rows_e = []
            for p in cache.get("produtos", []):
                for v in p.get("variacoes", []):
                    vd  = v.get("variacao", v)
                    est = int(vd.get("estoque", 0) or 0)
                    rows_e.append({
                        "Status":   "🔴" if est <= 3 else ("🟡" if est <= 10 else "🟢"),
                        "Produto":  p.get("nome", "")[:30],
                        "Variação": vd.get("nome", "")[:25],
                        "Cód.":     vd.get("codigo", ""),
                        "Estoque":  est,
                    })
            if rows_e:
                df_e = pd.DataFrame(rows_e).sort_values("Estoque")
                total_un = df_e["Estoque"].sum()
                _sec(f"{len(df_e)} variações · {total_un:,} unidades totais")
                filtro = st.selectbox("Filtrar por status",
                                       ["Todos", "🔴 Crítico (≤3)", "🟡 Baixo (≤10)", "🟢 Saudável (>10)"],
                                       key="rel_e_filtro")
                if "Crítico" in filtro:
                    df_e = df_e[df_e["Estoque"] <= 3]
                elif "Baixo" in filtro:
                    df_e = df_e[df_e["Estoque"] <= 10]
                elif "Saudável" in filtro:
                    df_e = df_e[df_e["Estoque"] > 10]
                st.dataframe(df_e, use_container_width=True, hide_index=True)

                buf_e = io.BytesIO()
                with pd.ExcelWriter(buf_e, engine="openpyxl") as wr:
                    df_e.to_excel(wr, index=False)
                buf_e.seek(0)
                st.download_button(
                    "📄 Exportar Excel", buf_e, f"estoque_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # ── Resultado ──
    with tab_f:
        rf1, rf2, rf3 = st.columns([1, 1, 1])
        d_ri = rf1.date_input("De",  value=date.today() - timedelta(days=30), key="rf_ini")
        d_rf = rf2.date_input("Até", value=date.today(), key="rf_fim")
        if rf3.button("📊 Gerar", use_container_width=True, type="primary", key="rf_btn"):
            with st.spinner("Calculando…"):
                try:
                    rec_f = api.buscar_contas_receber(str(d_ri), str(d_rf), limite=500)
                    pag_f = api.buscar_contas_pagar(str(d_ri), str(d_rf), limite=500)
                    if not isinstance(rec_f, list): rec_f = []
                    if not isinstance(pag_f, list): pag_f = []
                    tr_f  = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in rec_f)
                    tp_f  = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in pag_f)
                    res_f = tr_f - tp_f

                    ka, kb, kc = st.columns(3)
                    with ka: _kpi(f"R$ {tr_f:,.2f}",  "Receitas",  "kpi-grn", "💚")
                    with kb: _kpi(f"R$ {tp_f:,.2f}",  "Despesas",  "kpi-red", "❤️")
                    with kc: _kpi(f"R$ {res_f:,.2f}", "Resultado",
                                  "kpi-grn" if res_f >= 0 else "kpi-red", "⚡")

                    df_res = pd.DataFrame(
                        {"Valor": {"Receitas": tr_f, "Despesas": tp_f,
                                   "Resultado": max(0, res_f)}}
                    )
                    st.bar_chart(df_res)

                    # Lucro percentual
                    if tr_f > 0:
                        pct = res_f / tr_f * 100
                        cor_pct = "kpi-grn" if pct >= 0 else "kpi-red"
                        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                        _kpi(f"{pct:.1f}%", "Margem sobre receitas", cor_pct, "📊")
                except Exception as ex:
                    st.error(f"Erro: {ex}")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# LISTAS
# ══════════════════════════════════════════════════════════════════

def _listas():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("📋 Listas Salvas", "Gerencie todas as listas do sistema")

    tipos = [None, "pedido", "recebimento", "conferencia", "outro"]
    tabs_l = st.tabs(["🗂️ Todas", "🛒 Pedido", "📥 Recebimento", "✅ Conferência", "📌 Outro"])

    for tab_l, tipo in zip(tabs_l, tipos):
        with tab_l:
            listas = api.listar_listas_salvas(tipo)
            if listas:
                for lst in listas:
                    arq  = lst.get("_arquivo", "")
                    lnm  = lst.get("nome", arq)
                    lqt  = len(lst.get("itens", []))
                    ldt  = (lst.get("criado_em", "") or "")[:10]
                    ltp  = lst.get("tipo", "—")

                    with st.expander(f"📄 {lnm} · {lqt} itens · {ldt}"):
                        st.markdown(f"**Tipo:** {ltp} · **Arquivo:** `{arq}`")
                        itens_l = lst.get("itens", [])
                        if itens_l:
                            rows_l = [{
                                "Produto":  it.get("produto_nome",""),
                                "Variação": it.get("variacao_nome",""),
                                "Qtd":      it.get("quantidade",""),
                            } for it in itens_l[:50]]
                            st.dataframe(pd.DataFrame(rows_l), use_container_width=True, hide_index=True)
                            if len(itens_l) > 50:
                                st.caption(f"… e mais {len(itens_l)-50} itens")

                        xa, xb, xc = st.columns(3)
                        # Copiar texto
                        if xa.button("📋 Copiar", key=f"lista_copy_{arq}", use_container_width=True):
                            linhas = [f"LISTA: {lnm}", "=" * 36]
                            for it in itens_l:
                                v = f" / {it['variacao_nome']}" if it.get("variacao_nome") else ""
                                linhas.append(f"{it.get('produto_nome','')}{v} — {it.get('quantidade',0)} un")
                            _copiar_html("\n".join(linhas))

                        # Excel
                        if itens_l:
                            buf_l = io.BytesIO()
                            with pd.ExcelWriter(buf_l, engine="openpyxl") as wr:
                                pd.DataFrame([{
                                    "Produto":  it.get("produto_nome",""),
                                    "Variação": it.get("variacao_nome",""),
                                    "Qtd":      it.get("quantidade",""),
                                } for it in itens_l]).to_excel(wr, index=False)
                            buf_l.seek(0)
                            xb.download_button(
                                "📄 Excel", buf_l, f"{arq}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True, key=f"lista_xls_{arq}",
                            )

                        if xc.button("🗑️ Excluir", key=f"lista_del_{arq}", use_container_width=True):
                            try:
                                api.excluir_lista(arq)
                                st.warning(f"Lista '{lnm}' excluída.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Erro: {ex}")
            else:
                _empty_state("📋", "Nenhuma lista nesta categoria",
                             "Crie listas na aba Pedidos")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════

def _config(cache, loja_id, is_adm):
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    _pg_header("⚙️ Configurações", "Sincronização, lojas e usuários")

    tabs_cfg = ["🔄 Sincronização", "🏪 Loja ativa", "🔀 Versão"]
    if is_adm:
        tabs_cfg.append("👥 Usuários")
    tab_s, tab_l, tab_v, *tab_u_list = st.tabs(tabs_cfg)
    tab_u = tab_u_list[0] if tab_u_list else None

    # ── Sync ──
    with tab_s:
        if cache:
            sync = (cache.get("sincronizado_em", "") or "")[:16].replace("T", " às ")
            _alerta(
                f"Cache ativo: {cache.get('total',0):,} produtos",
                f"Loja: {cache.get('loja_nome','—')} · Sync: {sync}",
                tipo="grn",
            )
        else:
            _alerta("Nenhum cache para esta loja — sincronize para começar.", tipo="yel")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _sec("Sincronizar dados com GestãoClick")

        if st.button("🔄 Sincronizar Todas as Lojas", type="primary",
                      use_container_width=True, key="sync_all"):
            bar  = st.progress(0, text="Iniciando…")
            errs = []
            for idx, (lid, lnm) in enumerate(api.LOJAS.items()):
                def _prog(pag, tot, _n=lnm, _i=idx, _T=len(api.LOJAS)):
                    bar.progress((_i + pag / max(tot, 1)) / _T, text=f"{_n}: pág {pag}/{tot}")
                try:
                    api.sincronizar_produtos(loja_id=lid, progress_callback=_prog)
                except Exception as ex:
                    errs.append(f"{lnm}: {ex}")
            _alertas_estoque.clear()
            if errs:
                for e in errs: st.error(e)
            else:
                st.success("✅ Todas as lojas sincronizadas!")
                st.rerun()

    # ── Loja ──
    with tab_l:
        _sec("Loja ativa")
        opts = {v: k for k, v in api.LOJAS.items()}
        atual = api.LOJAS.get(str(loja_id), list(api.LOJAS.values())[0])
        nova  = st.selectbox("Selecione a loja", list(opts.keys()),
                              index=list(opts.keys()).index(atual) if atual in opts else 0,
                              key="cfg_loja")
        if st.button("✅ Trocar loja", use_container_width=True, key="cfg_loja_ok"):
            st.session_state["loja_ativa_id"]   = opts[nova]
            st.session_state["loja_ativa_nome"] = nova
            st.rerun()

        _sec("Lojas cadastradas")
        for lid2, lnm2 in api.LOJAS.items():
            c2 = api.carregar_cache(lid2)
            tot = c2.get("total", 0) if c2 else 0
            sync2 = (c2.get("sincronizado_em","") or "")[:10] if c2 else "—"
            cor2  = "grn" if c2 else "red"
            _alerta(f"**{lnm2}** — {tot:,} produtos", f"Sync: {sync2}", tipo=cor2)

    # ── Versão ──
    with tab_v:
        st.markdown("""
        <div class="card">
          <div style="font-size:.9rem;font-weight:700;margin-bottom:10px">🚀 Você está no Beta</div>
          <div style="font-size:.78rem;color:#64748b;line-height:1.7">
            ✦ Interface redesenhada com mobile-first<br>
            ✦ Dashboard com gráficos e alertas visuais<br>
            ✦ Clientes e Fornecedores com CRUD completo<br>
            ✦ Histórico de compras com detalhamento<br>
            ✦ Gerenciador de listas aprimorado<br>
            ✦ Usa os mesmos dados do Classic
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Voltar para o Classic", use_container_width=True, key="cfg_classic"):
            st.session_state["version"] = "classic"
            st.query_params["v"] = "classic"
            st.rerun()

    # ── Usuários ──
    if tab_u:
        with tab_u:
            _sec("Usuários do sistema")
            udb = api.carregar_usuarios()
            for uname, udata in udb.items():
                nome_u  = udata.get("nome", uname)
                setor_u = udata.get("setor", "—")
                st.markdown(
                    f'<div class="li">'
                    f'<div class="li-name">{nome_u} '
                    + _chip(setor_u, "ind")
                    + f'</div><div class="li-sub">{uname}</div></div>',
                    unsafe_allow_html=True,
                )
            if st.button("⚙️ Gerenciar no Classic", use_container_width=True, key="cfg_usr_cls"):
                st.session_state["version"] = "classic"
                st.query_params["v"] = "classic"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def run():
    st.markdown(_CSS, unsafe_allow_html=True)

    if not _check_auth():
        _tela_login()
        st.stop()
        return

    user    = st.session_state.usuario_logado
    udb     = api.carregar_usuarios()
    ud      = udb.get(user, {})
    setor   = ud.get("setor", "vendas")
    setores = api.carregar_setores()
    setor_c = setores.get(setor, {"paginas": []})
    perm    = set(setor_c.get("paginas", []))
    nome    = ud.get("nome", user).title()
    is_adm  = (setor == "admin")

    if "loja_ativa_id" not in st.session_state:
        st.session_state["loja_ativa_id"] = list(api.LOJAS.keys())[0]
    loja_id   = st.session_state["loja_ativa_id"]
    loja_nome = api.LOJAS.get(str(loja_id), "—")
    cache     = api.carregar_cache(loja_id)

    _header(nome, loja_nome)

    # ── Montar tabs por permissão ──
    _pgs: list[str] = []
    _fns: list      = []

    def _add(label, reqs, fn):
        if is_adm or any(r in perm for r in reqs):
            _pgs.append(label)
            _fns.append(fn)

    _add("🏠 Início",        ["dashboard"],
         lambda: _dashboard(cache, loja_id, loja_nome, nome, is_adm))
    _add("🛒 Pedidos",       ["pedido"],
         lambda: _pedidos(cache, loja_id))
    _add("📦 Estoque",       ["entrada", "acerto", "estoque_loja"],
         lambda: _estoque(cache, loja_id))
    _add("👥 Clientes",      ["clientes"],
         lambda: _clientes())
    _add("🏭 Fornecedores",  ["fornecedores"],
         lambda: _fornecedores())
    _add("🧾 Compras",       ["compras_hist"],
         lambda: _compras(loja_id))
    _add("💰 Financeiro",    ["financeiro"],
         lambda: _financeiro())
    _add("📊 Relatórios",    ["relatorios"],
         lambda: _relatorios(cache, loja_id))
    _add("📋 Listas",        ["listas"],
         lambda: _listas())
    _add("⚙️ Config",        ["sincronizacao", "usuarios"],
         lambda: _config(cache, loja_id, is_adm))

    if not _pgs:
        st.error("Sem permissões. Contate o administrador.")
        if st.button("Sair"):
            api.revogar_sessao(st.session_state.get("_sessao_token", ""))
            st.session_state.clear()
            st.rerun()
        return

    tabs = st.tabs(_pgs)
    for tab, fn in zip(tabs, _fns):
        with tab:
            fn()
