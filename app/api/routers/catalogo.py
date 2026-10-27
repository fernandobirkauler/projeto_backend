from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual, requer_perfil
from app.api.schemas.catalogo import (
    EstoqueCreate,
    EstoqueOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
    UnidadeCreate,
    UnidadeOut,
    UnidadeUpdate,
)
from app.domain.enums import Perfil
from app.domain.models.estoque import Estoque
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(tags=["catalogo"])

gestores = requer_perfil(Perfil.GERENTE, Perfil.ADMIN)


@router.post("/unidades", response_model=UnidadeOut, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    dados: UnidadeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    unidade = Unidade(**dados.model_dump())
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


@router.get("/unidades", response_model=list[UnidadeOut])
def listar_unidades(
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    stmt = select(Unidade)
    if not incluir_inativos:
        stmt = stmt.where(Unidade.ativo.is_(True))
    return list(db.scalars(stmt).all())


@router.patch("/unidades/{unidade_id}", response_model=UnidadeOut)
def atualizar_unidade(
    unidade_id: int,
    dados: UnidadeUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=404, detail="Unidade nao encontrada")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(unidade, campo, valor)

    db.commit()
    db.refresh(unidade)
    return unidade


@router.delete("/unidades/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=404, detail="Unidade nao encontrada")

    unidade.ativo = False
    db.commit()
    return None


@router.post("/produtos", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    stmt = select(Produto)
    if not incluir_inativos:
        stmt = stmt.where(Produto.ativo.is_(True))
    return list(db.scalars(stmt).all())


@router.patch("/produtos/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    produto.ativo = False
    db.commit()
    return None


@router.post("/estoques", response_model=EstoqueOut, status_code=status.HTTP_201_CREATED)
def definir_estoque(
    dados: EstoqueCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(gestores),
):
    estoque = db.scalar(
        select(Estoque).where(
            Estoque.unidade_id == dados.unidade_id,
            Estoque.produto_id == dados.produto_id,
        )
    )
    if estoque is None:
        estoque = Estoque(
            unidade_id=dados.unidade_id,
            produto_id=dados.produto_id,
            quantidade=dados.quantidade,
        )
        db.add(estoque)
    else:
        estoque.quantidade = dados.quantidade
    db.commit()
    db.refresh(estoque)
    return estoque
