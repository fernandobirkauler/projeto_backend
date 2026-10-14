# API Raízes do Nordeste — Back-end

Back-end do Projeto Multidisciplinar (Trilha Back-End): rede de lanchonetes com
pedidos multicanal (APP, TOTEM, BALCAO, PICKUP, WEB).

## Stack

- **Python 3.14** + **FastAPI** (Swagger automático em `/docs`)
- **SQLAlchemy** + **SQLite** (troca para Postgres só mudando a URL)
- **Alembic** (migrations)
- **PyJWT** + **bcrypt** (autenticação e hash de senha)

## Pré-requisitos

- Python 3.12+
- Git

## Como configurar

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Copiar variáveis de ambiente
copy .env.example .env        # Windows
```

## Como rodar

```bash
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- **Swagger:** http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Como rodar migrations (Alembic)

```bash
.venv\Scripts\alembic revision --autogenerate -m "descricao"
.venv\Scripts\alembic upgrade head
```

## Estrutura do projeto (camadas)

```
app/
  core/            configuracao (settings, .env)
  domain/          entidades e regras de negocio        <-- VOCE ESCREVE
  application/     casos de uso / servicos              <-- VOCE ESCREVE
  infrastructure/  banco, repositorios, integracoes     (base pronta)
  api/             rotas, auth, contratos (FastAPI)     <-- VOCE ESCREVE
  main.py          criacao da aplicacao FastAPI
migrations/        arquivos gerados pelo Alembic
```

## TODO (o que implementar)

- [ ] Definir entidades do dominio (Usuario, Unidade, Produto, Estoque, Pedido, ItemPedido, Pagamento, Fidelidade)
- [ ] Criar models SQLAlchemy + migrations
- [ ] Implementar autenticacao JWT + hash de senha (bcrypt)
- [ ] Implementar autorizacao por perfis/roles
- [ ] Implementar endpoints de pedidos (com `canalPedido`)
- [ ] Implementar pagamento mock
- [ ] Implementar padrao de erro global (JSON unico)
- [ ] Implementar logs/auditoria
- [ ] Criar seed do banco
- [ ] Colecao Postman/Insomnia com 10+ cenarios

## Evidências (preencher)

- Repositório: `<link>`
- Swagger local: http://127.0.0.1:8000/docs
- Coleção Postman/Insomnia: `<caminho do arquivo .json>`
