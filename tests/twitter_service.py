import os
import pprint

import tweepy
from dotenv import load_dotenv
import os
import pprint

import tweepy
from dotenv import load_dotenv

load_dotenv()
from loguru import logger
from requests_oauthlib import OAuth1Session

consumer_api_key = os.environ.get("TWITTER_APP_KEY")
consumer_secret = os.environ.get("TWITTER_APP_SECRET")


def create_tweet():
    client = tweepy.Client(
        consumer_key=consumer_api_key,
        consumer_secret=consumer_secret,
        access_token='15219792-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
        access_token_secret='KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71'
    )
    res = client.follow_user(target_user_id=2999368819)
    res = client.create_tweet(text='Tweeted from tweepy', in_reply_to_tweet_id=None)
    logger.info(res)


# create_tweet()
def rest_calls():
    oauth = OAuth1Session(
        client_key=consumer_api_key,
        client_secret=consumer_secret,
        resource_owner_key='15219792-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
        resource_owner_secret='KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71'
    )
    # "url":
    # url = "https://api.twitter.com/2/users/15219792?user.fields=created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
    # url = "https://api.twitter.com/2/tweets/search/recent?query=autogpt&tweet.fields=author_id,created_at,public_metrics,text"
    # url = "https://api.twitter.com/1.1/friendships/create.json?user_id=1472418552196079616"

    # response = oauth.get(url)
    # pprint.pp(response)
    # pprint.pp(response.json())

    # url = "https://api.twitter.com/2/users/15219792/following"
    # data = {"target_user_id": "2999368819"}
    # {
    #   "method": "POST",
    #   "url": "https://api.twitter.com/2/users/:user_id/tweets",
    #   "body": ""
    # }
    #
    # in_reply_to_tweet_id
    # https://api.twitter.com/2/tweets
    # data = {"text": "This is another reply to tweet from ChatGPT Twitter Plugin", "reply": {"in_reply_to_tweet_id":"1645301668702040066"}}
    # json = "{\"text\": \"a reply to tweet from ChatGPT Twitter Plugin\",\"in_reply_to_tweet_id\":\"1645299912702058497\"}"
    # url = "https://api.twitter.com/2/tweets"
    # url = "https://api.twitter.com/2/users/15219792/following"
    # data = {"target_user_id": "750748700"}
    #
    # json_str = json.dumps(data)
    # print(json_str.encode('unicode_escape').decode('ASCII'))
    # response = oauth.post(url,data=json_str,headers={'content-type':'application/json'})
    # pprint.pp(response)
    # pprint.pp(response.json())
    # url = "https://api.twitter.com/2/users/15219792/timelines/reverse_chronological"
    url = "https://api.twitter.com/2/tweets/search/recent?query=chatgpt"
    response = oauth.get(url)
    # response = oauth.get("https://api.twitter.com/2/users/750748700?user.fields=created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld")
    pprint.pp(response)
    pprint.pp(response.json())
#     1472418552196079616

# method: "GET"
#             url: "https://api.twitter.com/2/tweets/search/recent?query=example&tweet.fields=author_id,created_at,public_metrics,text"
# rest_calls()
# data = {"text": "This is a new tweet from ChatGPT Twitter Plugin!"}
# print(json.dumps(data))