from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class UnidadeCreate(BaseModel):
    nome: str
    endereco: str
    cidade: str


class UnidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str
    cidade: str
    ativo: bool


class ProdutoCreate(BaseModel):
    nome: str
    descricao: str | None = None
    preco: Decimal


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None = None
    preco: Decimal
    ativo: bool


class EstoqueCreate(BaseModel):
    unidade_id: int
    produto_id: int
    quantidade: int


class EstoqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unidade_id: int
    produto_id: int
    quantidade: int
