from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual, requer_perfil
from app.api.schemas.catalogo import (
    EstoqueCreate,
    EstoqueOut,
    ProdutoCreate,
    ProdutoOut,
    UnidadeCreate,
    UnidadeOut,
)
from app.domain.enums import Perfil
from app.domain.models.estoque import Estoque
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(tags=["catalogo"])


@router.post("/unidades", response_model=UnidadeOut, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    dados: UnidadeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requer_perfil(Perfil.GERENTE, Perfil.ADMIN)),
):
    unidade = Unidade(**dados.model_dump())
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


@router.get("/unidades", response_model=list[UnidadeOut])
def listar_unidades(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return list(db.scalars(select(Unidade)).all())


@router.post("/produtos", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requer_perfil(Perfil.GERENTE, Perfil.ADMIN)),
):
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return list(db.scalars(select(Produto)).all())


@router.post("/estoques", response_model=EstoqueOut, status_code=status.HTTP_201_CREATED)
def definir_estoque(
    dados: EstoqueCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requer_perfil(Perfil.GERENTE, Perfil.ADMIN)),
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
