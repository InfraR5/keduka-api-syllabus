from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    moodle_url: str
    moodle_token: str
    
    # Optional: Default fallback program if needed globally, but logic handles it.
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
