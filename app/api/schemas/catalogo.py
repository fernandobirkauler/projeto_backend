from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    endereco: str = Field(min_length=1, max_length=200)
    cidade: str = Field(min_length=1, max_length=200)


class UnidadeUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=200)
    endereco: str | None = Field(None, min_length=1, max_length=200)
    cidade: str | None = Field(None, min_length=1, max_length=200)
    ativo: bool | None = None


class UnidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str
    cidade: str
    ativo: bool


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    descricao: str | None = None
    preco: Decimal = Field(gt=0)


class ProdutoUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=200)
    descricao: str | None = None
    preco: Decimal | None = Field(None, gt=0)
    ativo: bool | None = None


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
    quantidade: int = Field(ge=0)


class EstoqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unidade_id: int
    produto_id: int
    quantidade: int
