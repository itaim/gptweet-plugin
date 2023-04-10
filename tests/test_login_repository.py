import pytest
from dotenv import load_dotenv
from loguru import logger

from server.datastore.login_repository import LoginRepository, AccessToken, rfc_date

load_dotenv()

USER_INFO_EXAMPLE = {'created_at': '2023-04-09T12:27:21.429Z',
                     'description': 'Programmer, system architect, Data/ML engineer and '
                                    'occasionally a scientist at https://t.co/JNvO4C4uL3. Views '
                                    'are my own.',
                     'identities': [{'access_token': '15219792-RGg8c8uMZLI3WMEACAT0tkp5FTThNByuwgm04I2VF',
                                     'access_token_secret': 'KZualFBMzR5T2LlBhjL8AWrZBzXakL3aspaYBGOaThr71',
                                     'connection': 'twitter',
                                     'isSocial': True,
                                     'provider': 'twitter',
                                     'user_id': '15219792'}],
                     'last_ip': '2a10:8006:904d:0:3921:4a65:a505:7422',
                     'last_login': '2023-04-09T16:22:36.296Z',
                     'location': 'Tel Aviv',
                     'logins_count': 3,
                     'name': 'Itai M',
                     'nickname': 'Itai M',
                     'picture': 'https://pbs.twimg.com/profile_images/1603632232278753282/5dHl_WzT_normal.jpg',
                     'screen_name': 'mastikair',
                     'updated_at': '2023-04-09T16:22:36.296Z',
                     'user_id': 'twitter|15219792'}


@pytest.fixture
def login_repository():
    namespace = 'tests'
    repository = LoginRepository(namespace=namespace)
    yield repository
    #
    repository.index.delete(delete_all=True, namespace=namespace)


def test_save_user(login_repository: LoginRepository):
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(3600))
    user = login_repository.upsert_user(user_email='itai@rolebotics.com', access_token=token,
                                        refresh_token="my_refresh_token", userinfo=USER_INFO_EXAMPLE)
    assert user is not None
    assert user.new


def test_update_user(login_repository: LoginRepository):
    token = AccessToken(access_token='my_access_token', expiry_date=rfc_date(3600))
    login_repository.upsert_user(user_id='15219792', access_token=token, refresh_token="my_refresh_token",
                                 userinfo=USER_INFO_EXAMPLE)
    token = AccessToken(access_token='my_new_acess_token', expiry_date=rfc_date(3600))
    user = login_repository.upsert_user(user_email='itai@rolebotics.com', access_token=token,
                                        refresh_token="my_new_refresh_token", userinfo=USER_INFO_EXAMPLE)
    assert user is not None
    assert not user.new


def do_access_expiry_test(login_repository: LoginRepository, offset: int, expected: bool):
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


def test_get_user_by_access_token(login_repository: LoginRepository):
    token = AccessToken(access_token='my_access_token', expiry_date=rfc_date(3600))
    login_repository.upsert_user(user_id='15219792', access_token=token, refresh_token="my_refresh_token",
                                 userinfo=USER_INFO_EXAMPLE)
    user = login_repository.get_user_by_access_token('my_access_token')
    logger.info(f'User {user}')
    assert user is not None


@pytest.mark.skip(reason="not implemented")
def test_check_access_expired(login_repository: LoginRepository):
    do_access_expiry_test(login_repository, -3600, True)


@pytest.mark.skip(reason="not implemented")
def test_check_access_valid(login_repository: LoginRepository):
    do_access_expiry_test(login_repository, +3600, False)


def test_update_access_token(login_repository: LoginRepository):
    token = AccessToken(access_token='my_acess_token', expiry_date=rfc_date(1))
    user = login_repository.upsert_user(user_email='itai@rolebotics.com', access_token=token,
                                        refresh_token="my_refresh_token", userinfo=USER_INFO_EXAMPLE)
    new_expiry_date = rfc_date(3600)
    new_token = AccessToken(access_token='my_refreshed_token', expiry_date=new_expiry_date)
    login_repository.update_access_token(user_id=user.user_id, new_access_token=new_token)
    user = login_repository.get_user(user.user_id)
    assert user.access_token == new_token.access_token
    assert user.expiry_date == new_token.expiry_date
