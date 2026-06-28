"""
EXEMPLO DIDÁTICO — Automação de transferência no GestaoClick com Playwright.

⚠️  Isto é um EXEMPLO para você ver como funcionaria. NÃO faz parte do sistema
    em produção e NÃO roda no servidor (Railway). Deve rodar NA SUA MÁQUINA,
    porque:
      - o reCAPTCHA invisível dá nota baixa para IP de nuvem → login bloqueado;
      - na sua máquina (IP residencial, navegador real) o login passa normal.

────────────────────────────────────────────────────────────────────────────
A ESTRATÉGIA (híbrida — a mais robusta):
  1. Playwright abre um navegador DE VERDADE e faz o login (o reCAPTCHA roda
     sozinho e passa, porque é um navegador real seu).
  2. Depois do login, lemos o cookie `x-token-auth`.
  3. Com o token, criamos a transferência pela API interna (rápido, sem precisar
     clicar em nada) — exatamente o mesmo endpoint que o snippet do sistema usa.

  Ou seja: o navegador serve SÓ para passar pelo login/reCAPTCHA. O trabalho
  pesado (criar 1 ou 200 transferências) é feito por API.

────────────────────────────────────────────────────────────────────────────
COMO RODAR (no seu computador):
    pip install playwright requests
    playwright install chromium

    # Windows (PowerShell):
    $env:GC_EMAIL="seu@email"; $env:GC_SENHA="suasenha"; python transferencia_playwright.py
    # Mac/Linux:
    export GC_EMAIL="seu@email" GC_SENHA="suasenha"
    python transferencia_playwright.py
────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import requests
from playwright.sync_api import sync_playwright

# ── O que transferir (exemplo) ──────────────────────────────────────────────
LOJA_ORIGEM  = {"id": "282941", "nome": "Miller"}
LOJA_DESTINO = {"id": "472451", "nome": "Estoque"}
ITENS = [
    {"codigo": "A010001", "variacao": "Preto / Aveludada", "qtd": 1},
    # {"codigo": "A010002", "variacao": "Branco / Aveludada", "qtd": 3},
]
OBSERVACAO = "Transferência via Playwright (exemplo)"

API = "https://app.api.click.app"


def pegar_token_via_login() -> str:
    """Abre o navegador, faz login e devolve o cookie x-token-auth."""
    email = os.environ["GC_EMAIL"]
    senha = os.environ["GC_SENHA"]

    with sync_playwright() as p:
        # headless=False → janela visível. O reCAPTCHA v3 "confia" mais num
        # navegador real interativo. Você consegue acompanhar/ajudar se precisar.
        navegador = p.chromium.launch(headless=False)
        pagina = navegador.new_page()
        pagina.goto("https://plug.gestaoclick.com/", wait_until="domcontentloaded")

        # ⚠️ Os seletores abaixo são ILUSTRATIVOS — ajuste conforme a tela de
        #    login real (clique direito → Inspecionar no campo para ver o id/name).
        pagina.fill("input[type='email'], input[name='email']", email)
        pagina.fill("input[type='password'], input[name='senha']", senha)
        pagina.click("button[type='submit'], button:has-text('Entrar')")

        # Espera entrar no painel (URL muda para a área logada)
        pagina.wait_for_url("**/estoque**", timeout=60000)

        # Lê o cookie de sessão
        cookies = pagina.context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "x-token-auth"), None)
        navegador.close()

    if not token:
        raise RuntimeError("Não encontrei o cookie x-token-auth após o login.")
    return token


def _num_br(valor: float) -> str:
    """1234.5 → '1234,50' (formato que a API espera)."""
    return f"{valor:.2f}".replace(".", ",")


def _para_float(txt) -> float:
    """'1.234,50' → 1234.5"""
    return float(str(txt).replace(".", "").replace(",", "."))


def criar_transferencia(token: str):
    """Cria a transferência pela API interna, usando o token do login."""
    h = {"x-token-auth": token}

    produtos = []
    for it in ITENS:
        # 1) Descobre os IDs internos (estoque_id, unidade_id) do produto na loja origem
        r = requests.get(
            f"{API}/estoque/produtos/buscaProdutosCompras",
            params={"loja": LOJA_ORIGEM["id"], "q": it["codigo"]},
            headers=h, timeout=20,
        )
        dados = (r.json().get("data") or [])
        if not dados:
            print(f"  ⚠️  não achei {it['codigo']} na loja origem — pulando")
            continue
        prod = dados[0]
        # Casa a variação pelo nome (ex.: "Preto / Aveludada")
        est = next((e for e in prod.get("ProdutosEstoque", [])
                    if e.get("variacoes") == it["variacao"]),
                   (prod.get("ProdutosEstoque") or [None])[0])
        custo = (est and est.get("valor_custo")) or prod.get("valor_custo") or "0,00"
        custo_n = _para_float(custo)
        q = it["qtd"]
        produtos.append({
            "possui_variacao": 1 if str(prod.get("possui_variacao")) == "1" else 0,
            "produto_id":  prod["produto_id"],
            "estoque_id":  est["id"] if est else prod.get("estoque_id"),
            "quantidade":  _num_br(q),
            "unidade_id":  prod.get("unidade_saida_id"),
            "unidade":     prod.get("unidade_saida") or "UN",
            "valor_custo": custo,
            "valor_total": _num_br(custo_n * q),
        })

    if not produtos:
        print("Nada para transferir.")
        return

    valor_total = sum(_para_float(p["valor_total"]) for p in produtos)
    body = {
        "TransferenciasEstoque": {
            "nome_loja_origem":  LOJA_ORIGEM["nome"],
            "loja_origem_id":    LOJA_ORIGEM["id"],
            "nome_loja_destino": LOJA_DESTINO["nome"],
            "loja_destino_id":   LOJA_DESTINO["id"],
            "valor_total":       _num_br(valor_total),
            "observacoes":       OBSERVACAO,
        },
        "TransferenciasEstoquesProduto": produtos,
    }

    # 2) Cria a transferência (mesmo endpoint/headers observados no HAR)
    r = requests.post(
        f"{API}/transferencias_estoques/adicionar",
        headers={**h, "content-type": "multipart/form-data"},
        data=json.dumps(body), timeout=30,
    )
    print("Resposta:", r.status_code, r.text[:300])


if __name__ == "__main__":
    print("1) Fazendo login (uma janela do navegador vai abrir)...")
    tok = pegar_token_via_login()
    print("   token obtido:", tok[:12], "...")
    print("2) Criando transferência via API...")
    criar_transferencia(tok)
    print("Pronto.")
