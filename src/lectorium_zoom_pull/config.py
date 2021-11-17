from pydantic import BaseSettings, SecretStr


class Config(BaseSettings):
    account_id: str
    api_key: SecretStr
    api_secret: SecretStr
    download_progress: bool = False
    debug: bool = False

    class Config:
        env_prefix = 'LZP_'
        case_sensitive = False
