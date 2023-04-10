import os

from fastapi import Depends, Body
from fastapi.responses import JSONResponse
from requests_oauthlib import OAuth1Session

from server.datastore.users_repository import AppUser
from server.models.base import TwitterAPIRequest
from server.routers.auth0_routes import validate_token

consumer_api_key = os.environ.get("TWITTER_APP_KEY")
consumer_secret = os.environ.get("TWITTER_APP_SECRET")


async def tweeter_api_request(
        request: TwitterAPIRequest,
        user:AppUser
):
    oauth = OAuth1Session(
        client_key=consumer_api_key,
        client_secret=consumer_secret,
        resource_owner_key=user.twitter_token,
        resource_owner_secret=user.twitter_token_secret
    )
    # logic here
    # url = "https://api.twitter.com/2/tweets/search/recent?query=chatgpt"
    #     response = oauth.get(url)
    #     # response = oauth.get("https://api.twitter.com/2/users/750748700?user.fields=created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld")
    #     pprint.pp(response)
    #     pprint.pp(response.json())
    return JSONResponse(content='')
