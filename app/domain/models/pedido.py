from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import CanalPedido, StatusPedido
from app.infrastructure.database import Base


class Pedido(Base):
    __tablename__ = "pedidos"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    canal_pedido: Mapped[CanalPedido] = mapped_column(Enum(CanalPedido))
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO
    )
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
