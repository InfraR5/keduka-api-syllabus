from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.config_provider import SSMConfigProvider

class Settings(BaseSettings):
    moodle_url: str = "https://seu-moodle.com/webservice/rest/server.php"
    moodle_host: str = "moodle.r5projetos.com.br"
    moodle_token: Optional[str] = None
    orchestrator_url: str = "http://localhost:8000"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# --- SSM ENHANCEMENT ---
# In production, we override the .env/default token with the one from AWS SSM
ssm = SSMConfigProvider()
# Path convention: /prod/keduka/{service}/moodle_token
_ssm_token = ssm.get_parameter("/prod/keduka/md-api-secao/moodle_token", default=settings.moodle_token)

# Expose as simple variables for compatibility with user's client code style
MOODLE_URL = settings.moodle_url
MOODLE_HOST = settings.moodle_host
MOODLE_TOKEN = _ssm_token or "TOKEN_NAO_CONFIGURADO"
ORCHESTRATOR_URL = settings.orchestrator_url

