from collections.abc import Callable, Generator, Mapping, Set
from typing import Any, AnyStr

from bson import ObjectId
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.fields import Undefined
from pydantic.typing import NoArgAnyCallable
from typing_extensions import Self

from mango.index import Index, IndexType


class ObjectIdField(ObjectId):
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[AnyStr], Self], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: AnyStr) -> Self:
        if cls.is_valid(v):
            return cls(v)
        raise ValueError("无效的 ObjectId")

    @classmethod
    def __modify_schema__(cls, field_schema: dict) -> None:
        field_schema.update(type="string")


class FieldInfo(PDFieldInfo):
    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.primary_key: bool = kwargs.pop("primary_key", False)
        self.index: bool | IndexType | Index | None = kwargs.pop("index", None)
        self.expire: int | None = kwargs.pop("expire", None)
        self.unique: bool = kwargs.pop("unique", None)
        super().__init__(default=default, **kwargs)


def Field(
    default: Any = Undefined,
    *,
    default_factory: NoArgAnyCallable | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclude: Set[int | str] | Mapping[int | str, Any] | Any | None = None,
    include: Set[int | str] | Mapping[int | str, Any] | Any | None = None,
    const: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    unique_items: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    allow_mutation: bool = True,
    regex: str | None = None,
    discriminator: str | None = None,
    repr: bool = True,
    primary_key: bool = False,
    index: bool | IndexType | Index | None = None,
    expire: int | None = None,
    unique: bool = False,
    **extra: Any,
) -> Any:
    """
    primary_key: 主键
    index: 索引
    expire: 到期时间, int 表示创建后多少秒后到期, datetime 表示到期时间
    unique: 唯一索引
    """
    field_info = FieldInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclude=exclude,
        include=include,
        const=const,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        max_digits=max_digits,
        decimal_places=decimal_places,
        min_items=min_items,
        max_items=max_items,
        unique_items=unique_items,
        min_length=min_length,
        max_length=max_length,
        allow_mutation=allow_mutation,
        regex=regex,
        discriminator=discriminator,
        repr=repr,
        primary_key=primary_key,
        index=index,
        expire=expire,
        unique=unique,
        **extra,
    )
    field_info._validate()
    return field_info
