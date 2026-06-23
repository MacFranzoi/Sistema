# Sistema Plug 2.0

Versão nova do sistema, **fora do Streamlit**: backend **FastAPI** + frontend
**SPA** em HTML/CSS/JS puro (sem npm, sem build). Reaproveita 100% do `api.py`
da raiz do repositório.

Roda em **paralelo** ao sistema atual (Streamlit) — os dois usam o mesmo
`api.py`, os mesmos caches e a mesma persistência via GitHub.

## Estrutura

```
v2/
├── main.py            # backend FastAPI (importa o api.py da raiz)
├── requirements.txt
├── Dockerfile         # build a partir da RAIZ do repo
├── static/
│   ├── index.html     # casca do app (nav fixo + área de conteúdo)
│   ├── app.js         # roteador SPA + chamadas ao backend
│   └── style.css      # tema escuro, cara de app
└── README.md
```

## Rodar localmente (teste)

A partir da **raiz** do repositório:

```bash
pip install -r v2/requirements.txt
cd v2
uvicorn main:app --reload --port 8000
```

Abra http://localhost:8000

> Sem `GITHUB_TOKEN` configurado, o login usa o `usuarios.json` local.
> Usuário padrão: `gustavo` / senha `admin`.

## Deploy no Railway (2º serviço)

1. No **mesmo projeto** Railway, crie um **novo serviço** a partir do mesmo
   repositório GitHub.
2. Em **Settings → Build**:
   - **Dockerfile Path**: `v2/Dockerfile`
   - **Root Directory**: deixe na raiz (`/`) — o Dockerfile precisa do `api.py`
     e dos caches da raiz.
3. Em **Variables**, copie as mesmas do serviço atual:
   - `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
4. Gere um domínio próprio (ex: `app2-...up.railway.app`) para testar **sem
   mexer no sistema atual**.

O serviço do Streamlit continua no ar normalmente. Quando o 2.0 estiver
completo, basta apontar o domínio principal para ele e desligar o Streamlit.

## Endpoints (backend)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/login` | Login (cria sessão em cookie) |
| POST | `/api/logout` | Encerra sessão |
| GET  | `/api/me` | Usuário logado + menu permitido |
| GET  | `/api/lojas` | Lista de lojas |
| GET  | `/api/dashboard` | Totais por loja |
| GET  | `/api/estoque` | Busca de estoque ao vivo |
| GET  | `/api/diagnostico` | Status das credenciais |
| GET  | `/api/docs` | Documentação automática (Swagger) |

## Status das telas

- ✅ Login, navegação (menu fixo, SPA), Dashboard, Estoque ao vivo
- 🚧 Demais telas: mostram placeholder "em construção" — migração incremental
