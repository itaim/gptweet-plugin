from dotenv import load_dotenv

from server.utils import find_relative_path

load_dotenv()
import pinecone
from fastapi.staticfiles import StaticFiles
from base64 import b64encode

import markdown2
# temp remove
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

# temp remove
from fastapi import Request
from loguru import logger
from server.routers.twitter_routes import tweeter_api_request
from server.datastore.users_repository import get_users_repository
import os

from server.models.base import SearchResponse, SearchRequest
from fastapi import Depends, Body
from server.routers.google_routes import google_search
from server.models.base import TwitterAPIRequest
from server.routers.auth0_routes import validate_token
from server.routers.auth0_routes import auth0_callback_request, auth0_login_request

# 0. Implement Google search endpoint
# 1. test locally
# 2. deploy to heroku - docker, env variables
# 3. test on openai
# 4. openapi error response
# 5. Automated social media agent: goal, topics, personality (imitate my style), tweets and replies rate

app = FastAPI()
app.mount("/.well-known", StaticFiles(directory=find_relative_path(".well-known")), name="static")
# app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
secret_key = b64encode(os.urandom(16)).decode('utf-8')

app.add_middleware(SessionMiddleware, secret_key=secret_key)


# Create a sub-application, in order to access just the query endpoint in an OpenAPI schema, found at http://0.0.0.0:8000/sub/openapi.json when the app is running locally
# sub_app = FastAPI(
#     title="Social Plugin API",
#     description="A plugin that enables users to interact with Twitter functionalities and perform Google searches through ChatGPT. Features include creating tweets, following users, getting the latest tweets from the feed, searching for tweets, and performing Google searches.",
#     version="1.0.0",
#     servers=[{"url": "https://social.rolebotics.com"}],
#     # dependencies=[Depends(validate_token)],
# )
# app.mount("/sub", sub_app)
# app.mount("/", auth_router)
# app.mount("/", twitter_router)
# app.mount("/", search_router)

@app.get("/auth0/callback")
async def auth0_callback(request: Request):
    return await auth0_callback_request(request)


@app.get("/auth0/login")
async def auth0_login(request: Request):
    return await auth0_login_request(request)


@app.post(
    "/twitter/api"
)
async def tweeter_api(
        request: TwitterAPIRequest = Body(...),
        user=Depends(validate_token)
):
    return await tweeter_api_request(request, user)


@app.post(
    "/google/api",
    response_model=SearchResponse
)
async def google_api(
        request: SearchRequest = Body(...),
        user=Depends(validate_token)
):
    return await google_search(request)


@app.get("/legal-info", response_class=HTMLResponse)
# @sub_app.get("/legal-info", response_class=HTMLResponse)
async def legal_info():
    logger.info(f'legal info pwd {os.getcwd()}')
    with open("static/privacy-policy.md", "r") as file:
        content = file.read()

    html_content = markdown2.markdown(content)
    return HTMLResponse(html_content)


@app.get("/", response_class=HTMLResponse)
# @sub_app.get("/home", response_class=HTMLResponse)
async def index():
    logger.info(f'home pwd {os.getcwd()}')
    with open("static/index.html", "r") as file:
        html_content = file.read()

    return HTMLResponse(content=html_content, status_code=200)


@app.on_event("startup")
async def startup():
    logger.info(f'Startup')
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    assert api_key is not None
    assert environment is not None
    pinecone.init(api_key=api_key, environment=environment)
    global users_repository
    users_repository = await get_users_repository()
    logger.info(f'Startup complete')


def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == '__main__':
    start()