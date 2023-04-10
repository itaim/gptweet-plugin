import os

from fastapi.responses import JSONResponse
from loguru import logger
from requests_oauthlib import OAuth1Session

from server.datastore.users_repository import AppUser
from server.models.base import TwitterAPIRequest, HttpMethod

consumer_api_key = os.environ.get("TWITTER_APP_KEY")
consumer_secret = os.environ.get("TWITTER_APP_SECRET")


async def tweeter_api_request(
        request: TwitterAPIRequest,
        user: AppUser
):
    # 'identities': [{'access_token': '15219792-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
    #                  'access_token_secret': 'KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71',
    oauth = OAuth1Session(
        client_key=consumer_api_key,
        client_secret=consumer_secret,
        # resource_owner_key=user.twitter_token,
        resource_owner_key='15219792-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
        # resource_owner_secret=user.twitter_token_secret
        resource_owner_secret='KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71'
    )
    if request.method == HttpMethod.POST:
        return oauth.post(request.url, data=request.body, headers={'content-type': 'application/json'})
    elif request.method == HttpMethod.GET:
        return oauth.get(request.url)
    elif request.method == HttpMethod.PUT:
        return oauth.put(request.url, data=request.body, headers={'content-type': 'application/json'})
    elif request.method == HttpMethod.DELETE:
        return oauth.delete(request.url)
    else:
        logger.error(f'Unhandled Method: {request.method}: request: {request}')
        return '{}'
