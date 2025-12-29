from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    moodle_url: str = "https://seu-moodle.com/webservice/rest/server.php"
    moodle_token: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Expose as simple variables for compatibility with user's client code style
MOODLE_URL = settings.moodle_url
# Token commented/optional as requested
MOODLE_TOKEN = settings.moodle_token or "TOKEN_NAO_CONFIGURADO"
