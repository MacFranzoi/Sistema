/* ── Sistema Plug 2.0 — SPA (roteador + chamadas ao backend) ── */

const Estado = {
  me: null,        // dados do usuário logado (/api/me)
  lojas: [],       // lista de lojas
  lojaId: "",      // loja selecionada ("" = todas)
  cat: null,       // categoria ativa no menu
  pagina: null,    // página ativa
};

// ── Helpers de fetch ───────────────────────────────────────────────
async function api(path, opts = {}) {
  const r = await fetch(path, { credentials: "same-origin", ...opts });
  if (r.status === 401) { mostrarLogin(); throw new Error("401"); }
  if (!r.ok) {
    let msg = "Erro " + r.status;
    try { msg = (await r.json()).detail || msg; } catch (e) {}
    throw new Error(msg);
  }
  return r.json();
}
async function apiPost(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}
const $ = (sel) => document.querySelector(sel);
const el = (html) => { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; };
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ── Login ──────────────────────────────────────────────────────────
function mostrarLogin() {
  $("#app").classList.add("hidden");
  $("#login").classList.remove("hidden");
}
$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#login-erro").textContent = "";
  try {
    await apiPost("/api/login", { usuario: $("#login-user").value, senha: $("#login-pass").value });
    await iniciarApp();
  } catch (err) {
    $("#login-erro").textContent = err.message === "401" ? "Usuário ou senha incorretos." : err.message;
  }
});
$("#btn-sair").addEventListener("click", async () => {
  try { await apiPost("/api/logout"); } catch (e) {}
  mostrarLogin();
});

// ── Inicialização ──────────────────────────────────────────────────
async function iniciarApp() {
  Estado.me = await api("/api/me");
  const dadosLojas = await api("/api/lojas");
  Estado.lojas = dadosLojas.lojas;

  $("#login").classList.add("hidden");
  $("#app").classList.remove("hidden");

  montarSeletorLoja();
  montarCategorias();
  montarTabbar();

  // página inicial: dashboard (ou a primeira permitida)
  const primeira = Estado.me.menu[0];
  if (primeira) navegar(primeira.id);
  else $("#conteudo").innerHTML = '<div class="placeholder">Sem páginas liberadas para o seu usuário.</div>';
}

function montarSeletorLoja() {
  const sel = $("#loja-sel");
  sel.innerHTML = '<option value="">Todas as lojas</option>' +
    Estado.lojas.map((l) => `<option value="${esc(l.id)}">${esc(l.nome)}</option>`).join("");
  sel.value = Estado.lojaId;
  sel.onchange = () => { Estado.lojaId = sel.value; if (Estado.pagina) navegar(Estado.pagina); };
}

// Agrupa o menu por categoria
function categorias() {
  const ordem = [], grupos = {};
  for (const m of Estado.me.menu) {
    if (!grupos[m.categoria]) { grupos[m.categoria] = []; ordem.push(m.categoria); }
    grupos[m.categoria].push(m);
  }
  return { ordem, grupos };
}

function montarCategorias() {
  const { ordem } = categorias();
  const icones = Estado.me.cat_icones || {};
  $("#cats").innerHTML = ordem.map((c) =>
    `<button class="cat-btn" data-cat="${esc(c)}"><span>${icones[c] || "•"}</span><span>${esc(c[0] + c.slice(1).toLowerCase())}</span></button>`
  ).join("");
  $("#cats").querySelectorAll(".cat-btn").forEach((b) => {
    b.onclick = () => { Estado.cat = b.dataset.cat; montarSubmenu(); marcarCategoria(); };
  });
}

function marcarCategoria() {
  $("#cats").querySelectorAll(".cat-btn").forEach((b) =>
    b.classList.toggle("ativo", b.dataset.cat === Estado.cat));
}

function montarSubmenu() {
  const { grupos } = categorias();
  const itens = grupos[Estado.cat] || [];
  $("#submenu").innerHTML = itens.map((m) =>
    `<button class="sub-item" data-pg="${esc(m.id)}">${m.icone} ${esc(m.rotulo)}</button>`
  ).join("");
  $("#submenu").querySelectorAll(".sub-item").forEach((b) => {
    b.onclick = () => navegar(b.dataset.pg);
  });
  marcarSubmenu();
}

function marcarSubmenu() {
  $("#submenu").querySelectorAll(".sub-item").forEach((b) =>
    b.classList.toggle("ativo", b.dataset.pg === Estado.pagina));
}

// Barra inferior (mobile): mostra todas as páginas em sequência
function montarTabbar() {
  $("#tabbar").innerHTML = Estado.me.menu.map((m) =>
    `<button class="tab-btn" data-pg="${esc(m.id)}"><span class="ic">${m.icone}</span><span>${esc(m.rotulo)}</span></button>`
  ).join("");
  $("#tabbar").querySelectorAll(".tab-btn").forEach((b) => {
    b.onclick = () => navegar(b.dataset.pg);
  });
}

// ── Roteador: SÓ o conteúdo muda (cara de app) ─────────────────────
async function navegar(pagina) {
  Estado.pagina = pagina;
  // acerta a categoria ativa conforme a página
  const m = Estado.me.menu.find((x) => x.id === pagina);
  if (m) { Estado.cat = m.categoria; montarSubmenu(); marcarCategoria(); }
  $("#tabbar").querySelectorAll(".tab-btn").forEach((b) =>
    b.classList.toggle("ativo", b.dataset.pg === pagina));
  marcarSubmenu();

  const cont = $("#conteudo");
  cont.innerHTML = '<div class="loading">Carregando…</div>';
  // reinicia a animação de fade
  cont.style.animation = "none"; void cont.offsetWidth; cont.style.animation = "";

  const render = PAGINAS[pagina] || PAGINAS._padrao;
  try {
    await render(cont, m);
  } catch (err) {
    if (err.message !== "401")
      cont.innerHTML = `<div class="aviso">Erro ao carregar: ${esc(err.message)}</div>`;
  }
}

// ── Páginas (views) ────────────────────────────────────────────────
const PAGINAS = {
  // Página ainda não migrada — placeholder
  _padrao: async (cont, m) => {
    cont.innerHTML = `
      <div class="page-title">${m ? m.icone + " " + esc(m.rotulo) : "Página"}</div>
      <div class="page-sub">Esta tela ainda não foi migrada para o 2.0.</div>
      <div class="placeholder">🚧 Em construção — disponível no sistema atual (Streamlit).</div>`;
  },

  dashboard: async (cont) => {
    const d = await api("/api/dashboard");
    cont.innerHTML = `
      <div class="page-title">🏠 Dashboard</div>
      <div class="page-sub">Olá, ${esc(Estado.me.nome)} 👋</div>
      <div class="stats">
        <div class="stat"><div class="stat-val">${d.total_catalogo}</div><div class="stat-lbl">Produtos no catálogo</div></div>
        <div class="stat"><div class="stat-val">${d.qtd_lojas}</div><div class="stat-lbl">Lojas ativas</div></div>
      </div>
      <div class="cards">
        ${d.lojas.map((l) => `
          <div class="card">
            <div class="card-head">🏪 ${esc(l.nome)}
              ${l.online ? '<span class="badge badge-green">● Online</span>' : '<span class="badge badge-red">● Sem cache</span>'}
            </div>
            <div class="stat-val" style="font-size:1.4rem">${l.total}</div>
            <div class="stat-lbl">Sincronizado: ${esc((l.sincronizado_em || "—").slice(0, 10))}</div>
          </div>`).join("")}
      </div>`;
  },

  estoque_loja: async (cont) => renderEstoque(cont),
  rel_estoque:  async (cont) => renderEstoque(cont),

  clientes:     async (cont) => renderCadastro(cont, {
    titulo: "👥 Clientes",
    sub: "Busca direto na GestãoClick",
    endpoint: "/api/clientes",
    chave: "clientes",
    colunas: ["Nome", "CPF/CNPJ", "E-mail", "Telefone", "Cidade"],
    campos: ["nome", "cpf_cnpj", "email", "telefone", "cidade"],
    placeholder: "Nome ou CPF/CNPJ",
    paramBusca: "termo",
  }),

  fornecedores: async (cont) => renderCadastro(cont, {
    titulo: "🏭 Fornecedores",
    sub: "Busca direto na GestãoClick",
    endpoint: "/api/fornecedores",
    chave: "fornecedores",
    colunas: ["Nome", "CPF/CNPJ", "E-mail", "Telefone", "Cidade"],
    campos: ["nome", "cpf_cnpj", "email", "telefone", "cidade"],
    placeholder: "Nome ou CNPJ",
    paramBusca: "termo",
  }),

  vendas:     async (cont) => renderPeriodo(cont, {
    titulo: "🧾 Vendas",
    sub: "Pedidos de venda",
    endpoint: "/api/vendas",
    chave: "vendas",
    colunas: ["Nº", "Data", "Cliente", "Total", "Status"],
    campos: ["numero", "data", "cliente", "total_fmt", "status"],
    formatTotal: true,
  }),

  orcamentos: async (cont) => renderPeriodo(cont, {
    titulo: "📋 Orçamentos",
    sub: "Orçamentos emitidos",
    endpoint: "/api/orcamentos",
    chave: "orcamentos",
    colunas: ["Nº", "Data", "Cliente", "Total", "Status"],
    campos: ["numero", "data", "cliente", "total_fmt", "status"],
    formatTotal: true,
  }),

  compras_hist: async (cont) => renderPeriodo(cont, {
    titulo: "📦 Histórico de Compras",
    sub: "Pedidos de compra",
    endpoint: "/api/compras",
    chave: "compras",
    colunas: ["Nº", "Data", "Fornecedor", "Total", "Status", "NF-e"],
    campos: ["numero", "data", "fornecedor", "total_fmt", "status", "nfe"],
    formatTotal: true,
  }),

  financeiro: async (cont) => renderFinanceiro(cont),
  relatorios: async (cont) => renderRelatorios(cont),
  sincronizacao: async (cont) => renderSincronizacao(cont),
  precos: async (cont) => renderPrecos(cont),
  disponibilidade: async (cont) => renderDisponibilidade(cont),
};

// View de estoque (busca ao vivo)
async function renderEstoque(cont) {
  const lojaNome = Estado.lojaId
    ? (Estado.lojas.find((l) => l.id === Estado.lojaId) || {}).nome
    : "Todas as lojas";
  cont.innerHTML = `
    <div class="page-title">🏪 Estoque ao vivo</div>
    <div class="page-sub">${esc(lojaNome)} — busca direto na GestãoClick</div>
    <div class="busca">
      <input id="est-nome" type="text" placeholder="Nome do produto…" />
      <input id="est-cod" type="text" placeholder="Código…" />
      <button id="est-buscar">Buscar</button>
    </div>
    <div id="est-resultado"><div class="placeholder">Digite um nome ou código e clique em Buscar.</div></div>`;

  const buscar = async () => {
    const nome = $("#est-nome").value.trim();
    const cod = $("#est-cod").value.trim();
    if (!nome && !cod) return;
    const res = $("#est-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ loja: Estado.lojaId, nome, codigo: cod });
      const d = await api("/api/estoque?" + q.toString());
      if (!d.produtos.length) { res.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      const linhas = [];
      for (const p of d.produtos) {
        if (p.variacoes.length) {
          for (const v of p.variacoes) linhas.push(linhaEstoque(p.nome, v.nome, v.codigo, v.estoque));
        } else {
          linhas.push(linhaEstoque(p.nome, "—", p.codigo_interno, p.estoque));
        }
      }
      res.innerHTML = `
        <table class="tabela">
          <thead><tr><th>Produto</th><th>Variação</th><th>Código</th><th>Estoque</th></tr></thead>
          <tbody>${linhas.join("")}</tbody>
        </table>`;
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#est-buscar").onclick = buscar;
  $("#est-nome").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
  $("#est-cod").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
}

function linhaEstoque(prod, varNome, cod, estoque) {
  const n = Number(estoque) || 0;
  const cls = n <= 0 ? "estoque-zero" : "estoque-ok";
  return `<tr><td>${esc(prod)}</td><td>${esc(varNome)}</td><td>${esc(cod)}</td>
    <td class="estoque-num ${cls}">${n}</td></tr>`;
}

// View genérica: busca por termo (clientes, fornecedores)
async function renderCadastro(cont, { titulo, sub, endpoint, chave, colunas, campos, placeholder, paramBusca }) {
  cont.innerHTML = `
    <div class="page-title">${titulo}</div>
    <div class="page-sub">${esc(sub)}</div>
    <div class="busca">
      <input id="cad-termo" type="text" placeholder="${esc(placeholder)}" />
      <button id="cad-buscar">Buscar</button>
    </div>
    <div id="cad-resultado"><div class="placeholder">Digite e clique em Buscar.</div></div>`;

  const buscar = async () => {
    const termo = $("#cad-termo").value.trim();
    const res = $("#cad-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ [paramBusca]: termo });
      const d = await api(endpoint + "?" + q.toString());
      const items = d[chave] || [];
      if (!items.length) { res.innerHTML = '<div class="placeholder">Nenhum resultado.</div>'; return; }
      res.innerHTML = `
        <table class="tabela">
          <thead><tr>${colunas.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
          <tbody>${items.map((it) =>
            `<tr>${campos.map((f) => `<td>${esc(it[f] ?? "")}</td>`).join("")}</tr>`
          ).join("")}</tbody>
        </table>`;
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#cad-buscar").onclick = buscar;
  $("#cad-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
}

// View genérica: busca por período (vendas, orçamentos)
function hoje() { return new Date().toISOString().slice(0, 10); }
function diasAtras(n) { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); }

async function renderPeriodo(cont, { titulo, sub, endpoint, chave, colunas, campos, formatTotal }) {
  const fim = hoje();
  const ini = diasAtras(30);
  cont.innerHTML = `
    <div class="page-title">${titulo}</div>
    <div class="page-sub">${esc(sub)}</div>
    <div class="busca" style="align-items:center">
      <label style="color:var(--txt2);font-size:.85rem">De</label>
      <input id="per-ini" type="date" value="${ini}" style="flex:none;width:150px" />
      <label style="color:var(--txt2);font-size:.85rem">Até</label>
      <input id="per-fim" type="date" value="${fim}" style="flex:none;width:150px" />
      <button id="per-buscar">Buscar</button>
    </div>
    <div id="per-resultado"><div class="loading">Carregando…</div></div>`;

  const buscar = async () => {
    const data_ini = $("#per-ini").value;
    const data_fim = $("#per-fim").value;
    const res = $("#per-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ loja: Estado.lojaId, data_ini, data_fim });
      const d = await api(endpoint + "?" + q.toString());
      const items = d[chave] || [];
      if (!items.length) { res.innerHTML = '<div class="placeholder">Nenhum resultado no período.</div>'; return; }
      if (formatTotal) items.forEach((it) => { it.total_fmt = "R$ " + Number(it.total || 0).toFixed(2).replace(".", ","); });
      res.innerHTML = `
        <div class="stat-lbl" style="margin-bottom:8px">${items.length} registros</div>
        <table class="tabela">
          <thead><tr>${colunas.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
          <tbody>${items.map((it) =>
            `<tr>${campos.map((f) => `<td>${esc(it[f] ?? "")}</td>`).join("")}</tr>`
          ).join("")}</tbody>
        </table>`;
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#per-buscar").onclick = buscar;
  buscar();
}

const moeda = (n) => "R$ " + Number(n || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Financeiro: abas Receber / Pagar
async function renderFinanceiro(cont) {
  cont.innerHTML = `
    <div class="page-title">💳 Financeiro</div>
    <div class="page-sub">Contas a receber e a pagar</div>
    <div class="submenu" style="position:static;padding:0;border:none;margin-bottom:16px">
      <button class="sub-item ativo" data-fin="receber">💰 A Receber</button>
      <button class="sub-item" data-fin="pagar">💸 A Pagar</button>
    </div>
    <div class="busca" style="align-items:center">
      <label style="color:var(--txt2);font-size:.85rem">De</label>
      <input id="fin-ini" type="date" value="${diasAtras(30)}" style="flex:none;width:150px" />
      <label style="color:var(--txt2);font-size:.85rem">Até</label>
      <input id="fin-fim" type="date" value="${diasFrente(30)}" style="flex:none;width:150px" />
      <button id="fin-buscar">Buscar</button>
    </div>
    <div id="fin-resultado"><div class="loading">Carregando…</div></div>`;

  let tipo = "receber";
  const buscar = async () => {
    const res = $("#fin-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ tipo, data_ini: $("#fin-ini").value, data_fim: $("#fin-fim").value });
      const d = await api("/api/financeiro?" + q.toString());
      const ehReceber = tipo === "receber";
      const linhas = d.contas.map((c) => `
        <tr><td>${esc(c.descricao)}</td><td>${esc(c.nome)}</td><td>${esc(c.vencimento)}</td>
        <td>${moeda(c.valor)}</td><td>${moeda(c.pago)}</td>
        <td>${c.quitado ? '<span class="badge badge-green">✅ Pago</span>' : '<span class="badge badge-red">⏳ Aberto</span>'}</td></tr>`).join("");
      res.innerHTML = `
        <div class="stats">
          <div class="stat"><div class="stat-val" style="color:var(--acc2)">${moeda(d.total)}</div><div class="stat-lbl">Total a ${ehReceber ? "receber" : "pagar"}</div></div>
          <div class="stat"><div class="stat-val" style="color:var(--green)">${moeda(d.pago)}</div><div class="stat-lbl">${ehReceber ? "Recebido" : "Pago"}</div></div>
          <div class="stat"><div class="stat-val" style="color:var(--red)">${moeda(d.aberto)}</div><div class="stat-lbl">Em aberto</div></div>
        </div>
        ${d.contas.length ? `<table class="tabela">
          <thead><tr><th>Descrição</th><th>${ehReceber ? "Cliente" : "Fornecedor"}</th><th>Vencimento</th><th>Valor</th><th>Pago</th><th>Situação</th></tr></thead>
          <tbody>${linhas}</tbody></table>` : '<div class="placeholder">Nenhuma conta no período.</div>'}`;
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };

  cont.querySelectorAll("[data-fin]").forEach((b) => {
    b.onclick = () => {
      tipo = b.dataset.fin;
      cont.querySelectorAll("[data-fin]").forEach((x) => x.classList.toggle("ativo", x === b));
      buscar();
    };
  });
  $("#fin-buscar").onclick = buscar;
  buscar();
}

function diasFrente(n) { const d = new Date(); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); }

// Relatórios: vendas por período (resumo + gráfico simples de barras)
async function renderRelatorios(cont) {
  cont.innerHTML = `
    <div class="page-title">📊 Relatórios</div>
    <div class="page-sub">Vendas por período</div>
    <div class="busca" style="align-items:center">
      <label style="color:var(--txt2);font-size:.85rem">De</label>
      <input id="rel-ini" type="date" value="${diasAtras(30)}" style="flex:none;width:150px" />
      <label style="color:var(--txt2);font-size:.85rem">Até</label>
      <input id="rel-fim" type="date" value="${hoje()}" style="flex:none;width:150px" />
      <button id="rel-buscar">Gerar</button>
    </div>
    <div id="rel-resultado"><div class="loading">Carregando…</div></div>`;

  const buscar = async () => {
    const res = $("#rel-resultado");
    res.innerHTML = '<div class="loading">Gerando…</div>';
    try {
      const q = new URLSearchParams({ loja: Estado.lojaId, data_ini: $("#rel-ini").value, data_fim: $("#rel-fim").value });
      const d = await api("/api/rel_vendas?" + q.toString());
      const maxV = Math.max(1, ...d.serie.map((s) => s.valor));
      const barras = d.serie.map((s) => `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <div style="width:90px;color:var(--txt2);font-size:.75rem;flex-shrink:0">${esc(s.data)}</div>
          <div style="flex:1;background:var(--bg);border-radius:4px;overflow:hidden">
            <div style="width:${(s.valor / maxV * 100).toFixed(1)}%;min-width:2px;height:20px;background:linear-gradient(90deg,var(--acc),var(--acc2))"></div>
          </div>
          <div style="width:110px;text-align:right;font-size:.78rem">${moeda(s.valor)}</div>
        </div>`).join("");
      const linhas = d.vendas.map((v) => `
        <tr><td>${esc(v.data)}</td><td>${esc(v.numero)}</td><td>${esc(v.cliente)}</td>
        <td>${moeda(v.total)}</td><td>${esc(v.status)}</td></tr>`).join("");
      res.innerHTML = `
        <div class="stats">
          <div class="stat"><div class="stat-val">${d.qtd}</div><div class="stat-lbl">Pedidos</div></div>
          <div class="stat"><div class="stat-val" style="color:var(--green)">${moeda(d.total)}</div><div class="stat-lbl">Faturamento</div></div>
          <div class="stat"><div class="stat-val">${moeda(d.ticket_medio)}</div><div class="stat-lbl">Ticket médio</div></div>
        </div>
        ${d.serie.length ? `<div class="card" style="margin-bottom:20px"><div class="card-head">📈 Vendas por dia</div>${barras}</div>` : ""}
        ${d.vendas.length ? `<table class="tabela">
          <thead><tr><th>Data</th><th>Nº</th><th>Cliente</th><th>Valor</th><th>Status</th></tr></thead>
          <tbody>${linhas}</tbody></table>` : '<div class="placeholder">Nenhuma venda no período.</div>'}`;
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#rel-buscar").onclick = buscar;
  buscar();
}

// Sincronização: status por loja + botão sincronizar tudo
async function renderSincronizacao(cont) {
  cont.innerHTML = `
    <div class="page-title">🔄 Sincronização</div>
    <div class="page-sub">Atualiza o cache de produtos a partir da GestãoClick</div>
    <div class="busca"><button id="sinc-btn">🔄 Sincronizar todas as lojas</button></div>
    <div id="sinc-status"><div class="loading">Carregando…</div></div>`;

  const carregarStatus = async () => {
    const d = await api("/api/sincronizacao/status");
    $("#sinc-status").innerHTML = `<div class="cards">${d.lojas.map((l) => `
      <div class="card">
        <div class="card-head">🏪 ${esc(l.nome)}
          ${l.online ? '<span class="badge badge-green">● Cache OK</span>' : '<span class="badge badge-red">● Sem cache</span>'}
        </div>
        <div class="stat-val" style="font-size:1.4rem">${l.total}</div>
        <div class="stat-lbl">Sincronizado: ${esc((l.sincronizado_em || "—").slice(0, 16).replace("T", " "))}</div>
      </div>`).join("")}</div>`;
  };

  $("#sinc-btn").onclick = async () => {
    const btn = $("#sinc-btn");
    btn.disabled = true; btn.textContent = "Sincronizando… (pode levar 1-2 min)";
    try {
      const d = await apiPost("/api/sincronizar", {});
      const erros = d.resultados.filter((r) => !r.ok);
      await carregarStatus();
      if (erros.length) {
        $("#sinc-status").insertAdjacentHTML("afterbegin",
          `<div class="aviso">Concluído com erros: ${erros.map((e) => esc(e.nome + ": " + e.erro)).join("; ")}</div>`);
      }
    } catch (err) {
      $("#sinc-status").insertAdjacentHTML("afterbegin", `<div class="aviso">${esc(err.message)}</div>`);
    } finally {
      btn.disabled = false; btn.textContent = "🔄 Sincronizar todas as lojas";
    }
  };
  carregarStatus();
}

// Carrega grupos (árvore) uma vez e cacheia
let _gruposCache = null;
async function carregarGrupos() {
  if (_gruposCache) return _gruposCache;
  try { _gruposCache = (await api("/api/grupos")).grupos || []; }
  catch (e) { _gruposCache = []; }
  return _gruposCache;
}
function selectGrupos(id, grupos) {
  return `<select id="${id}" class="loja-sel" style="min-width:200px">
    <option value="">Todos os grupos</option>
    ${grupos.map((g) => `<option value="${esc(g.id)}">${esc(g.label)}</option>`).join("")}
  </select>`;
}

// Preços: busca produtos, edita custo/venda, salva em lote
async function renderPrecos(cont) {
  const grupos = await carregarGrupos();
  cont.innerHTML = `
    <div class="page-title">💰 Tabela de Preços</div>
    <div class="page-sub">Edite custo e venda; salve em lote</div>
    <div class="busca">
      <input id="pr-termo" type="text" placeholder="Nome ou código…" />
      ${selectGrupos("pr-grupo", grupos)}
      <button id="pr-buscar">Buscar</button>
    </div>
    <div id="pr-resultado"><div class="placeholder">Busque produtos para editar os preços.</div></div>`;

  const buscar = async () => {
    const res = $("#pr-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ loja: Estado.lojaId, termo: $("#pr-termo").value.trim(), grupo: $("#pr-grupo").value });
      const d = await api("/api/precos?" + q.toString());
      if (!d.produtos.length) { res.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      res.innerHTML = `
        <div class="stat-lbl" style="margin-bottom:8px">${d.produtos.length} produtos</div>
        <table class="tabela" id="pr-tabela">
          <thead><tr><th>Cód.</th><th>Produto</th><th>Custo (R$)</th><th>Venda (R$)</th><th>Margem</th></tr></thead>
          <tbody>${d.produtos.map((p, i) => `
            <tr data-id="${esc(p.id)}" data-nome="${esc(p.nome)}">
              <td>${esc(p.codigo)}</td><td>${esc(p.nome)}</td>
              <td><input class="pr-in pr-custo" type="number" step="0.01" value="${p.custo}" data-i="${i}" style="width:100px"></td>
              <td><input class="pr-in pr-venda" type="number" step="0.01" value="${p.venda}" data-i="${i}" style="width:100px"></td>
              <td class="pr-margem" data-i="${i}">${p.margem}%</td>
            </tr>`).join("")}</tbody>
        </table>
        <div class="busca" style="margin-top:16px"><button id="pr-salvar">💾 Salvar preços</button></div>
        <div id="pr-msg"></div>`;

      // recalcula margem ao editar
      const recalc = (i) => {
        const c = Number($(`.pr-custo[data-i="${i}"]`).value) || 0;
        const v = Number($(`.pr-venda[data-i="${i}"]`).value) || 0;
        const m = c > 0 ? (((v - c) / c) * 100).toFixed(1) : "0.0";
        $(`.pr-margem[data-i="${i}"]`).textContent = m + "%";
      };
      res.querySelectorAll(".pr-in").forEach((inp) => {
        inp.style.cssText += ";background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--txt);padding:6px 8px";
        inp.addEventListener("input", () => recalc(inp.dataset.i));
      });

      $("#pr-salvar").onclick = async () => {
        const itens = [];
        res.querySelectorAll("#pr-tabela tbody tr").forEach((tr, i) => {
          itens.push({
            produto_id: tr.dataset.id,
            produto_nome: tr.dataset.nome,
            valor_custo: Number($(`.pr-custo[data-i="${i}"]`).value) || 0,
            valor_venda: Number($(`.pr-venda[data-i="${i}"]`).value) || 0,
          });
        });
        const btn = $("#pr-salvar"); btn.disabled = true; btn.textContent = "Salvando…";
        try {
          const r = await apiPost("/api/precos", { loja: Estado.lojaId, itens });
          let msg = `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ ${r.atualizados} preço(s) atualizado(s).</div>`;
          if (r.erros.length) msg += `<div class="aviso">${r.erros.map((e) => esc(e.nome + ": " + e.erro)).join("<br>")}</div>`;
          $("#pr-msg").innerHTML = msg;
        } catch (err) {
          $("#pr-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
        } finally {
          btn.disabled = false; btn.textContent = "💾 Salvar preços";
        }
      };
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#pr-buscar").onclick = buscar;
  $("#pr-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
}

// Disponibilidade: checkbox por loja, salva mudanças
async function renderDisponibilidade(cont) {
  const grupos = await carregarGrupos();
  cont.innerHTML = `
    <div class="page-title">🔘 Disponibilidade por Loja</div>
    <div class="page-sub">Controle em quais lojas cada produto está ativo</div>
    <div class="busca">
      <input id="dp-termo" type="text" placeholder="Nome ou código…" />
      ${selectGrupos("dp-grupo", grupos)}
      <label style="color:var(--txt2);font-size:.85rem;display:flex;align-items:center;gap:6px">
        <input id="dp-div" type="checkbox"> Só divergentes</label>
      <button id="dp-buscar">Buscar</button>
    </div>
    <div id="dp-resultado"><div class="placeholder">Busque produtos para editar a disponibilidade.</div></div>`;

  const buscar = async () => {
    const res = $("#dp-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({
        termo: $("#dp-termo").value.trim(), grupo: $("#dp-grupo").value,
        so_divergentes: $("#dp-div").checked,
      });
      const d = await api("/api/disponibilidade?" + q.toString());
      if (!d.produtos.length) { res.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      const cabLojas = d.lojas.map((l) => `<th>${esc(l.nome)}</th>`).join("");
      const linhas = d.produtos.map((p) => `
        <tr data-id="${esc(p.id)}">
          <td>${p.divergente ? "⚠️" : ""}</td><td>${esc(p.codigo)}</td><td>${esc(p.nome)}</td>
          ${d.lojas.map((l) => `<td style="text-align:center"><input type="checkbox" class="dp-chk" data-loja="${esc(l.id)}" ${p.lojas[l.id] ? "checked" : ""}></td>`).join("")}
        </tr>`).join("");
      res.innerHTML = `
        <div class="stat-lbl" style="margin-bottom:8px">${d.produtos.length} produtos</div>
        <table class="tabela" id="dp-tabela">
          <thead><tr><th>⚠️</th><th>Cód.</th><th>Produto</th>${cabLojas}</tr></thead>
          <tbody>${linhas}</tbody>
        </table>
        <div class="busca" style="margin-top:16px"><button id="dp-salvar">💾 Salvar disponibilidade</button></div>
        <div id="dp-msg"></div>`;

      // guarda estado original p/ enviar só mudanças
      const original = new Map();
      res.querySelectorAll("#dp-tabela tbody tr").forEach((tr) => {
        tr.querySelectorAll(".dp-chk").forEach((chk) => {
          original.set(tr.dataset.id + "|" + chk.dataset.loja, chk.checked);
        });
      });

      $("#dp-salvar").onclick = async () => {
        const mudancas = [];
        res.querySelectorAll("#dp-tabela tbody tr").forEach((tr) => {
          tr.querySelectorAll(".dp-chk").forEach((chk) => {
            const key = tr.dataset.id + "|" + chk.dataset.loja;
            if (original.get(key) !== chk.checked) {
              mudancas.push({ produto_id: tr.dataset.id, loja_id: chk.dataset.loja, ativo: chk.checked });
            }
          });
        });
        if (!mudancas.length) { $("#dp-msg").innerHTML = '<div class="placeholder">Nenhuma mudança para salvar.</div>'; return; }
        const btn = $("#dp-salvar"); btn.disabled = true; btn.textContent = "Salvando…";
        try {
          const r = await apiPost("/api/disponibilidade", { mudancas });
          let msg = `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ ${r.aplicadas} alteração(ões) salva(s).</div>`;
          if (r.erros.length) msg += `<div class="aviso">${r.erros.length} erro(s).</div>`;
          $("#dp-msg").innerHTML = msg;
        } catch (err) {
          $("#dp-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
        } finally {
          btn.disabled = false; btn.textContent = "💾 Salvar disponibilidade";
        }
      };
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#dp-buscar").onclick = buscar;
  $("#dp-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
}

// ── Arranca ────────────────────────────────────────────────────────
(async function () {
  try { await iniciarApp(); }
  catch (e) { mostrarLogin(); }
})();
