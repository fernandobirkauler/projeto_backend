from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import TipoMovimento


class SaldoOut(BaseModel):
    usuario_id: int
    pontos: int


class MovimentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int | None = None
    tipo: TipoMovimento
    pontos: int
    criado_em: datetime
