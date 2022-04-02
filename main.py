import os
import pathlib
import pickle

from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

load_dotenv()

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

# RFC的には上でもよさそう
# https://stackoverflow.com/questions/46643795/oauth-2-device-flow-redirect-url
# ただ、Doorkeeperの仕様により、以下の値を使うと画面に認可コードが表示されるようになる
# https://github.com/doorkeeper-gem/doorkeeper/wiki/Authorization-Code-Flow
# REDIRECT_URI = 'com.example.thinkami:/oauthlib/sample'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
REQUEST_SCOPE = 'read'

AUTHORIZATION_SERVER_BASE_URL = 'http://localhost:3801'
AUTHORIZE_URL = f'{AUTHORIZATION_SERVER_BASE_URL}/oauth/authorize'
TOKEN_URL = f'{AUTHORIZATION_SERVER_BASE_URL}/oauth/token'

BASE_DIR = pathlib.Path(__file__).resolve().parent
OAUTH_TOKEN_FILE_PATH = f'{BASE_DIR}/oauth_token.pickle'

# 本来、OAuth2.0はhttps通信が必要
# ただ、今回はlocalhostのASなため、http通信可能にする設定を行っておく
# https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def save_token(token):
    with open(OAUTH_TOKEN_FILE_PATH, 'wb') as f:
        pickle.dump(token, f, protocol=5)
        print('===== tokenを保存しました =====')


def fetch_token():
    # すでにトークン類を取得済の場合は、そのトークン類を使う
    if pathlib.Path(OAUTH_TOKEN_FILE_PATH).is_file():
        with open(OAUTH_TOKEN_FILE_PATH, 'rb') as f:
            return pickle.load(f)

    # トークン類がない場合は、認可コードグラントフローにより取得
    session = OAuth2Session(
        client_id=CLIENT_ID,
        scope=REQUEST_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = session.authorization_url(AUTHORIZE_URL)

    print('URLをブラウザにコピペし、認可コードを取得してください:', authorization_url)
    code = input('表示されている認可コードをコピペしてください: ')

    token = session.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        code=code,
    )

    return token


def fetch_resource_server(token):
    session = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        token=token,
        scope=REQUEST_SCOPE,
        # アクセストークンが有効期限切れの場合、リフレッシュトークンを使って自動更新する
        auto_refresh_url=TOKEN_URL,
        auto_refresh_kwargs={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
        token_updater=save_token,
    )

    return session.get('http://localhost:3801/api/memos/').json()


def main():
    # トークン類の取得
    token = fetch_token()

    # もしトークン類を保存していない場合、保存しておく
    if not pathlib.Path(OAUTH_TOKEN_FILE_PATH).is_file():
        save_token(token)

    # リソースサーバよりデータを取得
    response_body = fetch_resource_server(token)
    print(response_body)


if __name__ == '__main__':
    main()
