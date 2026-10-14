import enum


class Perfil(str, enum.Enum):
    CLIENTE = "CLIENTE"
    GERENTE = "GERENTE"
    COZINHA = "COZINHA"
    ADMIN = "ADMIN"


class CanalPedido(str, enum.Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"


class StatusPedido(str, enum.Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class StatusPagamento(str, enum.Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"


class TipoMovimento(str, enum.Enum):
    ACUMULO = "ACUMULO"
    RESGATE = "RESGATE"
