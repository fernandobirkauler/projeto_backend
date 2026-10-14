from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracoes da aplicacao, lidas do arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "API Raizes do Nordeste"
    database_url: str = "sqlite:///./raizes.db"
    secret_key: str = "troque-esta-chave"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"


settings = Settings()
