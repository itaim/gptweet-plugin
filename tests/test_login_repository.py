import os
import random
from base64 import b64encode

from dotenv import load_dotenv

load_dotenv()
import pytest

from loguru import logger

from server.datastore.users_repository import UsersRepository, AccessToken, rfc_date


def user_info(user_id):
    return {'created_at': '2023-04-09T12:27:21.429Z',
            'description': 'Programmer, system architect, Data/ML engineer and '
                           'occasionally a scientist at https://t.co/JNvO4C4uL3. Views '
                           'are my own.',
            'identities': [{'access_token': f'{user_id}-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
                            'access_token_secret': 'KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71',
                            'connection': 'twitter',
                            'isSocial': True,
                            'provider': 'twitter',
                            'user_id': f'{user_id}'}],
            'last_ip': '2a10:8006:904d:0:3921:4a65:a505:7422',
            'last_login': '2023-04-09T16:22:36.296Z',
            'location': 'Tel Aviv',
            'logins_count': 3,
            'name': 'Itai M',
            'nickname': 'Itai M',
            'picture': 'https://pbs.twimg.com/profile_images/1603632232278753282/5dHl_WzT_normal.jpg',
            'screen_name': 'mastikair',
            'updated_at': '2023-04-09T16:22:36.296Z',
            'user_id': f'twitter|{user_id}'}


@pytest.fixture
def login_repository():
    namespace = 'tests'
    repository = UsersRepository(namespace=namespace)
    yield repository
    #
    repository.index.delete(delete_all=True, namespace=namespace)


def test_save_user(login_repository: UsersRepository):
    user_id = '123456'
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(3600))
    user = login_repository.upsert_user(user_id=user_id, access_token=token,
                                        refresh_token="my_refresh_token", userinfo=user_info(user_id))
    assert user is not None
    assert user.new


def test_update_user(login_repository: UsersRepository):
    user_id = '123456'
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(3600))
    login_repository.upsert_user(user_id=user_id, access_token=token,
                                 refresh_token="my_refresh_token", userinfo=user_info(user_id))
    token = AccessToken(access_token='my_new_acess_token', expiry_date=rfc_date(3600))
    user = login_repository.upsert_user(user_email='itai@rolebotics.com', access_token=token,
                                        refresh_token="my_new_refresh_token", userinfo=user_info(user_id))
    assert user is not None
    assert not user.new


def do_access_expiry_test(login_repository: UsersRepository, offset: int, expected: bool):
    # acess_token = 'my_acess_token_669'
    # token = AccessToken(access_token=acess_token, expiry_date=rfc_date(offset))
    # user = login_repository.upsert_user(access_token=token, refresh_token="my_refresh_token",
    #                                     user_email='itai@rolebotics.com',
    #                                     userinfo=USER_INFO_EXAMPLE)
    # logger.info(f'Created user with id: {user.user_id}')
    # res = login_repository.check_access_expiration(access_token=acess_token)
    # if expected:
    #     assert res.refresh_token == "my_refresh_token"
    # else:
    #     assert not res
    pass


def test_save_two_users(login_repository: UsersRepository):
    first_id = b64encode(os.urandom(4)).decode('utf-8')
    token = AccessToken(access_token=f'{first_id}_acess_token', expiry_date=rfc_date(3600))
    login_repository.upsert_user(user_id=first_id, access_token=token,
                                             refresh_token=f'{first_id}_refresh_token', userinfo=user_info(first_id))

    second_id = b64encode(os.urandom(4)).decode('utf-8')
    token = AccessToken(access_token=f'{second_id}_acess_token', expiry_date=rfc_date(3600))
    login_repository.upsert_user(user_id=second_id, access_token=token,
                                              refresh_token=f'{second_id}_refresh_token', userinfo=user_info(second_id))

    readFirst = login_repository.get_user(first_id)
    readSecond = login_repository.get_user(second_id)
    assert readFirst.user_id == first_id
    assert readSecond.user_id == second_id


def test_get_user_by_access_token(login_repository: UsersRepository):
    user_id = '123456'
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(1))
    login_repository.upsert_user(user_id=user_id, access_token=token,
                                 refresh_token="my_refresh_token", userinfo=user_info(user_id))
    user = login_repository.get_user_by_access_token('my_access_token')
    logger.info(f'User {user}')
    assert user is not None


@pytest.mark.skip(reason="not implemented")
def test_check_access_expired(login_repository: UsersRepository):
    do_access_expiry_test(login_repository, -3600, True)


@pytest.mark.skip(reason="not implemented")
def test_check_access_valid(login_repository: UsersRepository):
    do_access_expiry_test(login_repository, +3600, False)


def test_update_access_token(login_repository: UsersRepository):
    user_id = '123456'
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(1))
    user = login_repository.upsert_user(user_id=user_id, access_token=token,
                                        refresh_token="my_refresh_token", userinfo=user_info(user_id))
    new_expiry_date = rfc_date(3600)
    new_token = AccessToken(access_token='my_refreshed_token', expiry_date=new_expiry_date)
    login_repository.update_access_token(user_id=user.user_id, new_access_token=new_token)
    user = login_repository.get_user(user.user_id)
    assert user.access_token == new_token.access_token
    assert user.expiry_date == new_token.expiry_date
