from decimal import Decimal

from app.core.security import hash_senha
from app.domain.enums import Perfil
from app.domain.models.estoque import Estoque
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.infrastructure.database import SessionLocal


def seed() -> None:
    db = SessionLocal()
    try:
        gerente = db.query(Usuario).filter_by(email="gerente@raizes.com").first()
        if gerente is None:
            db.add(
                Usuario(
                    nome="Gerente Raizes",
                    email="gerente@raizes.com",
                    senha_hash=hash_senha("gerente123"),
                    perfil=Perfil.GERENTE,
                )
            )
            db.commit()

        unidade = db.query(Unidade).filter_by(nome="Raizes Centro").first()
        if unidade is None:
            unidade = Unidade(nome="Raizes Centro", endereco="Rua do Sol, 100", cidade="Recife")
            db.add(unidade)
            db.commit()
            db.refresh(unidade)

        catalogo = [
            ("Cuscuz Nordestino", "Cuscuz com manteiga de garrafa", "12.50", 50),
            ("Bolo de Rolo", "Fatia de bolo de rolo", "18.00", 30),
            ("Suco de Caja", "Suco natural 500ml", "7.00", 40),
        ]
        for nome, descricao, preco, quantidade in catalogo:
            produto = db.query(Produto).filter_by(nome=nome).first()
            if produto is None:
                produto = Produto(nome=nome, descricao=descricao, preco=Decimal(preco))
                db.add(produto)
                db.commit()
                db.refresh(produto)

            estoque = (
                db.query(Estoque).filter_by(unidade_id=unidade.id, produto_id=produto.id).first()
            )
            if estoque is None:
                db.add(Estoque(unidade_id=unidade.id, produto_id=produto.id, quantidade=quantidade))

        db.commit()
        print("Seed concluido.")
        print("Gerente -> gerente@raizes.com / gerente123")
        print(f"Unidade id={unidade.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
