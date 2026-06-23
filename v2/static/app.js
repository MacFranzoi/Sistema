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
  rel_estoque: async (cont) => renderEstoque(cont),
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

// ── Arranca ────────────────────────────────────────────────────────
(async function () {
  try { await iniciarApp(); }
  catch (e) { mostrarLogin(); }
})();
