from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    moodle_url: str
    moodle_token: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Expose as simple variables for compatibility with user's client code style
MOODLE_URL = settings.moodle_url
MOODLE_TOKEN = settings.moodle_token
