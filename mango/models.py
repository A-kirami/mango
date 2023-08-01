import contextlib
from collections.abc import Mapping, MutableMapping, Sequence
from functools import reduce
from typing import TYPE_CHECKING, Any, ClassVar

import bson
from bson import ObjectId
from pydantic import BaseModel
from pydantic.main import ModelMetaclass
from typing_extensions import Self, dataclass_transform

from mango.encoder import Encoder
from mango.expression import Expression, ExpressionField, Operators
from mango.fields import Field, FieldInfo, ObjectIdField
from mango.meta import MetaConfig, inherit_meta
from mango.result import AggregateResult, FindMapping, FindResult
from mango.source import Mango
from mango.stage import Pipeline
from mango.utils import add_fields, all_check, validate_fields

if TYPE_CHECKING:
    from bson.codec_options import CodecOptions
    from pydantic.fields import ModelField
    from pymongo.results import DeleteResult, UpdateResult

    from mango.drive import Collection, Database

operators = tuple(str(i) for i in Operators)


def is_need_default_pk(
    bases: tuple[type[Any], ...], annotate: dict[str, Any] | None = None
) -> bool:
    # 未定义任何字段
    if not annotate:
        return False

    # 存在 id 字段但未定义主键
    if "id" in annotate:
        return False

    # 存在 id 字段但未定义主键，且其被继承
    return not any(getattr(base, "id", None) for base in bases)


def set_default_pk(model: type["Document"]) -> None:
    value = Field(default_factory=ObjectId, allow_mutation=False, init=False)
    add_fields(model, id=(ObjectIdField, value))
    model.__primary_key__ = "id"


def flat_filter(data: Mapping[str, Any]) -> dict[str, Any]:
    flatted = {}
    for key, value in data.items():
        if key.startswith(operators):
            flatted |= flat_filter(reduce(lambda x, y: x | y, value))
        elif "." in key:
            parent, child = key.split(".", maxsplit=1)
            flatted[parent] = flat_filter({child: value})
        else:
            for operator in operators:
                if ov := value.get(operator):
                    flatted[key] = ov
    return flatted


def merge_map(data: MutableMapping[Any, Any], into: Mapping[Any, Any]) -> None:
    for k, v in into.items():
        k = str(k)
        if isinstance(data.get(k), dict) and isinstance(v, dict | EmbeddedDocument):
            merge_map(data[k], v if isinstance(v, dict) else v.dict())
        else:
            data[k] = v


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class MetaDocument(ModelMetaclass):
    def __new__(
        cls,
        cname: str,
        bases: tuple[type[Any], ...],
        attrs: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        meta = MetaConfig

        for base in reversed(bases):
            if base != BaseModel and issubclass(base, Document):
                meta = inherit_meta(base.__meta__, MetaConfig)

        kwargs.setdefault("database", kwargs.pop("db", None))

        allowed_meta_kwargs = {
            key
            for key in dir(meta)
            if not (key.startswith("__") and key.endswith("__"))
        }
        meta_kwargs = {
            key: kwargs.pop(key) for key in kwargs.keys() & allowed_meta_kwargs
        }

        attrs["__meta__"] = inherit_meta(attrs.get("Meta"), meta, **meta_kwargs)
        attrs["__encoder__"] = Encoder.create(attrs["__meta__"].bson_encoders)

        scls = super().__new__(cls, cname, bases, attrs, **kwargs)

        # 由于此处代码使用了 setattr，导致子类重写父类的字段时会引发错误，暂无解决办法
        # NameError: Field name "xxx" shadows a BaseModel attribute;
        # use a different field name with "alias='xxx'".
        for fname, field in scls.__fields__.items():
            setattr(scls, fname, ExpressionField(field, []))
            if isinstance(finfo := field.field_info, FieldInfo) and finfo.primary_key:
                pk = finfo.alias or fname
                if getattr(scls, "__primary_key__", pk) != pk:
                    raise ValueError("文档的主键应唯一")
                finfo.allow_mutation = False
                scls.__primary_key__ = pk

        if not hasattr(scls, "__primary_key__") and is_need_default_pk(
            bases, attrs.get("__annotations__")
        ):
            set_default_pk(scls)

        Mango.register_model(scls)

        return scls


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class MetaEmbeddedDocument(ModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: tuple[type[Any], ...],
        attrs: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        scls = super().__new__(cls, name, bases, attrs, **kwargs)
        for fname, field in scls.__fields__.items():
            setattr(scls, fname, ExpressionField(field, []))
            if isinstance(finfo := field.field_info, FieldInfo) and finfo.primary_key:
                raise ValueError("内嵌文档不可设置主键")
        return scls


class Document(BaseModel, metaclass=MetaDocument):
    if TYPE_CHECKING:  # pragma: no cover
        id: ClassVar[ObjectId]
        __fields__: ClassVar[dict[str, ModelField]]
        __meta__: ClassVar[type[MetaConfig]]
        __encoder__: ClassVar[CodecOptions]
        __collection__: ClassVar[Collection]
        __primary_key__: ClassVar[str]

        def __init_subclass__(
            cls,
            *,
            name: str | None = None,
            db: Database | str | None = None,
            **kwargs: Any,
        ) -> None:
            ...

    Meta = MetaConfig

    @property
    def pk(self) -> Any:
        """主键值"""
        return getattr(self, self.__primary_key__)

    async def insert(self) -> Self:
        """插入文档"""
        await self.__collection__.insert_one(self.doc())
        return self

    async def update(self, **kwargs: Any) -> bool:
        """更新文档"""
        if kwargs:
            values = validate_fields(self.__class__, kwargs)
            for field, value in values.items():
                setattr(self, field, value)
        result: UpdateResult = await self.__collection__.update_one(
            {"_id": self.pk}, {"$set": self.doc(exclude={self.__primary_key__})}
        )
        return bool(result.modified_count)

    async def save(self, **kwargs: Any) -> Self:
        """保存文档，如果文档不存在，则插入，否则更新它。"""
        existing_doc = await self.__collection__.find_one({"_id": self.pk})
        if existing_doc:
            await self.update(**kwargs)
        else:
            await self.insert()
        return self

    async def delete(self) -> bool:
        """删除文档"""
        result: DeleteResult = await self.__collection__.delete_one({"_id": self.pk})
        return bool(result.deleted_count)

    def doc(self, **kwargs: Any) -> dict[str, Any]:
        """转换为 MongoDB 文档"""
        kwargs["by_alias"] = self.__meta__.by_alias
        data = self.dict(**kwargs)
        pk = self.__primary_key__
        exclude = kwargs.get("exclude")
        if not (exclude and pk in exclude):
            data["_id"] = data.pop(pk)
        return bson.decode(bson.encode(data, codec_options=self.__encoder__))

    @classmethod
    def from_doc(cls, document: dict[str, Any]) -> Self:
        """从文档构建模型实例"""
        with contextlib.suppress(KeyError):
            document[cls.__primary_key__] = document.pop("_id")
        return cls(**document)

    @classmethod
    async def save_all(cls, *documents: Self) -> None:
        """保存全部文档"""
        await cls.__collection__.insert_many(doc.doc() for doc in documents)

    @classmethod
    def aggregate(
        cls, pipeline: Pipeline | Sequence[Mapping[str, Any]], *args: Any, **kwargs: Any
    ) -> AggregateResult:
        """聚合查询"""
        cursor = cls.__collection__.aggregate(pipeline, *args, **kwargs)
        return AggregateResult(cursor)

    @classmethod
    def find(
        cls,
        *args: FindMapping | Expression | bool,
    ) -> FindResult[Self]:
        """使用表达式查询文档"""
        if all_check(args, Expression | Mapping):
            return FindResult(cls, *args)  # type: ignore
        raise TypeError("查询表达式类型不正确")

    @classmethod
    async def get(cls, _id: Any) -> Self | None:
        """通过主键查询文档"""
        return await cls.find({"_id": _id}).get()

    @classmethod
    async def get_or_create(
        cls,
        *args: FindMapping | Expression | bool,
        defaults: FindMapping | Self | None = None,
    ) -> Self:
        """获取文档, 如果不存在, 则创建"""
        result: FindResult[Self] = FindResult(cls, *args)  # type: ignore
        if model := await result.get():
            return model
        default = defaults.doc() if isinstance(defaults, Document) else defaults or {}
        data = flat_filter(result.filter)
        merge_map(data, default)
        model = cls.from_doc(data)
        return await model.save()

    class Config:
        validate_assignment = True


class EmbeddedDocument(BaseModel, metaclass=MetaEmbeddedDocument):
    class Config:
        validate_assignment = True
