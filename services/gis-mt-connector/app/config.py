from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # URL-ы
    auth_base_url: str = "https://markirovka.sandbox.crptech.ru"
    true_api_base_url: str = "https://markirovka.sandbox.crptech.ru/api/v3/true-api"
    true_api_base_url_v4: str = "https://markirovka.sandbox.crptech.ru/api/v4/true-api"
    signer_url: str = "http://local-signer-stub:8000/sign"
    database_url: str = "sqlite:///./connector.db"

    # Идентификаторы OMS
    oms_connection: str = ""
    oms_id: str = ""

    # ИНН участника
    participant_inn: str = ""

    # Товарная группа для документов LK_RECEIPT
    product_group: str = "wheelchairs"

    # Настройки кэширования и лимитов
    token_cache_seconds: int = 36000
    rate_limit_per_sec: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"