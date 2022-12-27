from collections.abc import Generator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar

import bson
from bson import ObjectId
from bson.codec_options import CodecOptions
from pydantic import BaseModel
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from pymongo.results import DeleteResult, UpdateResult
from typing_extensions import Self, dataclass_transform

from mango.drive import Client, Collection, Database, connect
from mango.encoder import Encoder, EncodeType
from mango.expression import Expression, ExpressionField
from mango.fields import Field, FieldInfo, ObjectIdField
from mango.index import Index, IndexType
from mango.result import AggregateResult, FindMapping, FindResult
from mango.stage import Pipeline
from mango.utils import all_check, field_validate, to_snake_case


class MetaConfig(BaseModel):
    database: Database
    collection: Collection
    primary_key: str
    indexes: Sequence[Index]
    encode_type: EncodeType = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
        frozen = True


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class ModelMeta(ModelMetaclass):
    if TYPE_CHECKING:  # pragma: no cover
        __fields__: dict[str, ModelField]
        meta: MetaConfig

    def __new__(
        cls,
        cname: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
        *,
        name: str | None = None,
        db: Database | str | None = None,
        embedded: bool = False,
        indexes: Sequence[Index] | None = None,
    ):
        meta: dict[str, Any] = {}

        base, *_ = bases
        if not (embedded or base is BaseModel):
            meta["database"] = cls.__get_database(cls, db)
            meta["collection"] = meta["database"][name or to_snake_case(cname)]
            meta["primary_key"] = cls.__get_default_pk(cls, bases, attrs)
            meta["indexes"] = [*(indexes or []), *(cls.__get_indexes(cls, attrs))]

        scls = super().__new__(cls, cname, bases, attrs)

        if raw_meta := attrs.pop("Meta", None) or getattr(scls, "meta", None):
            if isinstance(raw_meta, MetaConfig):
                raw_meta = raw_meta.dict()
            else:
                raw_meta = {
                    k: v for k, v in raw_meta.__dict__.items() if not k.startswith("__")
                }
            meta = raw_meta | meta

        # 由于此处代码使用了 setattr，导致子类重写父类的字段时会引发错误，暂无解决办法
        # NameError: Field name "id" shadows a BaseModel attribute; use a different field name with "alias='id'".
        for field_name, field in scls.__fields__.items():
            setattr(scls, field_name, ExpressionField(field, []))
            if (
                not meta.get("primary_key")
                and isinstance(info := field.field_info, FieldInfo)
                and info.primary_key
            ):
                meta["primary_key"] = info.alias or field_name

        scls.__encoder__ = Encoder.create(meta.get("encode_type"))

        if meta:
            scls.meta = MetaConfig(**meta)

        return scls

    def __get_default_pk(self, bases, attrs: dict[str, Any]) -> str:
        for name, attr in attrs.items():
            if isinstance(attr, FieldInfo) and attr.primary_key:
                attrs[name].allow_mutation = False
                return attr.alias or name

        for base in bases:
            if getattr(base, "id", None):
                return ""

        if "id" in attrs["__annotations__"]:
            return ""

        attrs["id"] = Field(default_factory=ObjectId, allow_mutation=False, init=False)
        attrs["__annotations__"]["id"] = ObjectIdField
        return "id"

    def __get_database(self, db: Database | str | None = None) -> Database:
        try:
            client = Client._client[0]
        except IndexError:
            client = connect()

        if isinstance(db, Database):
            return db
        elif isinstance(db, str):
            return client[db]
        else:
            return client.default_database

    def __get_indexes(self, attrs: dict[str, Any]) -> Generator[Index, None, None]:
        for name, attr in attrs.items():
            if isinstance(attr, FieldInfo):
                if index := attr.index:
                    if index is True:
                        yield Index(name)
                    elif isinstance(index, IndexType):
                        yield Index((name, index))
                    elif isinstance(index, Index):
                        yield index
                elif expire := attr.expire:
                    yield Index(name, expireAfterSeconds=expire)


class Model(BaseModel, metaclass=ModelMeta):
    id: ClassVar[ObjectId]
    meta: ClassVar[MetaConfig]
    __encoder__: ClassVar[CodecOptions]

    if TYPE_CHECKING:  # pragma: no cover

        def __init_subclass__(
            cls,
            *,
            name: str | None = None,
            db: Database | str | None = None,
            embedded: bool = False,
            indexes: Sequence[Index] | None = None,
        ) -> None:
            ...

    @property
    def pk(self) -> Any:
        """主键值"""
        return getattr(self, self.meta.primary_key)

    async def save(self) -> Self:
        """保存数据"""
        await self.meta.collection.insert_one(self.doc())
        return self

    async def update(self, **kwargs) -> bool:
        """更新数据"""
        if kwargs:
            values = field_validate(self.__class__, kwargs)
            self = self.copy(update=values)
        result: UpdateResult = await self.meta.collection.update_one(
            {"_id": self.pk}, {"$set": self.doc(exclude={self.meta.primary_key})}
        )
        return bool(result.modified_count)

    async def delete(self) -> bool:
        """删除数据"""
        result: DeleteResult = await self.meta.collection.delete_one({"_id": self.pk})
        return bool(result.deleted_count)

    def doc(self, **kwargs) -> dict[str, Any]:
        """转换为 MongoDB 文档"""
        data = self.dict(**kwargs)
        if self.meta.primary_key not in kwargs["exclude"]:
            data["_id"] = data.pop(self.meta.primary_key)
        return bson.decode(bson.encode(data), codec_options=self.__encoder__)

    @classmethod
    def from_doc(cls, document: dict[str, Any]) -> Self:
        """从文档构建模型实例"""
        document[cls.meta.primary_key] = document.pop("_id")
        return cls(**document)

    @classmethod
    def aggregate(
        cls, pipeline: Pipeline | Sequence[Mapping[str, Any]], *args, **kwargs
    ) -> AggregateResult:
        """聚合查询"""
        cursor = cls.meta.collection.aggregate(pipeline, *args, **kwargs)
        return AggregateResult(cursor)

    @classmethod
    def find(
        cls,
        *args: FindMapping | Expression | bool,
    ) -> FindResult[Self]:
        """使用表达式查询数据"""
        if all_check(args, Expression | Mapping):
            return FindResult(cls, *args)  # type: ignore
        else:
            raise TypeError("查询表达式类型不正确")

    @classmethod
    async def get(cls, _id: Any) -> Self | None:
        """通过主键查询数据"""
        return await cls.find({"_id": _id}).get()

    class Config:
        validate_assignment = True
