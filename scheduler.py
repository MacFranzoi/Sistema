"""Tarefas em background — roda junto com o Streamlit no Railway."""
import os
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()


def _sincronizar_todas_lojas():
    """Sincroniza cache de produtos de todas as lojas via API GestãoClick."""
    try:
        import api
        # loja_id=None sincroniza todas; depois sincroniza cada loja individualmente
        lojas = [None] + list(api.LOJAS.keys())
        for loja_id in lojas:
            try:
                api.sincronizar_produtos(loja_id)
                logger.info(f"Cache sincronizado: loja={loja_id}")
            except Exception as e:
                logger.warning(f"Falha sync loja={loja_id}: {e}")
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")


def _atualizar_estoque_cache():
    """Atualiza só o estoque no cache existente (mais rápido que sync completo)."""
    try:
        import api
        import json
        import os
        for loja_id in api.LOJAS.keys():
            try:
                cache = api.carregar_cache(loja_id)
                if not cache:
                    continue
                # Busca estoque ao vivo e atualiza o cache local
                dados = api.buscar_estoque_ao_vivo(loja_id=loja_id, max_paginas=10)
                # Monta mapa produto_id + variacao_id → estoque
                estoque_map = {}
                for p in dados.get("produtos", []):
                    pid = str(p.get("id", ""))
                    for v in p.get("variacoes", []):
                        vd = v.get("variacao", {})
                        vid = str(vd.get("id", ""))
                        estoque_map[f"{pid}_{vid}"] = vd.get("estoque", 0)
                # Aplica no cache
                for p in cache.get("produtos", []):
                    pid = str(p.get("id", ""))
                    for v in p.get("variacoes", []):
                        vd = v.get("variacao", {})
                        vid = str(vd.get("id", ""))
                        k = f"{pid}_{vid}"
                        if k in estoque_map:
                            vd["estoque"] = estoque_map[k]
                # Persiste o cache atualizado diretamente no arquivo
                cache["sincronizado_em"] = datetime.now().isoformat()
                p_path = api.cache_path(loja_id)
                with open(p_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                logger.info(f"Estoque cache atualizado: loja={loja_id}")
            except Exception as e:
                logger.warning(f"Falha atualização estoque loja={loja_id}: {e}")
    except Exception as e:
        logger.error(f"Erro atualização estoque: {e}")


# Último push do cache de vendas pro GitHub (epoch). Usado para não fazer
# commit a cada ciclo de poucos minutos — só de tempos em tempos.
_ultimo_push_vendas = 0.0
# Intervalo mínimo entre pushes ao GitHub (segundos). Default 1h.
_PUSH_VENDAS_INTERVALO = int(os.environ.get("PUSH_VENDAS_INTERVALO_SEG", "3600"))


def _sincronizar_vendas_todas_lojas(completo=False):
    """Monitora vendas de cada loja. Por padrão faz a atualização INCREMENTAL
    (só o dia de hoje, leve). Com completo=True refaz os 6 meses (base).
    Faz push pro GitHub no máximo a cada _PUSH_VENDAS_INTERVALO (evita spam
    de commits quando o intervalo é de minutos)."""
    global _ultimo_push_vendas
    import time as _time
    fazer_push = (_time.time() - _ultimo_push_vendas) >= _PUSH_VENDAS_INTERVALO
    try:
        import api
        for loja_id in list(api.LOJAS.keys()) + [None]:
            try:
                if completo:
                    cv = api.sincronizar_vendas(loja_id, dias=180, push_github=fazer_push)
                else:
                    cv = api.atualizar_vendas_incremental(loja_id, push_github=fazer_push)
                logger.info(f"Vendas {'completas' if completo else 'incrementais'}: "
                            f"loja={loja_id} ({cv.get('pedidos', 0)} vendas)"
                            + (" [+github]" if fazer_push else ""))
            except Exception as e:
                logger.warning(f"Falha sync vendas loja={loja_id}: {e}")
        if fazer_push:
            _ultimo_push_vendas = _time.time()
    except Exception as e:
        logger.error(f"Erro na sincronização de vendas: {e}")


def start():
    """Inicia o scheduler em background. Chama apenas uma vez."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger

        sched = BackgroundScheduler(timezone="America/Sao_Paulo")

        # Sync completo a cada 2 horas
        sched.add_job(
            _sincronizar_todas_lojas,
            IntervalTrigger(hours=2),
            id="sync_lojas",
            replace_existing=True,
            misfire_grace_time=300,
        )

        # Atualização rápida de estoque a cada N minutos (env SYNC_ESTOQUE_MIN, default 1) — monitora mudanças de estoque ao vivo.
        _estoque_min = max(1, int(os.environ.get("SYNC_ESTOQUE_MIN", "1")))
        sched.add_job(
            _atualizar_estoque_cache,
            IntervalTrigger(minutes=_estoque_min),
            id="atualizar_estoque",
            replace_existing=True,
            misfire_grace_time=60,
        )

        # Sync completo todo dia às 6h
        sched.add_job(
            _sincronizar_todas_lojas,
            CronTrigger(hour=6, minute=0),
            id="sync_diario",
            replace_existing=True,
        )

        # Monitor de vendas INCREMENTAL a cada N minutos (só o dia de hoje,
        # leve). Configurável via SYNC_VENDAS_MIN (default 1).
        _venda_min = max(1, int(os.environ.get("SYNC_VENDAS_MIN", "1")))
        sched.add_job(
            _sincronizar_vendas_todas_lojas,
            IntervalTrigger(minutes=_venda_min),
            id="sync_vendas_intervalo",
            replace_existing=True,
            misfire_grace_time=120,
        )

        # Sync COMPLETO de vendas todo dia às 5h (refreeza a base de 6 meses)
        sched.add_job(
            _sincronizar_vendas_todas_lojas,
            CronTrigger(hour=5, minute=0),
            id="sync_vendas_diario",
            kwargs={"completo": True},
            replace_existing=True,
            misfire_grace_time=600,
        )

        sched.start()
        logger.info(f"Scheduler iniciado: produtos 2h, estoque {_estoque_min}min, "
                    f"sync diário 6h, vendas incremental {_venda_min}min + full 5h "
                    f"(push github a cada {_PUSH_VENDAS_INTERVALO//60}min)")

        # Primeira sincronização logo no boot (em thread, sem travar o app).
        # Só sincroniza vendas se ainda não houver cache (evita refazer a cada
        # reinício); o cold start já tenta recuperar do GitHub.
        def _boot_sync():
            try:
                import api
                for loja_id in list(api.LOJAS.keys()) + [None]:
                    if api.carregar_cache_vendas(loja_id):
                        continue  # já tem (local ou recuperado do GitHub)
                    try:
                        cv = api.sincronizar_vendas(loja_id, dias=180, push_github=True)
                        logger.info(f"Boot sync vendas loja={loja_id}: "
                                    f"{cv.get('pedidos', 0)} vendas")
                    except Exception as e:
                        logger.warning(f"Boot sync vendas loja={loja_id} falhou: {e}")
            except Exception as e:
                logger.error(f"Erro no boot sync: {e}")

        threading.Thread(target=_boot_sync, daemon=True).start()

    except ImportError:
        logger.warning("APScheduler não instalado — tarefas automáticas desativadas")
    except Exception as e:
        logger.error(f"Erro ao iniciar scheduler: {e}")
