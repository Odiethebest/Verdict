from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    EVAL_CONCURRENCY: int = 20
    JUDGE_MODEL: str = "gpt-4o-mini"
    JUDGE_TEMPERATURE: float = 0.0
    JUDGE_SAMPLES: int = 1


settings = Settings()
