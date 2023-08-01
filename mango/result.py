from collections.abc import AsyncGenerator, Generator, Mapping
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

from motor.motor_asyncio import AsyncIOMotorCursor, AsyncIOMotorLatentCommandCursor
from pydantic import BaseModel

from mango.expression import Expression, ExpressionField
from mango.index import Order
from mango.utils import any_check, is_sequence, validate_fields

if TYPE_CHECKING:  # pragma: no cover
    from pymongo.results import DeleteResult

    from mango.models import Document

T_Model = TypeVar("T_Model", bound="Document")

KeyField: TypeAlias = str | ExpressionField

FindMapping: TypeAlias = Mapping[KeyField, Any]

DirectionType: TypeAlias = Order

SortType: TypeAlias = tuple[str, DirectionType]


class FindOptions(BaseModel):
    limit: int = 0
    skip: int = 0
    sort: list[SortType] = []

    def kwdict(self, *exclude: str) -> dict[str, Any]:
        return self.dict(exclude=set(exclude), exclude_defaults=True)


class FindResult(Generic[T_Model]):
    def __init__(
        self,
        model: type[T_Model],
        *filter: FindMapping | Expression,
    ) -> None:
        self.model = model
        self.collection = model.__collection__
        self._filter = filter
        self.options = FindOptions()

    def __await__(self) -> Generator[None, None, list[T_Model]]:
        """`await` : 等待时，将返回获取的模型列表"""
        documents = yield from self.cursor.to_list(length=None).__await__()
        instances: list[T_Model] = []
        for document in documents:
            instances.append(self.model.from_doc(document))
            yield
        return instances

    async def __aiter__(self) -> AsyncGenerator[T_Model, None]:
        """`async for`: 异步迭代查询结果"""
        async for document in self.cursor:  # type: ignore
            yield self.model.from_doc(document)

    @property
    def cursor(self) -> AsyncIOMotorCursor:
        return self.collection.find(self.filter, **self.options.kwdict())

    @property
    def filter(self) -> dict[str, Any]:
        """查询过滤条件"""
        compiled: dict[str, Any] = {}
        for condition in self._filter:
            if isinstance(condition, Mapping):
                condition = dict(condition)
            elif isinstance(condition, Expression):
                condition = condition.struct()
            else:
                raise TypeError("查询过滤条件不正确, 应为映射或表达式")
            compiled |= self._compile(condition)
        return compiled

    def _compile(
        self,
        source: Mapping[KeyField, Any] | Mapping[str, Any],
    ) -> dict[str, Any]:
        compiled: dict[str, Any] = {}

        for key, value in source.items():
            key = str(key)
            if isinstance(value, Expression):
                compiled[key] = value.struct()
            elif isinstance(value, Mapping):
                compiled[key] = self._compile(value)
            elif is_sequence(value):
                compiled[key] = []
                for i in value:
                    if isinstance(i, Expression):
                        i = i.struct()
                    if isinstance(i, Mapping):
                        i = self._compile(i)
                    compiled[key].append(i)
            else:
                compiled[key] = value

        return compiled

    def limit(self, limit: int = 0) -> "FindResult[T_Model]":
        """限制查询条件返回结果的数量"""
        self.options.limit += limit
        return self

    def skip(self, skip: int = 0) -> "FindResult[T_Model]":
        """跳过指定数目的文档"""
        self.options.skip += skip
        return self

    def sort(self, *orders: Any) -> "FindResult[T_Model]":
        """对查询文档流进行排序"""
        if not (len(orders) != 2 or any_check(orders, is_sequence)):  # noqa: PLR2004
            orders = (orders,)
        for order in orders:
            direction = Order.ASC
            if is_sequence(order):
                key, direction = order
            else:
                key = order

            try:
                key, direction = str(key), Order(direction)
            except ValueError as e:
                raise TypeError("键应为字符串或字段, 排序方向应为 Order 枚举成员") from e
            else:
                self.options.sort.append((key, direction))

        return self

    def asc(self, *keys: Any) -> "FindResult[T_Model]":
        """升序排列"""
        self.options.sort.extend(self._sort_order(*keys))
        return self

    def desc(self, *keys: Any) -> "FindResult[T_Model]":
        """降序排列"""
        self.options.sort.extend(self._sort_order(*keys, reverse=True))
        return self

    def _sort_order(
        self, *keys: Any, reverse: bool = False
    ) -> Generator[SortType, None, None]:
        direction: Order = Order.DESC if reverse else Order.ASC
        for key in keys:
            yield str(key), direction

    async def count(self) -> int:
        """获得符合条件的文档总数"""
        return await self.collection.count_documents(
            self.filter, **self.options.kwdict("sort")
        )

    async def get(self) -> T_Model | None:
        """
        从数据库中获取单个文档。
        返回单个文档，如果没有找到匹配的文档，返回“None”。
        """
        if document := await self.collection.find_one(self.filter):
            return self.model.from_doc(document)
        return None

    async def delete(self) -> int:
        """删除符合条件的文档"""
        result: DeleteResult = await self.collection.delete_many(self.filter)
        return result.deleted_count

    async def update(self, **kwargs: Any) -> None:
        """使用提供的信息更新查找到的文档"""
        values = validate_fields(self.model, kwargs)
        await self.collection.update_many(self.filter, {"$set": values})


class AggregateResult:
    def __init__(self, cursor: AsyncIOMotorLatentCommandCursor) -> None:
        self.cursor = cursor

    def __await__(self) -> Generator[None, None, list[dict[str, Any]]]:
        """
        `await` : 等待时，将返回聚合管道的结果文档列表
        """
        return (yield from self.cursor.to_list(length=None).__await__())

    async def __aiter__(self) -> AsyncGenerator[dict[str, Any], None]:
        """`async for`: 异步迭代聚合管道的结果文档"""
        async for document in self.cursor:  # type: ignore
            yield document
