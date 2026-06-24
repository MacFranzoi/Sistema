# CLAUDE.md — Sistema Plug ERP

Contexto completo do projeto para novas sessões de desenvolvimento.

---

## O que é

ERP para gestão de estoque, pedidos, vendas e compras de lojas de acessórios para celulares.
O sistema se integra ao **GestaoClick** (ERP externo) e tem duas interfaces:

1. **Streamlit** (`app.py`) — versão original, 23 páginas, deploy porta 8501
2. **v2** — versão nova em migração: FastAPI (`v2/main.py`) + SPA puro HTML/CSS/JS (`v2/static/`)

**A v2 é o foco atual de desenvolvimento.** O Streamlit está em manutenção apenas.

---

## Arquitetura

```
v2/static/app.js (SPA)
    ↓ fetch
v2/main.py (FastAPI, 40+ endpoints REST, porta 8000)
    ↓ importa
api.py (lógica centralizada, 2973 linhas)
    ↓ chama
GestaoClick API  |  GitHub API  |  Supabase (opcional)  |  Claude/OpenAI
```

`api.py` é compartilhado entre o Streamlit e o FastAPI — **nunca duplicar lógica nos dois backends**.

---

## Estrutura de Arquivos

```
/
├── api.py                    # Lógica core (autenticação, cache, GestaoClick, IA, persistência)
├── app.py                    # Interface Streamlit (legado)
├── db.py                     # Camada Supabase (opcional, com fallback automático)
├── requirements.txt          # Deps Streamlit
├── Dockerfile                # Deploy Streamlit
│
├── v2/
│   ├── main.py               # FastAPI backend (40+ endpoints)
│   ├── requirements.txt      # Deps FastAPI
│   ├── Dockerfile            # Deploy FastAPI (build a partir da raiz)
│   ├── static/
│   │   ├── index.html        # Shell SPA (mínimo)
│   │   ├── app.js            # Roteador + renderizadores (~1800 linhas)
│   │   └── style.css         # Tema escuro
│   └── tests/
│       └── test_flows.py     # Testes async (pytest)
│
├── usuarios.json             # Usuários e senhas (no .gitignore se sensível)
├── setores.json              # Permissões por setor
├── disponibilidade_lojas.json
├── custos_tipo.json
├── sessoes.json              # Sessões ativas (no .gitignore)
├── cache_produtos*.json      # Cache catálogo por loja (no .gitignore)
└── listas/                   # Listas salvas (JSON) — persistidas também no GitHub
```

---

## Variáveis de Ambiente

| Variável | Uso | Obrigatória? |
|---|---|---|
| `GITHUB_TOKEN` | Persistência de listas no repo | Recomendado |
| `ANTHROPIC_API_KEY` | Parse inteligente de pedidos (Claude) | Não |
| `OPENAI_API_KEY` | Transcrição de áudio (Whisper) | Não |
| `SUPABASE_URL` | Banco de dados remoto | Não |
| `SUPABASE_KEY` | Chave Supabase | Não |
| `SENTRY_DSN` | Monitoramento de erros (v2) | Não |
| `PORT` | Porta FastAPI (Railway injeta) | Não (default 8000) |

**Hardcoded em `api.py`** (credenciais GestaoClick):
```python
ACCESS_TOKEN = "998d6e5bed008c2023d5c5bc062ac9311e05c045"
SECRET_TOKEN = "884b009905a80a147cea7172f25c83700c097166"
BASE_URL = "https://api.gestaoclick.com/api"
```

---

## Deploy (Railway)

Dois serviços no mesmo repositório:
- **Serviço 1**: `Dockerfile` (raiz) → Streamlit porta 8501
- **Serviço 2**: `v2/Dockerfile` → FastAPI porta 8000

O `v2/Dockerfile` copia `api.py`, `*.json` e `listas/` da raiz — os dois serviços compartilham o mesmo `api.py`.

---

## Como Rodar Localmente

```bash
# FastAPI v2
cd v2
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Testes
cd /home/user/Sistema
pytest v2/tests/test_flows.py -v
```

---

## Autenticação

- Login por usuário/senha → cookie `session_token`
- Sessões armazenadas em `sessoes.json`
- Controle por setor (`setores.json`): cada setor tem lista de `paginas` permitidas
- Setores: `admin`, `gerencia`, `estoque`, `compras`, `vendas`
- Endpoint de auth: `POST /api/login`, `POST /api/logout`, `GET /api/me`

---

## Frontend (app.js) — Padrões

**Estado global:**
```javascript
Estado = { me, lojas, lojaId, cat, pagina }
```

**Helpers de fetch:**
```javascript
api(path, opts)        // GET com tratamento de 401
apiPost(path, body)    // POST JSON
```

**Cada página** = função `renderXxx(cont)` adicionada ao objeto `PAGINAS`.

**Roteamento:** SPA cliente-side sem hash. `navegar(pagina)` muda DOM.

**Voz:** `ativarMicWhisper(btn, onTexto)` — MediaRecorder → `/api/voz/transcrever` (Whisper). Funciona em todos os browsers modernos (não depende de SpeechRecognition).

---

## Persistência de Dados

| Dado | Onde fica | Como acessar |
|---|---|---|
| Usuários/setores | `usuarios.json` / `setores.json` | `carregar_usuarios()`, `carregar_setores()` |
| Cache de produtos | `cache_produtos_{lojaId}.json` | `carregar_cache(loja_id)` |
| Listas salvas | `listas/*.json` + GitHub | `salvar_lista()`, `listar_listas_salvas()` |
| Disponibilidade | `disponibilidade_lojas.json` | `carregar_disponibilidade()` |
| Sessões | `sessoes.json` | `criar_sessao()`, `validar_sessao()` |
| Docs remotos | Supabase (se configurado) | `db.ler()`, `db.salvar()` |

---

## Integrações Externas

| Serviço | O que faz | Função em api.py |
|---|---|---|
| **GestaoClick** | Catálogo, estoque, vendas, compras | `sincronizar_produtos()`, `buscar_vendas()`, etc. |
| **Claude (Anthropic)** | Parse de pedidos WhatsApp em texto | `parse_pedido_whatsapp()` |
| **OpenAI Whisper** | Transcrição de áudio | `transcrever_audio()` / `POST /api/voz/transcrever` |
| **GitHub API** | Persistência de listas | `_gh_push_arquivo()`, `_gh_listar_listas()` |
| **Supabase** | BD remoto opcional | `db.py` com fallback automático |
| **Sentry** | Erros em produção (v2) | `sentry_sdk.init()` em `v2/main.py` |

---

## Endpoints FastAPI (v2/main.py) — Mapa Rápido

```
Auth:         POST /api/login  POST /api/logout  GET /api/me
Lojas:        GET /api/lojas
Dashboard:    GET /api/dashboard
Estoque:      GET /api/estoque  GET /api/grupos  GET /api/disponibilidade  POST /api/disponibilidade
              POST /api/estoque/ajustar
Preços:       GET /api/precos  POST /api/precos
Produtos:     GET /api/produtos/buscar  POST /api/produtos/criar  POST /api/produtos/clonar
Clientes:     GET /api/clientes
Fornecedores: GET /api/fornecedores
Transações:   GET /api/vendas  GET /api/orcamentos  GET /api/compras  GET /api/financeiro
Pedido:       POST /api/pedido/whatsapp  POST /api/pedido/registrar  GET /api/pedido/kits
Entrada:      POST /api/entrada/whatsapp  GET /api/entrada/codigo
              POST /api/entrada/importar-excel  POST /api/entrada/importar-nfe
              GET /api/entrada/template  POST /api/entrada/aprovacao
Listas:       GET /api/listas  POST /api/listas  GET /api/listas/{arq}  DELETE /api/listas/{arq}
Etiquetas:    GET /api/etiquetas/formatos  POST /api/etiquetas/pdf
Aprovações:   GET /api/aprovacoes  POST /api/aprovacoes/{id}
Usuários:     GET/POST /api/usuarios  PUT/DELETE /api/usuarios/{login}
Sync:         GET /api/sincronizacao/status  POST /api/sincronizar
Voz:          POST /api/voz/transcrever  (Whisper, requer OPENAI_API_KEY)
Health:       GET /health
```

---

## Testes

```bash
pytest v2/tests/test_flows.py -v
```

14 testes cobrindo: health, login/logout, me, lojas, dashboard, grupos, estoque, etc.
Os testes rodam contra o app ao vivo (`AsyncClient` httpx).

---

## Decisões Técnicas Importantes

- **Sem npm/webpack**: frontend é JS puro sem build step. Tudo em um único `app.js`.
- **api.py é a fonte da verdade**: qualquer lógica de negócio fica aqui, nunca nos backends.
- **Supabase é opcional**: `db.py` faz fallback silencioso para GitHub se não configurado.
- **Credenciais GestaoClick são hardcoded** em `api.py` (não há plano de mover para env vars no momento).
- **Voz usa MediaRecorder + Whisper** (não SpeechRecognition, que só funciona no Chrome).

---

## O que Já Foi Implementado (sessões anteriores)

- `buscar_estoque_ao_vivo()` em `api.py` — query direta na GestaoClick sem cache
- `db.py` — camada Supabase com fallback
- Wrappers Supabase em `api.py` (usuários, setores, custos, disponibilidade, listas)
- Sentry integrado em `v2/main.py`
- Endpoint `POST /api/voz/transcrever` em `v2/main.py`
- `ativarMicWhisper()` em `app.js` — gravação via MediaRecorder → Whisper
- Botão 🎤 Voz em Entrada (modoWpp) e Pedido de Compra
- 14 testes em `v2/tests/test_flows.py`
