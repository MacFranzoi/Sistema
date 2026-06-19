"""
Sistema Beta — UI redesenhada, mobile-first, SaaS-ready.
Usa o mesmo api.py e dados da versão Classic.
"""

import streamlit as st
import pandas as pd
import io
from datetime import date, datetime, timedelta
import api

# ──────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────

_BETA_CSS = """
<style>
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Cores ── */
:root {
  --acc: #4f46e5;
  --acc2: #7c3aed;
  --bg: #f1f5f9;
  --card: #ffffff;
  --txt: #0f172a;
  --txt2: #64748b;
  --bor: #e2e8f0;
  --red: #ef4444;
  --grn: #22c55e;
  --yel: #f59e0b;
}

[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
}

/* ── Header ── */
.bh {
  background: linear-gradient(135deg, var(--acc) 0%, var(--acc2) 100%);
  color: white;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky; top: 0; z-index: 100;
}
.bh-logo { font-weight: 700; font-size: 1.05rem; letter-spacing: -0.3px; }
.bh-beta {
  background: rgba(255,255,255,0.25);
  padding: 2px 7px; border-radius: 20px;
  font-size: 0.6rem; font-weight: 700;
  letter-spacing: 0.8px; margin-left: 7px;
}
.bh-right { font-size: 0.75rem; opacity: 0.85; }

/* ── Conteúdo ── */
.bc { padding: 14px 16px; max-width: 860px; margin: 0 auto; }

/* ── Seção título ── */
.b-sec {
  font-size: 0.65rem; font-weight: 700; color: var(--txt2);
  text-transform: uppercase; letter-spacing: 0.8px;
  margin: 16px 0 8px;
}

/* ── KPI card ── */
.bk {
  background: var(--card);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,.07);
}
.bk-val {
  font-size: 1.55rem; font-weight: 700;
  color: var(--txt); line-height: 1.1;
}
.bk-lbl { font-size: 0.68rem; color: var(--txt2); font-weight: 500; margin-top: 3px; }
.bk-red  { color: var(--red) !important; }
.bk-grn  { color: var(--grn) !important; }
.bk-acc  { color: var(--acc) !important; }

/* ── Alert card ── */
.ba {
  border-left: 4px solid var(--red);
  background: #fff5f5;
  border-radius: 0 8px 8px 0;
  padding: 9px 12px; margin-bottom: 7px;
}
.ba-warn { border-left-color: var(--yel); background: #fffbeb; }
.ba-ok   { border-left-color: var(--grn); background: #f0fdf4; }
.ba-t  { font-size: 0.8rem; font-weight: 600; color: var(--txt); }
.ba-s  { font-size: 0.7rem; color: var(--txt2); margin-top: 2px; }

/* ── Card genérico ── */
.bcard {
  background: var(--card);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
  margin-bottom: 12px;
}

/* ── Botões de nav ── */
[data-testid="stButton"] > button {
  border-radius: 8px !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  min-height: 38px !important;
}

/* ── Tag / chip ── */
.chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.65rem;
  font-weight: 600;
}
.chip-red  { background:#fee2e2; color:#dc2626; }
.chip-yel  { background:#fef3c7; color:#b45309; }
.chip-grn  { background:#dcfce7; color:#15803d; }
.chip-blue { background:#ede9fe; color:#4f46e5; }

/* ── Mobile ── */
@media (max-width:640px) {
  .bc { padding: 10px 10px 70px !important; }
}

/* ── Divider ── */
.b-div { border: none; border-top: 1px solid var(--bor); margin: 14px 0; }

/* ── Versão switcher ── */
.vsw {
  font-size:0.68rem; color:var(--txt2); text-align:center; margin-top:6px;
}
</style>
"""

# ──────────────────────────────────────────────────────────────────
# Helpers de UI
# ──────────────────────────────────────────────────────────────────

def _kpi(val, lbl, cls=""):
    st.markdown(f'<div class="bk"><div class="bk-val {cls}">{val}</div><div class="bk-lbl">{lbl}</div></div>', unsafe_allow_html=True)

def _alerta(titulo, sub="", tipo="red"):
    cls = "ba" if tipo == "red" else ("ba ba-warn" if tipo == "yel" else "ba ba-ok")
    st.markdown(f'<div class="{cls}"><div class="ba-t">{titulo}</div><div class="ba-s">{sub}</div></div>', unsafe_allow_html=True)

def _sec(titulo):
    st.markdown(f'<div class="b-sec">{titulo}</div>', unsafe_allow_html=True)

def _chip(texto, cor="blue"):
    return f'<span class="chip chip-{cor}">{texto}</span>'


# ──────────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────────

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


def _login_page():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
          background: linear-gradient(135deg, #ede9fe 0%, #f1f5f9 100%) !important;
        }}
        section[data-testid="stMain"] {{
          display:flex !important; align-items:center !important;
          justify-content:center !important; min-height:100dvh !important;
        }}
        [data-testid="stForm"] {{
          background:#fff !important;
          border:1px solid #e2e8f0 !important;
          border-radius:16px !important;
          padding:2rem !important;
          box-shadow:0 8px 40px rgba(79,70,229,.12) !important;
        }}
        [data-testid="stForm"] button[type="submit"] {{
          background:linear-gradient(135deg,#4f46e5,#7c3aed) !important;
          color:#fff !important; font-weight:600 !important;
          border:none !important; border-radius:8px !important;
          margin-top:.8rem !important;
        }}
        </style>
        <div style="text-align:center;margin-bottom:1.5rem">
          <div style="display:inline-flex;align-items:center;justify-content:center;
            width:52px;height:52px;border-radius:14px;
            background:linear-gradient(135deg,#4f46e5,#7c3aed);
            box-shadow:0 4px 20px rgba(79,70,229,.35);margin-bottom:12px">
            <span style="font-size:1.5rem">⚡</span>
          </div>
          <div style="font-size:1.3rem;font-weight:700;color:#0f172a;letter-spacing:-.4px">
            Plug ERP <span style="background:#ede9fe;color:#4f46e5;
            font-size:.6rem;padding:2px 7px;border-radius:12px;font-weight:700;
            vertical-align:middle;margin-left:4px">BETA</span>
          </div>
          <div style="font-size:.72rem;color:#94a3b8;margin-top:4px">
            Interface redesenhada · Mobile-first
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("beta_login"):
            u_in = st.text_input("Usuário")
            s_in = st.text_input("Senha", type="password")
            ok   = st.form_submit_button("Entrar", use_container_width=True)

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

        st.markdown('<div class="vsw">Prefere a versão anterior?</div>', unsafe_allow_html=True)
        if st.button("← Voltar para o Classic", use_container_width=True, key="beta_login_switch"):
            st.session_state["version"] = "classic"
            st.query_params["v"] = "classic"
            st.rerun()


# ──────────────────────────────────────────────────────────────────
# Navegação
# ──────────────────────────────────────────────────────────────────

_NAV = [
    ("🏠", "dashboard",  "Início"),
    ("🛒", "pedidos",    "Pedidos"),
    ("📦", "estoque",    "Estoque"),
    ("💰", "financeiro", "Financeiro"),
    ("📊", "relatorios", "Relatórios"),
    ("⚙️", "config",    "Config"),
]

_PG_MAP = {
    "dashboard":  ["dashboard"],
    "pedidos":    ["pedido"],
    "estoque":    ["entrada", "acerto", "estoque_loja", "etiquetas"],
    "financeiro": ["financeiro"],
    "relatorios": ["relatorios"],
    "config":     ["sincronizacao", "usuarios", "listas"],
}

def _allowed_beta_pages(paginas_perm):
    result = []
    for _, pid, _ in _NAV:
        reqs = _PG_MAP.get(pid, [pid])
        if any(r in paginas_perm for r in reqs):
            result.append(pid)
    return result

def _get_beta_page(allowed):
    if "beta_pagina" not in st.session_state:
        _p = st.query_params.get("bp", "dashboard")
        st.session_state["beta_pagina"] = _p if _p in allowed else (allowed[0] if allowed else "dashboard")
    if st.session_state["beta_pagina"] not in allowed:
        st.session_state["beta_pagina"] = allowed[0] if allowed else "dashboard"
    return st.session_state["beta_pagina"]

def _render_nav(pg, nome_usr, allowed):
    items = [(e, pid, lbl) for e, pid, lbl in _NAV if pid in allowed]
    cols = st.columns(len(items))
    for col, (emoji, pid, lbl) in zip(cols, items):
        active = pg == pid
        tp = "primary" if active else "secondary"
        if col.button(f"{emoji} {lbl}", use_container_width=True, type=tp, key=f"bnav_{pid}"):
            st.session_state["beta_pagina"] = pid
            st.query_params["bp"] = pid
            st.rerun()

def _render_header(nome_usr, loja_nome):
    st.markdown(f"""
    <div class="bh">
      <div class="bh-logo">⚡ Plug ERP <span class="bh-beta">BETA</span></div>
      <div class="bh-right">🏪 {loja_nome} · {nome_usr}</div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Alertas de estoque baixo
# ──────────────────────────────────────────────────────────────────

def _detectar_alertas_estoque(cache, limiar_critico=3, limiar_baixo=10):
    criticos, baixos = [], []
    for p in (cache or {}).get("produtos", []):
        for v in p.get("variacoes", []):
            vd = v.get("variacao", v)
            est = int(vd.get("estoque", 0) or 0)
            item = {
                "produto": p.get("nome", ""),
                "variacao": vd.get("nome", ""),
                "cod": vd.get("codigo", ""),
                "estoque": est,
            }
            if est <= limiar_critico:
                criticos.append(item)
            elif est <= limiar_baixo:
                baixos.append(item)
    return (sorted(criticos, key=lambda x: x["estoque"]),
            sorted(baixos,   key=lambda x: x["estoque"]))


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Dashboard
# ──────────────────────────────────────────────────────────────────

def _pg_dashboard(cache, loja_id, loja_nome):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    # KPIs principais
    _sec("Visão geral")
    total_prods = cache.get("total", 0) if cache else 0
    sync_em = (cache.get("sincronizado_em","") or "")[:10] if cache else "—"
    total_lojas = len(api.LOJAS)

    k1, k2, k3 = st.columns(3)
    with k1: _kpi(f"{total_prods:,}", "Produtos no catálogo", "bk-acc")
    with k2: _kpi(total_lojas, "Lojas ativas")
    with k3: _kpi(sync_em, "Última sync")

    # Alertas de estoque
    _sec("⚠️ Alertas de estoque")
    if cache:
        criticos, baixos = _detectar_alertas_estoque(cache)
        if not criticos and not baixos:
            _alerta("Estoque saudável — nenhuma variação crítica", tipo="ok")
        else:
            if criticos:
                for item in criticos[:5]:
                    _alerta(
                        f"CRÍTICO · {item['produto']} / {item['variacao']}",
                        f"Estoque: {item['estoque']} un · Cód: {item['cod']}",
                        "red"
                    )
                if len(criticos) > 5:
                    st.caption(f"+ {len(criticos)-5} outros itens críticos")
            if baixos:
                for item in baixos[:3]:
                    _alerta(
                        f"Baixo · {item['produto']} / {item['variacao']}",
                        f"Estoque: {item['estoque']} un",
                        "yel"
                    )
                if len(baixos) > 3:
                    st.caption(f"+ {len(baixos)-3} outros com estoque baixo")
    else:
        st.info("Sincronize os produtos para ver alertas de estoque.")

    # Resumo financeiro
    _sec("💰 Financeiro do mês")
    if "beta_fin" not in st.session_state:
        try:
            _ini = date.today().replace(day=1)
            _fim = date.today()
            _rec = api.buscar_contas_receber(data_ini=str(_ini), data_fim=str(_fim), limite=500)
            _pag = api.buscar_contas_pagar(data_ini=str(_ini), data_fim=str(_fim), limite=500)
            if not isinstance(_rec, list): _rec = []
            if not isinstance(_pag, list): _pag = []
            _tr = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in _rec)
            _tp = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in _pag)
            st.session_state["beta_fin"] = (_tr, _tp)
        except Exception:
            st.session_state["beta_fin"] = (0.0, 0.0)

    _tr, _tp = st.session_state.get("beta_fin", (0.0, 0.0))
    _res = _tr - _tp
    f1, f2, f3 = st.columns(3)
    with f1: _kpi(f"R$ {_tr:,.0f}", "A receber", "bk-grn")
    with f2: _kpi(f"R$ {_tp:,.0f}", "A pagar", "bk-red")
    with f3: _kpi(f"R$ {_res:,.0f}", "Resultado", "bk-grn" if _res >= 0 else "bk-red")

    if st.button("🔄 Atualizar financeiro", key="dash_fin_refresh"):
        st.session_state.pop("beta_fin", None)
        st.rerun()

    # Status lojas
    _sec("🏪 Status das lojas")
    cols_l = st.columns(len(api.LOJAS))
    for col, (lid, lnome) in zip(cols_l, api.LOJAS.items()):
        c = api.carregar_cache(lid)
        t = c.get("total", 0) if c else 0
        s = (c.get("sincronizado_em","") or "")[:10] if c else "—"
        cor = "#22c55e" if c else "#ef4444"
        col.markdown(f"""
        <div class="bcard" style="text-align:center;padding:12px">
          <div style="font-size:.65rem;color:#64748b;font-weight:600">{lnome}</div>
          <div style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:4px 0">{t}</div>
          <div style="font-size:.6rem;color:{cor};font-weight:600">
            {"● Online" if c else "● Sem cache"}
          </div>
          <div style="font-size:.6rem;color:#94a3b8;margin-top:2px">{s}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Pedidos (simplificado, mobile-first)
# ──────────────────────────────────────────────────────────────────

def _pg_pedidos(cache, loja_id):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    if "beta_ped_itens" not in st.session_state:
        st.session_state.beta_ped_itens = []

    itens = st.session_state.beta_ped_itens

    # Banner lista aberta
    _lista_arq = st.session_state.get("beta_lista_arq")
    if _lista_arq:
        import json as _jb, os as _ob
        _cam = _ob.path.join(api.DIR_LISTAS, _lista_arq)
        try:
            with open(_cam, encoding="utf-8") as _fb:
                _db = json.load(_fb)
            _ln = _db.get("nome","—")
        except Exception:
            _ln = _lista_arq
        _bla1, _bla2, _bla3 = st.columns([4, 1, 1])
        _bla1.info(f"📂 **{_ln}**")
        if _bla2.button("💾", use_container_width=True, key="beta_sv_lista"):
            try:
                import json as _jsv, os as _osv
                _cam_sv = _osv.path.join(api.DIR_LISTAS, _lista_arq)
                with open(_cam_sv, encoding="utf-8") as _f_sv:
                    _d_sv = _jsv.load(_f_sv)
                _d_sv["itens"] = itens
                _d_sv["atualizado_em"] = datetime.now().isoformat()
                _sv_str = _jsv.dumps(_d_sv, ensure_ascii=False, indent=2)
                with open(_cam_sv, "w", encoding="utf-8") as _f_sv:
                    _f_sv.write(_sv_str)
                api._gh_push_arquivo(f"listas/{_lista_arq}", _sv_str, f"Salva: {_ln}")
                st.success("✅ Salvo!")
            except Exception as _ex_sv:
                st.error(f"Erro: {_ex_sv}")
        if _bla3.button("✕", use_container_width=True, key="beta_fechar_lista"):
            st.session_state.pop("beta_lista_arq", None)
            st.rerun()

    # Abas de input
    tab_wpp, tab_cat, tab_avl, tab_lst = st.tabs(["📱 WhatsApp", "🔍 Catálogo", "✏️ Avulso", "📂 Listas"])

    with tab_wpp:
        _sec("Colar pedido do WhatsApp")
        _txt_wpp = st.text_area("Cole o texto aqui", height=150, key="beta_wpp_txt",
                                 placeholder="Ex:\niPhone 15 - masculino 2, feminino 3\nSamsung A55 - brilho 5")
        if st.button("🤖 Processar com IA", use_container_width=True, type="primary", key="beta_wpp_proc"):
            if not _txt_wpp.strip():
                st.warning("Cole o texto do pedido.")
            elif not cache:
                st.warning("Sincronize os produtos primeiro.")
            else:
                with st.spinner("Processando com IA…"):
                    try:
                        catalogo = "\n".join(
                            f"{p.get('codigo_interno','')} | {p.get('nome','')}"
                            for p in cache.get("produtos", [])[:300]
                        )
                        resultado = api.parse_pedido_whatsapp(_txt_wpp, catalogo)
                        st.session_state["beta_wpp_resultado"] = resultado
                    except Exception as _ex_wpp:
                        st.error(f"Erro na IA: {_ex_wpp}")

        if "beta_wpp_resultado" in st.session_state:
            _res = st.session_state["beta_wpp_resultado"]
            _sec(f"Resultado ({len(_res)} itens)")
            _adicionar = []
            for _i, _r in enumerate(_res):
                _conf = _r.get("confianca","")
                _cor = "grn" if _conf == "alta" else ("yel" if _conf == "media" else "red")
                _cbr1, _cbr2 = st.columns([4, 1])
                _check = _cbr1.checkbox(
                    f"**{_r.get('nome_produto') or _r.get('modelo_digitado','')}** "
                    f"{'/ ' + str(_r.get('variacoes',[])) if _r.get('variacoes') else ''} "
                    f"— {_r.get('quantidade',1)} un",
                    value=bool(_r.get("nome_produto")),
                    key=f"beta_wpp_{_i}"
                )
                _cbr2.markdown(_chip(_conf.upper() if _conf else "?", _cor), unsafe_allow_html=True)
                if _check and _r.get("nome_produto"):
                    _prods_match = api.buscar_produtos(_r.get("cod_interno") or _r.get("nome_produto",""), cache)
                    if _prods_match:
                        _p = _prods_match[0]
                        _variacoes = _r.get("variacoes", ["padrão"])
                        for _var in (_variacoes if _variacoes else ["padrão"]):
                            _adicionar.append({
                                "produto_id": _p["id"],
                                "produto_nome": _p["nome"],
                                "variacao_nome": str(_var),
                                "variacao_id": None,
                                "quantidade": int(_r.get("quantidade", 1)),
                                "fornecedor": "",
                                "valor_custo": "",
                                "observacao": "",
                            })

            if st.button("➕ Adicionar selecionados ao pedido", use_container_width=True, type="primary", key="beta_wpp_add"):
                if _adicionar:
                    st.session_state.beta_ped_itens.extend(_adicionar)
                    st.session_state.pop("beta_wpp_resultado", None)
                    st.success(f"✅ {len(_adicionar)} item(ns) adicionado(s)!")
                    st.rerun()

    with tab_cat:
        if not cache:
            st.warning("Sincronize os produtos primeiro.")
        else:
            _sec("Buscar no catálogo")
            _termo_cat = st.text_input("🔍 Produto", key="beta_cat_busca", placeholder="ex: iPhone 15, Samsung A55…")
            _prods_cat = api.buscar_produtos(_termo_cat, cache) if _termo_cat else []
            if _prods_cat:
                _nomes_cat = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in _prods_cat]
                _sel_cat   = st.selectbox("Selecione", _nomes_cat, key="beta_cat_sel")
                _prod_sel  = _prods_cat[_nomes_cat.index(_sel_cat)]

                _vars_cat = [v["variacao"] for v in _prod_sel.get("variacoes", [])]
                if _vars_cat:
                    _df_vars = pd.DataFrame([{
                        "_vid": vd["id"],
                        "Variação": vd.get("nome",""),
                        "Cód": vd.get("codigo",""),
                        "Estoque": int(vd.get("estoque",0) or 0),
                        "Qtd": 0
                    } for vd in _vars_cat])

                    _qtd_cols = {}
                    for _, _vrow in _df_vars.iterrows():
                        _vc1, _vc2, _vc3 = st.columns([3, 1, 1])
                        _vc1.caption(f"{_vrow['Variação']} ({_vrow['Cód']})")
                        _vc2.caption(f"Est: {_vrow['Estoque']}")
                        _qtd_cols[_vrow.name] = _vc3.number_input(
                            "Qtd", min_value=0, value=0, key=f"beta_var_qtd_{_vrow.name}",
                            label_visibility="collapsed"
                        )

                    _forn_cat = st.text_input("Fornecedor", key="beta_cat_forn")
                    _custo_cat = st.text_input("Custo unit. (R$)", key="beta_cat_custo")

                    if st.button("➕ Adicionar ao pedido", use_container_width=True, type="primary", key="beta_cat_add"):
                        _adicionados = 0
                        for _idx, _vrow in _df_vars.iterrows():
                            _q = _qtd_cols.get(_idx, 0)
                            if _q > 0:
                                _vd_obj = _vars_cat[_idx]
                                st.session_state.beta_ped_itens.append({
                                    "produto_id": _prod_sel["id"],
                                    "produto_nome": _prod_sel["nome"],
                                    "cod_interno": _prod_sel.get("codigo_interno",""),
                                    "variacao_id": _vd_obj["id"],
                                    "variacao_nome": _vd_obj.get("nome",""),
                                    "variacao_cod": _vd_obj.get("codigo",""),
                                    "quantidade": int(_q),
                                    "fornecedor": _forn_cat,
                                    "valor_custo": _custo_cat,
                                    "observacao": "",
                                })
                                _adicionados += 1
                        if _adicionados:
                            st.success(f"✅ {_adicionados} variação(ões) adicionada(s)!")
                            st.rerun()
                        else:
                            st.warning("Preencha a quantidade em pelo menos uma variação.")

    with tab_avl:
        _sec("Adicionar item avulso")
        _av1, _av2 = st.columns([3, 1])
        _desc_av = _av1.text_input("Descrição", key="beta_av_desc", placeholder="ex: Película Samsung A55")
        _qtd_av  = _av2.number_input("Qtd", min_value=1, value=1, key="beta_av_qtd")
        _av3, _av4 = st.columns(2)
        _forn_av  = _av3.text_input("Fornecedor", key="beta_av_forn")
        _custo_av = _av4.text_input("Custo unit.", key="beta_av_custo")
        if st.button("➕ Adicionar avulso", use_container_width=True, key="beta_av_add"):
            if _desc_av.strip():
                st.session_state.beta_ped_itens.append({
                    "produto_nome": _desc_av,
                    "variacao_nome": "",
                    "quantidade": int(_qtd_av),
                    "fornecedor": _forn_av,
                    "valor_custo": _custo_av,
                    "observacao": "",
                    "_avulso": True,
                })
                st.success("✅ Adicionado!")
                st.rerun()

    with tab_lst:
        _sec("Carregar lista salva")
        _listas = api.listar_listas_salvas("pedido")
        if _listas:
            for _lst in _listas[:10]:
                _lc1, _lc2 = st.columns([4, 1])
                _lnome_lst = _lst.get("nome","—")
                _lqtd_lst  = len(_lst.get("itens", []))
                _ldata_lst = (_lst.get("criado_em","") or "")[:10]
                _lc1.write(f"**{_lnome_lst}** · {_lqtd_lst} itens · {_ldata_lst}")
                if _lc2.button("Abrir", key=f"beta_lst_open_{_lst['_arquivo']}", use_container_width=True):
                    st.session_state.beta_ped_itens = list(_lst.get("itens", []))
                    st.session_state["beta_lista_arq"] = _lst["_arquivo"]
                    st.rerun()
        else:
            st.info("Nenhuma lista de pedido salva.")

        _sec("Salvar lista atual")
        _novo_nome = st.text_input("Nome da nova lista", key="beta_nova_lista_nome")
        if st.button("💾 Salvar lista atual", use_container_width=True, key="beta_salvar_lista"):
            if not itens:
                st.warning("O pedido está vazio.")
            elif not _novo_nome.strip():
                st.warning("Digite um nome para a lista.")
            else:
                api.salvar_lista(_novo_nome, "pedido", itens)
                st.success(f"✅ Lista '{_novo_nome}' salva!")
                st.rerun()

    # ── Pedido atual ──────────────────────────────────────────────
    if itens:
        st.divider()
        _sec(f"Pedido atual — {len(itens)} item(ns)")

        _ped_header = st.columns([4, 1, 1])
        _ped_header[0].caption("Produto / Variação")
        _ped_header[1].caption("Qtd")
        _ped_header[2].caption("Del")

        for _pi, _pit in enumerate(list(itens)):
            _pnome = f"{_pit.get('produto_nome','')} / {_pit.get('variacao_nome','')}" if _pit.get('variacao_nome') else _pit.get('produto_nome','')
            _pc1, _pc2, _pc3 = st.columns([4, 1, 1])
            _pc1.caption(_pnome[:45] + ("…" if len(_pnome) > 45 else ""))
            _nova_q = _pc2.number_input("q", min_value=1, value=int(_pit.get("quantidade",1)),
                                         label_visibility="collapsed", key=f"beta_pit_q_{_pi}")
            if _nova_q != _pit.get("quantidade"):
                st.session_state.beta_ped_itens[_pi]["quantidade"] = _nova_q
            if _pc3.button("🗑", key=f"beta_pit_del_{_pi}", use_container_width=True):
                st.session_state.beta_ped_itens.pop(_pi)
                st.rerun()

        # Export row
        _sec("Exportar")
        _exp1, _exp2, _exp3 = st.columns(3)

        # Excel
        _buf_ped = io.BytesIO()
        _df_ped = pd.DataFrame([{
            "Produto": it.get("produto_nome",""),
            "Variação": it.get("variacao_nome",""),
            "Qtd": it.get("quantidade",0),
            "Fornecedor": it.get("fornecedor",""),
            "Custo": it.get("valor_custo",""),
        } for it in itens])
        with pd.ExcelWriter(_buf_ped, engine="openpyxl") as _wr:
            _df_ped.to_excel(_wr, index=False, sheet_name="Pedido")
        _buf_ped.seek(0)
        _exp1.download_button("📄 Excel", _buf_ped, f"pedido_{date.today()}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

        # Texto
        if _exp2.button("📋 Copiar texto", use_container_width=True, key="beta_ped_txt"):
            import html as _h, streamlit.components.v1 as _cv
            _linhas = [f"PEDIDO {date.today()}", "="*40]
            for _it in itens:
                _linhas.append(f"{_it.get('produto_nome','')} / {_it.get('variacao_nome','')} — {_it.get('quantidade',0)} un")
            _txt = "\n".join(_linhas)
            _cv.html(f'<textarea id="ct" style="position:fixed;top:-9999px">{_h.escape(_txt)}</textarea>'
                     f'<p style="margin:0;font:13px sans-serif;color:#28a745">✅ Copiado!</p>'
                     f'<script>(function(){{var e=document.getElementById("ct");e.focus();e.select();'
                     f'try{{navigator.clipboard.writeText(e.value).catch(function(){{document.execCommand("copy")}})}}catch(ex){{document.execCommand("copy")}}}})()</script>',
                     height=35)

        # Limpar
        if _exp3.button("🗑️ Limpar tudo", use_container_width=True, key="beta_ped_clear"):
            st.session_state.beta_ped_itens = []
            st.session_state.pop("beta_lista_arq", None)
            st.rerun()
    else:
        st.info("Pedido vazio — use as abas acima para adicionar itens.")

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Estoque (entrada + acerto + etiquetas unificados)
# ──────────────────────────────────────────────────────────────────

def _pg_estoque(cache, loja_id):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    if not cache:
        st.warning("Sincronize os produtos primeiro.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    _modo = st.radio("Modo", ["📥 Entrada", "📊 Acerto", "🏷️ Etiquetas"],
                      horizontal=True, key="beta_est_modo", label_visibility="collapsed")

    st.divider()
    _termo_est = st.text_input("🔍 Buscar produto", key="beta_est_busca", placeholder="Nome ou código")
    _prods_est = api.buscar_produtos(_termo_est, cache) if _termo_est else []

    if not _prods_est:
        if _termo_est:
            st.info("Nenhum produto encontrado.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    _nomes_est = [f"{p.get('codigo_interno','')} — {p['nome']}" for p in _prods_est]
    _sel_est   = st.selectbox("Produto", _nomes_est, key="beta_est_sel", label_visibility="collapsed")
    _prod_est  = _prods_est[_nomes_est.index(_sel_est)]
    _vars_est  = [v["variacao"] for v in _prod_est.get("variacoes", [])]

    if _modo == "📥 Entrada" or _modo == "📊 Acerto":
        _modo_api = "soma" if "Entrada" in _modo else "set"
        _label_qtd = "Qtd a adicionar" if _modo_api == "soma" else "Novo estoque"

        _qtds_est = {}
        for _vd in _vars_est:
            _vc1, _vc2, _vc3 = st.columns([3, 1, 1])
            _vc1.write(f"**{_vd.get('nome','')}** · {_vd.get('codigo','')}")
            _vc2.caption(f"Atual: {int(_vd.get('estoque',0) or 0)}")
            _qtds_est[_vd["id"]] = _vc3.number_input(
                _label_qtd, min_value=0, value=0,
                key=f"beta_est_q_{_vd['id']}", label_visibility="collapsed"
            )

        _obs_est = st.text_input("Observação", key="beta_est_obs")
        if st.button(f"✅ Aplicar {_modo}", use_container_width=True, type="primary", key="beta_est_apply"):
            _erros, _ok = [], 0
            for _vid, _q in _qtds_est.items():
                if _q > 0:
                    try:
                        api.atualizar_estoque_variacao(_prod_est["id"], _vid, _q, loja_id=loja_id, modo=_modo_api)
                        _ok += 1
                    except Exception as _ex_est:
                        _erros.append(str(_ex_est))
            if _ok:
                st.success(f"✅ {_ok} variação(ões) atualizada(s)!")
            if _erros:
                for _e in _erros:
                    st.error(_e)

    else:  # Etiquetas
        if "beta_etiq_itens" not in st.session_state:
            st.session_state.beta_etiq_itens = []

        _qtds_etiq = {}
        for _vd in _vars_est:
            _ve1, _ve2 = st.columns([4, 1])
            _ve1.write(f"{_vd.get('nome','')} · {_vd.get('codigo','')}")
            _qtds_etiq[_vd["id"]] = _ve2.number_input(
                "Qtd", min_value=0, value=0,
                key=f"beta_etiq_q_{_vd['id']}", label_visibility="collapsed"
            )

        if st.button("➕ Adicionar à lista", use_container_width=True, key="beta_etiq_add"):
            _add_etiq = 0
            for _vd in _vars_est:
                _q = _qtds_etiq.get(_vd["id"], 0)
                if _q > 0:
                    st.session_state.beta_etiq_itens.append({
                        "variacao_id": _vd["id"],
                        "produto_nome": _prod_est["nome"],
                        "variacao_nome": _vd.get("nome",""),
                        "variacao_cod": _vd.get("codigo",""),
                        "quantidade": int(_q),
                    })
                    _add_etiq += 1
            if _add_etiq:
                st.success(f"✅ {_add_etiq} adicionado(s)!")

        if st.session_state.beta_etiq_itens:
            _sec(f"Lista de etiquetas ({len(st.session_state.beta_etiq_itens)} itens)")
            _df_etiq = pd.DataFrame(st.session_state.beta_etiq_itens)
            st.dataframe(_df_etiq[["produto_nome","variacao_nome","quantidade"]].rename(
                columns={"produto_nome":"Produto","variacao_nome":"Variação","quantidade":"Qtd"}
            ), use_container_width=True, hide_index=True)

            _url_etiq = api.gerar_url_etiquetas([
                {"variacao_id": it["variacao_id"], "quantidade": it["quantidade"]}
                for it in st.session_state.beta_etiq_itens
                if it.get("variacao_id")
            ])
            if _url_etiq:
                st.link_button("🏷️ Gerar Etiquetas no GestãoClick", _url_etiq, use_container_width=True)

            if st.button("🗑️ Limpar lista", use_container_width=True, key="beta_etiq_clear"):
                st.session_state.beta_etiq_itens = []
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Financeiro
# ──────────────────────────────────────────────────────────────────

def _pg_financeiro(loja_id):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    _tab_r, _tab_p = st.tabs(["💰 A Receber", "💸 A Pagar"])

    def _render_contas(tipo):
        _f1, _f2, _f3 = st.columns([1, 1, 1])
        _ini = _f1.date_input("De", value=date.today() - timedelta(days=30), key=f"beta_fin_{tipo}_ini")
        _fim = _f2.date_input("Até", value=date.today() + timedelta(days=30), key=f"beta_fin_{tipo}_fim")
        if _f3.button("🔄 Carregar", use_container_width=True, key=f"beta_fin_{tipo}_btn"):
            st.session_state.pop(f"beta_fin_{tipo}_dados", None)

        if f"beta_fin_{tipo}_dados" not in st.session_state:
            with st.spinner("Carregando…"):
                try:
                    fn = api.buscar_contas_receber if tipo == "rec" else api.buscar_contas_pagar
                    st.session_state[f"beta_fin_{tipo}_dados"] = fn(str(_ini), str(_fim), limite=300)
                except Exception as _ex_fin:
                    st.error(f"Erro: {_ex_fin}")
                    st.session_state[f"beta_fin_{tipo}_dados"] = []

        contas = st.session_state.get(f"beta_fin_{tipo}_dados", [])
        if not isinstance(contas, list): contas = []

        _total  = sum(float(c.get("valor") or c.get("valor_total") or 0) for c in contas)
        _pago   = sum(float(c.get("valor_pago") or 0) for c in contas)
        _aberto = _total - _pago

        _k1, _k2, _k3 = st.columns(3)
        with _k1: _kpi(f"R$ {_total:,.0f}", "Total", "bk-acc")
        with _k2: _kpi(f"R$ {_pago:,.0f}", "Recebido/Pago", "bk-grn")
        with _k3: _kpi(f"R$ {_aberto:,.0f}", "Em aberto", "bk-red")

        if contas:
            _rows_fin = []
            for _c in contas:
                _sit = "✅" if (str(_c.get("situacao_id",""))=="2" or str(_c.get("pago",""))=="1") else "⏳"
                _rows_fin.append({
                    "Sit.": _sit,
                    "Descrição": (_c.get("descricao") or _c.get("historico",""))[:30],
                    "Parte": (_c.get("cliente_nome") or _c.get("fornecedor_nome") or "")[:20],
                    "Vencto": (_c.get("data_vencimento") or "")[:10],
                    "Valor": f"R$ {float(_c.get('valor') or _c.get('valor_total') or 0):,.2f}",
                })
            st.dataframe(pd.DataFrame(_rows_fin), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento no período.")

    with _tab_r: _render_contas("rec")
    with _tab_p: _render_contas("pag")

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Relatórios
# ──────────────────────────────────────────────────────────────────

def _pg_relatorios(cache, loja_id):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    _tab_v, _tab_e, _tab_f = st.tabs(["📈 Vendas", "📦 Estoque", "💰 Resultado"])

    with _tab_v:
        _rv1, _rv2, _rv3 = st.columns([1, 1, 1])
        _d_v_ini = _rv1.date_input("De", value=date.today() - timedelta(days=30), key="beta_rv_ini")
        _d_v_fim = _rv2.date_input("Até", value=date.today(), key="beta_rv_fim")
        if _rv3.button("📊 Gerar", use_container_width=True, key="beta_rv_btn", type="primary"):
            with st.spinner("Carregando vendas…"):
                try:
                    _vendas = api.buscar_vendas(str(_d_v_ini), str(_d_v_fim), loja_id=loja_id, limite=500)
                    if not isinstance(_vendas, list): _vendas = []
                    if _vendas:
                        _total_v = sum(float(v.get("valor_total") or 0) for v in _vendas)
                        _ka, _kb, _kc = st.columns(3)
                        with _ka: _kpi(len(_vendas), "Pedidos", "bk-acc")
                        with _kb: _kpi(f"R$ {_total_v:,.0f}", "Total", "bk-grn")
                        with _kc: _kpi(f"R$ {(_total_v/len(_vendas)):.0f}", "Ticket médio")

                        _rows_v = []
                        for _v in _vendas:
                            _rows_v.append({
                                "Data":    (_v.get("data_emissao") or "")[:10],
                                "Nº":      _v.get("numero",""),
                                "Cliente": (_v.get("cliente_nome","") or "")[:25],
                                "Valor":   float(_v.get("valor_total") or 0),
                                "Status":  _v.get("status",""),
                            })
                        _df_v = pd.DataFrame(_rows_v)
                        st.dataframe(_df_v, use_container_width=True, hide_index=True)

                        _sec("Vendas por dia")
                        _df_chart = _df_v.groupby("Data")["Valor"].sum().reset_index()
                        _df_chart = _df_chart.set_index("Data")
                        st.bar_chart(_df_chart)
                    else:
                        st.info("Nenhuma venda no período.")
                except Exception as _ex_v:
                    st.error(f"Erro: {_ex_v}")

    with _tab_e:
        if not cache:
            st.info("Sincronize os produtos para ver o relatório de estoque.")
        else:
            _prods_r = cache.get("produtos", [])
            _rows_e = []
            for _p in _prods_r:
                for _v in _p.get("variacoes", []):
                    _vd = _v.get("variacao", _v)
                    _est = int(_vd.get("estoque", 0) or 0)
                    _rows_e.append({
                        "Produto":  _p.get("nome",""),
                        "Variação": _vd.get("nome",""),
                        "Cód.":     _vd.get("codigo",""),
                        "Estoque":  _est,
                        "Status":   "🔴" if _est <= 3 else ("🟡" if _est <= 10 else "🟢"),
                    })
            _df_e = pd.DataFrame(_rows_e).sort_values("Estoque")
            _sec(f"{len(_df_e)} variações · {_df_e['Estoque'].sum()} unidades total")
            _filtro_status = st.selectbox("Filtrar", ["Todos","🔴 Crítico (≤3)","🟡 Baixo (≤10)","🟢 Normal"],
                                           key="beta_re_filtro")
            if "Crítico" in _filtro_status:
                _df_e = _df_e[_df_e["Estoque"] <= 3]
            elif "Baixo" in _filtro_status:
                _df_e = _df_e[_df_e["Estoque"] <= 10]
            st.dataframe(_df_e, use_container_width=True, hide_index=True)

            _buf_e = io.BytesIO()
            with pd.ExcelWriter(_buf_e, engine="openpyxl") as _wr_e:
                _df_e.to_excel(_wr_e, index=False, sheet_name="Estoque")
            _buf_e.seek(0)
            st.download_button("📄 Exportar Excel", _buf_e, "estoque.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)

    with _tab_f:
        _rfi1, _rfi2, _rfi3 = st.columns([1, 1, 1])
        _d_f_ini = _rfi1.date_input("De", value=date.today() - timedelta(days=30), key="beta_rf_ini")
        _d_f_fim = _rfi2.date_input("Até", value=date.today(), key="beta_rf_fim")
        if _rfi3.button("📊 Gerar", use_container_width=True, key="beta_rf_btn", type="primary"):
            with st.spinner("Calculando…"):
                try:
                    _rec_f = api.buscar_contas_receber(str(_d_f_ini), str(_d_f_fim), limite=500)
                    _pag_f = api.buscar_contas_pagar(str(_d_f_ini), str(_d_f_fim), limite=500)
                    if not isinstance(_rec_f, list): _rec_f = []
                    if not isinstance(_pag_f, list): _pag_f = []
                    _tr_f = sum(float(r.get("valor") or r.get("valor_total") or 0) for r in _rec_f)
                    _tp_f = sum(float(p.get("valor") or p.get("valor_total") or 0) for p in _pag_f)
                    _res_f = _tr_f - _tp_f
                    _fa, _fb, _fc = st.columns(3)
                    with _fa: _kpi(f"R$ {_tr_f:,.0f}", "Total a receber", "bk-grn")
                    with _fb: _kpi(f"R$ {_tp_f:,.0f}", "Total a pagar", "bk-red")
                    with _fc: _kpi(f"R$ {_res_f:,.0f}", "Resultado",
                                    "bk-grn" if _res_f >= 0 else "bk-red")

                    # Chart comparativo
                    _df_comp = pd.DataFrame({
                        "Valor": [_tr_f, _tp_f, max(0, _res_f)],
                        "Tipo":  ["Receber", "Pagar", "Resultado"]
                    }).set_index("Tipo")
                    st.bar_chart(_df_comp)
                except Exception as _ex_f:
                    st.error(f"Erro: {_ex_f}")

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# PÁGINA: Configurações
# ──────────────────────────────────────────────────────────────────

def _pg_config(cache, loja_id, is_admin):
    st.markdown('<div class="bc">', unsafe_allow_html=True)

    _tab_sync, _tab_loja, _tab_ver = st.tabs(["🔄 Sync", "🏪 Loja", "🔀 Versão"])

    with _tab_sync:
        _sec("Sincronizar produtos")
        if cache:
            _s_em = (cache.get("sincronizado_em","") or "")[:16].replace("T"," às ")
            st.success(f"Cache atual: **{cache.get('total',0)}** produtos — sync {_s_em}")
        else:
            st.warning("Nenhum cache para esta loja.")

        if st.button("🔄 Sincronizar Todas as Lojas", type="primary", use_container_width=True, key="beta_sync_all"):
            _bar = st.progress(0)
            _txt = st.empty()
            _erros_s = []
            for _idx, (_lid, _lnome) in enumerate(api.LOJAS.items()):
                _txt.info(f"Sincronizando **{_lnome}**… ({_idx+1}/{len(api.LOJAS)})")
                def _prog(pag, total, _n=_lnome, _i=_idx, _tot=len(api.LOJAS)):
                    _bar.progress((_i + pag/max(total,1))/_tot, text=f"{_n}: {pag}/{total}")
                try:
                    api.sincronizar_produtos(loja_id=_lid, progress_callback=_prog)
                except Exception as _ex_s:
                    _erros_s.append(f"{_lnome}: {_ex_s}")
            if _erros_s:
                for _e in _erros_s: st.error(_e)
            else:
                st.success("✅ Todas as lojas sincronizadas!")
                st.rerun()

    with _tab_loja:
        _sec("Loja ativa")
        _loja_opts = {v: k for k, v in api.LOJAS.items()}
        _loja_atual_nome = api.LOJAS.get(str(loja_id), list(api.LOJAS.values())[0])
        _loja_nova = st.selectbox("Selecionar loja", list(_loja_opts.keys()),
                                   index=list(_loja_opts.keys()).index(_loja_atual_nome)
                                   if _loja_atual_nome in _loja_opts else 0,
                                   key="beta_loja_sel")
        if st.button("✅ Aplicar", key="beta_loja_apply", use_container_width=True):
            st.session_state["loja_ativa_id"] = _loja_opts[_loja_nova]
            st.session_state["loja_ativa_nome"] = _loja_nova
            st.rerun()

    with _tab_ver:
        _sec("Versão do sistema")
        st.markdown("""
        <div class="bcard">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:8px">🚀 Você está no Beta</div>
          <div style="font-size:.75rem;color:#64748b">
            Interface redesenhada, mobile-first, com alertas de estoque em tempo real.<br>
            O Beta usa os mesmos dados e API do Classic.
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Voltar para o Classic", use_container_width=True, key="beta_switch_classic"):
            st.session_state["version"] = "classic"
            st.query_params["v"] = "classic"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────

def run():
    import json  # noqa — necessário no escopo local de algumas funções inline
    st.markdown(_BETA_CSS, unsafe_allow_html=True)

    if not _check_auth():
        _login_page()
        st.stop()
        return

    # Dados do usuário
    _user    = st.session_state.usuario_logado
    _udb     = api.carregar_usuarios()
    _ud      = _udb.get(_user, {})
    _setor   = _ud.get("setor", "vendas")
    _setores = api.carregar_setores()
    _setor_c = _setores.get(_setor, {"paginas": []})
    _perm    = set(_setor_c.get("paginas", []))
    _nome    = _ud.get("nome", _user)
    _is_admin = _setor == "admin"

    # Loja
    if "loja_ativa_id" not in st.session_state:
        st.session_state["loja_ativa_id"] = list(api.LOJAS.keys())[0]
    _loja_id   = st.session_state["loja_ativa_id"]
    _loja_nome = api.LOJAS.get(str(_loja_id), "—")

    # Cache
    _cache = api.carregar_cache(_loja_id)

    # Header
    _render_header(_nome, _loja_nome)

    # Nav
    _allowed = _allowed_beta_pages(_perm)
    if not _allowed:
        _allowed = ["dashboard"]
    _pg = _get_beta_page(_allowed)
    _render_nav(_pg, _nome, _allowed)

    # Roteamento
    if   _pg == "dashboard":  _pg_dashboard(_cache, _loja_id, _loja_nome)
    elif _pg == "pedidos":    _pg_pedidos(_cache, _loja_id)
    elif _pg == "estoque":    _pg_estoque(_cache, _loja_id)
    elif _pg == "financeiro": _pg_financeiro(_loja_id)
    elif _pg == "relatorios": _pg_relatorios(_cache, _loja_id)
    elif _pg == "config":     _pg_config(_cache, _loja_id, _is_admin)
    else:
        _pg_dashboard(_cache, _loja_id, _loja_nome)
