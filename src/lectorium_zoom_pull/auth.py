from datetime import datetime, timezone

import jwt

from lectorium_zoom_pull.config import Config


OAUTH_ENDPOINT = 'https://zoom.us/oauth/token'


def jwt_access_token(config: Config) -> str:
    ALGORITHM = 'HS256'
    TTL_SECONDS = 10

    now = datetime.now(tz=timezone.utc)
    expiration = int(now.timestamp()) + TTL_SECONDS
    payload = {
        'iss': config.api_key.get_secret_value(),
        'exp': expiration
    }
    return jwt.encode(
        payload,
        config.api_secret.get_secret_value(),
        algorithm=ALGORITHM
    )
