import logging
import time

from fastapi import Request

logger = logging.getLogger("raizes.api")


async def log_requisicoes(request: Request, call_next):
    inicio = time.perf_counter()
    resposta = await call_next(request)
    duracao_ms = (time.perf_counter() - inicio) * 1000
    logger.info(
        "%s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        resposta.status_code,
        duracao_ms,
    )
    return resposta
