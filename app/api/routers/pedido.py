from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual, requer_perfil
from app.api.schemas.pedido import (
    ItemPedidoOut,
    PagamentoCreate,
    PagamentoOut,
    PedidoCreate,
    PedidoOut,
    StatusUpdate,
)
from app.domain.enums import (
    CanalPedido,
    Perfil,
    StatusPagamento,
    StatusPedido,
    TipoMovimento,
)
from app.domain.models.estoque import Estoque
from app.domain.models.item_pedido import ItemPedido
from app.domain.models.movimento_pontos import MovimentoPontos
from app.domain.models.pagamento import Pagamento
from app.domain.models.pedido import Pedido
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

TRANSICOES = {
    StatusPedido.AGUARDANDO_PAGAMENTO: {StatusPedido.CANCELADO},
    StatusPedido.EM_PREPARO: {StatusPedido.PRONTO, StatusPedido.CANCELADO},
    StatusPedido.PRONTO: {StatusPedido.ENTREGUE, StatusPedido.CANCELADO},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}


def _to_out(pedido: Pedido, itens: list[ItemPedido]) -> PedidoOut:
    return PedidoOut(
        id=pedido.id,
        unidade_id=pedido.unidade_id,
        canalPedido=pedido.canal_pedido,
        status=pedido.status,
        valor_total=pedido.valor_total,
        itens=[ItemPedidoOut.model_validate(i) for i in itens],
    )


def _devolver_estoque(db: Session, pedido: Pedido) -> None:
    itens = db.scalars(select(ItemPedido).where(ItemPedido.pedido_id == pedido.id)).all()
    for item in itens:
        estoque = db.scalar(
            select(Estoque).where(
                Estoque.unidade_id == pedido.unidade_id,
                Estoque.produto_id == item.produto_id,
            )
        )
        if estoque is not None:
            estoque.quantidade += item.quantidade


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    dados: PedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    unidade = db.get(Unidade, dados.unidade_id)
    if unidade is None:
        raise HTTPException(status_code=404, detail="Unidade nao encontrada")
    if not unidade.ativo:
        raise HTTPException(status_code=409, detail="Unidade inativa")

    quantidades: dict[int, int] = {}
    for item in dados.itens:
        quantidades[item.produto_id] = quantidades.get(item.produto_id, 0) + item.quantidade

    produtos: dict[int, Produto] = {}
    estoques: dict[int, Estoque] = {}
    for produto_id, quantidade in quantidades.items():
        produto = db.get(Produto, produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado")
        if not produto.ativo:
            raise HTTPException(status_code=409, detail=f"Produto {produto_id} indisponivel")

        estoque = db.scalar(
            select(Estoque).where(
                Estoque.unidade_id == dados.unidade_id,
                Estoque.produto_id == produto_id,
            )
        )
        if estoque is None or estoque.quantidade < quantidade:
            raise HTTPException(
                status_code=409,
                detail=f"Estoque insuficiente: produto {produto_id}",
            )
        produtos[produto_id] = produto
        estoques[produto_id] = estoque

    total = Decimal("0")
    itens: list[ItemPedido] = []
    for item in dados.itens:
        produto = produtos[item.produto_id]
        total += produto.preco * item.quantidade
        itens.append(
            ItemPedido(
                produto_id=produto.id,
                quantidade=item.quantidade,
                preco_unitario=produto.preco,
            )
        )

    for produto_id, quantidade in quantidades.items():
        estoques[produto_id].quantidade -= quantidade

    pedido = Pedido(
        usuario_id=usuario.id,
        unidade_id=dados.unidade_id,
        canal_pedido=dados.canalPedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        valor_total=total,
    )
    db.add(pedido)
    db.flush()
    for item_pedido in itens:
        item_pedido.pedido_id = pedido.id
        db.add(item_pedido)
    db.commit()
    db.refresh(pedido)
    return _to_out(pedido, itens)


@router.get("", response_model=list[PedidoOut])
def listar_pedidos(
    canalPedido: CanalPedido | None = None,
    status_pedido: StatusPedido | None = Query(None, alias="status"),
    unidadeId: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    stmt = select(Pedido)

    # Cliente so enxerga os proprios pedidos (LGPD: minimizacao de dados).
    if usuario.perfil == Perfil.CLIENTE:
        stmt = stmt.where(Pedido.usuario_id == usuario.id)
    if canalPedido is not None:
        stmt = stmt.where(Pedido.canal_pedido == canalPedido)
    if status_pedido is not None:
        stmt = stmt.where(Pedido.status == status_pedido)
    if unidadeId is not None:
        stmt = stmt.where(Pedido.unidade_id == unidadeId)

    pedidos = db.scalars(stmt).all()

    resultado = []
    for pedido in pedidos:
        itens = db.scalars(select(ItemPedido).where(ItemPedido.pedido_id == pedido.id)).all()
        resultado.append(_to_out(pedido, list(itens)))
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
        raise HTTPException(status_code=409, detail="Pedido nao esta aguardando pagamento")

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
        _devolver_estoque(db, pedido)

    db.commit()
    db.refresh(pagamento)
    return pagamento


@router.patch("/{pedido_id}/status", response_model=PedidoOut)
def atualizar_status(
    pedido_id: int,
    dados: StatusUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requer_perfil(Perfil.COZINHA, Perfil.GERENTE, Perfil.ADMIN)),
):
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if dados.status not in TRANSICOES[pedido.status]:
        raise HTTPException(
            status_code=409,
            detail=f"Transicao invalida: {pedido.status.value} -> {dados.status.value}",
        )

    if dados.status == StatusPedido.CANCELADO:
        _devolver_estoque(db, pedido)

    pedido.status = dados.status
    db.commit()
    db.refresh(pedido)

    itens = db.scalars(select(ItemPedido).where(ItemPedido.pedido_id == pedido.id)).all()
    return _to_out(pedido, list(itens))
