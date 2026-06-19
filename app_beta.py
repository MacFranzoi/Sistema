"""Sistema Beta v4 — Modern sidebar SaaS UI."""

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
[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"]{display:none!important}
[data-testid="stAppViewContainer"]{background:#f9fafb!important}
[data-testid="stMain"]{background:#f9fafb!important}

/* ── Sidebar ── */
[data-testid="stSidebar"]{
  background:#ffffff!important;
  border-right:1px solid #e5e7eb!important;
  min-width:230px!important;width:230px!important}
[data-testid="stSidebar"]>div{padding:0!important}
[data-testid="stSidebar"] section[data-testid="stSidebarContent"]{
  padding:0 10px!important}

/* sidebar radio → nav items */
[data-testid="stSidebar"] [data-testid="stRadio"]>label{display:none!important}
[data-testid="stSidebar"] [data-testid="stRadio"]>div{
  flex-direction:column!important;gap:2px!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{
  border-radius:8px!important;padding:10px 12px!important;
  cursor:pointer!important;font-size:.85rem!important;
  color:#6b7280!important;font-weight:500!important;
  width:100%!important;margin:0!important;
  display:flex!important;align-items:center!important;gap:8px!important;
  transition:background .12s,color .12s!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{
  background:#f3f4f6!important;color:#111827!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
  background:#eef2ff!important;color:#4338ca!important;font-weight:700!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label>div:first-child{
  display:none!important}

/* sidebar selectbox/divider */
[data-testid="stSidebar"] [data-testid="stSelectbox"] label{
  font-size:.65rem!important;font-weight:700!important;
  color:#9ca3af!important;text-transform:uppercase!important;letter-spacing:.5px!important}
[data-testid="stSidebar"] hr{border-color:#f3f4f6!important;margin:10px 0!important}

/* ── Main content ── */
.block-container{padding:32px 36px 60px!important;max-width:980px!important}

/* ── Page header ── */
.pg-title{font-size:1.35rem;font-weight:800;color:#111827;letter-spacing:-.5px;margin:0}
.pg-sub{font-size:.78rem;color:#9ca3af;margin-top:3px;margin-bottom:22px}

/* ── Cards ── */
.card{background:#fff;border:1px solid #f3f4f6;border-radius:12px;
  padding:20px 24px;margin-bottom:14px;
  box-shadow:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03)}

/* ── KPI ── */
.kpi{background:#fff;border:1px solid #f3f4f6;border-radius:12px;
  padding:18px 20px;height:100%;position:relative;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.05)}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;
  height:3px;background:#e5e7eb;border-radius:12px 12px 0 0}
.kpi-ind::before{background:#4f46e5}
.kpi-grn::before{background:#059669}
.kpi-red::before{background:#dc2626}
.kpi-amb::before{background:#d97706}
.kpi-lbl{font-size:.67rem;font-weight:700;color:#9ca3af;
  text-transform:uppercase;letter-spacing:.6px}
.kpi-icon{float:right;font-size:1.5rem;opacity:.12;margin-top:-2px}
.kpi-val{font-size:1.7rem;font-weight:800;color:#111827;line-height:1.1;margin-top:6px}
.kpi-sub{font-size:.7rem;color:#9ca3af;margin-top:5px}
.kpi-grn .kpi-val{color:#059669}.kpi-red .kpi-val{color:#dc2626}
.kpi-ind .kpi-val{color:#4f46e5}.kpi-amb .kpi-val{color:#d97706}

/* ── Section label ── */
.sec{font-size:.65rem;font-weight:700;color:#9ca3af;text-transform:uppercase;
  letter-spacing:.9px;margin:22px 0 10px;display:flex;align-items:center;gap:10px}
.sec::after{content:'';flex:1;height:1px;background:#f3f4f6}

/* ── Alerts ── */
.alerta{display:flex;gap:12px;border-radius:10px;padding:12px 16px;
  margin-bottom:10px;border:1px solid}
.alerta-red{background:#fef2f2;border-color:#fecaca}
.alerta.alerta-yel{background:#fffbeb;border-color:#fde68a}
.alerta.alerta-grn{background:#f0fdf4;border-color:#bbf7d0}
.alerta.alerta-ind{background:#eef2ff;border-color:#c7d2fe}
.alerta-ico{font-size:.95rem;flex-shrink:0;margin-top:2px}
.alerta-body{flex:1}
.alerta-t{font-size:.82rem;font-weight:600;color:#111827}
.alerta-s{font-size:.71rem;color:#6b7280;margin-top:2px}

/* ── Chips ── */
.chip{display:inline-flex;align-items:center;padding:2px 9px;
  border-radius:20px;font-size:.62rem;font-weight:700;letter-spacing:.2px}
.chip-red{background:#fee2e2;color:#b91c1c}
.chip-yel{background:#fef3c7;color:#92400e}
.chip-grn{background:#dcfce7;color:#15803d}
.chip-ind{background:#e0e7ff;color:#4338ca}
.chip-blue{background:#dbeafe;color:#1e40af}
.chip-gray{background:#f3f4f6;color:#374151}

/* ── List rows ── */
.li{background:#fff;border:1px solid #f3f4f6;border-radius:10px;
  padding:13px 16px;margin-bottom:7px;
  box-shadow:0 1px 2px rgba(0,0,0,.04)}
.li-name{font-size:.84rem;font-weight:600;color:#111827}
.li-sub{font-size:.71rem;color:#9ca3af;margin-top:2px}

/* ── Buttons ── */
[data-testid="stButton"]>button{
  border-radius:8px!important;font-weight:600!important;
  font-size:.82rem!important;min-height:40px!important;
  border:1px solid #e5e7eb!important;
  transition:box-shadow .15s,transform .1s,border-color .15s!important}
[data-testid="stButton"]>button:hover{
  box-shadow:0 4px 12px rgba(0,0,0,.09)!important;
  transform:translateY(-1px)!important;border-color:#d1d5db!important}
[data-testid="stButton"]>button[kind="primary"]{
  background:#4f46e5!important;border-color:#4f46e5!important;
  color:#fff!important;box-shadow:0 1px 3px rgba(79,70,229,.25)!important}
[data-testid="stButton"]>button[kind="primary"]:hover{
  background:#4338ca!important;border-color:#4338ca!important;
  box-shadow:0 4px 14px rgba(79,70,229,.35)!important}

/* ── Inputs ── */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input{
  border-radius:8px!important;font-size:.875rem!important;
  border-color:#e5e7eb!important}
[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,[data-testid="stTextArea"] label{
  font-size:.74rem!important;font-weight:600!important;color:#6b7280!important}

/* ── DataFrames ── */
[data-testid="stDataFrame"]>div{
  border-radius:10px!important;border:1px solid #f3f4f6!important;
  box-shadow:0 1px 3px rgba(0,0,0,.04)!important;overflow:hidden!important}

/* ── Expanders ── */
[data-testid="stExpander"]{
  border:1px solid #f3f4f6!important;border-radius:10px!important;
  background:#fff!important;margin-bottom:8px!important;
  box-shadow:0 1px 2px rgba(0,0,0,.04)!important}
[data-testid="stExpander"] summary{
  font-size:.84rem!important;font-weight:600!important;
  color:#374151!important;padding:13px 16px!important}

/* ── Inner tabs (inside pages) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
  background:transparent!important;border-bottom:1px solid #f3f4f6!important;
  padding:0!important;gap:0!important}
[data-testid="stTabs"] [data-baseweb="tab"]{
  font-size:.8rem!important;font-weight:500!important;
  padding:10px 14px!important;color:#6b7280!important;
  background:none!important;border:none!important;
  border-bottom:2px solid transparent!important;margin-bottom:-1px!important}
[data-testid="stTabs"] [aria-selected="true"]{
  color:#4f46e5!important;border-bottom-color:#4f46e5!important;
  font-weight:700!important}

/* ── Mobile: hide sidebar, full width ── */
@media(max-width:768px){
  [data-testid="stSidebar"]{display:none!important}
  .block-container{padding:16px 14px 60px!important}
  .kpi-val{font-size:1.35rem!important}
  .pg-title{font-size:1.1rem!important}}
</style>"""

# ══════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════

def _safe_int(v):
    try: return int(float(str(v or 0)))
    except (ValueError, TypeError): return 0

def _kpi(val, lbl, cls="", icon="", sub=""):
    ico = f'<span class="kpi-icon">{icon}</span>' if icon else ""
    sub_h = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="kpi {cls}">'
        f'<div class="kpi-lbl">{lbl}{ico}</div>'
        f'<div class="kpi-val">{val}</div>{sub_h}</div>',
        unsafe_allow_html=True)

def _alerta(titulo, sub="", tipo="red"):
    icons = {"red":"🔴","yel":"🟡","grn":"✅","ind":"💡"}
    cls = f"alerta alerta-{tipo}"
    sub_h = f'<div class="alerta-s">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="alerta-ico">{icons.get(tipo,"•")}</div>'
        f'<div class="alerta-body"><div class="alerta-t">{titulo}</div>{sub_h}</div></div>',
        unsafe_allow_html=True)

def _sec(txt):
    st.markdown(f'<div class="sec">{txt}</div>', unsafe_allow_html=True)

def _chip(txt, cor="ind"):
    return f'<span class="chip chip-{cor}">{txt}</span>'

def _pg_header(title, subtitle=""):
    sub = f'<div class="pg-sub">{subtitle}</div>' if subtitle else '<div style="height:18px"></div>'
    st.markdown(f'<div class="pg-title">{title}</div>{sub}', unsafe_allow_html=True)

def _empty_state(icon, msg, hint=""):
    hint_h = f'<div style="font-size:.73rem;color:#9ca3af;margin-top:6px">{hint}</div>' if hint else ""
    st.markdown(
        f'<div class="card" style="text-align:center;padding:44px 20px">'
        f'<div style="font-size:2.8rem;margin-bottom:12px;opacity:.4">{icon}</div>'
        f'<div style="font-size:.9rem;font-weight:600;color:#374151">{msg}</div>'
        f'{hint_h}</div>', unsafe_allow_html=True)

def _copiar_html(texto):
    import html as _h, streamlit.components.v1 as cv
    cv.html(
        f'<textarea id="ct" style="position:fixed;top:-9999px">{_h.escape(texto)}</textarea>'
        f'<p style="margin:0;font:13px/1.4 system-ui;color:#059669;'
        f'background:#f0fdf4;padding:8px 12px;border-radius:8px;'
        f'border:1px solid #bbf7d0">✅ Copiado para a área de transferência!</p>'
        f'<script>(function(){{var e=document.getElementById("ct");e.focus();e.select();'
        f'try{{navigator.clipboard.writeText(e.value).catch(function(){{'
        f'document.execCommand("copy")}});}}catch(ex){{document.execCommand("copy");}}'
        f'}})();</script>', height=46)

def _stock_bar_html(name, current, ref=20):
    pct = min(100, int(current / max(1, ref) * 100))
    fg = "#ef4444" if current <= 3 else ("#f59e0b" if current <= 10 else "#22c55e")
    bg = "#fee2e2" if current <= 3 else ("#fef3c7" if current <= 10 else "#dcfce7")
    return (
        f'<div style="margin-bottom:10px">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
        f'<span style="font-size:.73rem;font-weight:500;color:#374151">{name[:38]}</span>'
        f'<span style="font-size:.72rem;font-weight:700;color:{fg}">{current} un</span>'
        f'</div>'
        f'<div style="background:{bg};border-radius:4px;height:6px;overflow:hidden">'
        f'<div style="width:{pct}%;height:100%;background:{fg};border-radius:4px;'
        f'transition:width .3s"></div></div></div>')


# ══════════════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════════════

def _check_auth():
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None
    if st.session_state.usuario_logado is None:
        t = st.query_params.get("t", "")
        if t:
            u = api.validar_sessao(t)
            if u:
                st.session_state.usuario_logado = u
                st.session_state["_sessao_token"] = t
    return st.session_state.usuario_logado is not None


def _tela_login():
    st.markdown("""<style>
    [data-testid="stAppViewContainer"]{
      background:linear-gradient(145deg,#f0f4ff 0%,#faf5ff 50%,#f0f9ff 100%)!important}
    section[data-testid="stMain"]>div{
      display:flex;align-items:center;justify-content:center;min-height:100dvh}
    [data-testid="stForm"]{
      background:#fff!important;border:1px solid #e5e7eb!important;
      border-radius:16px!important;padding:2.5rem 2.2rem 2rem!important;
      box-shadow:0 8px 40px rgba(79,70,229,.12)!important;width:100%!important}
    [data-testid="stForm"] button[type="submit"]{
      background:#4f46e5!important;color:#fff!important;font-weight:700!important;
      border:none!important;border-radius:8px!important;min-height:44px!important;
      font-size:.88rem!important;margin-top:.5rem!important;
      box-shadow:0 2px 12px rgba(79,70,229,.3)!important}
    </style>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin-bottom:2rem">
          <div style="display:inline-flex;align-items:center;justify-content:center;
            width:52px;height:52px;border-radius:14px;background:#4f46e5;
            box-shadow:0 6px 20px rgba(79,70,229,.4);margin-bottom:16px">
            <span style="font-size:1.5rem">⚡</span></div>
          <div style="font-size:1.45rem;font-weight:800;color:#111827;letter-spacing:-.5px">
            Plug ERP</div>
          <div style="margin-top:6px">
            <span style="background:#eef2ff;color:#4338ca;font-size:.58rem;
              padding:3px 10px;border-radius:20px;font-weight:700;letter-spacing:.5px">
              BETA</span></div>
          <div style="font-size:.75rem;color:#9ca3af;margin-top:10px">
            Interface redesenhada · Mobile-first</div>
        </div>""", unsafe_allow_html=True)

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

        st.markdown('<hr style="margin:16px 0 12px;opacity:.1">', unsafe_allow_html=True)
        if st.button("← Usar versão Classic", use_container_width=True, key="btl_cls"):
            st.session_state["version"] = "classic"
            st.query_params["v"] = "classic"
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# Stock alerts cache
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def _alertas_estoque(loja_id):
    try:
        c = api.carregar_cache(loja_id)
        criticos, baixos = [], []
        for p in (c or {}).get("produtos", []):
            for v in p.get("variacoes", []):
                vd  = v.get("variacao", v)
                est = _safe_int(vd.get("estoque", 0))
                item = {"produto": p.get("nome",""), "variacao": vd.get("nome",""),
                        "cod": vd.get("codigo",""), "estoque": est}
                if est <= 3:    criticos.append(item)
                elif est <= 10: baixos.append(item)
        return (sorted(criticos, key=lambda x: x["estoque"]),
                sorted(baixos,   key=lambda x: x["estoque"]))
    except Exception:
        return ([], [])


# ══════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════

def _dashboard(cache, loja_id, loja_nome, nome, is_adm):
    hora = datetime.now().hour
    saud = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")
    st.markdown(
        f'<div style="margin-bottom:22px">'
        f'<div style="font-size:1.05rem;font-weight:700;color:#111827">'
        f'{saud}, {nome.split()[0]} 👋</div>'
        f'<div style="font-size:.75rem;color:#9ca3af;margin-top:2px">'
        f'{date.today().strftime("%d/%m/%Y")} · {loja_nome}</div></div>',
        unsafe_allow_html=True)

    total  = cache.get("total", 0) if cache else 0
    sync_em = (cache.get("sincronizado_em","") or "")[:10] if cache else "—"
    criticos, baixos = _alertas_estoque(loja_id) if cache else ([], [])
    n_crit = len(criticos)

    # KPIs
    _sec("Visão geral")
    k1, k2, k3, k4 = st.columns(4)
    with k1: _kpi(f"{total:,}", "Produtos", "kpi-ind", "📦", f"sync {sync_em}")
    with k2: _kpi(len(api.LOJAS), "Lojas ativas", "", "🏪")
    with k3: _kpi(n_crit, "Críticos", "kpi-red" if n_crit else "kpi-grn", "🚨",
                  f"+ {len(baixos)} baixo(s)")
    with k4:
        fk = f"beta_fin_{loja_id}"
        if fk in st.session_state:
            tr, tp = st.session_state[fk]
            res = tr - tp
            _kpi(f"R$ {res:,.0f}", "Resultado mês",
                 "kpi-grn" if res >= 0 else "kpi-red", "💰")
        else:
            _kpi("—", "Resultado mês", "", "💰", "carregando…")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Estoque visual + top alertas
    if cache and (criticos or baixos):
        _sec("⚠️ Alertas de estoque")
        col_bars, col_list = st.columns([3, 2])
        with col_bars:
            top = (criticos + baixos)[:10]
            bars = "".join(_stock_bar_html(
                f"{it['produto']} / {it['variacao']}", it["estoque"]
            ) for it in top)
            st.markdown(f'<div class="card" style="padding:18px 20px">{bars}</div>',
                        unsafe_allow_html=True)
        with col_list:
            for it in criticos[:4]:
                _alerta(f"{it['produto'][:24]} / {it['variacao'][:16]}",
                        f"Estoque: {it['estoque']} un · Cód: {it['cod']}", "red")
        if st.button("🔄 Atualizar alertas", key="d_ref_alerta"):
            _alertas_estoque.clear(); st.rerun()
    elif cache:
        _alerta("Todos os produtos com estoque saudável!", tipo="grn")

    # Financeiro
    _sec("💰 Financeiro do mês")
    fk = f"beta_fin_{loja_id}"
    if fk not in st.session_state:
        with st.spinner("Carregando…"):
            try:
                ini = date.today().replace(day=1)
                rec = api.buscar_contas_receber(str(ini), str(date.today()), limite=500)
                pag = api.buscar_contas_pagar(str(ini), str(date.today()), limite=500)
                if not isinstance(rec, list): rec = []
                if not isinstance(pag, list): pag = []
                tr = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in rec)
                tp = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in pag)
                st.session_state[fk] = (tr, tp)
            except Exception:
                st.session_state[fk] = (0.0, 0.0)

    tr, tp = st.session_state.get(fk, (0.0, 0.0))
    res = tr - tp
    f1, f2, f3 = st.columns(3)
    with f1: _kpi(f"R$ {tr:,.2f}", "A receber", "kpi-grn", "💚")
    with f2: _kpi(f"R$ {tp:,.2f}", "A pagar",   "kpi-red", "❤️")
    with f3: _kpi(f"R$ {res:,.2f}", "Resultado", "kpi-grn" if res >= 0 else "kpi-red", "⚡")

    if tr > 0 or tp > 0:
        st.bar_chart(pd.DataFrame({"Valor": {"A receber": tr, "A pagar": tp, "Resultado": max(0,res)}}))

    if st.button("🔄 Atualizar financeiro", key="d_ref_fin"):
        st.session_state.pop(fk, None); st.rerun()

    # Lojas status
    _sec("🏪 Status das lojas")
    cols_l = st.columns(len(api.LOJAS))
    for col, (lid, lnm) in zip(cols_l, api.LOJAS.items()):
        c = api.carregar_cache(lid)
        t = c.get("total",0) if c else 0
        s = (c.get("sincronizado_em","") or "")[:10] if c else "—"
        online = bool(c)
        col.markdown(
            f'<div class="card" style="text-align:center;padding:14px 8px">'
            f'<div style="font-size:.63rem;font-weight:700;color:#9ca3af">{lnm}</div>'
            f'<div style="font-size:1.5rem;font-weight:800;color:#111827;margin:6px 0">{t}</div>'
            f'<div style="font-size:.62rem;font-weight:700;'
            f'color:{"#059669" if online else "#dc2626"}">'
            f'{"● Online" if online else "● Sem dados"}</div>'
            f'<div style="font-size:.58rem;color:#9ca3af;margin-top:2px">{s}</div>'
            f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PEDIDOS
# ══════════════════════════════════════════════════════════════════

def _pedidos(cache, loja_id):
    _pg_header("🛒 Pedidos de Compra", "Crie e gerencie pedidos para fornecedores")

    if "beta_ped" not in st.session_state:
        st.session_state.beta_ped = []
    itens = st.session_state.beta_ped

    # Lista aberta
    _arq = st.session_state.get("beta_ped_arq")
    if _arq:
        try:
            import os as _os
            with open(_os.path.join(api.DIR_LISTAS, _arq), encoding="utf-8") as f:
                _d = json.load(f)
            _ln = _d.get("nome", _arq)
        except Exception:
            _ln = _arq
        b1, b2, b3 = st.columns([5,1,1])
        b1.info(f"📂 Lista aberta: **{_ln}**")
        if b2.button("💾 Salvar", key="ped_sv", use_container_width=True):
            try:
                import os as _os2
                cam = _os2.path.join(api.DIR_LISTAS, _arq)
                with open(cam, encoding="utf-8") as f: _d = json.load(f)
                _d["itens"] = itens; _d["atualizado_em"] = datetime.now().isoformat()
                _s = json.dumps(_d, ensure_ascii=False, indent=2)
                with open(cam,"w",encoding="utf-8") as f: f.write(_s)
                api._gh_push_arquivo(f"listas/{_arq}", _s, f"Salva: {_ln}")
                st.success("✅ Lista salva!")
            except Exception as ex: st.error(f"Erro: {ex}")
        if b3.button("✕", key="ped_fechar", use_container_width=True):
            st.session_state.pop("beta_ped_arq", None); st.rerun()

    tab_wpp, tab_cat, tab_avl, tab_lst = st.tabs(
        ["📱 WhatsApp / IA", "🔍 Catálogo", "✏️ Avulso", "📂 Listas"])

    # ── WhatsApp ──
    with tab_wpp:
        txt = st.text_area("Texto do pedido", height=130, key="wpp_txt",
            placeholder="Ex:\niPhone 15 - masculino 2, feminino 3\nSamsung A55 - brilho 5",
            label_visibility="collapsed")
        if st.button("🤖 Processar com IA", type="primary", use_container_width=True, key="wpp_proc"):
            if not txt.strip(): st.warning("Cole o texto.")
            elif not cache: st.warning("Sincronize os produtos primeiro.")
            else:
                with st.spinner("Processando…"):
                    try:
                        cat = "\n".join(f"{p.get('codigo_interno','')} | {p.get('nome','')}"
                                        for p in cache.get("produtos",[])[:400])
                        res = api.parse_pedido_whatsapp(txt, cat)
                        st.session_state["wpp_res"] = res
                        for i,r in enumerate(res):
                            st.session_state[f"wpp_chk_{i}"] = bool(r.get("nome_produto"))
                        st.rerun()
                    except Exception as ex: st.error(f"Erro: {ex}")

        res = st.session_state.get("wpp_res", [])
        if res:
            _sec(f"Resultado — {len(res)} item(ns)")
            for i, r in enumerate(res):
                conf = r.get("confianca","baixa")
                cor  = "grn" if conf=="alta" else ("yel" if conf=="media" else "red")
                c1, c2 = st.columns([5,1])
                np_ = r.get("nome_produto") or r.get("modelo_digitado","—")
                lbl = f"{np_} · {', '.join(str(v) for v in r.get('variacoes',[]))} · {r.get('quantidade',1)} un"
                st.session_state[f"wpp_chk_{i}"] = c1.checkbox(
                    lbl, value=st.session_state.get(f"wpp_chk_{i}", bool(r.get("nome_produto"))),
                    key=f"wpp_chk_r_{i}")
                c2.markdown(_chip(conf.upper(), cor), unsafe_allow_html=True)

            ca, cb = st.columns(2)
            if ca.button("➕ Adicionar selecionados", type="primary", use_container_width=True, key="wpp_add"):
                added = 0
                for i, r in enumerate(res):
                    if not st.session_state.get(f"wpp_chk_{i}", False): continue
                    np_ = r.get("nome_produto")
                    if not np_ or not cache:
                        st.session_state.beta_ped.append({
                            "produto_nome": r.get("modelo_digitado", np_ or "—"),
                            "variacao_nome": ", ".join(str(v) for v in r.get("variacoes",[])),
                            "quantidade": int(r.get("quantidade",1)),
                            "fornecedor":"","valor_custo":"","_avulso":True})
                        added += 1; continue
                    prods_m = api.buscar_produtos(r.get("cod_interno") or np_, cache)
                    if prods_m:
                        p = prods_m[0]
                        for vr in (r.get("variacoes") or [""]):
                            vd_m = next((v.get("variacao",v) for v in p.get("variacoes",[])
                                         if str(vr).lower() in v.get("variacao",v).get("nome","").lower()), None)
                            entry = {"produto_id":p["id"],"produto_nome":p["nome"],
                                     "cod_interno":p.get("codigo_interno",""),
                                     "quantidade":int(r.get("quantidade",1)),
                                     "fornecedor":"","valor_custo":""}
                            if vd_m:
                                entry.update({"variacao_id":vd_m["id"],"variacao_nome":vd_m.get("nome",""),
                                              "variacao_cod":vd_m.get("codigo","")})
                            else:
                                entry["variacao_nome"] = str(vr)
                            st.session_state.beta_ped.append(entry); added += 1
                    else:
                        st.session_state.beta_ped.append({
                            "produto_nome":np_,"variacao_nome":", ".join(str(v) for v in r.get("variacoes",[])),
                            "quantidade":int(r.get("quantidade",1)),"fornecedor":"","valor_custo":"","_avulso":True})
                        added += 1
                if added:
                    st.session_state.pop("wpp_res",None); st.success(f"✅ {added} item(ns) adicionado(s)!"); st.rerun()
            if cb.button("✕ Descartar", use_container_width=True, key="wpp_clr"):
                st.session_state.pop("wpp_res",None); st.rerun()

    # ── Catálogo ──
    with tab_cat:
        if not cache:
            st.warning("Sincronize os produtos primeiro.")
        else:
            termo = st.text_input("🔍 Buscar produto", key="cat_busca",
                placeholder="Nome ou código…", label_visibility="collapsed")
            prods = api.buscar_produtos(termo, cache) if termo else []
            if prods:
                nomes = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in prods]
                sel   = st.selectbox("Produto", nomes, key="cat_sel", label_visibility="collapsed")
                prod  = prods[nomes.index(sel)]
                vars_ = [v.get("variacao",v) for v in prod.get("variacoes",[])]
                if vars_:
                    _qtds = {}
                    for vd in vars_:
                        vc1,vc2,vc3 = st.columns([3,1,1])
                        vc1.caption(f"**{vd.get('nome','')}** · `{vd.get('codigo','')}`")
                        ev = _safe_int(vd.get("estoque",0))
                        vc2.caption(f"{'🔴' if ev<=3 else '🟡' if ev<=10 else '🟢'} {ev} un")
                        _qtds[vd["id"]] = vc3.number_input("q",min_value=0,value=0,step=1,
                            key=f"cat_q_{vd['id']}",label_visibility="collapsed")
                    cf1,cf2 = st.columns(2)
                    forn  = cf1.text_input("Fornecedor", key="cat_forn")
                    custo = cf2.text_input("Custo unit. (R$)", key="cat_custo")
                    if st.button("➕ Adicionar", type="primary", use_container_width=True, key="cat_add"):
                        added_c = sum(1 for vd in vars_ if int(_qtds.get(vd["id"],0))>0 and
                            st.session_state.beta_ped.append({
                                "produto_id":prod["id"],"produto_nome":prod["nome"],
                                "cod_interno":prod.get("codigo_interno",""),
                                "variacao_id":vd["id"],"variacao_nome":vd.get("nome",""),
                                "variacao_cod":vd.get("codigo",""),
                                "quantidade":int(_qtds[vd["id"]]),"fornecedor":forn,"valor_custo":custo}) is None)
                        if added_c: st.success(f"✅ {added_c} variação(ões) adicionada(s)!"); st.rerun()
                        else: st.warning("Preencha a quantidade em pelo menos uma variação.")
            elif termo: st.info("Nenhum produto encontrado.")

    # ── Avulso ──
    with tab_avl:
        a1,a2 = st.columns([3,1])
        desc  = a1.text_input("Descrição", key="avl_desc", placeholder="Ex: Película Samsung A55")
        qtd_a = a2.number_input("Qtd", min_value=1, value=1, key="avl_qtd")
        b1,b2 = st.columns(2)
        fa = b1.text_input("Fornecedor", key="avl_forn")
        ca = b2.text_input("Custo unit. (R$)", key="avl_custo")
        if st.button("➕ Adicionar avulso", type="primary", use_container_width=True, key="avl_add"):
            if desc.strip():
                st.session_state.beta_ped.append({"produto_nome":desc.strip(),"variacao_nome":"",
                    "quantidade":int(qtd_a),"fornecedor":fa,"valor_custo":ca,"_avulso":True})
                st.success("✅ Adicionado!"); st.rerun()
            else: st.warning("Digite uma descrição.")

    # ── Listas ──
    with tab_lst:
        listas = api.listar_listas_salvas("pedido")
        if listas:
            for lst in listas[:15]:
                lc1,lc2 = st.columns([5,1])
                lnm = lst.get("nome","—"); lqt = len(lst.get("itens",[])); ldt = (lst.get("criado_em","") or "")[:10]
                lc1.markdown(f'<div class="li"><div class="li-name">{lnm}</div>'
                             f'<div class="li-sub">{lqt} itens · {ldt}</div></div>', unsafe_allow_html=True)
                if lc2.button("Abrir", key=f"lst_op_{lst['_arquivo']}", use_container_width=True):
                    st.session_state.beta_ped = list(lst.get("itens",[])); st.session_state["beta_ped_arq"] = lst["_arquivo"]; st.rerun()
        else: _empty_state("📂","Nenhuma lista de pedido salva","Salve um pedido abaixo")
        st.divider()
        nn = st.text_input("Nome para salvar", key="ped_novo_nome", placeholder="Ex: Pedido 15/06")
        if st.button("💾 Salvar pedido como lista", use_container_width=True, key="ped_salvar"):
            if not itens: st.warning("Pedido vazio.")
            elif not nn.strip(): st.warning("Digite um nome.")
            else: api.salvar_lista(nn.strip(),"pedido",itens); st.success(f"✅ Salvo!"); st.rerun()

    # Pedido atual
    if itens:
        st.divider()
        tq = sum(_safe_int(it.get("quantidade",0)) for it in itens)
        try: tv = sum(float(str(it.get("valor_custo","0") or "0").replace(",","."))*_safe_int(it.get("quantidade",1)) for it in itens)
        except: tv = 0
        m1,m2,m3 = st.columns(3)
        m1.metric("Itens",len(itens)); m2.metric("Unidades",tq)
        if tv>0: m3.metric("Custo estimado",f"R$ {tv:,.2f}")
        _sec("Itens do pedido")
        for i, it in enumerate(list(itens)):
            nome_v = it.get("variacao_nome","")
            linha  = it.get("produto_nome","") + (f" / {nome_v}" if nome_v else "")
            pc1,pc2,pc3 = st.columns([5,1,1])
            forn_txt = f" · {it['fornecedor']}" if it.get("fornecedor") else ""
            avulso_txt = " " + _chip("avulso","gray") if it.get("_avulso") else ""
            pc1.markdown(f'<div class="li"><div class="li-name">{linha[:52]}{avulso_txt}</div>'
                         f'<div class="li-sub">{it.get("valor_custo","")}{forn_txt}</div></div>',
                         unsafe_allow_html=True)
            nq = pc2.number_input("q",min_value=1,value=max(1,_safe_int(it.get("quantidade",1))),
                                   step=1,label_visibility="collapsed",key=f"ped_q_{i}")
            if nq != it.get("quantidade"): st.session_state.beta_ped[i]["quantidade"] = nq
            if pc3.button("🗑",key=f"ped_del_{i}",use_container_width=True):
                st.session_state.beta_ped.pop(i); st.rerun()

        st.divider(); _sec("Exportar")
        ea,eb,ec = st.columns(3)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as wr:
            pd.DataFrame([{"Produto":it.get("produto_nome",""),"Variação":it.get("variacao_nome",""),
                "Qtd":it.get("quantidade",0),"Fornecedor":it.get("fornecedor",""),
                "Custo":it.get("valor_custo","")} for it in itens]).to_excel(wr, index=False)
        buf.seek(0)
        ea.download_button("📄 Excel", buf, f"pedido_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        if eb.button("📋 Copiar texto", use_container_width=True, key="ped_txt"):
            linhas = [f"PEDIDO — {date.today()}","="*42]
            for it in itens:
                v = f" / {it['variacao_nome']}" if it.get("variacao_nome") else ""
                linhas.append(f"{it.get('produto_nome','')}{v} — {it.get('quantidade',0)} un")
            _copiar_html("\n".join(linhas))
        if ec.button("🗑️ Limpar", use_container_width=True, key="ped_lmp"):
            st.session_state.beta_ped = []; st.session_state.pop("beta_ped_arq",None); st.rerun()

        with st.expander("📤 Registrar Compra no GestãoClick"):
            itens_cad = [it for it in itens if it.get("produto_id") and it.get("variacao_id")]
            st.info(f"**{len(itens_cad)}** cadastrado(s) · **{len(itens)-len(itens_cad)}** avulso(s) ignorado(s).")
            rg1,rg2 = st.columns(2)
            forn_gc = rg1.text_input("Buscar fornecedor",key="gc_forn")
            data_gc = rg2.date_input("Data",value=date.today(),key="gc_data")
            obs_gc  = st.text_input("Observações",key="gc_obs")
            if st.button("🔍 Buscar fornecedor",use_container_width=True,key="gc_buscar"):
                with st.spinner("Buscando…"):
                    try: st.session_state["gc_forns"] = api.buscar_fornecedores(forn_gc, limite=20)
                    except Exception as ex: st.error(f"Erro: {ex}")
            forns = st.session_state.get("gc_forns",[])
            if forns:
                opts = {f"{f.get('razao_social') or f.get('nome','—')} ({f.get('cnpj','')})":f["id"] for f in forns}
                fsel = st.selectbox("Fornecedor",list(opts.keys()),key="gc_fsel")
                fid  = opts[fsel]
                if "gc_sits" not in st.session_state:
                    try:
                        sits = api.buscar_situacoes_compras()
                        st.session_state["gc_sits"] = {s.get("nome","—"):s.get("id","1") for s in sits
                            if isinstance(s,dict) and s.get("nome")} or {"Aguardando recebimento":"1"}
                    except: st.session_state["gc_sits"] = {"Aguardando recebimento":"1"}
                sit_sel = st.selectbox("Situação",list(st.session_state["gc_sits"].keys()),key="gc_sit")
                sit_id  = st.session_state["gc_sits"][sit_sel]
                if st.button("✅ Confirmar e registrar",type="primary",use_container_width=True,key="gc_ok"):
                    if not itens_cad: st.error("Nenhum item cadastrado.")
                    else:
                        with st.spinner("Enviando…"):
                            try:
                                api.registrar_compra_gestaoclick(itens_cad,fid,data_gc,sit_id,obs_gc,loja_id)
                                st.success("✅ Compra registrada!"); st.session_state.pop("gc_forns",None)
                            except Exception as ex: st.error(f"Erro: {ex}")
    else:
        _empty_state("🛒","Pedido vazio","Use as abas acima para adicionar produtos")


# ══════════════════════════════════════════════════════════════════
# ESTOQUE
# ══════════════════════════════════════════════════════════════════

def _estoque(cache, loja_id):
    _pg_header("📦 Estoque", "Entrada, acerto de estoque e etiquetas")
    if not cache:
        _empty_state("📦","Cache vazio","Vá em Configurações → Sincronização"); return

    all_vars = [(p, v.get("variacao",v)) for p in cache.get("produtos",[]) for v in p.get("variacoes",[])]
    def _e(vd): return _safe_int(vd.get("estoque",0))
    n_t=len(all_vars); n_c=sum(1 for _,vd in all_vars if _e(vd)<=3)
    n_b=sum(1 for _,vd in all_vars if 3<_e(vd)<=10); n_ok=n_t-n_c-n_b

    s1,s2,s3,s4 = st.columns(4)
    with s1: _kpi(n_t,"Variações","kpi-ind","📦")
    with s2: _kpi(n_c,"Críticos","kpi-red" if n_c else "","🔴")
    with s3: _kpi(n_b,"Baixos","kpi-amb" if n_b else "","🟡")
    with s4: _kpi(n_ok,"Saudáveis","kpi-grn","🟢")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    modo = st.radio("Modo",["📥 Entrada","📊 Acerto","🏷️ Etiquetas","📋 Visão geral"],
                    horizontal=True,key="est_modo",label_visibility="collapsed")
    st.divider()

    if modo == "📋 Visão geral":
        rows_c = []
        for p,vd in all_vars:
            est = _e(vd)
            if est<=10:
                rows_c.append({"Status":"🔴 Crítico" if est<=3 else "🟡 Baixo",
                    "Produto":p.get("nome","")[:30],"Variação":vd.get("nome","")[:25],
                    "Cód.":vd.get("codigo",""),"Estoque":est})
        if rows_c:
            df_c = pd.DataFrame(rows_c).sort_values("Estoque")
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            bars = "".join(_stock_bar_html(f"{r['Produto']} / {r['Variação']}",r["Estoque"]) for r in rows_c[:15])
            st.markdown(f'<div class="card" style="padding:18px 20px">{bars}</div>', unsafe_allow_html=True)
        else: _alerta("Todos os itens com estoque saudável!",tipo="grn")
        return

    termo = st.text_input("🔍 Buscar produto",key="est_busca",placeholder="Nome ou código interno")
    prods = api.buscar_produtos(termo,cache) if termo else []
    if not prods:
        if termo: st.info("Nenhum produto encontrado.")
        if modo!="🏷️ Etiquetas": return

    prod=None; vars_=[]
    if prods:
        nomes = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in prods]
        sel   = st.selectbox("Produto",nomes,key="est_sel",label_visibility="collapsed")
        prod  = prods[nomes.index(sel)]
        vars_ = [v.get("variacao",v) for v in prod.get("variacoes",[])]
        if not vars_: st.warning("Produto sem variações."); return

    if modo in ("📥 Entrada","📊 Acerto") and prod:
        modo_api = "soma" if "Entrada" in modo else "set"
        qtds = {}
        for vd in vars_:
            v1,v2,v3 = st.columns([3,1,1])
            ea = _e(vd)
            v1.markdown(f'<div style="font-size:.83rem;font-weight:600">{vd.get("nome","")}</div>'
                        f'<div style="font-size:.7rem;color:#9ca3af">`{vd.get("codigo","")}`</div>',
                        unsafe_allow_html=True)
            v2.metric("Atual",f"{'🔴' if ea<=3 else '🟡' if ea<=10 else '🟢'} {ea}")
            qtds[vd["id"]] = v3.number_input("q",min_value=0,value=0,step=1,
                key=f"est_q_{vd['id']}",label_visibility="collapsed")
        if st.button(f"✅ Aplicar {modo}",type="primary",use_container_width=True,key="est_ok"):
            ok_c,errs = 0,[]
            for vd in vars_:
                q = int(qtds.get(vd["id"],0))
                if q>0:
                    try: api.atualizar_estoque_variacao(prod["id"],vd["id"],q,loja_id=loja_id,modo=modo_api); ok_c+=1
                    except Exception as ex: errs.append(f"{vd.get('nome','')}: {ex}")
            if ok_c: st.success(f"✅ {ok_c} variação(ões) atualizada(s)!"); _alertas_estoque.clear()
            for e in errs: st.error(e)

    if modo=="🏷️ Etiquetas":
        if "beta_etiq" not in st.session_state: st.session_state.beta_etiq = []
        if prod and vars_:
            qtds_e = {}
            for vd in vars_:
                e1,e2 = st.columns([4,1])
                e1.write(f"{vd.get('nome','')} · `{vd.get('codigo','')}`")
                qtds_e[vd["id"]] = e2.number_input("Qtd",min_value=0,value=0,step=1,
                    key=f"etiq_q_{vd['id']}",label_visibility="collapsed")
            if st.button("➕ Adicionar à lista",use_container_width=True,key="etiq_add"):
                ae=0
                for vd in vars_:
                    q=int(qtds_e.get(vd["id"],0))
                    if q>0:
                        st.session_state.beta_etiq.append({"variacao_id":vd["id"],
                            "produto_nome":prod["nome"],"variacao_nome":vd.get("nome",""),
                            "variacao_cod":vd.get("codigo",""),"quantidade":q}); ae+=1
                if ae: st.success(f"✅ {ae} adicionado(s)!"); st.rerun()
        ei = st.session_state.get("beta_etiq",[])
        if ei:
            _sec(f"Lista — {len(ei)} item(ns)")
            st.dataframe(pd.DataFrame(ei)[["produto_nome","variacao_nome","quantidade"]].rename(
                columns={"produto_nome":"Produto","variacao_nome":"Variação","quantidade":"Qtd"}),
                use_container_width=True, hide_index=True)
            url_et = api.gerar_url_etiquetas([{"variacao_id":it["variacao_id"],"quantidade":it["quantidade"]}
                for it in ei if it.get("variacao_id")])
            if url_et: st.link_button("🏷️ Gerar no GestãoClick",url_et,use_container_width=True)
            if st.button("🗑️ Limpar",use_container_width=True,key="etiq_clr"):
                st.session_state.beta_etiq=[]; st.rerun()
        else: _empty_state("🏷️","Lista vazia","Busque um produto e adicione acima")


# ══════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════

def _clientes():
    _pg_header("👥 Clientes","Cadastro e gestão de clientes")
    with st.expander("➕ Novo cliente"):
        nc1,nc2 = st.columns(2)
        ncn = nc1.text_input("Nome / Razão Social *",key="cli_nn")
        ncd = nc2.text_input("CPF / CNPJ",key="cli_nd")
        nc3,nc4 = st.columns(2)
        nct = nc3.text_input("Telefone",key="cli_nt"); nce = nc4.text_input("E-mail",key="cli_ne")
        ncc = st.text_input("Cidade",key="cli_nc"); nco = st.text_area("Observações",key="cli_no",height=68)
        if st.button("✅ Cadastrar",type="primary",use_container_width=True,key="cli_new_ok"):
            if not ncn.strip(): st.warning("Nome obrigatório.")
            else:
                with st.spinner("Salvando…"):
                    try:
                        api.criar_cliente({"nome":ncn,"cpf_cnpj":ncd,"telefone":nct,"email":nce,"cidade":ncc,"observacoes":nco})
                        st.success(f"✅ Cliente '{ncn}' cadastrado!"); st.session_state.pop("cli_res",None)
                    except Exception as ex: st.error(f"Erro: {ex}")

    _sec("Buscar clientes")
    sc1,sc2 = st.columns([4,1])
    termo_c = sc1.text_input("🔍",key="cli_t",placeholder="Nome ou CPF/CNPJ…",label_visibility="collapsed")
    if sc2.button("Buscar",use_container_width=True,key="cli_buscar"):
        with st.spinner("…"):
            try: st.session_state["cli_res"] = api.buscar_clientes(termo_c, limite=30)
            except Exception as ex: st.error(f"Erro: {ex}"); st.session_state["cli_res"]=[]

    clientes = st.session_state.get("cli_res")
    if clientes is None and not termo_c:
        try: clientes = api.buscar_clientes("", limite=20); st.session_state["cli_res"] = clientes
        except: clientes = []

    for ci, c in enumerate(clientes or []):
        nome_c = c.get("nome") or c.get("razao_social") or "—"
        doc    = c.get("cpf") or c.get("cnpj") or ""
        tel    = c.get("telefone") or c.get("celular") or ""
        with st.expander(f"👤 {nome_c}" + (f"  ·  {doc}" if doc else "")):
            d1,d2 = st.columns(2)
            d1.write(f"**Tel.:** {tel or '—'}"); d1.write(f"**E-mail:** {c.get('email','—')}")
            d2.write(f"**Cidade:** {c.get('cidade','—')}"); d2.write(f"**Estado:** {c.get('estado','—')}")
            _sec("Editar")
            e1,e2 = st.columns(2)
            en = e1.text_input("Nome",value=nome_c,key=f"cli_en_{ci}")
            ed = e2.text_input("CPF/CNPJ",value=doc,key=f"cli_ed_{ci}")
            e3,e4 = st.columns(2)
            et = e3.text_input("Telefone",value=tel,key=f"cli_et_{ci}")
            ee = e4.text_input("E-mail",value=c.get("email",""),key=f"cli_ee_{ci}")
            eo = st.text_area("Obs.",value=c.get("observacoes",""),key=f"cli_eo_{ci}",height=60)
            cs,cd = st.columns(2)
            if cs.button("💾 Salvar",use_container_width=True,key=f"cli_sv_{ci}"):
                with st.spinner("…"):
                    try:
                        api.atualizar_cliente(c["id"],{"nome":en,"cpf_cnpj":ed,"telefone":et,"email":ee,"observacoes":eo})
                        st.success("✅ Atualizado!"); st.session_state.pop("cli_res",None); st.rerun()
                    except Exception as ex: st.error(f"Erro: {ex}")
            if cd.button("🗑️ Excluir",use_container_width=True,key=f"cli_dl_{ci}"):
                with st.spinner("…"):
                    try: api.excluir_cliente(c["id"]); st.warning("Excluído."); st.session_state.pop("cli_res",None); st.rerun()
                    except Exception as ex: st.error(f"Erro: {ex}")

    if not (clientes or []):
        _empty_state("👥","Nenhum cliente","Use a busca ou cadastre um novo acima")


# ══════════════════════════════════════════════════════════════════
# FORNECEDORES
# ══════════════════════════════════════════════════════════════════

def _fornecedores():
    _pg_header("🏭 Fornecedores","Cadastro e gestão de fornecedores")
    with st.expander("➕ Novo fornecedor"):
        nf1,nf2 = st.columns(2)
        nfn = nf1.text_input("Razão Social *",key="forn_nn"); nfc = nf2.text_input("CNPJ",key="forn_nc")
        nf3,nf4 = st.columns(2)
        nft = nf3.text_input("Telefone",key="forn_nt"); nfe = nf4.text_input("E-mail",key="forn_ne")
        nfo = st.text_area("Observações",key="forn_no",height=68)
        if st.button("✅ Cadastrar",type="primary",use_container_width=True,key="forn_new_ok"):
            if not nfn.strip(): st.warning("Razão Social obrigatória.")
            else:
                with st.spinner("Salvando…"):
                    try:
                        api.criar_fornecedor({"razao_social":nfn,"cnpj":nfc,"telefone":nft,"email":nfe,"observacoes":nfo})
                        st.success(f"✅ '{nfn}' cadastrado!"); st.session_state.pop("forn_res",None)
                    except Exception as ex: st.error(f"Erro: {ex}")

    _sec("Buscar fornecedores")
    sf1,sf2 = st.columns([4,1])
    termo_f = sf1.text_input("🔍",key="forn_t",placeholder="Nome ou CNPJ…",label_visibility="collapsed")
    if sf2.button("Buscar",use_container_width=True,key="forn_buscar"):
        with st.spinner("…"):
            try: st.session_state["forn_res"] = api.buscar_fornecedores(termo_f,limite=30)
            except Exception as ex: st.error(f"Erro: {ex}"); st.session_state["forn_res"]=[]

    forn_list = st.session_state.get("forn_res")
    if forn_list is None and not termo_f:
        try: forn_list = api.buscar_fornecedores("",limite=20); st.session_state["forn_res"]=forn_list
        except: forn_list=[]

    for fi, f in enumerate(forn_list or []):
        nome_f = f.get("razao_social") or f.get("nome") or "—"
        cnpj_f = f.get("cnpj") or ""
        tel_f  = f.get("telefone") or ""
        with st.expander(f"🏭 {nome_f}" + (f"  ·  {cnpj_f}" if cnpj_f else "")):
            d1,d2 = st.columns(2)
            d1.write(f"**Tel.:** {tel_f or '—'}"); d1.write(f"**E-mail:** {f.get('email','—')}")
            d2.write(f"**Obs.:** {(f.get('observacoes') or '')[:60]}")
            _sec("Editar")
            ef1,ef2 = st.columns(2)
            efn = ef1.text_input("Razão Social",value=nome_f,key=f"forn_en_{fi}")
            efc = ef2.text_input("CNPJ",value=cnpj_f,key=f"forn_ec_{fi}")
            ef3,ef4 = st.columns(2)
            eft = ef3.text_input("Telefone",value=tel_f,key=f"forn_et_{fi}")
            efe = ef4.text_input("E-mail",value=f.get("email",""),key=f"forn_ee_{fi}")
            efo = st.text_area("Obs.",value=f.get("observacoes",""),key=f"forn_eo_{fi}",height=60)
            cs,cd = st.columns(2)
            if cs.button("💾 Salvar",use_container_width=True,key=f"forn_sv_{fi}"):
                with st.spinner("…"):
                    try:
                        api.atualizar_fornecedor(f["id"],{"razao_social":efn,"cnpj":efc,"telefone":eft,"email":efe,"observacoes":efo})
                        st.success("✅ Atualizado!"); st.session_state.pop("forn_res",None); st.rerun()
                    except Exception as ex: st.error(f"Erro: {ex}")
            if cd.button("🗑️ Excluir",use_container_width=True,key=f"forn_dl_{fi}"):
                with st.spinner("…"):
                    try: api.excluir_fornecedor(f["id"]); st.warning("Excluído."); st.session_state.pop("forn_res",None); st.rerun()
                    except Exception as ex: st.error(f"Erro: {ex}")

    if not (forn_list or []):
        _empty_state("🏭","Nenhum fornecedor","Use a busca ou cadastre acima")


# ══════════════════════════════════════════════════════════════════
# COMPRAS
# ══════════════════════════════════════════════════════════════════

def _compras(loja_id):
    _pg_header("🧾 Histórico de Compras","Consulte e detalhe pedidos de compra")
    c1,c2,c3 = st.columns([1,1,1])
    d_ini = c1.date_input("De",value=date.today()-timedelta(days=30),key="cmp_ini")
    d_fim = c2.date_input("Até",value=date.today(),key="cmp_fim")
    if c3.button("🔄 Carregar",type="primary",use_container_width=True,key="cmp_load"):
        st.session_state.pop("cmp_data",None)

    if "cmp_data" not in st.session_state:
        with st.spinner("Carregando…"):
            try:
                res = api.buscar_compras(str(d_ini),str(d_fim),loja_id=loja_id,limite=100)
                st.session_state["cmp_data"] = res if isinstance(res,list) else []
            except Exception as ex: st.error(f"Erro: {ex}"); st.session_state["cmp_data"]=[]

    compras = st.session_state.get("cmp_data",[])
    if compras:
        tv = sum(float(c.get("valor_total") or 0) for c in compras)
        np_ = sum(1 for c in compras if str(c.get("situacao_id","")) not in ("2","3","4"))
        mk1,mk2,mk3 = st.columns(3)
        with mk1: _kpi(len(compras),"Compras","kpi-ind","🧾")
        with mk2: _kpi(f"R$ {tv:,.2f}","Total","kpi-grn","💰")
        with mk3: _kpi(np_,"Pendentes","kpi-amb" if np_ else "","⏳")
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

        for ci,cmp in enumerate(compras):
            num  = cmp.get("codigo") or cmp.get("numero") or cmp.get("id","")
            forn = (cmp.get("fornecedor_nome") or cmp.get("fornecedor") or "—")[:28]
            data_c = (cmp.get("data_emissao") or "")[:10]
            val  = float(cmp.get("valor_total") or 0)
            sit  = cmp.get("situacao") or cmp.get("status") or "—"
            sit_id = str(cmp.get("situacao_id",""))
            sit_cor = "grn" if sit_id in ("3","4") else ("yel" if sit_id=="2" else "gray")
            with st.expander(f"#{num} · {forn} · {data_c} · R$ {val:,.2f}"):
                d1,d2 = st.columns(2)
                d1.write(f"**Fornecedor:** {forn}"); d1.write(f"**Data:** {data_c}")
                d2.write(f"**Valor:** R$ {val:,.2f}")
                d2.markdown(f"**Situação:** {_chip(sit,sit_cor)}",unsafe_allow_html=True)
                if st.button("📋 Ver itens",key=f"cmp_det_{ci}"):
                    with st.spinner("…"):
                        try:
                            det = api.buscar_compra(cmp["id"],loja_id)
                            pl  = det.get("produtos",det.get("itens",[]))
                            if pl:
                                st.dataframe(pd.DataFrame([{
                                    "Produto":(p.get("nome_produto") or p.get("produto_nome",""))[:28],
                                    "Variação":p.get("variacao_nome",""),
                                    "Qtd":p.get("quantidade",""),
                                    "Custo":f"R$ {float(p.get('valor_custo') or 0):,.2f}"}
                                    for p in pl]),use_container_width=True,hide_index=True)
                            else: st.info("Nenhum item encontrado.")
                        except Exception as ex: st.error(f"Erro: {ex}")
    else:
        _empty_state("🧾","Nenhuma compra encontrada","Ajuste o período e clique em Carregar")


# ══════════════════════════════════════════════════════════════════
# FINANCEIRO
# ══════════════════════════════════════════════════════════════════

def _financeiro():
    _pg_header("💰 Financeiro","Contas a receber e a pagar")
    tab_r,tab_p = st.tabs(["💚 A Receber","❤️ A Pagar"])

    def _render_fin(tipo):
        key_d = f"fin2_{tipo}"
        f1,f2,f3 = st.columns([1,1,1])
        ini = f1.date_input("De",value=date.today()-timedelta(days=30),key=f"{tipo}_ini")
        fim = f2.date_input("Até",value=date.today()+timedelta(days=30),key=f"{tipo}_fim")
        if f3.button("🔄 Carregar",use_container_width=True,key=f"{tipo}_btn"):
            st.session_state.pop(key_d,None)
        if key_d not in st.session_state:
            with st.spinner("Carregando…"):
                try:
                    fn = api.buscar_contas_receber if tipo=="rec" else api.buscar_contas_pagar
                    dados = fn(str(ini),str(fim),limite=300)
                    st.session_state[key_d] = dados if isinstance(dados,list) else []
                except Exception as ex: st.error(f"Erro: {ex}"); st.session_state[key_d]=[]
        contas = st.session_state.get(key_d,[])
        if not isinstance(contas,list): contas=[]
        total = sum(float(c.get("valor") or c.get("valor_total") or 0) for c in contas)
        pago  = sum(float(c.get("valor_pago") or 0) for c in contas)
        aberto= total-pago
        k1,k2,k3 = st.columns(3)
        cor = "kpi-grn" if tipo=="rec" else "kpi-red"
        with k1: _kpi(f"R$ {total:,.2f}","Total",cor,"💰")
        with k2: _kpi(f"R$ {pago:,.2f}","Quitado","kpi-grn","✅")
        with k3: _kpi(f"R$ {aberto:,.2f}","Em aberto","kpi-amb" if aberto else "","⏳")
        if contas:
            by_d = {}
            for c in contas:
                venc = (c.get("data_vencimento") or "")[:10]
                v    = float(c.get("valor") or c.get("valor_total") or 0)
                if venc: by_d[venc] = by_d.get(venc,0)+v
            if len(by_d)>1:
                st.bar_chart(pd.DataFrame({"Valor":by_d}).sort_index())
            rows=[]
            for c in contas:
                pago_c = str(c.get("situacao_id","")) in ("2","3") or str(c.get("pago",""))=="1"
                rows.append({"Status":"✅ Quitado" if pago_c else "⏳ Aberto",
                    "Descrição":(c.get("descricao") or c.get("historico",""))[:30],
                    "Parte":(c.get("cliente_nome") or c.get("fornecedor_nome") or "")[:20],
                    "Vencto":(c.get("data_vencimento") or "")[:10],
                    "Valor":f"R$ {float(c.get('valor') or c.get('valor_total') or 0):,.2f}"})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            buf_f=io.BytesIO()
            with pd.ExcelWriter(buf_f,engine="openpyxl") as wr: pd.DataFrame(rows).to_excel(wr,index=False)
            buf_f.seek(0)
            st.download_button("📄 Exportar Excel",buf_f,f"fin_{tipo}_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,key=f"fin_xls_{tipo}")
        else: _empty_state("💰","Sem lançamentos no período","Ajuste as datas e clique em Carregar")

    with tab_r: _render_fin("rec")
    with tab_p: _render_fin("pag")


# ══════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ══════════════════════════════════════════════════════════════════

def _relatorios(cache, loja_id):
    _pg_header("📊 Relatórios","Vendas, estoque e resultado")
    tab_v,tab_e,tab_r = st.tabs(["📈 Vendas","📦 Estoque","💰 Resultado"])

    with tab_v:
        rv1,rv2,rv3 = st.columns([1,1,1])
        d_ini = rv1.date_input("De",value=date.today()-timedelta(days=30),key="rv_ini")
        d_fim = rv2.date_input("Até",value=date.today(),key="rv_fim")
        if rv3.button("📊 Gerar",type="primary",use_container_width=True,key="rv_btn"):
            with st.spinner("Carregando…"):
                try:
                    vendas = api.buscar_vendas(str(d_ini),str(d_fim),loja_id=loja_id,limite=500)
                    if not isinstance(vendas,list): vendas=[]
                    if vendas:
                        tv=sum(float(v.get("valor_total") or 0) for v in vendas)
                        k1,k2,k3=st.columns(3)
                        with k1: _kpi(len(vendas),"Pedidos","kpi-ind","🛒")
                        with k2: _kpi(f"R$ {tv:,.2f}","Total","kpi-grn","💰")
                        with k3: _kpi(f"R$ {tv/len(vendas):,.2f}","Ticket médio","","📊")
                        rows_v=[{"Data":(v.get("data_emissao","") or "")[:10],"Nº":v.get("numero",""),
                            "Cliente":(v.get("cliente_nome","") or "")[:20],
                            "Valor":float(v.get("valor_total") or 0),"Status":v.get("status","")} for v in vendas]
                        df_v=pd.DataFrame(rows_v)
                        st.bar_chart(df_v.groupby("Data")["Valor"].sum())
                        st.dataframe(df_v,use_container_width=True,hide_index=True)
                    else: _empty_state("📈","Nenhuma venda no período")
                except Exception as ex: st.error(f"Erro: {ex}")

    with tab_e:
        if not cache: _empty_state("📦","Cache vazio","Sincronize em Configurações")
        else:
            rows_e=[]
            for p in cache.get("produtos",[]):
                for v in p.get("variacoes",[]):
                    vd=v.get("variacao",v); est=_safe_int(vd.get("estoque",0))
                    rows_e.append({"Status":"🔴" if est<=3 else "🟡" if est<=10 else "🟢",
                        "Produto":p.get("nome","")[:28],"Variação":vd.get("nome","")[:22],
                        "Cód.":vd.get("codigo",""),"Estoque":est})
            df_e=pd.DataFrame(rows_e).sort_values("Estoque")
            _sec(f"{len(df_e)} variações · {df_e['Estoque'].sum():,} unidades")
            filtro=st.selectbox("Filtrar",["Todos","🔴 Crítico","🟡 Baixo","🟢 Saudável"],key="rel_ef")
            if "Crítico" in filtro: df_e=df_e[df_e["Estoque"]<=3]
            elif "Baixo" in filtro: df_e=df_e[df_e["Estoque"]<=10]
            elif "Saudável" in filtro: df_e=df_e[df_e["Estoque"]>10]
            st.dataframe(df_e,use_container_width=True,hide_index=True)
            buf_e=io.BytesIO()
            with pd.ExcelWriter(buf_e,engine="openpyxl") as wr: df_e.to_excel(wr,index=False)
            buf_e.seek(0)
            st.download_button("📄 Excel",buf_e,f"estoque_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

    with tab_r:
        rf1,rf2,rf3=st.columns([1,1,1])
        d_ri=rf1.date_input("De",value=date.today()-timedelta(days=30),key="rf_ini")
        d_rf=rf2.date_input("Até",value=date.today(),key="rf_fim")
        if rf3.button("📊 Gerar",type="primary",use_container_width=True,key="rf_btn"):
            with st.spinner("…"):
                try:
                    rec_f=api.buscar_contas_receber(str(d_ri),str(d_rf),limite=500)
                    pag_f=api.buscar_contas_pagar(str(d_ri),str(d_rf),limite=500)
                    if not isinstance(rec_f,list): rec_f=[]
                    if not isinstance(pag_f,list): pag_f=[]
                    tr_f=sum(float(r.get("valor") or r.get("valor_total") or 0) for r in rec_f)
                    tp_f=sum(float(p.get("valor") or p.get("valor_total") or 0) for p in pag_f)
                    res_f=tr_f-tp_f
                    ka,kb,kc=st.columns(3)
                    with ka: _kpi(f"R$ {tr_f:,.2f}","Receitas","kpi-grn","💚")
                    with kb: _kpi(f"R$ {tp_f:,.2f}","Despesas","kpi-red","❤️")
                    with kc: _kpi(f"R$ {res_f:,.2f}","Resultado","kpi-grn" if res_f>=0 else "kpi-red","⚡")
                    st.bar_chart(pd.DataFrame({"Valor":{"Receitas":tr_f,"Despesas":tp_f,"Resultado":max(0,res_f)}}))
                    if tr_f>0:
                        pct=res_f/tr_f*100
                        st.markdown(f'<div style="font-size:.8rem;color:#6b7280;margin-top:8px">'
                            f'Margem: <b style="color:{"#059669" if pct>=0 else "#dc2626"}">{pct:.1f}%</b></div>',
                            unsafe_allow_html=True)
                except Exception as ex: st.error(f"Erro: {ex}")


# ══════════════════════════════════════════════════════════════════
# LISTAS
# ══════════════════════════════════════════════════════════════════

def _listas():
    _pg_header("📋 Listas Salvas","Gerencie todas as listas do sistema")
    tipos=[None,"pedido","recebimento","conferencia","outro"]
    tabs_l=st.tabs(["🗂️ Todas","🛒 Pedido","📥 Recebimento","✅ Conferência","📌 Outro"])
    for tab_l,tipo in zip(tabs_l,tipos):
        with tab_l:
            listas=api.listar_listas_salvas(tipo)
            if not listas: _empty_state("📋","Nenhuma lista","Crie na aba Pedidos"); continue
            for lst in listas:
                arq=lst.get("_arquivo",""); lnm=lst.get("nome",arq)
                lqt=len(lst.get("itens",[])); ldt=(lst.get("criado_em","") or "")[:10]
                with st.expander(f"📄 {lnm} · {lqt} itens · {ldt}"):
                    itens_l=lst.get("itens",[])
                    if itens_l:
                        st.dataframe(pd.DataFrame([{"Produto":it.get("produto_nome",""),
                            "Variação":it.get("variacao_nome",""),"Qtd":it.get("quantidade","")}
                            for it in itens_l[:50]]),use_container_width=True,hide_index=True)
                        if len(itens_l)>50: st.caption(f"… e mais {len(itens_l)-50} itens")
                    xa,xb,xc=st.columns(3)
                    if xa.button("📋 Copiar",key=f"ll_cp_{arq}",use_container_width=True):
                        linhas=[f"LISTA: {lnm}","="*36]
                        for it in itens_l:
                            v=f" / {it['variacao_nome']}" if it.get("variacao_nome") else ""
                            linhas.append(f"{it.get('produto_nome','')}{v} — {it.get('quantidade',0)} un")
                        _copiar_html("\n".join(linhas))
                    if itens_l:
                        buf_l=io.BytesIO()
                        with pd.ExcelWriter(buf_l,engine="openpyxl") as wr:
                            pd.DataFrame([{"Produto":it.get("produto_nome",""),"Variação":it.get("variacao_nome",""),
                                "Qtd":it.get("quantidade","")} for it in itens_l]).to_excel(wr,index=False)
                        buf_l.seek(0)
                        xb.download_button("📄 Excel",buf_l,f"{arq}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,key=f"ll_xl_{arq}")
                    if xc.button("🗑️ Excluir",key=f"ll_dl_{arq}",use_container_width=True):
                        try: api.excluir_lista(arq); st.warning("Excluída."); st.rerun()
                        except Exception as ex: st.error(f"Erro: {ex}")


# ══════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════

def _config(cache, loja_id, is_adm):
    _pg_header("⚙️ Configurações","Sincronização, lojas e versão")
    tabs_c=["🔄 Sincronização","🏪 Loja ativa","🔀 Versão"]
    if is_adm: tabs_c.append("👥 Usuários")
    tab_s,tab_l,tab_v,*tab_u_l = st.tabs(tabs_c)
    tab_u = tab_u_l[0] if tab_u_l else None

    with tab_s:
        if cache:
            sync=(cache.get("sincronizado_em","") or "")[:16].replace("T"," às ")
            _alerta(f"Cache: {cache.get('total',0):,} produtos · {cache.get('loja_nome','—')} · {sync}",tipo="grn")
        else: _alerta("Nenhum cache — sincronize para começar.",tipo="yel")
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
        if st.button("🔄 Sincronizar Todas as Lojas",type="primary",use_container_width=True,key="sync_all"):
            bar=st.progress(0,text="Iniciando…"); errs=[]
            for idx,(lid,lnm) in enumerate(api.LOJAS.items()):
                def _p(pag,tot,_n=lnm,_i=idx,_T=len(api.LOJAS)):
                    bar.progress((_i+pag/max(tot,1))/_T,text=f"{_n}: pág {pag}/{tot}")
                try: api.sincronizar_produtos(loja_id=lid,progress_callback=_p)
                except Exception as ex: errs.append(f"{lnm}: {ex}")
            _alertas_estoque.clear()
            if errs:
                for e in errs: st.error(e)
            else: st.success("✅ Todas as lojas sincronizadas!"); st.rerun()

    with tab_l:
        opts={v:k for k,v in api.LOJAS.items()}
        atual=api.LOJAS.get(str(loja_id),list(api.LOJAS.values())[0])
        nova=st.selectbox("Loja",list(opts.keys()),
                          index=list(opts.keys()).index(atual) if atual in opts else 0,key="cfg_lj")
        if st.button("✅ Trocar loja",use_container_width=True,key="cfg_lj_ok"):
            st.session_state["loja_ativa_id"]=opts[nova]
            st.session_state["loja_ativa_nome"]=nova; st.rerun()

    with tab_v:
        st.markdown("""<div class="card">
          <div style="font-size:.95rem;font-weight:700;margin-bottom:10px">🚀 Você está no Beta</div>
          <div style="font-size:.78rem;color:#6b7280;line-height:1.7">
            ✦ Sidebar de navegação — padrão SaaS moderno<br>
            ✦ Dashboard com gráficos e alertas visuais<br>
            ✦ Clientes e Fornecedores com CRUD completo<br>
            ✦ Histórico de compras com detalhamento<br>
            ✦ Gerenciador de listas aprimorado<br>
            ✦ Usa os mesmos dados do Classic</div></div>""",unsafe_allow_html=True)
        if st.button("← Voltar para o Classic",use_container_width=True,key="cfg_cls"):
            st.session_state["version"]="classic"; st.query_params["v"]="classic"; st.rerun()

    if tab_u:
        with tab_u:
            _sec("Usuários do sistema")
            udb=api.carregar_usuarios()
            for un,ud in udb.items():
                st.markdown(
                    f'<div class="li"><div class="li-name">{ud.get("nome",un)} '
                    +_chip(ud.get("setor","—"),"ind")
                    +f'</div><div class="li-sub">{un}</div></div>',unsafe_allow_html=True)
            if st.button("⚙️ Gerenciar no Classic",use_container_width=True,key="cfg_usr_cls"):
                st.session_state["version"]="classic"; st.query_params["v"]="classic"; st.rerun()


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def run():
    st.markdown(_CSS, unsafe_allow_html=True)

    if not _check_auth():
        _tela_login(); st.stop(); return

    user    = st.session_state.usuario_logado
    udb     = api.carregar_usuarios()
    ud      = udb.get(user, {})
    setor   = ud.get("setor","vendas")
    setores = api.carregar_setores()
    setor_c = setores.get(setor,{"paginas":[]})
    perm    = set(setor_c.get("paginas",[]))
    nome    = ud.get("nome",user).title()
    is_adm  = (setor=="admin")

    if "loja_ativa_id" not in st.session_state:
        st.session_state["loja_ativa_id"] = list(api.LOJAS.keys())[0]
    loja_id   = st.session_state["loja_ativa_id"]
    loja_nome = api.LOJAS.get(str(loja_id),"—")
    cache     = api.carregar_cache(loja_id)

    # ── Páginas disponíveis ──
    all_pages = [
        ("dashboard",   "🏠 Dashboard",     ["dashboard"]),
        ("pedidos",     "🛒 Pedidos",        ["pedido"]),
        ("estoque",     "📦 Estoque",        ["entrada","acerto","estoque_loja"]),
        ("clientes",    "👥 Clientes",       ["clientes"]),
        ("fornecedores","🏭 Fornecedores",   ["fornecedores"]),
        ("compras",     "🧾 Compras",        ["compras_hist"]),
        ("financeiro",  "💰 Financeiro",     ["financeiro"]),
        ("relatorios",  "📊 Relatórios",     ["relatorios"]),
        ("listas",      "📋 Listas",         ["listas"]),
        ("config",      "⚙️ Config",         ["sincronizacao","usuarios"]),
    ]
    pages = [(pid,lbl) for pid,lbl,reqs in all_pages
             if is_adm or any(r in perm for r in reqs)]

    if not pages:
        st.error("Sem permissões. Contate o administrador.")
        if st.button("Sair"):
            api.revogar_sessao(st.session_state.get("_sessao_token",""))
            st.session_state.clear(); st.rerun()
        return

    page_ids  = [p[0] for p in pages]
    page_lbls = [p[1] for p in pages]

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:20px 16px 8px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
            <div style="width:34px;height:34px;border-radius:9px;background:#4f46e5;
              display:flex;align-items:center;justify-content:center;font-size:1.1rem;
              box-shadow:0 2px 8px rgba(79,70,229,.35)">⚡</div>
            <div>
              <div style="font-weight:800;font-size:.95rem;color:#111827;line-height:1">Plug ERP</div>
              <div style="font-size:.58rem;font-weight:700;color:#9ca3af;
                letter-spacing:.5px;text-transform:uppercase">Beta</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<hr style="margin:4px 0 10px">', unsafe_allow_html=True)

        # Nav
        if "beta_page" not in st.session_state or st.session_state.beta_page not in page_ids:
            st.session_state.beta_page = page_ids[0]

        current_idx = page_ids.index(st.session_state.beta_page) if st.session_state.beta_page in page_ids else 0
        sel = st.radio("nav", page_lbls, index=current_idx,
                       key="beta_nav_radio", label_visibility="collapsed")
        if page_lbls[current_idx] != sel:
            new_pid = page_ids[page_lbls.index(sel)]
            st.session_state.beta_page = new_pid
            st.rerun()

        # Loja selector
        st.markdown('<hr style="margin:10px 0 8px">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.6rem;font-weight:700;color:#9ca3af;'
                    'text-transform:uppercase;letter-spacing:.5px;padding:0 4px;margin-bottom:4px">'
                    'Loja ativa</div>', unsafe_allow_html=True)
        opts_l = list(api.LOJAS.values())
        atual_nm = api.LOJAS.get(str(loja_id), opts_l[0])
        nova_l = st.selectbox("Loja", opts_l,
                               index=opts_l.index(atual_nm) if atual_nm in opts_l else 0,
                               key="sb_loja", label_visibility="collapsed")
        if nova_l != atual_nm:
            inv = {v:k for k,v in api.LOJAS.items()}
            st.session_state["loja_ativa_id"] = inv[nova_l]
            st.session_state["loja_ativa_nome"] = nova_l
            st.rerun()

        # User
        st.markdown('<hr style="margin:8px 0 8px">', unsafe_allow_html=True)
        st.markdown(
            f'<div style="padding:0 4px 4px">'
            f'<div style="font-size:.78rem;font-weight:600;color:#374151">{nome}</div>'
            f'<div style="font-size:.67rem;color:#9ca3af">{setor}</div></div>',
            unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True, key="sb_logout"):
            api.revogar_sessao(st.session_state.get("_sessao_token",""))
            st.session_state.clear(); st.rerun()
        if st.button("← Classic", use_container_width=True, key="sb_classic"):
            st.session_state["version"]="classic"; st.query_params["v"]="classic"; st.rerun()

    # ── Conteúdo principal ──
    page = st.session_state.get("beta_page", page_ids[0])
    try:
        if page=="dashboard":   _dashboard(cache, loja_id, loja_nome, nome, is_adm)
        elif page=="pedidos":   _pedidos(cache, loja_id)
        elif page=="estoque":   _estoque(cache, loja_id)
        elif page=="clientes":  _clientes()
        elif page=="fornecedores": _fornecedores()
        elif page=="compras":   _compras(loja_id)
        elif page=="financeiro": _financeiro()
        elif page=="relatorios": _relatorios(cache, loja_id)
        elif page=="listas":    _listas()
        elif page=="config":    _config(cache, loja_id, is_adm)
    except Exception as _e:
        st.error(f"Erro nesta página: {_e}")
        st.caption("Recarregue a página ou contate o administrador.")
