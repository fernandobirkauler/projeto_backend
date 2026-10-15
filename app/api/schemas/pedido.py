from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import CanalPedido, StatusPedido


class ItemPedidoIn(BaseModel):
    produto_id: int
    quantidade: int


class PedidoCreate(BaseModel):
    unidade_id: int
    canalPedido: CanalPedido
    itens: list[ItemPedidoIn]


class ItemPedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    quantidade: int
    preco_unitario: Decimal


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unidade_id: int
    canalPedido: CanalPedido
    status: StatusPedido
    valor_total: Decimal
    itens: list[ItemPedidoOut] = []
