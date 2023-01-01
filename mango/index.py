from collections.abc import Mapping
from enum import Enum, unique
from typing import Any, TypeAlias

import pymongo


class IndexEnum(Enum):
    def __str__(self) -> str:
        return self.name


@unique
class Order(int, IndexEnum):
    ASC = pymongo.ASCENDING
    """升序排序"""
    DESC = pymongo.DESCENDING
    """降序排序"""


@unique
class Attr(str, IndexEnum):
    GEO2D = pymongo.GEO2D
    """二维地理空间索引"""
    GEOSPHERE = pymongo.GEOSPHERE
    """球型地理空间索引"""
    HASHED = pymongo.HASHED
    """散列索引"""
    TEXT = pymongo.TEXT
    """文本索引"""


IndexType: TypeAlias = Order | Attr
IndexTuple: TypeAlias = tuple[str, IndexType | Mapping[str, Any]]


class Index(pymongo.IndexModel):
    ASC = Order.ASC
    """升序排序"""
    DESC = Order.DESC
    """降序排序"""
    GEO2D = Attr.GEO2D
    """二维地理空间索引"""
    GEOSPHERE = Attr.GEOSPHERE
    """球型地理空间索引"""
    HASHED = Attr.HASHED
    """散列索引"""
    TEXT = Attr.TEXT
    """文本索引"""

    def __init__(
        self,
        *keys: str | IndexTuple,
        name: str | None = None,
        unique: bool = False,
        background: bool = False,
        sparse: bool = False,
        **kwargs: Any,
    ) -> None:
        keys = tuple((k, self.ASC) if isinstance(k, str) else k for k in keys)
        params = {
            "name": name,
            "unique": unique,
            "background": background,
            "sparse": sparse,
        }
        params = {k: v for k, v in params.items() if v}
        super().__init__(
            keys,
            **params,
            **kwargs,
        )
