from fastapi import FastAPI

from app.api.errors import registrar_handlers
from app.api.middleware import log_requisicoes
from app.api.routers import auth, catalogo, pedido
from app.core.config import settings
from app.core.logging import configurar_logs

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Back-end da rede de lanchonetes Raizes do Nordeste. "
        "Projeto Multidisciplinar - Trilha Back-End."
    ),
)


@app.get("/health", tags=["infra"])
def health():
    """Endpoint de verificacao: confirma que a API esta no ar."""
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(pedido.router)
app.include_router(catalogo.router)
registrar_handlers(app)
configurar_logs()
app.middleware("http")(log_requisicoes)
