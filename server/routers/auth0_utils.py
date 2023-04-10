import datetime
import http.client
import json
import os
import pprint
import time
from functools import lru_cache
from typing import Dict, Any
from urllib.parse import urlencode

# temp remove
from auth0.management import Users
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException
from fastapi import Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from loguru import logger

from server.datastore.users_repository import UsersRepository, AccessToken, AppUser, get_users_repository

# secret_key = b64encode(os.urandom(16)).decode('utf-8')


auth0_client_id = os.environ.get("AUTH0_CLIENT_ID")
auth0_client_secret = os.environ.get("AUTH0_CLIENT_SECRET")
# dev-tuuwr1anluaql1ho.us.auth0.com
auth0_domain = os.environ.get("AUTH0_DOMAIN")

auth0_management_client_id = os.environ.get("AUTH0_MANAGEMENT_CLIENT_ID")
auth0_management_client_secret = os.environ.get("AUTH0_MANAGEMENT_CLIENT_SECRET")
auth0_management_domain = os.environ['AUTH0_MANAGEMENT_DOMAIN']
logger.info(f'Auth0 domain: {auth0_domain}')
auth0 = OAuth()
auth0.register(
    name="auth0",
    client_id=auth0_client_id,
    client_secret=auth0_client_secret,
    api_base_url=f"https://{auth0_domain}",
    access_token_url=f"https://{auth0_domain}/oauth/token",
    authorize_url=f"https://{auth0_domain}/authorize",
    client_kwargs={
        "scope": "openid profile"
    },
    server_metadata_url=f'https://{auth0_domain}/.well-known/openid-configuration'
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{auth0_domain}/authorize",
    tokenUrl=f"https://{auth0_domain}/oauth/token",
    scopes={"openid": "OpenID Connect authentication", "profile": "User profile information"},
)


# login_repo = LoginRepository(namespace=os.environ.get('ENVIRONMENT', 'production'))


async def auth0_login_request(request: Request):
    # Save the redirect_uri in the user's session
    request.session["redirect_uri"] = request.query_params.get("redirect_uri")
    redirect_uri = f"{request.url_for('auth0_callback')}"
    logger.info(f'Redirect uri {redirect_uri}')
    auth0_client = auth0.create_client('auth0')
    return await auth0_client.authorize_redirect(request, redirect_uri)


def get_ttl_hash(seconds=3600 * 23):
    return round(time.time() / seconds)


@lru_cache()
def get_auth0_management_api_token(ttl_hash: int = None) -> str:
    conn = http.client.HTTPSConnection(auth0_management_domain)
    payload = urlencode({
        'grant_type': 'client_credentials',
        'client_id': auth0_management_client_id,
        'client_secret': auth0_management_client_secret,
        'audience': f'https://{auth0_management_domain}/api/v2/'
    })
    # grant_type=client_credentials&client_id=xxx&client_secret=xxx&audience=https://dev-tuuwr1anluaql1ho.us.auth0.com/api/v2/
    headers = {'content-type': "application/x-www-form-urlencoded"}
    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    data = res.read()
    response_data = json.loads(data.decode("utf-8"))
    logger.debug(f'auth0_management_api_token {data}')
    return response_data["access_token"]


# ,
#                                  management_token: str = Depends(get_auth0_management_api_token)
async def auth0_callback_request(request: Request):
    auth0_client = auth0.create_client('auth0')
    token = await auth0_client.authorize_access_token(request)
    logger.info(f'auth0 user_info {pprint.pformat(token)}')
    try:

        expiry_date = datetime.datetime.fromtimestamp(token['expires_at'] / 1000.0)
        access_token = AccessToken(access_token=token['access_token'], expiry_date=expiry_date)
        userinfo_ = token['userinfo']
        twitter_id = userinfo_['sub'].split('|')[1]
        # , management_token
        auth0_user = await get_twitter_credentials(twitter_id)
        users: UsersRepository = get_users_repository()
        users.upsert_user(access_token=access_token, refresh_token='', user_id=twitter_id,
                          userinfo=auth0_user)
    except Exception as e:
        logger.exception('auth0_callback_request')

    result = {
        "access_token": token["access_token"],
        "token_type": "Bearer",
        "expires_in": token.get("expires_in", 36000),
        "scope": "openid profile"
    }
    return result


async def get_twitter_credentials(user_id) -> Dict[
    str, Any]:
    management_token = get_auth0_management_api_token(ttl_hash=get_ttl_hash())
    logger.info(f'Management token {management_token}')
    users = Users(auth0_domain, management_token)
    res = users.get(id=f'twitter|{user_id}')
    logger.debug(f'Management API result: {pprint.pformat(res)}')
    return res


async def no_auth_user() -> AppUser:
    users = get_users_repository()
    return users.get_user("15219792")


async def validate_token(token: str = Depends(oauth2_scheme)) -> AppUser:
    try:
        users: UsersRepository = get_users_repository()
        user = users.get_user_by_access_token(token)
        if not user:
            raise HTTPException(status_code=401, detail='User with access token not found')
        return user
    except Exception as e:
        logger.error(e)

# DEFAULT_OAUTH2_REDIRECT_URI = "https://social.rolebotics.com/api/oauth.v2.access"

# @auth_router.post('')
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     # Decode and validate the token, retrieve user information from the token or database
#     # ...
#     return {}
#
#
# @auth_router.get("/secure-endpoint")
# async def secure_endpoint(current_user: Dict[str, str] = Depends(get_current_user)):
#     # Your secure endpoint logic here
#     ...


# def start():
#     uvicorn.run("auth0_route:app", host="0.0.0.0", port=8000, reload=True)
#
#
# if __name__ == '__main__':
#     start()
