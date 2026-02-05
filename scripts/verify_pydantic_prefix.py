import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mock the environment to simulate the user following .env.example
os.environ["DATABASE_URL"] = "postgresql://localhost:5432/production_db"  # pragma: allowlist secret
# Unset the correct one if it exists
if "ALIM_DATABASE_URL" in os.environ:
    del os.environ["ALIM_DATABASE_URL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ALIM_", case_sensitive=False)
    database_url: str = "sqlite:///default.db"


settings = Settings()
print(f"Env Var 'DATABASE_URL': {os.environ.get('DATABASE_URL')}")
print(f"Settings.database_url: {settings.database_url}")

if settings.database_url == "sqlite:///default.db":
    print("MISMATCH CONFIRMED: Pydantic ignored the non-prefixed variable.")
else:
    print("SURPRISE: Pydantic picked it up.")
