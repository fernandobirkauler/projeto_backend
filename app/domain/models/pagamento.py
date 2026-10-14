from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import StatusPagamento
from app.infrastructure.database import Base


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    status: Mapped[StatusPagamento] = mapped_column(
        Enum(StatusPagamento), default=StatusPagamento.PENDENTE
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
