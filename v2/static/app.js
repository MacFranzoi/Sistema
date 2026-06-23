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
  acerto: async (cont) => renderAjusteEstoque(cont, {
    titulo: "🔧 Acerto de Estoque",
    sub: "Define o valor absoluto do estoque (inventário/correção)",
    modo: "set", rotuloQtd: "Qtd correta", botao: "📊 Confirmar acerto",
  }),
  entrada: async (cont) => renderAjusteEstoque(cont, {
    titulo: "📥 Entrada de Mercadoria",
    sub: "Soma ao estoque atual",
    modo: "soma", rotuloQtd: "Qtd a somar", botao: "📥 Confirmar entrada",
  }),
  novo_modelo: async (cont) => renderNovoProduto(cont),
  clonar_modelo: async (cont) => renderClonar(cont),
  usuarios: async (cont) => renderUsuarios(cont),
  aprovacoes: async (cont) => renderAprovacoes(cont),
  listas: async (cont) => renderListas(cont),
  etiquetas: async (cont) => renderEtiquetas(cont),
  pedido: async (cont) => renderPedido(cont),
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

// Ajuste de estoque (Acerto = set, Entrada = soma) — busca, monta lista, confirma
async function renderAjusteEstoque(cont, { titulo, sub, modo, rotuloQtd, botao }) {
  const lojaNome = Estado.lojaId
    ? (Estado.lojas.find((l) => l.id === Estado.lojaId) || {}).nome
    : null;
  const lista = []; // {produto_id, produto_nome, variacao_id, variacao_nome, variacao_cod, quantidade}

  cont.innerHTML = `
    <div class="page-title">${titulo}</div>
    <div class="page-sub">${esc(sub)}</div>
    ${lojaNome ? `<div class="card" style="margin-bottom:12px">🏪 Loja: <b>${esc(lojaNome)}</b></div>`
               : '<div class="aviso">Selecione uma loja no topo antes de confirmar.</div>'}
    <div class="busca">
      <input id="aj-termo" type="text" placeholder="Buscar produto (nome ou código)…" />
      <button id="aj-buscar">Buscar</button>
    </div>
    <div id="aj-prod"></div>
    <div id="aj-lista" style="margin-top:20px"></div>`;

  const renderLista = () => {
    const div = $("#aj-lista");
    if (!lista.length) { div.innerHTML = '<div class="placeholder">Nenhum item na lista ainda.</div>'; return; }
    div.innerHTML = `
      <div class="page-sub">📝 Lista (${lista.length} itens)</div>
      <table class="tabela">
        <thead><tr><th>Produto</th><th>Variação</th><th>Qtd</th><th></th></tr></thead>
        <tbody>${lista.map((it, i) => `
          <tr><td>${esc(it.produto_nome)}</td><td>${esc(it.variacao_nome)}</td>
          <td class="estoque-num">${it.quantidade}</td>
          <td><button class="btn-sair aj-rem" data-i="${i}">✕</button></td></tr>`).join("")}</tbody>
      </table>
      <div class="busca" style="margin-top:16px">
        <button id="aj-limpar" class="btn-sair">🗑️ Limpar</button>
        <button id="aj-confirmar">${botao}</button>
      </div>
      <div id="aj-msg"></div>`;
    div.querySelectorAll(".aj-rem").forEach((b) => b.onclick = () => { lista.splice(+b.dataset.i, 1); renderLista(); });
    $("#aj-limpar").onclick = () => { lista.length = 0; renderLista(); };
    $("#aj-confirmar").onclick = confirmar;
  };

  const confirmar = async () => {
    if (!Estado.lojaId) { $("#aj-msg").innerHTML = '<div class="aviso">Selecione uma loja no topo.</div>'; return; }
    if (!lista.length) return;
    const btn = $("#aj-confirmar"); btn.disabled = true; btn.textContent = "Enviando…";
    try {
      const r = await apiPost("/api/estoque/ajustar", { loja: Estado.lojaId, modo, itens: lista });
      let msg = `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ ${r.aplicados} ajuste(s) aplicado(s).</div>`;
      if (r.erros.length) msg += `<div class="aviso">${r.erros.map((e) => esc(e.produto + " / " + e.variacao + ": " + e.erro)).join("<br>")}</div>`;
      $("#aj-msg").innerHTML = msg;
      if (!r.erros.length) { lista.length = 0; renderLista(); $("#aj-msg").innerHTML = msg; }
    } catch (err) {
      $("#aj-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    } finally {
      btn.disabled = false; btn.textContent = botao;
    }
  };

  const buscar = async () => {
    const prodDiv = $("#aj-prod");
    prodDiv.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ termo: $("#aj-termo").value.trim(), loja: Estado.lojaId });
      const d = await api("/api/produtos/buscar?" + q.toString());
      if (!d.produtos.length) { prodDiv.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      prodDiv.innerHTML = d.produtos.map((p, pi) => `
        <div class="card" style="margin-bottom:10px">
          <div class="card-head">${esc(p.nome)} <span class="stat-lbl">${esc(p.codigo_interno)}</span></div>
          <table class="tabela">
            <thead><tr><th>Variação</th><th>Cód.</th><th>Estoque atual</th><th>${esc(rotuloQtd)}</th></tr></thead>
            <tbody>${p.variacoes.map((v, vi) => `
              <tr><td>${esc(v.nome)}</td><td>${esc(v.codigo)}</td><td>${v.estoque}</td>
              <td><input type="number" min="0" class="aj-qtd" data-p="${pi}" data-v="${vi}" style="width:90px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--txt);padding:6px 8px"></td></tr>`).join("")}</tbody>
          </table>
          <div class="busca" style="margin-top:10px"><button class="aj-add" data-p="${pi}">➕ Adicionar à lista</button></div>
        </div>`).join("");

      prodDiv.querySelectorAll(".aj-add").forEach((btn) => {
        btn.onclick = () => {
          const pi = +btn.dataset.p;
          const p = d.produtos[pi];
          let n = 0;
          prodDiv.querySelectorAll(`.aj-qtd[data-p="${pi}"]`).forEach((inp) => {
            const qtd = Number(inp.value);
            if (qtd > 0) {
              const v = p.variacoes[+inp.dataset.v];
              lista.push({
                produto_id: p.id, produto_nome: p.nome,
                variacao_id: v.id, variacao_nome: v.nome, quantidade: qtd,
              });
              inp.value = ""; n++;
            }
          });
          if (n) renderLista();
        };
      });
    } catch (err) {
      prodDiv.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#aj-buscar").onclick = buscar;
  $("#aj-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
  renderLista();
}

// Novo Produto
async function renderNovoProduto(cont) {
  const grupos = await carregarGrupos();
  const variacoes = []; // {nome, codigo}
  cont.innerHTML = `
    <div class="page-title">➕ Novo Produto</div>
    <div class="page-sub">Cadastra um modelo com variações na GestãoClick</div>
    <div class="cards" style="grid-template-columns:1fr 1fr;margin-bottom:16px">
      <div class="card">
        <input id="np-nome" placeholder="Nome do produto *" class="np-in" />
        <input id="np-cod" placeholder="Código interno *" class="np-in" />
        ${selectGrupos("np-grupo", grupos)}
      </div>
      <div class="card">
        <input id="np-custo" placeholder="Valor de custo (R$)" value="0.00" class="np-in" />
        <input id="np-venda" placeholder="Valor de venda (R$)" value="0.00" class="np-in" />
        <label style="color:var(--txt2);font-size:.85rem;display:flex;align-items:center;gap:6px;margin-top:8px">
          <input id="np-ativo" type="checkbox" checked> Produto ativo</label>
      </div>
    </div>
    <div class="card" style="margin-bottom:16px">
      <div class="card-head">Variações</div>
      <div class="busca">
        <input id="np-var-nome" placeholder="Nome da variação (ex: Preto)" />
        <input id="np-var-cod" placeholder="Código (ex: IP18PM0001)" />
        <button id="np-var-add">➕</button>
      </div>
      <div id="np-var-lista"></div>
    </div>
    <div class="busca"><button id="np-salvar">✅ Cadastrar produto</button></div>
    <div id="np-msg"></div>`;

  cont.querySelectorAll(".np-in").forEach((i) =>
    i.style.cssText = "display:block;width:100%;margin-bottom:8px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--txt);padding:10px 12px;outline:none");

  const renderVars = () => {
    $("#np-var-lista").innerHTML = variacoes.length ? `
      <table class="tabela"><thead><tr><th>Variação</th><th>Código</th><th></th></tr></thead>
      <tbody>${variacoes.map((v, i) => `<tr><td>${esc(v.nome)}</td><td>${esc(v.codigo)}</td>
        <td><button class="btn-sair np-var-rem" data-i="${i}">✕</button></td></tr>`).join("")}</tbody></table>`
      : '<div class="placeholder">Adicione pelo menos uma variação.</div>';
    $("#np-var-lista").querySelectorAll(".np-var-rem").forEach((b) =>
      b.onclick = () => { variacoes.splice(+b.dataset.i, 1); renderVars(); });
  };
  $("#np-var-add").onclick = () => {
    const nome = $("#np-var-nome").value.trim();
    if (!nome) return;
    variacoes.push({ nome, codigo: $("#np-var-cod").value.trim() });
    $("#np-var-nome").value = ""; $("#np-var-cod").value = "";
    renderVars();
  };
  $("#np-salvar").onclick = async () => {
    const btn = $("#np-salvar"); btn.disabled = true; btn.textContent = "Cadastrando…";
    try {
      const r = await apiPost("/api/produtos/criar", {
        nome: $("#np-nome").value.trim(), codigo_interno: $("#np-cod").value.trim(),
        grupo_id: $("#np-grupo").value, valor_custo: $("#np-custo").value.trim() || "0.00",
        valor_venda: $("#np-venda").value.trim() || "0.00", ativo: $("#np-ativo").checked,
        loja: Estado.lojaId, variacoes: variacoes.map((v) => ({ nome: v.nome, codigo: v.codigo, estoque: "0" })),
      });
      $("#np-msg").innerHTML = `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ Produto cadastrado! Sincronize para vê-lo na lista.</div>`;
      variacoes.length = 0; renderVars();
      $("#np-nome").value = ""; $("#np-cod").value = "";
    } catch (err) {
      $("#np-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    } finally {
      btn.disabled = false; btn.textContent = "✅ Cadastrar produto";
    }
  };
  renderVars();
}

// Clonar Produto
async function renderClonar(cont) {
  cont.innerHTML = `
    <div class="page-title">🔁 Clonar Produto</div>
    <div class="page-sub">Copia as variações de um modelo existente para um novo</div>
    <div class="busca">
      <input id="cl-termo" type="text" placeholder="Buscar modelo de origem…" />
      <button id="cl-buscar">Buscar</button>
    </div>
    <div id="cl-resultado"><div class="placeholder">Busque o modelo que servirá de base.</div></div>`;

  const buscar = async () => {
    const res = $("#cl-resultado");
    res.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ termo: $("#cl-termo").value.trim(), loja: Estado.lojaId });
      const d = await api("/api/produtos/buscar?" + q.toString());
      if (!d.produtos.length) { res.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      res.innerHTML = d.produtos.map((p, i) => `
        <div class="card" style="margin-bottom:10px">
          <div class="card-head">${esc(p.nome)} <span class="stat-lbl">${esc(p.codigo_interno)} · ${p.variacoes.length} variações</span></div>
          <div class="busca">
            <input class="cl-novo-nome" data-i="${i}" placeholder="Nome do novo modelo" />
            <input class="cl-novo-cod" data-i="${i}" placeholder="Código interno" />
            <button class="cl-clonar" data-i="${i}">🔁 Clonar</button>
          </div>
          <div class="cl-msg" data-i="${i}"></div>
        </div>`).join("");
      res.querySelectorAll(".cl-clonar").forEach((btn) => {
        btn.onclick = async () => {
          const i = btn.dataset.i, p = d.produtos[+i];
          const nome = res.querySelector(`.cl-novo-nome[data-i="${i}"]`).value.trim();
          const cod = res.querySelector(`.cl-novo-cod[data-i="${i}"]`).value.trim();
          const msg = res.querySelector(`.cl-msg[data-i="${i}"]`);
          btn.disabled = true; btn.textContent = "Clonando…";
          try {
            await apiPost("/api/produtos/clonar", { produto_id: p.id, novo_nome: nome, novo_codigo: cod, loja: Estado.lojaId });
            msg.innerHTML = `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ '${esc(nome)}' criado! Sincronize para vê-lo.</div>`;
          } catch (err) {
            msg.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
          } finally {
            btn.disabled = false; btn.textContent = "🔁 Clonar";
          }
        };
      });
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  $("#cl-buscar").onclick = buscar;
  $("#cl-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
}

// Usuários (admin): lista + adicionar + editar/excluir + importar
async function renderUsuarios(cont) {
  cont.innerHTML = '<div class="loading">Carregando…</div>';
  let d;
  try { d = await api("/api/usuarios"); }
  catch (err) { cont.innerHTML = `<div class="aviso">${esc(err.message)}</div>`; return; }
  const setorOpts = d.setores.map((s) => `<option value="${esc(s.id)}">${esc(s.label)}</option>`).join("");

  cont.innerHTML = `
    <div class="page-title">👤 Usuários</div>
    <div class="page-sub">Gerenciamento de contas e setores</div>
    <div class="busca"><button id="us-importar" class="btn-sair">📋 Importar funcionários do GestãoClick</button></div>
    <div id="us-imp-msg"></div>
    <table class="tabela" style="margin-bottom:24px">
      <thead><tr><th>Login</th><th>Nome</th><th>Setor</th><th></th></tr></thead>
      <tbody>${d.usuarios.map((u) => `
        <tr data-login="${esc(u.login)}">
          <td><b>${esc(u.login)}</b></td><td>${esc(u.nome)}</td><td>${esc(u.setor_label)}</td>
          <td><button class="btn-sair us-edit" data-login="${esc(u.login)}">✏️</button></td>
        </tr>`).join("")}</tbody>
    </table>
    <div class="card" style="max-width:440px">
      <div class="card-head">➕ Adicionar usuário</div>
      <input id="us-login" class="us-in" placeholder="Login (sem espaços)" />
      <input id="us-nome" class="us-in" placeholder="Nome completo" />
      <input id="us-senha" class="us-in" placeholder="Senha inicial" />
      <select id="us-setor" class="loja-sel" style="width:100%;margin-bottom:8px">${setorOpts}</select>
      <div class="busca"><button id="us-add">Salvar</button></div>
      <div id="us-add-msg"></div>
    </div>
    <div id="us-edit-box"></div>`;

  cont.querySelectorAll(".us-in").forEach((i) =>
    i.style.cssText = "display:block;width:100%;margin-bottom:8px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--txt);padding:10px 12px;outline:none");

  $("#us-importar").onclick = async () => {
    const btn = $("#us-importar"); btn.disabled = true; btn.textContent = "Importando…";
    try {
      const r = await apiPost("/api/usuarios/importar", {});
      let m = "";
      if (r.criados && r.criados.length) m += `<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ ${r.criados.length} conta(s): ${r.criados.map((c) => esc(c.login + " (senha: " + c.senha + ")")).join(", ")}</div>`;
      if (r.ja_existem && r.ja_existem.length) m += `<div class="placeholder">Já existiam: ${esc(r.ja_existem.join(", "))}</div>`;
      $("#us-imp-msg").innerHTML = m || '<div class="placeholder">Nenhum funcionário novo encontrado.</div>';
      if (r.criados && r.criados.length) setTimeout(() => navegar("usuarios"), 1500);
    } catch (err) { $("#us-imp-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
    finally { btn.disabled = false; btn.textContent = "📋 Importar funcionários do GestãoClick"; }
  };

  $("#us-add").onclick = async () => {
    try {
      await apiPost("/api/usuarios", {
        login: $("#us-login").value, nome: $("#us-nome").value,
        senha: $("#us-senha").value, setor: $("#us-setor").value,
      });
      navegar("usuarios");
    } catch (err) { $("#us-add-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
  };

  cont.querySelectorAll(".us-edit").forEach((b) => {
    b.onclick = () => {
      const u = d.usuarios.find((x) => x.login === b.dataset.login);
      $("#us-edit-box").innerHTML = `
        <div class="card" style="max-width:440px;margin-top:16px">
          <div class="card-head">✏️ Editar: ${esc(u.login)}</div>
          <input id="ue-nome" class="us-in" value="${esc(u.nome)}" placeholder="Nome" />
          <input id="ue-senha" class="us-in" placeholder="Nova senha (vazio = manter)" />
          <select id="ue-setor" class="loja-sel" style="width:100%;margin-bottom:8px">${d.setores.map((s) => `<option value="${esc(s.id)}" ${s.id === u.setor ? "selected" : ""}>${esc(s.label)}</option>`).join("")}</select>
          <div class="busca"><button id="ue-salvar">💾 Salvar</button><button id="ue-excluir" class="btn-sair">🗑️ Excluir</button></div>
          <div id="ue-msg"></div>`;
      $("#us-edit-box").querySelectorAll(".us-in").forEach((i) =>
        i.style.cssText = "display:block;width:100%;margin-bottom:8px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--txt);padding:10px 12px;outline:none");
      $("#ue-salvar").onclick = async () => {
        try {
          await api(`/api/usuarios/${encodeURIComponent(u.login)}`, {
            method: "PUT", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nome: $("#ue-nome").value, senha: $("#ue-senha").value, setor: $("#ue-setor").value }),
          });
          navegar("usuarios");
        } catch (err) { $("#ue-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
      };
      $("#ue-excluir").onclick = async () => {
        if (!confirm(`Excluir o usuário '${u.login}'?`)) return;
        try {
          await api(`/api/usuarios/${encodeURIComponent(u.login)}`, { method: "DELETE" });
          navegar("usuarios");
        } catch (err) { $("#ue-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
      };
      $("#us-edit-box").scrollIntoView({ behavior: "smooth" });
    };
  });
}

// Aprovações de entrada
async function renderAprovacoes(cont) {
  cont.innerHTML = '<div class="loading">Carregando…</div>';
  let d;
  try { d = await api("/api/aprovacoes"); }
  catch (err) { cont.innerHTML = `<div class="aviso">${esc(err.message)}</div>`; return; }

  const itensTabela = (itens) => `
    <table class="tabela"><thead><tr><th>Produto</th><th>Variação</th><th>Qtd</th></tr></thead>
    <tbody>${itens.map((i) => `<tr><td>${esc(i.produto)}</td><td>${esc(i.variacao)}</td><td>${i.qtd}</td></tr>`).join("")}</tbody></table>`;

  cont.innerHTML = `
    <div class="page-title">✅ Aprovações de Entrada</div>
    <div class="page-sub">Entradas aguardando aprovação</div>
    ${d.pendentes.length ? d.pendentes.map((a) => `
      <div class="card" style="margin-bottom:12px">
        <div class="card-head">🔔 ${esc(a.criador)} · ${esc(a.loja_nome)} · ${a.itens.length} itens <span class="stat-lbl">${esc(a.criado_em)}</span></div>
        ${a.obs_envio ? `<div class="placeholder" style="padding:8px;margin-bottom:8px">${esc(a.obs_envio)}</div>` : ""}
        ${itensTabela(a.itens)}
        ${d.pode_aprovar ? `
          <input class="ap-obs us-in" data-id="${esc(a.id)}" placeholder="Observação (opcional)" />
          <div class="busca"><button class="ap-ok" data-id="${esc(a.id)}">✅ Aprovar e aplicar</button>
            <button class="ap-no btn-sair" data-id="${esc(a.id)}">❌ Rejeitar</button></div>
          <div class="ap-msg" data-id="${esc(a.id)}"></div>` : '<div class="placeholder">Aguardando um administrador.</div>'}
      </div>`).join("") : '<div class="placeholder">Nenhuma entrada aguardando aprovação.</div>'}
    ${d.historico.length ? `
      <div class="page-sub" style="margin-top:24px">📋 Histórico</div>
      <table class="tabela">
        <thead><tr><th>Status</th><th>Envio</th><th>Por</th><th>Loja</th><th>Itens</th><th>Aprovador</th><th>Obs</th></tr></thead>
        <tbody>${d.historico.map((h) => `<tr>
          <td>${h.status === "aprovado" ? '<span class="badge badge-green">✅ Aprovado</span>' : '<span class="badge badge-red">❌ Rejeitado</span>'}</td>
          <td>${esc(h.criado_em)}</td><td>${esc(h.criador)}</td><td>${esc(h.loja_nome)}</td>
          <td>${h.itens.length}</td><td>${esc(h.aprovador)}</td><td>${esc(h.obs_aprovacao)}</td></tr>`).join("")}</tbody>
      </table>` : ""}`;

  cont.querySelectorAll(".ap-obs").forEach((i) =>
    i.style.cssText = "display:block;width:100%;margin:8px 0;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--txt);padding:10px 12px;outline:none");

  const decidir = async (id, aprovado) => {
    const obs = (cont.querySelector(`.ap-obs[data-id="${id}"]`) || {}).value || "";
    const msg = cont.querySelector(`.ap-msg[data-id="${id}"]`);
    try {
      await apiPost(`/api/aprovacoes/${encodeURIComponent(id)}`, { aprovado, obs, loja: Estado.lojaId });
      navegar("aprovacoes");
    } catch (err) { msg.innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
  };
  cont.querySelectorAll(".ap-ok").forEach((b) => b.onclick = () => {
    if (aprovado_loja_ok()) decidir(b.dataset.id, true);
    else cont.querySelector(`.ap-msg[data-id="${b.dataset.id}"]`).innerHTML = '<div class="aviso">Selecione uma loja no topo antes de aprovar.</div>';
  });
  cont.querySelectorAll(".ap-no").forEach((b) => b.onclick = () => decidir(b.dataset.id, false));
}
function aprovado_loja_ok() { return !!Estado.lojaId; }

// Listas salvas
async function renderListas(cont) {
  const TIPOS = { "": "Todas", pedido: "🛒 Pedido", entrada: "📥 Entrada", acerto: "🔧 Acerto", etiquetas: "🏷️ Etiquetas" };
  let filtro = "";
  cont.innerHTML = `
    <div class="page-title">📋 Listas salvas</div>
    <div class="page-sub">Listas de pedido, entrada, acerto e etiquetas</div>
    <div class="submenu" style="position:static;padding:0;border:none;margin-bottom:16px">
      ${Object.entries(TIPOS).map(([k, v], i) => `<button class="sub-item ${i === 0 ? "ativo" : ""}" data-tipo="${k}">${v}</button>`).join("")}
    </div>
    <div id="ls-resultado"><div class="loading">Carregando…</div></div>`;

  const carregar = async () => {
    const res = $("#ls-resultado");
    res.innerHTML = '<div class="loading">Carregando…</div>';
    try {
      const q = new URLSearchParams({ tipo: filtro });
      const d = await api("/api/listas?" + q.toString());
      if (!d.listas.length) { res.innerHTML = '<div class="placeholder">Nenhuma lista encontrada.</div>'; return; }
      res.innerHTML = d.listas.map((l) => `
        <div class="card" style="margin-bottom:10px" data-arq="${esc(l.arquivo)}">
          <div class="card-head">${esc(l.nome)}
            <span class="stat-lbl">${esc(TIPOS[l.tipo] || l.tipo)} · ${esc(l.loja_nome)} · ${l.n_itens} itens · ${esc(l.criado_em)}</span></div>
          <div class="busca">
            <button class="ls-ver" data-arq="${esc(l.arquivo)}">👁️ Ver itens</button>
            <button class="ls-del btn-sair" data-arq="${esc(l.arquivo)}">🗑️ Excluir</button>
          </div>
          <div class="ls-itens" data-arq="${esc(l.arquivo)}"></div>
        </div>`).join("");

      res.querySelectorAll(".ls-ver").forEach((b) => b.onclick = async () => {
        const box = res.querySelector(`.ls-itens[data-arq="${CSS.escape(b.dataset.arq)}"]`);
        if (box.innerHTML) { box.innerHTML = ""; return; }
        box.innerHTML = '<div class="loading">Carregando…</div>';
        try {
          const dd = await api("/api/listas/" + encodeURIComponent(b.dataset.arq));
          box.innerHTML = `<table class="tabela" style="margin-top:8px">
            <thead><tr><th>Produto</th><th>Variação</th><th>Código</th><th>Qtd</th></tr></thead>
            <tbody>${dd.itens.map((i) => `<tr><td>${esc(i.produto)}</td><td>${esc(i.variacao)}</td><td>${esc(i.codigo)}</td><td>${esc(i.qtd)}</td></tr>`).join("")}</tbody></table>`;
        } catch (err) { box.innerHTML = `<div class="aviso">${esc(err.message)}</div>`; }
      });
      res.querySelectorAll(".ls-del").forEach((b) => b.onclick = async () => {
        if (!confirm("Excluir esta lista?")) return;
        try { await api("/api/listas/" + encodeURIComponent(b.dataset.arq), { method: "DELETE" }); carregar(); }
        catch (err) { alert(err.message); }
      });
    } catch (err) {
      res.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
  cont.querySelectorAll("[data-tipo]").forEach((b) => b.onclick = () => {
    filtro = b.dataset.tipo;
    cont.querySelectorAll("[data-tipo]").forEach((x) => x.classList.toggle("ativo", x === b));
    carregar();
  });
  carregar();
}

// Helper reutilizável: busca produtos e chama onAdd(item) por variação com qtd>0
function montarBuscaProdutos(prodDiv, onAdd, { rotuloQtd = "Qtd", comCusto = false } = {}) {
  return async (termo) => {
    prodDiv.innerHTML = '<div class="loading">Buscando…</div>';
    try {
      const q = new URLSearchParams({ termo, loja: Estado.lojaId });
      const d = await api("/api/produtos/buscar?" + q.toString());
      if (!d.produtos.length) { prodDiv.innerHTML = '<div class="placeholder">Nenhum produto encontrado.</div>'; return; }
      prodDiv.innerHTML = d.produtos.map((p, pi) => `
        <div class="card" style="margin-bottom:10px">
          <div class="card-head">${esc(p.nome)} <span class="stat-lbl">${esc(p.codigo_interno)}</span></div>
          <table class="tabela">
            <thead><tr><th>Variação</th><th>Cód.</th><th>Estoque</th>${comCusto ? "<th>Custo</th>" : ""}<th>${esc(rotuloQtd)}</th></tr></thead>
            <tbody>${p.variacoes.map((v, vi) => `
              <tr><td>${esc(v.nome)}</td><td>${esc(v.codigo)}</td><td>${v.estoque}</td>
              ${comCusto ? `<td><input type="number" step="0.01" min="0" class="mb-custo" data-p="${pi}" data-v="${vi}" placeholder="0.00" style="width:80px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--txt);padding:6px 8px"></td>` : ""}
              <td><input type="number" min="0" class="mb-qtd" data-p="${pi}" data-v="${vi}" style="width:80px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--txt);padding:6px 8px"></td></tr>`).join("")}</tbody>
          </table>
          <div class="busca" style="margin-top:10px"><button class="mb-add" data-p="${pi}">➕ Adicionar</button></div>
        </div>`).join("");
      prodDiv.querySelectorAll(".mb-add").forEach((btn) => {
        btn.onclick = () => {
          const pi = +btn.dataset.p, p = d.produtos[pi]; let n = 0;
          prodDiv.querySelectorAll(`.mb-qtd[data-p="${pi}"]`).forEach((inp) => {
            const qtd = Number(inp.value);
            if (qtd > 0) {
              const v = p.variacoes[+inp.dataset.v];
              const custoInp = comCusto ? prodDiv.querySelector(`.mb-custo[data-p="${pi}"][data-v="${inp.dataset.v}"]`) : null;
              onAdd({
                produto_id: p.id, produto_nome: p.nome,
                variacao_id: v.id, variacao_nome: v.nome, variacao_cod: v.codigo,
                quantidade: qtd, valor_custo: custoInp ? (custoInp.value || "0.00") : "0.00",
              });
              inp.value = ""; if (custoInp) custoInp.value = ""; n++;
            }
          });
        };
      });
    } catch (err) {
      prodDiv.innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
    }
  };
}

// Etiquetas: monta lista e gera PDF
async function renderEtiquetas(cont) {
  let formatos = [];
  try { formatos = (await api("/api/etiquetas/formatos")).formatos; } catch (e) {}
  const lista = [];
  cont.innerHTML = `
    <div class="page-title">🏷️ Etiquetas</div>
    <div class="page-sub">Monte a lista e gere o PDF com código de barras</div>
    <div class="busca">
      <input id="et-termo" type="text" placeholder="Buscar produto…" />
      <button id="et-buscar">Buscar</button>
    </div>
    <div id="et-prod"></div>
    <div id="et-lista" style="margin-top:20px"></div>`;

  const renderLista = () => {
    const div = $("#et-lista");
    if (!lista.length) { div.innerHTML = '<div class="placeholder">Nenhum item na lista.</div>'; return; }
    div.innerHTML = `
      <div class="page-sub">📝 Lista (${lista.length} itens · ${lista.reduce((s, i) => s + i.quantidade, 0)} etiquetas)</div>
      <table class="tabela"><thead><tr><th>Produto / Variação</th><th>Cód.</th><th>Qtd</th><th></th></tr></thead>
      <tbody>${lista.map((it, i) => `<tr><td>${esc(it.produto_nome)} / ${esc(it.variacao_nome)}</td>
        <td>${esc(it.variacao_cod)}</td><td>${it.quantidade}</td>
        <td><button class="btn-sair et-rem" data-i="${i}">✕</button></td></tr>`).join("")}</tbody></table>
      <div class="busca" style="margin-top:16px">
        <select id="et-fmt" class="loja-sel" style="min-width:260px">${formatos.map((f) => `<option value="${esc(f.id)}">${esc(f.label)}</option>`).join("")}</select>
        <button id="et-pdf">🖨️ Baixar PDF</button>
        <button id="et-limpar" class="btn-sair">🗑️ Limpar</button>
      </div>
      <div id="et-msg"></div>`;
    div.querySelectorAll(".et-rem").forEach((b) => b.onclick = () => { lista.splice(+b.dataset.i, 1); renderLista(); });
    $("#et-limpar").onclick = () => { lista.length = 0; renderLista(); };
    $("#et-pdf").onclick = async () => {
      const btn = $("#et-pdf"); btn.disabled = true; btn.textContent = "Gerando…";
      try {
        const r = await fetch("/api/etiquetas/pdf", {
          method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ formato: $("#et-fmt").value, itens: lista }),
        });
        if (!r.ok) throw new Error("Erro ao gerar PDF (" + r.status + ")");
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "etiquetas.pdf"; a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        $("#et-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
      } finally {
        btn.disabled = false; btn.textContent = "🖨️ Baixar PDF";
      }
    };
  };

  const buscar = montarBuscaProdutos($("#et-prod"), (it) => { lista.push(it); renderLista(); }, { rotuloQtd: "Qtd etiquetas" });
  $("#et-buscar").onclick = () => buscar($("#et-termo").value.trim());
  $("#et-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar($("#et-termo").value.trim()); });
  renderLista();
}

// Pedido de Compra (versão manual: monta itens, escolhe fornecedor/situação e registra)
async function renderPedido(cont) {
  const lista = [];
  let situacoes = [];
  try { situacoes = (await api("/api/situacoes_compras")).situacoes; } catch (e) {}
  cont.innerHTML = `
    <div class="page-title">🛒 Pedido de Compra</div>
    <div class="page-sub">Monte o pedido, escolha o fornecedor e registre na GestãoClick</div>
    <div class="busca">
      <input id="pe-termo" type="text" placeholder="Buscar produto…" />
      <button id="pe-buscar">Buscar</button>
    </div>
    <div id="pe-prod"></div>
    <div id="pe-lista" style="margin-top:20px"></div>`;

  const renderLista = () => {
    const div = $("#pe-lista");
    if (!lista.length) { div.innerHTML = '<div class="placeholder">Nenhum item no pedido.</div>'; return; }
    div.innerHTML = `
      <div class="page-sub">📝 Pedido (${lista.length} itens)</div>
      <table class="tabela"><thead><tr><th>Produto</th><th>Variação</th><th>Qtd</th><th>Custo</th><th></th></tr></thead>
      <tbody>${lista.map((it, i) => `<tr><td>${esc(it.produto_nome)}</td><td>${esc(it.variacao_nome)}</td>
        <td>${it.quantidade}</td><td>${moeda(it.valor_custo)}</td>
        <td><button class="btn-sair pe-rem" data-i="${i}">✕</button></td></tr>`).join("")}</tbody></table>
      <div class="card" style="margin-top:16px;max-width:520px">
        <div class="card-head">Dados do pedido</div>
        <input id="pe-forn-termo" class="pe-in" placeholder="Buscar fornecedor…" />
        <select id="pe-forn" class="loja-sel" style="width:100%;margin-bottom:8px"><option value="">— selecione um fornecedor —</option></select>
        <select id="pe-sit" class="loja-sel" style="width:100%;margin-bottom:8px">
          <option value="">— situação —</option>
          ${situacoes.map((s) => `<option value="${esc(s.id)}">${esc(s.nome)}</option>`).join("")}</select>
        <input id="pe-data" type="date" class="pe-in" value="${hoje()}" />
        <input id="pe-obs" class="pe-in" placeholder="Observações (opcional)" />
        <div class="busca"><button id="pe-registrar">✅ Registrar pedido</button>
          <button id="pe-limpar" class="btn-sair">🗑️ Limpar</button></div>
        <div id="pe-msg"></div>
      </div>`;
    div.querySelectorAll(".pe-in").forEach((i) =>
      i.style.cssText = "display:block;width:100%;margin-bottom:8px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--txt);padding:10px 12px;outline:none");
    div.querySelectorAll(".pe-rem").forEach((b) => b.onclick = () => { lista.splice(+b.dataset.i, 1); renderLista(); });
    $("#pe-limpar").onclick = () => { lista.length = 0; renderLista(); };

    // busca de fornecedor
    let fornTimer;
    $("#pe-forn-termo").addEventListener("input", () => {
      clearTimeout(fornTimer);
      fornTimer = setTimeout(async () => {
        const termo = $("#pe-forn-termo").value.trim();
        if (termo.length < 2) return;
        try {
          const d = await api("/api/fornecedores?termo=" + encodeURIComponent(termo));
          $("#pe-forn").innerHTML = '<option value="">— selecione —</option>' +
            d.fornecedores.map((f) => `<option value="${esc(f.id)}">${esc(f.nome)}</option>`).join("");
        } catch (e) {}
      }, 400);
    });

    $("#pe-registrar").onclick = async () => {
      const btn = $("#pe-registrar"); btn.disabled = true; btn.textContent = "Registrando…";
      try {
        await apiPost("/api/pedido/registrar", {
          fornecedor_id: $("#pe-forn").value, situacao_id: $("#pe-sit").value,
          data_emissao: $("#pe-data").value, observacoes: $("#pe-obs").value,
          loja: Estado.lojaId, itens: lista,
        });
        $("#pe-msg").innerHTML = '<div class="aviso" style="background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:#86efac">✅ Pedido registrado na GestãoClick!</div>';
        lista.length = 0;
        setTimeout(() => renderLista(), 1800);
      } catch (err) {
        $("#pe-msg").innerHTML = `<div class="aviso">${esc(err.message)}</div>`;
      } finally {
        btn.disabled = false; btn.textContent = "✅ Registrar pedido";
      }
    };
  };

  const buscar = montarBuscaProdutos($("#pe-prod"), (it) => { lista.push(it); renderLista(); }, { rotuloQtd: "Qtd", comCusto: true });
  $("#pe-buscar").onclick = () => buscar($("#pe-termo").value.trim());
  $("#pe-termo").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar($("#pe-termo").value.trim()); });
  renderLista();
}

// ── Arranca ────────────────────────────────────────────────────────
(async function () {
  try { await iniciarApp(); }
  catch (e) { mostrarLogin(); }
})();
