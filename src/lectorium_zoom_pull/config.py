import os

from pydantic import BaseSettings, SecretStr


class Config(BaseSettings):
    account_id: str
    api_key: SecretStr
    api_secret: SecretStr

    class Config:
        env_prefix = 'LZP_'
        secrets_dir = os.getenv('LZP_SECRETS_DIR') or '/run/secrets'
        case_sensitive = False
