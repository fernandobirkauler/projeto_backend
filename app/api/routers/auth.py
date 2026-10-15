from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.usuario import TokenOut, UsuarioCreate, UsuarioLogin, UsuarioOut
from app.core.security import criar_token, hash_senha, verificar_senha
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def register(dados: UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    usuario = Usuario(nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenOut)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas"
        )

    token = criar_token({"sub": str(usuario.id)})
    return TokenOut(access_token=token)
