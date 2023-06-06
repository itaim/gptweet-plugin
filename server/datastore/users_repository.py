import datetime
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Any

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from server.models.app_user import AppUser

DATABASE_URL = os.environ['DATABASE_URL']


@dataclass
class AccessToken:
    access_token: str
    expiry_date: datetime


@dataclass
class OAuth2Login:
    access_token: str
    refresh_token: str
    expiry_date: datetime


class UsersRepository:
    def __init__(self):
        database_url = os.environ['DATABASE_URL']
        url = make_url(database_url).set(drivername='postgresql+psycopg2')
        self.engine = create_engine(url)

    # @logger.catch
    def upsert_user(self, access_token: AccessToken, refresh_token: str, user_id: str,
                    userinfo: Dict[str, Any]) -> AppUser:
        identities = userinfo['identities'][0]
        with Session(self.engine) as session:
            user = session.get(AppUser, user_id)
            if user:
                user.twitter_token = identities['access_token']
                user.twitter_token_secret = identities['access_token_secret']
                user.access_token = access_token.access_token,
                user.expiry_date = access_token.expiry_date,
                user.refresh_token = refresh_token,
                user.logins_count += 1
                logger.info(f'User {user.user_id} found and updated')
            else:
                user = AppUser(
                    user_id=user_id,
                    provider=identities.get('provider', 'twitter'),
                    twitter_token=identities['access_token'],
                    twitter_token_secret=identities['access_token_secret'],
                    access_token=access_token.access_token,
                    expiry_date=access_token.expiry_date,
                    refresh_token=refresh_token,
                    name=userinfo.get('name', user.name if user else ''),
                    nickname=userinfo.get('nickname', user.nickname if user else ''),
                    screen_name=userinfo.get('screen_name', user.screen_name if user else ''),
                    picture=userinfo.get('picture', user.picture if user else ''),
                    location=userinfo.get('location', user.location if user else ''),
                    description=userinfo.get('description', user.location if user else ''),
                    created_at=datetime.utcnow(),
                    logins_count=0,
                    last_ip=userinfo.get('last_ip', None))
                session.add(user)
                logger.info(f'New user {user.user_id} created')
            session.commit()
        return user

    @logger.catch
    def get_user(self, user_id: str) -> AppUser | None:
        with Session(self.engine) as session:
            return session.get(AppUser, user_id)

    @logger.catch
    def get_user_by_access_token(self, access_token: str) -> AppUser | None:
        with Session(self.engine) as session:
            return session.query(AppUser).filter_by(access_token=access_token).one_or_none()


def rfc_date(expires_in: int) -> datetime:
    return datetime.utcnow() + timedelta(seconds=expires_in)


@lru_cache()
def get_users_repository() -> UsersRepository:
    return UsersRepository()
