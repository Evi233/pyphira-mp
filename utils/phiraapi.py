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

class ChartInfo(BaseModel):
    """谱面信息模型"""
    id: int
    name: str
    level: Optional[str] = None
    difficulty: Optional[float] = 0.0
    charter: Optional[str] = None
    composer: Optional[str] = None
    illustrator: Optional[str] = None
    description: Optional[str] = None
    ranked: Optional[bool] = False
    reviewed: Optional[bool] = False
    stable: Optional[bool] = False
    stableRequest: Optional[bool] = False
    illustration: Optional[str] = None
    preview: Optional[str] = None
    file: Optional[str] = None
    uploader: Optional[int] = 0
    tags: Optional[list[str]] = None
    rating: Optional[float] = 0.0
    ratingCount: Optional[int] = 0
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    chartUpdated: Optional[datetime] = None

class RecordResult(BaseModel):
    """玩家游玩判定结果"""
    score: int
    perfect: int
    good: int
    bad: int
    miss: int
    max_combo: int
    accuracy: float
    full_combo: bool
    std: float
    std_score: float

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
    @classmethod
    def get_chart_info(cls, chartid: int) -> ChartInfo:
        """
        获取谱面信息（无需认证）
        
        Args:
            chartid: 谱面ID
            
        Returns:
            ChartInfo: 谱面信息对象
            
        Raises:
            IOError: 当HTTP请求失败时抛出
        """
        def request_func():
            return requests.get(f"{cls.host}chart/{chartid}")
        
        response_text = cls.fetch(request_func)
        return ChartInfo.model_validate_json(response_text)
        
    @classmethod
    def get_record_result(cls, recordid: int) -> RecordResult:
        """
        获取游玩判定结果（无需认证）
        
        Args:
            recordid: 记录ID
            
        Returns:
            RecordResult: 判定结果对象
            
        Raises:
            IOError: 当HTTP请求失败时抛出
        """
        def request_func():
            return requests.get(f"{cls.host}record/{recordid}")
        
        response_text = cls.fetch(request_func)
        return RecordResult.model_validate_json(response_text)