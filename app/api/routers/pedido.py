from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual
from app.api.schemas.pedido import (
    ItemPedidoOut,
    PagamentoCreate,
    PagamentoOut,
    PedidoCreate,
    PedidoOut,
)
from app.domain.enums import CanalPedido, Perfil, StatusPagamento, StatusPedido, TipoMovimento
from app.domain.models.estoque import Estoque
from app.domain.models.item_pedido import ItemPedido
from app.domain.models.movimento_pontos import MovimentoPontos
from app.domain.models.pagamento import Pagamento
from app.domain.models.pedido import Pedido
from app.domain.models.produto import Produto
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def _to_out(pedido: Pedido, itens: list[ItemPedido]) -> PedidoOut:
    return PedidoOut(
        id=pedido.id,
        unidade_id=pedido.unidade_id,
        canalPedido=pedido.canal_pedido,
        status=pedido.status,
        valor_total=pedido.valor_total,
        itens=[ItemPedidoOut.model_validate(i) for i in itens],
    )


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    dados: PedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    total = Decimal("0")
    itens: list[ItemPedido] = []

    for item in dados.itens:
        produto = db.get(Produto, item.produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail=f"Produto {item.produto_id} nao encontrado")

        estoque = db.scalar(
            select(Estoque).where(
                Estoque.unidade_id == dados.unidade_id,
                Estoque.produto_id == item.produto_id,
            )
        )
        if estoque is None or estoque.quantidade < item.quantidade:
            raise HTTPException(
                status_code=400, detail=f"Estoque insuficiente: produto {item.produto_id}"
            )

        total += produto.preco * item.quantidade
        itens.append(
            ItemPedido(
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco,
            )
        )

    pedido = Pedido(
        usuario_id=usuario.id,
        unidade_id=dados.unidade_id,
        canal_pedido=dados.canalPedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        valor_total=total,
    )
    db.add(pedido)
    db.flush()
    for i in itens:
        i.pedido_id = pedido.id
        db.add(i)
    db.commit()
    db.refresh(pedido)
    return _to_out(pedido, itens)


@router.get("", response_model=list[PedidoOut])
def listar_pedidos(
    canalPedido: CanalPedido | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    stmt = select(Pedido)
    if canalPedido is not None:
        stmt = stmt.where(Pedido.canal_pedido == canalPedido)
    pedidos = db.scalars(stmt).all()

    resultado = []
    for p in pedidos:
        itens = db.scalars(select(ItemPedido).where(ItemPedido.pedido_id == p.id)).all()
        resultado.append(_to_out(p, list(itens)))
    return resultado


@router.post(
    "/{pedido_id}/pagamento",
    response_model=PagamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def pagar_pedido(
    pedido_id: int,
    dados: PagamentoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    eh_gestor = usuario.perfil in (Perfil.GERENTE, Perfil.ADMIN)
    if pedido.usuario_id != usuario.id and not eh_gestor:
        raise HTTPException(status_code=403, detail="Pedido pertence a outro usuario")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(status_code=400, detail="Pedido nao esta aguardando pagamento")

    status_pagamento = StatusPagamento.APROVADO if dados.aprovado else StatusPagamento.RECUSADO
    pagamento = Pagamento(
        pedido_id=pedido.id,
        status=status_pagamento,
        valor=pedido.valor_total,
    )
    db.add(pagamento)

    if dados.aprovado:
        pedido.status = StatusPedido.EM_PREPARO
        db.add(
            MovimentoPontos(
                usuario_id=pedido.usuario_id,
                pedido_id=pedido.id,
                tipo=TipoMovimento.ACUMULO,
                pontos=int(pedido.valor_total),
            )
        )
    else:
        pedido.status = StatusPedido.CANCELADO

    db.commit()
    db.refresh(pagamento)
    return pagamento
