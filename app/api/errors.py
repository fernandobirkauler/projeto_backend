from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def erro_json(status_code: int, mensagem: str, detalhes: list | None = None) -> JSONResponse:
    corpo = {
        "erro": {
            "status": status_code,
            "mensagem": mensagem,
        }
    }
    if detalhes is not None:
        corpo["erro"]["detalhes"] = detalhes
    return JSONResponse(status_code=status_code, content=corpo)


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return erro_json(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        detalhes = [
            {"campo": ".".join(str(p) for p in e["loc"]), "mensagem": e["msg"]}
            for e in exc.errors()
        ]
        return erro_json(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Dados de entrada invalidos",
            detalhes=detalhes,
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return erro_json(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Erro interno do servidor",
        )
