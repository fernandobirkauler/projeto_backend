# API Raízes do Nordeste — Back-end

Back-end do Projeto Multidisciplinar (Trilha Back-End): rede de lanchonetes com
pedidos multicanal (**APP, TOTEM, BALCAO, PICKUP, WEB**), autenticação JWT,
regra de perfil, pagamento mock e programa de fidelidade.

## Stack

- **Python 3.14** + **FastAPI** (Swagger automático em `/docs`)
- **SQLAlchemy 2.x** + **SQLite** (troca para Postgres só mudando a `DATABASE_URL`)
- **Alembic** (migrations)
- **PyJWT** + **bcrypt** (token e hash de senha)
- **Pydantic v2** (validação/contratos)

## Pré-requisitos

- Python 3.12+
- Git

## Como configurar

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate            # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Copiar variáveis de ambiente
copy .env.example .env            # Windows
```

## Como rodar

```bash
# aplica as migrations
.venv\Scripts\alembic upgrade head

# popula dados de exemplo (gerente, unidade, produtos e estoque)
.venv\Scripts\python seed.py

# sobe a API
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- **Swagger:** http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Credenciais do seed

| Perfil | E-mail | Senha |
|---|---|---|
| GERENTE | `gerente@raizes.com` | `gerente123` |
| COZINHA | `cozinha@raizes.com` | `cozinha123` |

> Crie um usuário CLIENTE pelo `POST /auth/register` para testar a regra de perfil.

## Endpoints

| Método | Rota | Quem pode | Descrição |
|---|---|---|---|
| GET | `/health` | público | Verificação da API |
| POST | `/auth/register` | público | Cadastro (nasce como CLIENTE) |
| POST | `/auth/login` | público | Login, retorna o token JWT |
| POST | `/unidades` | GERENTE, ADMIN | Cria unidade |
| GET | `/unidades?incluir_inativos=true` | autenticado | Lista unidades ativas (ou todas) |
| PATCH | `/unidades/{id}` | GERENTE, ADMIN | Edita unidade (campos parciais) |
| DELETE | `/unidades/{id}` | GERENTE, ADMIN | Desativa unidade (*soft delete*) |
| POST | `/produtos` | GERENTE, ADMIN | Cria produto |
| GET | `/produtos?incluir_inativos=true` | autenticado | Lista produtos ativos (ou todos) |
| PATCH | `/produtos/{id}` | GERENTE, ADMIN | Edita produto (campos parciais) |
| DELETE | `/produtos/{id}` | GERENTE, ADMIN | Desativa produto (*soft delete*) |
| POST | `/estoques` | GERENTE, ADMIN | Define/atualiza estoque |
| POST | `/pedidos` | autenticado | Cria pedido (com `canalPedido`) e baixa o estoque |
| GET | `/pedidos?canalPedido=TOTEM&status=PRONTO&unidadeId=1` | autenticado | Filtra por canal, status e unidade (CLIENTE vê só os próprios) |
| POST | `/pedidos/{id}/pagamento` | dono ou gestor | Pagamento mock (aprova/recusa) |
| PATCH | `/pedidos/{id}/status` | COZINHA, GERENTE, ADMIN | Avança status (EM_PREPARO→PRONTO→ENTREGUE) |

## Fluxo principal (MVP)

```
POST /pedidos            -> valida e baixa o estoque, status AGUARDANDO_PAGAMENTO
POST /pedidos/1/pagamento {"aprovado": true}
   |- cria Pagamento APROVADO
   |- pedido.status = EM_PREPARO
   \- credita pontos de fidelidade (MovimentoPontos)
PATCH /pedidos/1/status {"status": "PRONTO"}    (COZINHA)
PATCH /pedidos/1/status {"status": "ENTREGUE"}  (COZINHA)
```

Regras aplicadas no fluxo:

- **Estoque**: validado e **decrementado** na criação; **devolvido** se o pagamento for recusado ou o pedido cancelado.
- **Transições válidas**: `AGUARDANDO_PAGAMENTO→CANCELADO`, `EM_PREPARO→PRONTO|CANCELADO`, `PRONTO→ENTREGUE|CANCELADO`. Transição inválida retorna `409`.
- **Idempotência do pagamento**: tentar pagar um pedido que não está mais aguardando retorna `409`.
- **Catálogo**: unidades e produtos têm edição (`PATCH`) e exclusão lógica (`DELETE` → `ativo=false`), preservando o histórico de pedidos. Pedidos **não são excluídos**: o encerramento é feito por `CANCELADO`.
- **Privacidade (LGPD)**: `GET /pedidos` devolve apenas os pedidos do próprio `CLIENTE`; `COZINHA`, `GERENTE` e `ADMIN` enxergam todos e podem filtrar por `unidadeId`.

### Exemplo rápido (curl)

```bash
# 1. login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"gerente@raizes.com\",\"senha\":\"gerente123\"}"

# 2. criar pedido (troque <TOKEN> e use canalPedido)
curl -X POST http://127.0.0.1:8000/pedidos \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d "{\"unidade_id\":1,\"canalPedido\":\"TOTEM\",\"itens\":[{\"produto_id\":1,\"quantidade\":2}]}"

# 3. pagar
curl -X POST http://127.0.0.1:8000/pedidos/1/pagamento \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d "{\"aprovado\":true}"
```

## Enums de domínio

- **Perfil:** `CLIENTE`, `GERENTE`, `COZINHA`, `ADMIN`
- **canalPedido:** `APP`, `TOTEM`, `BALCAO`, `PICKUP`, `WEB`
- **StatusPedido:** `AGUARDANDO_PAGAMENTO`, `EM_PREPARO`, `PRONTO`, `ENTREGUE`, `CANCELADO`
- **StatusPagamento:** `PENDENTE`, `APROVADO`, `RECUSADO`
- **TipoMovimento:** `ACUMULO`, `RESGATE`

## Erro JSON padronizado

Todas as respostas de erro seguem o mesmo formato:

```json
{
  "erro": {
    "status": 403,
    "mensagem": "Acesso negado para o seu perfil"
  }
}
```

Erros de validação (422) incluem `detalhes`:

```json
{
  "erro": {
    "status": 422,
    "mensagem": "Dados de entrada invalidos",
    "detalhes": [
      { "campo": "body.canalPedido", "mensagem": "Input should be 'APP', 'TOTEM', 'BALCAO', 'PICKUP' or 'WEB'" }
    ]
  }
}
```

## Logs / auditoria

- Cada requisição é registrada via middleware: **método, rota, status e tempo (ms)**.
- A trilha de auditoria de negócio fica nas tabelas `pagamentos` e `movimentos_pontos`.

## DER (Diagrama Entidade-Relacionamento)

```mermaid
erDiagram
    USUARIOS ||--o{ PEDIDOS : "faz"
    USUARIOS ||--o{ MOVIMENTOS_PONTOS : "acumula"
    UNIDADES ||--o{ PEDIDOS : "recebe"
    UNIDADES ||--o{ ESTOQUES : "possui"
    PRODUTOS ||--o{ ESTOQUES : "estocado"
    PRODUTOS ||--o{ ITENS_PEDIDO : "compõe"
    PEDIDOS  ||--o{ ITENS_PEDIDO : "contém"
    PEDIDOS  ||--o{ PAGAMENTOS : "é pago por"
    PEDIDOS  ||--o{ MOVIMENTOS_PONTOS : "gera"

    USUARIOS {
        int id PK
        string nome
        string email
        string senha_hash
        enum perfil
        bool ativo
        datetime criado_em
    }
    UNIDADES {
        int id PK
        string nome
        string endereco
        string cidade
        bool ativo
    }
    PRODUTOS {
        int id PK
        string nome
        string descricao
        numeric preco
        bool ativo
    }
    ESTOQUES {
        int id PK
        int unidade_id FK
        int produto_id FK
        int quantidade
    }
    PEDIDOS {
        int id PK
        int usuario_id FK
        int unidade_id FK
        enum canal_pedido
        enum status
        numeric valor_total
        datetime criado_em
    }
    ITENS_PEDIDO {
        int id PK
        int pedido_id FK
        int produto_id FK
        int quantidade
        numeric preco_unitario
    }
    PAGAMENTOS {
        int id PK
        int pedido_id FK
        enum status
        numeric valor
        datetime criado_em
    }
    MOVIMENTOS_PONTOS {
        int id PK
        int usuario_id FK
        int pedido_id FK
        enum tipo
        int pontos
        datetime criado_em
    }
```

## Estrutura do projeto (camadas)

```
app/
  core/            configuracao (settings, .env, seguranca/JWT, logging)
  domain/          entidades (models) e enums
  infrastructure/  banco (engine, sessao, Base)
  api/
    deps.py        dependencias (usuario atual, regra de perfil)
    errors.py      erro JSON padronizado
    middleware.py  log de requisicoes
    routers/       auth, catalogo, pedido
    schemas/       contratos Pydantic
  main.py          criacao da aplicacao FastAPI
migrations/        arquivos gerados pelo Alembic
postman/           colecao para importar no Postman/Insomnia
seed.py            dados de exemplo
```

## Coleção de testes

Importe o arquivo `postman/raizes-do-nordeste.postman_collection.json` no
Postman ou Insomnia. São **34 requisições** em 4 pastas (Auth, Catalogo,
Pedidos, Erros), com testes automáticos de status e captura de token.

### Cenários (24 principais)

| ID | Cenário | Endpoint | Esperado | Evidência (Postman) |
|---|---|---|---|---|
| T01 | Login válido (gerente) | POST /auth/login | 200 + token | Auth/Login gerente |
| T02 | Cadastro de usuário | POST /auth/register | 201 | Auth/Registrar cliente |
| T03 | Login válido (cozinha) | POST /auth/login | 200 + token | Auth/Login cozinha |
| T04 | Criar unidade (gestor) | POST /unidades | 201 | Catalogo/Criar unidade (gerente) |
| T05 | Criar produto | POST /produtos | 201 | Catalogo/Criar produto |
| T06 | Definir estoque | POST /estoques | 201 | Catalogo/Definir estoque |
| T07 | Listar produtos | GET /produtos | 200 | Catalogo/Listar produtos |
| T08 | Criar pedido TOTEM | POST /pedidos | 201 + AGUARDANDO_PAGAMENTO | Pedidos/Criar pedido TOTEM |
| T09 | Filtrar por canal | GET /pedidos?canalPedido=TOTEM | 200 | Pedidos/Listar (filtro TOTEM) |
| T10 | Pagamento aprovado | POST /pedidos/{id}/pagamento | 201 + APROVADO | Pedidos/Pagar (aprovado) |
| T11 | Status → PRONTO | PATCH /pedidos/{id}/status | 200 + PRONTO | Pedidos/Atualizar → PRONTO |
| T12 | Status → ENTREGUE | PATCH /pedidos/{id}/status | 200 + ENTREGUE | Pedidos/Atualizar → ENTREGUE |
| T13 | Sem token | GET /pedidos | 401 + erro padrão | Erros/Sem token |
| T14 | Perfil sem permissão | POST /unidades (cliente) | 403 + erro padrão | Catalogo/Criar unidade (cliente) |
| T15 | Canal inválido | POST /pedidos | 422 + detalhes | Erros/Canal invalido |
| T16 | Estoque insuficiente | POST /pedidos | 409 + erro padrão | Pedidos/Estoque insuficiente |
| T17 | Transição inválida | PATCH /pedidos/{id}/status | 409 | Pedidos/Transicao invalida |
| T18 | Pagamento recusado | POST /pedidos/{id}/pagamento | 201 + RECUSADO | Pedidos/Pagar (recusado) |
| T19 | Editar unidade | PATCH /unidades/{id} | 200 + nome atualizado | Catalogo/Editar unidade (gerente) |
| T20 | Excluir unidade (*soft delete*) | DELETE /unidades/{id} | 204 e some da listagem | Catalogo/Excluir unidade (gerente) |
| T21 | Editar unidade sem permissão | PATCH /unidades/{id} (cliente) | 403 | Catalogo/Editar unidade (cliente) |
| T22 | Editar produto | PATCH /produtos/{id} | 200 + preço novo | Catalogo/Editar produto |
| T23 | Recurso inexistente | PATCH /unidades/999999 | 404 + erro padrão | Catalogo/Editar unidade inexistente |
| T24 | Pedidos por unidade | GET /pedidos?unidadeId=1 | 200, só da unidade | Pedidos/Listar por unidade (gerente) |

**Ordem sugerida:** Auth → Catalogo → Pedidos → Erros. A coleção captura
automaticamente `tokenGerente`, `tokenCliente`, `tokenCozinha`, `pedidoId` e `pedidoRecusaId`.

## Migrations (Alembic)

```bash
.venv\Scripts\alembic revision --autogenerate -m "descricao"
.venv\Scripts\alembic upgrade head
```

## Qualidade de código

```bash
.venv\Scripts\python -m ruff check app seed.py
.venv\Scripts\python -m ruff format app seed.py
```

## Repositório

- GitHub: https://github.com/fernandobirkauler/projeto_backend
- Swagger local: http://127.0.0.1:8000/docs
- Coleção: `postman/raizes-do-nordeste.postman_collection.json`
