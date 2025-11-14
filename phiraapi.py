from typing import Callable, Optional
import requests
from requests import Response
from pydantic import BaseModel
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed


class UserInfo(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None
    language: Optional[str] = None
    bio: Optional[str] = None
    exp: Optional[int] = 0
    rks: Optional[float] = 0.0
    joined: Optional[datetime] = None
    lastLogin: Optional[datetime] = None
    roles: Optional[int] = 0
    banned: Optional[bool] = False
    loginBanned: Optional[bool] = False
    followerCount: Optional[int] = 0
    followingCount: Optional[int] = 0
    email: Optional[str] = None


class PhiraFetcher:
    host: str = "https://phira.5wyxi.com/"

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))  # 最多重试5次，每次等待1秒
    def fetch(request_func: Callable[[], Response]) -> str:
        response = request_func()
        if not (200 <= response.status_code < 300):
            raise IOError(f"HTTP request failed with status code: {response.status_code}")
        return response.text

    @classmethod
    def get_user_info(cls, token: str) -> UserInfo:
        def request_func():
            return requests.get(
                f"{cls.host}me",
                headers={"Authorization": f"Bearer {token}"}
            )
        response_text = cls.fetch(request_func)
        return UserInfo.model_validate_json(response_text)
