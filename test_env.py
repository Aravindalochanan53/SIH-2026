from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_SERVER: str = "NONE"
    DB_NAME: str = "NONE"
    DB_DRIVER: str = "NONE"
    DATABASE_URL: str = "NONE"


settings = TestSettings()

print("DB_SERVER:", settings.DB_SERVER)
print("DB_NAME:", settings.DB_NAME)
print("DB_DRIVER:", settings.DB_DRIVER)
print("DATABASE_URL:", settings.DATABASE_URL)