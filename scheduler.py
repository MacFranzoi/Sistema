"""Tarefas em background — roda junto com o Streamlit no Railway."""
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

        # Atualização rápida de estoque a cada 15 minutos
        sched.add_job(
            _atualizar_estoque_cache,
            IntervalTrigger(minutes=15),
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

        sched.start()
        logger.info("Scheduler iniciado: sync 2h, estoque 15min, sync diário 6h")

    except ImportError:
        logger.warning("APScheduler não instalado — tarefas automáticas desativadas")
    except Exception as e:
        logger.error(f"Erro ao iniciar scheduler: {e}")
