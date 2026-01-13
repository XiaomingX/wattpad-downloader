from typing import List, Optional, Tuple
from typing_extensions import TypedDict
import re
import unicodedata
import logging
from os import environ
from enum import Enum
import backoff
from eliot import to_file, start_action
from eliot.stdlib import EliotHandler
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pydantic import TypeAdapter, model_validator, field_validator
from pydantic_settings import BaseSettings
from aiohttp import ClientResponseError
from aiohttp_client_cache.session import CachedSession
from aiohttp_client_cache import FileBackend, RedisBackend

load_dotenv(override=True)

handler = EliotHandler()

if environ.get("DEBUG"):
    to_file(open("eliot.log", "wb"))

logger = logging.Logger("wpd")
logger.addHandler(handler)

# --- #


class CacheTypes(Enum):
    file = "file"
    redis = "redis"


class Config(BaseSettings):
    USE_CACHE: bool = True
    CACHE_TYPE: CacheTypes = CacheTypes.file
    REDIS_CONNECTION_URL: str = ""

    @field_validator("USE_CACHE", mode="before")
    def validate_use_cache(cls, value):
        # Return default if value is an empty string
        if value == "":
            return True  # Default value for USE_CACHE
        return value

    @field_validator("CACHE_TYPE", mode="before")
    def validate_cache_type(cls, value):
        # Thanks https://stackoverflow.com/a/78157474
        if value == "":
            return "file"
        return value

    @model_validator(mode="after")
    def prevent_mismatched_redis_url(self):
        match self.CACHE_TYPE:
            case CacheTypes.file:
                if self.REDIS_CONNECTION_URL:
                    raise ValueError(
                        "REDIS_CONNECTION_URL provided when File cache selected. To use Redis as a cache, set CACHE_TYPE=redis."
                    )
            case CacheTypes.redis:
                if not self.REDIS_CONNECTION_URL:
                    raise ValueError(
                        "REDIS_CONNECTION_URL not provided when Redis cache selected. To use File cache, set CACHE_TYPE=file."
                    )
        return self


config = Config()

# --- #

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}

if config.USE_CACHE:
    match config.CACHE_TYPE:
        case CacheTypes.file:
            cache = FileBackend(use_temp=True, expire_after=43200)  # 12 hours
        case CacheTypes.redis:
            cache = RedisBackend(
                cache_name="wpd-aiohttp-cache",
                address=config.REDIS_CONNECTION_URL,
                expire_after=43200,  # 12 hours
            )
else:
    cache = None

logger.info(f"Using {cache=}")

# --- Utilities --- #


def slugify(value, allow_unicode=False) -> str:
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Thanks https://stackoverflow.com/a/295466.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


async def wp_get_cookies(username: str, password: str) -> dict:
    # source: https://github.com/TheOnlyWayUp/WP-DM-Export/blob/dd4c7c51cb43f2108e0f63fc10a66cd24a740e4e/src/API/src/main.py#L25-L58
    """Retrieves authorization cookies from Wattpad by logging in with user creds.

    Args:
        username (str): Username.
        password (str): Password.

    Raises:
        ValueError: Bad status code.
        ValueError: No cookies returned.

    Returns:
        dict: Authorization cookies.
    """
    with start_action(action_type="api_fetch_cookies"):
        async with CachedSession(headers=headers, cache=None, trust_env=True) as session:
            async with session.post(
                "https://www.wattpad.com/auth/login?nextUrl=%2F&_data=routes%2Fauth.login",
                data={
                    "username": username.lower(),
                    "password": password,
                },  # the username.lower() is for caching
            ) as response:
                if response.status != 204:
                    raise ValueError("Not a 204.")

                cookies = {
                    k: v.value
                    for k, v in response.cookies.items()  # Thanks https://stackoverflow.com/a/32281245
                }

                if not cookies:
                    raise ValueError("No cookies.")

                return cookies


# --- Models --- #


class Language(TypedDict):
    name: str


class User(TypedDict):
    username: str


class Part(TypedDict):
    id: int
    title: str


class Story(TypedDict):
    id: str
    title: str
    createDate: str
    modifyDate: str
    language: Language
    user: User
    description: str
    cover: str
    completed: bool
    tags: List[str]
    mature: bool
    url: str
    parts: List[Part]
    isPaywalled: bool


story_ta = TypeAdapter(Story)

# --- API Calls --- #


@backoff.on_exception(backoff.expo, ClientResponseError, max_time=15)
async def fetch_story_from_partId(
    part_id: int, cookies: Optional[dict] = None, session: Optional[CachedSession] = None
) -> Tuple[str, Story]:
    """Return a Story ID from a Part ID."""
    with start_action(action_type="api_fetch_storyFromPartId"):
        if session:
            async with session.get(
                f"https://www.wattpad.com/api/v3/story_parts/{part_id}?fields=groupId,group(tags,id,title,createDate,modifyDate,language(name),description,completed,mature,url,isPaywalled,user(username),parts(id,title),cover)"
            ) as response:
                response.raise_for_status()
                body = await response.json()
            return str(body["groupId"]), story_ta.validate_python(body["group"])
        
        async with CachedSession(
            headers=headers, cache=None if cookies else cache, trust_env=True
        ) as session:  # Don't cache requests with Cookies.
            async with session.get(
                f"https://www.wattpad.com/api/v3/story_parts/{part_id}?fields=groupId,group(tags,id,title,createDate,modifyDate,language(name),description,completed,mature,url,isPaywalled,user(username),parts(id,title),cover)"
            ) as response:
                response.raise_for_status()
                body = await response.json()
        return str(body["groupId"]), story_ta.validate_python(body["group"])


@backoff.on_exception(backoff.expo, ClientResponseError, max_time=15)
async def retrieve_story(story_id: int, cookies: Optional[dict] = None, session: Optional[CachedSession] = None) -> Story:
    """Taking a story_id, return its information from the Wattpad API."""
    with start_action(action_type="api_fetch_story", story_id=story_id):
        if session:
            async with session.get(
                f"https://www.wattpad.com/api/v3/stories/{story_id}?fields=tags,id,title,createDate,modifyDate,language(name),description,completed,mature,url,isPaywalled,user(username),parts(id,title),cover"
            ) as response:
                response.raise_for_status()
                body = await response.json()
            return story_ta.validate_python(body)

        async with CachedSession(
            headers=headers, cookies=cookies, cache=None if cookies else cache, trust_env=True
        ) as session:
            async with session.get(
                f"https://www.wattpad.com/api/v3/stories/{story_id}?fields=tags,id,title,createDate,modifyDate,language(name),description,completed,mature,url,isPaywalled,user(username),parts(id,title),cover"
            ) as response:
                response.raise_for_status()
                body = await response.json()
        return story_ta.validate_python(body)


@backoff.on_exception(backoff.expo, ClientResponseError, max_time=15)
async def fetch_part_content(part_id: int, cookies: Optional[dict] = None, session: Optional[CachedSession] = None) -> str:
    """Return the HTML Content of a Part, handling pagination."""
    all_content = []
    page = 1
    
    with start_action(action_type="api_fetch_partContent", part_id=part_id):
        if session:
            while True:
                url = f"https://www.wattpad.com/apiv2/?m=storytext&id={part_id}"
                if page > 1:
                    url += f"&page={page}"
                async with session.get(url) as response:
                    if response.status == 404: break
                    response.raise_for_status()
                    body = await response.text()
                    if not body or body.strip() == "" or body in all_content: break
                    all_content.append(body)
                    if len(body) < 10: break
                    page += 1
                    if page > 50: break
            combined_html = "".join(all_content)
            return clean_content(combined_html)

        async with CachedSession(
            headers=headers, cookies=cookies, cache=None if cookies else cache, trust_env=True
        ) as session:
            while True:
                url = f"https://www.wattpad.com/apiv2/?m=storytext&id={part_id}"
                if page > 1:
                    url += f"&page={page}"
                
                async with session.get(url) as response:
                    if response.status == 404:
                        break
                    response.raise_for_status()
                    body = await response.text()
                    
                    if not body or body.strip() == "":
                        break
                    
                    # Simple check for duplicates if the API doesn't 404 on out-of-bounds
                    if body in all_content:
                        break
                        
                    all_content.append(body)
                    
                    # Some versions of the API don't 404, they just return empty or same
                    # Let's try to find if there's more. 
                    # If the content length is very small, it might be the end.
                    if len(body) < 10: # Arbitrary small number
                        break
                        
                    page += 1
                    if page > 50: # Safety limit
                        break

        combined_html = "".join(all_content)
        return clean_content(combined_html)


def clean_content(html: str) -> str:
    """Clean unwanted HTML tags and convert to plain text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "iframe", "noscript", "meta", "link"]):
        tag.decompose()
    
    # Replace <p> and <br> with newlines to preserve structure in TXT
    for p in soup.find_all("p"):
        p.append("\n")
    for br in soup.find_all("br"):
        br.replace_with("\n")
        
    return soup.get_text(separator="\n", strip=True)


@backoff.on_exception(backoff.expo, ClientResponseError, max_time=15)
async def fetch_cover(url: str, session: Optional[CachedSession] = None) -> bytes:
    """Fetch cover image bytes."""
    with start_action(action_type="api_fetch_cover", url=url):
        if session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()

        async with CachedSession(
            headers=headers, cache=None, trust_env=True
        ) as session:  # Don't cache images.
            async with session.get(url) as response:
                response.raise_for_status()

                body = await response.read()

        return body


# --- TXT Generation Utilities --- #

def get_metadata_text(data: Story) -> str:
    """Generate a plain text summary of book metadata."""
    lines = [
        f"Title: {data['title']}",
        f"Author: {data['user']['username']}",
        f"Language: {data['language']['name']}",
        f"Created: {data['createDate']}",
        f"Modified: {data['modifyDate']}",
        f"Completed: {data['completed']}",
        f"Mature: {data['mature']}",
        f"Tags: {', '.join(data['tags'])}",
        f"URL: {data['url']}",
        "\n--- Description ---\n",
        data['description'],
        "\n" + "="*20 + "\n"
    ]
    return "\n".join(lines)


async def download_chapter(
    part: Part,
    cookies: Optional[dict] = None,
    session: Optional[CachedSession] = None,
) -> str:
    """Download and clean a single chapter."""
    content = await fetch_part_content(part["id"], cookies=cookies, session=session)
    return f"{part['title']}\n\n{content}"
