from typing import (
    AbstractSet,
    Any,
    AnyStr,
    Callable,
    Generator,
    Mapping,
    Optional,
    Union,
)

from bson import ObjectId
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.fields import Undefined
from pydantic.typing import NoArgAnyCallable
from typing_extensions import Self

from mango.index import Attr, Index, Order


class ObjectIdField(ObjectId):
    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[str], "ObjectIdField"], None, None]:
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
        self.index: Union[bool, Order, Attr, Index, None] = kwargs.pop("index", None)  # type: ignore
        self.expire: Optional[int] = kwargs.pop("expire", None)
        self.unique: bool = kwargs.pop("unique", None)
        super().__init__(default=default, **kwargs)


def Field(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Optional[
        Union[AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any]
    ] = None,
    include: Optional[
        Union[AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any]
    ] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    discriminator: Optional[str] = None,
    repr: bool = True,
    primary_key: bool = False,
    index: Optional[Union[bool, Order, Attr, Index]] = None,  # type: ignore
    expire: Optional[int] = None,
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
