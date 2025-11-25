from pydantic_settings import BaseSettings


class Config(BaseSettings):
    TIMEZONE: str = "Europe/Kyiv"
    MONGODB_URI: str = "mongodb://mock"
    TELEGRAM_BOT_TOKEN: str = "mock_token"
    TELEGRAM_GROUP: str = "mock_group"
    ACCOUNT_NUMBER: str = "mock_account"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Config()
