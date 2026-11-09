from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual
from app.api.schemas.fidelidade import MovimentoOut, SaldoOut
from app.domain.enums import Perfil, TipoMovimento
from app.domain.models.movimento_pontos import MovimentoPontos
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(prefix="/fidelidade", tags=["fidelidade"])


def _resolver_usuario(usuario: Usuario, usuarioId: int | None) -> int:
    """Cliente so acessa os proprios pontos; gestao pode consultar outro usuario."""
    if usuarioId is None or usuarioId == usuario.id:
        return usuario.id
    if usuario.perfil == Perfil.CLIENTE:
        raise HTTPException(status_code=403, detail="Cliente so consulta os proprios pontos")
    return usuarioId


def _somar(db: Session, usuario_id: int, tipo: TipoMovimento) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(MovimentoPontos.pontos), 0)).where(
            MovimentoPontos.usuario_id == usuario_id,
            MovimentoPontos.tipo == tipo,
        )
    )
    return int(total or 0)


@router.get("/saldo", response_model=SaldoOut)
def consultar_saldo(
    usuarioId: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    alvo = _resolver_usuario(usuario, usuarioId)
    pontos = _somar(db, alvo, TipoMovimento.ACUMULO) - _somar(db, alvo, TipoMovimento.RESGATE)
    return SaldoOut(usuario_id=alvo, pontos=pontos)


@router.get("/movimentos", response_model=list[MovimentoOut])
def listar_movimentos(
    usuarioId: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    alvo = _resolver_usuario(usuario, usuarioId)
    movimentos = db.scalars(
        select(MovimentoPontos)
        .where(MovimentoPontos.usuario_id == alvo)
        .order_by(MovimentoPontos.criado_em.desc(), MovimentoPontos.id.desc())
    ).all()
    return list(movimentos)
