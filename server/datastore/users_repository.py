import datetime
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Any

from loguru import logger
from pydantic import BaseModel

from server.datastore.utils import get_or_create_index


@dataclass
class AccessToken:
    access_token: str
    expiry_date: datetime


@dataclass
class OAuth2Login:
    access_token: str
    refresh_token: str
    expiry_date: datetime


# class UserInfo(BaseModel):
#     email_verified:str
#     given_name:str
#     family_name:str

#     REGISTERED_CLAIMS = [
#         'sub', 'name', 'given_name', 'family_name', 'middle_name', 'nickname',
#         'preferred_username', 'profile', 'picture', 'website', 'email',
#         'email_verified', 'gender', 'birthdate', 'zoneinfo', 'locale',
#         'phone_number', 'phone_number_verified', 'address', 'updated_at',
#     ]

# USER_PROPERTIES = ["user_id", "provider", "access_token", "twitter_token", "twitter_token_secret", "expiry_date",
#                    "refresh_token", "name","nickname", 'description', 'location', 'login_count', "last_ip",
#                     "picture", "user_info", "created_at", "updated_at", 'screen_name']


# SCHEMA = {
#     "class": USERS_INDEX_NAME,
#     "description": "App Users",
#     "vectorIndexType": "hnsw",
#     # "vectorizer": "text2vec-openai",
#     "properties": USERS_INDEX_PROPERTIES
#
# }


# {'id': '113588745676457958318', 'email': 'itai.marks@gmail.com', 'verified_email': True, 'name': 'itai marks', 'given_name': 'itai', 'family_name': 'marks', 'picture': 'https://lh3.googleusercontent.com/a/AGNmyxbEqx68MGd-niJx1USjRkkUmNxRb2ncHKfh4yyHJQc=s96-c', 'locale': 'en-GB'}

class AppUser(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    user_id: str
    provider: str
    access_token: str
    twitter_token: str
    twitter_token_secret: str
    expiry_date: datetime
    refresh_token: str
    name: str
    nickname: str
    screen_name: str
    picture: str
    description: str
    location: str
    last_ip: str
    created_at: datetime
    # updated_at: str
    logins_count: int
    # last_login: str


def user_from_props(d: Dict[str, Any]) -> AppUser:
    # return User.parse_obj(d)
    # parse_obj
    return AppUser(user_id=d['user_id'],
                   provider=d.get('provider', 'twitter'),
                   access_token=d['access_token'],
                   twitter_token=d['twitter_token'],
                   twitter_token_secret=d['twitter_token_secret'],
                   expiry_date=d['expiry_date'],
                   refresh_token=d.get('refresh_token', ''),
                   name=d.get('name', ''),
                   nickname=d.get('nickname', ''),
                   screen_name=d.get('screen_name', ''),
                   picture=d.get('picture', ''),
                   description=d.get('description', ''),
                   location=d.get('location', ''),
                   # updated_at=d.get('updated_at', ''),
                   # last_login=d.get('last_login', ''),
                   logins_count=d.get('logins_count', 0),
                   last_ip=d.get('last_ip', ''),
                   created_at=d['created_at'])


class ClientUser(BaseModel):
    user_id: str
    new: bool
    nickname: str
    name: str
    picture: str


def client_user(d: Dict[str, Any], user_id: Optional[str] = None) -> ClientUser:
    return ClientUser(user_id=user_id or d['user_id'], new=user_id is None,
                      name=d.get('name', None),
                      nickname=d.get('nickname', None),
                      picture=d.get('picture', None))


NULL_EMBEDDING = [0.0] * 1536


class UsersRepository:
    def __init__(self, namespace: str):
        index_name = os.environ.get("PINECONE_USERS_INDEX")
        assert index_name is not None
        self.namespace = namespace
        self.index = get_or_create_index(index_name=index_name, metadata_config=None)

    # def authenticate(self, email: str, password: str):
    #     user = self.get_user_by_email(email)
    #     if user and user.p ["password"] == password:
    #         return user
    #     return None

    @logger.catch
    def upsert_user(self, access_token: AccessToken, refresh_token: str, user_id: str,
                    userinfo: Dict[str, Any]) -> ClientUser:

        user = self.get_user(user_id)

        def props(user: Optional[AppUser] = None):
            # USER_PROPERTIES = ["user_id", "provider", "access_token", "twitter_token", "twitter_token_secret", "expiry_date",
            #                    "refresh_token", "name","nickname", 'description', 'location', 'auth0_login_count', "last_ip",
            #                     "picture", "user_info", "created_at", "updated_at", 'screen_name']
            identities = userinfo['identities'][0]
            return {
                "access_token": access_token.access_token,
                "expiry_date": access_token.expiry_date,
                "provider": identities.get('provider', 'twitter'),
                "twitter_token": identities['access_token'],
                "twitter_token_secret": identities['access_token_secret'],
                "refresh_token": refresh_token,
                "name": userinfo.get('name', user.name if user else ''),
                "nickname": userinfo.get('nickname', user.nickname if user else ''),
                "picture": userinfo.get('picture', user.picture if user else ''),
                "location": userinfo.get('location', user.location if user else ''),
                "screen_name": userinfo.get('screen_name', user.screen_name if user else ''),
                # "updated_at": userinfo.get('updated_at', user.updated_at if user else ''),
                # "last_login": userinfo.get('last_login', user.last_login if user else ''),
                "logins_count": userinfo.get('logins_count', user.logins_count if user else '')
            }

        if user:
            logger.info(f'User {user_id} found')
            properties = props(user)
            #
            res = self.index.update(id=user.user_id, set_metadata=properties, namespace=self.namespace)
            logger.info(f'User {user.user_id} updated, success: {True if not res else res}')
            cu = client_user(user.dict(), user.user_id)
            return cu
        else:
            props = props()
            props["user_id"] = user_id
            props["created_at"] = rfc_date(0)

            response = self.index.upsert(vectors=[
                (
                    user_id,  # Vector ID
                    NULL_EMBEDDING,
                    props,
                )
            ], namespace=self.namespace)

            logger.info(
                f'Created user with id {user_id} for access_token {access_token.access_token}. response {response}')
            return client_user(props)

    # def _lookup_user(self, where_filter) -> Optional[User]:
    #     res = self.index.query(vector=[0.0] * 1536, filter=where_filter, include_metadata=True,
    #                            namesapce=self.namespace, top_k=1)
    #     if res.matches:
    #         props = res.matches[0].metadata
    #         logger.info(f'Found matching user props: {props}')
    #         return user_from_props(props)
    #     else:
    #         return None

    # def get_user_by_access_token(self, access_token) -> Optional[User]:
    #     where_filter = {
    #         "access_token": {"$eq": access_token},
    #     }
    #     return self._lookup_user(where_filter)

    # def get_user_by_email(self, email: str):
    #     where_filter = {
    #         "email_address": {"$eq": email},
    #     }
    #     return self._lookup_user(where_filter)

    # @logger.catch
    # def check_access_expiration(self, access_token) -> Optional[User]:
    #     user = self.get_user_by_access_token(access_token)
    #     if not user:
    #         raise Exception(f'User with access token {access_token} not found')
    #     if user.expiry_date <= rfc_date(0):
    #         return user
    #     else:
    #         return None

    @logger.catch
    def update_access_token(self, user_id: str, new_access_token: AccessToken):
        data = {"access_token": new_access_token.access_token, 'expiry_date': new_access_token.expiry_date}
        # , namespace=self.namespace
        res = self.index.update(id=user_id, set_metadata=data, namespace=self.namespace)
        logger.info(f'access token for user {user_id} updated, success: {res is None or res}')

    @logger.catch
    def get_user(self, user_id: str) -> Optional[AppUser]:
        by_id = self.index.query(id=user_id, include_metadata=True, top_k=1, namespace=self.namespace)
        if by_id.matches:
            props = by_id.matches[0].metadata
            logger.info(f'Found matching user props: {props}')
            return user_from_props(props)
        else:
            return None

    def get_user_by_access_token(self, access_token: str) -> AppUser | None:
        # filter
        where_filter = {
            "access_token": {"$eq": access_token},
        }
        by_token = self.index.query(vector=NULL_EMBEDDING, include_metadata=True, top_k=1, namespace=self.namespace,
                                    filter=where_filter)
        if by_token.matches:
            props = by_token.matches[0].metadata
            logger.info(f'Found matching user props: {props}')
            return user_from_props(props)
        else:
            return None


def rfc_date(expires_in: int) -> datetime:
    return datetime.utcnow() + timedelta(seconds=expires_in)


@lru_cache()
def get_users_repository() -> UsersRepository:
    return UsersRepository(namespace=os.environ.get('ENVIRONMENT', 'production'))
