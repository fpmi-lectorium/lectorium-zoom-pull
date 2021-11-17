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
    encoded = jwt.encode(
        payload,
        config.api_secret.get_secret_value(),
        algorithm=ALGORITHM
    )

    # Different versions of PyJWT return `bytes' or `str'
    #
    # 1.7.1, which is system-provided in Ubuntu 20.04.3, returns `bytes'
    # Starting 2.0.0, docs claim to return `str'
    if isinstance(encoded, bytes):
        encoded = encoded.decode()

    return encoded
