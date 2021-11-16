import json

import requests
from requests.auth import HTTPBasicAuth

from lectorium_zoom_pull.secrets import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI


OAUTH_ENDPOINT = 'https://zoom.us/oauth/token'


def load_refresh_token(path: str) -> str:
    with open(path, 'r') as fd:
        tokens = json.load(fd)
        return tokens['refresh_token']


def store_tokens(tokens: dict, path: str) -> None:
    with open(path, 'w') as fd:
        json.dump(tokens, fd)


def call_oauth(request_body: dict) -> dict:
    response = requests.post(
        OAUTH_ENDPOINT,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data=request_body,
    )
    if response.status_code != 200:
        raise ValueError('Bad response {}: {}'.format(
            response.status_code, response.text
        ))

    return json.loads(response.text)


def authorize(path, auth_code=None) -> dict:
    if auth_code:
        request_body = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': REDIRECT_URI,
        }
    else:
        current_refresh_token = load_refresh_token(path)
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': current_refresh_token,
        }

    tokens = call_oauth(request_body)
    store_tokens(tokens, path)
    return tokens
