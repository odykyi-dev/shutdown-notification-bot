from pydantic_settings import BaseSettings


class Config(BaseSettings):
    TIMEZONE: str = "Europe/Kyiv"
    MONGODB_URI: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_GROUP: str
    ACCOUNT_NUMBER: str
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Config()
