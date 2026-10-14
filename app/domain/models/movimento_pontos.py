from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import TipoMovimento
from app.infrastructure.database import Base


class MovimentoPontos(Base):
    __tablename__ = "movimentos_pontos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"), nullable=True)
    tipo: Mapped[TipoMovimento] = mapped_column(Enum(TipoMovimento))
    pontos: Mapped[int] = mapped_column()
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
