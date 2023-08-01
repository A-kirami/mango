import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from mango.drive import DEFAULT_CONNECT_URI, Client
from mango.utils import get_indexes, to_snake_case

if TYPE_CHECKING:  # pragma: no cover
    from mango.models import Document


async def init_model(model: type["Document"], *, revise_index: bool = False) -> None:
    """初始化文档模型"""
    meta = model.__meta__
    db = Client.get_database(meta.database)
    model.__collection__ = db[meta.name or to_snake_case(model.__name__)]
    await init_index(model, revise_index=revise_index)


async def init_index(model: type["Document"], *, revise_index: bool = False) -> None:
    """初始化文档索引"""
    required = ["_id_"]
    if indexes := list(get_indexes(model)):
        required += await model.__collection__.create_indexes(indexes)
    if revise_index:
        index_info = await model.__collection__.index_information()
        for index in set(index_info) - set(required):
            await model.__collection__.drop_index(index)


class Mango:
    _document_models: ClassVar[set[type["Document"]]] = set()

    @classmethod
    async def init(
        cls,
        db: str | None = None,
        *,
        uri: str = DEFAULT_CONNECT_URI,
        revise_index: bool = False,
        **kwargs: Any,
    ) -> None:
        if db or uri or not Client._clients:
            cls.connect(db, uri, **kwargs)
        tasks = [
            init_model(model, revise_index=revise_index)
            for model in cls._document_models
        ]
        await asyncio.gather(*tasks)

    @classmethod
    def connect(
        cls,
        db: str | None = None,
        /,
        uri: str = DEFAULT_CONNECT_URI,
        **kwargs: Any,
    ) -> Client:
        """创建连接"""
        client = Client(uri, **kwargs)
        client.get_database(db)
        return client

    @classmethod
    def disconnect(cls, *clients: Client) -> None:
        """断开连接"""
        for client in Client._clients.copy():
            if not clients or client in clients:
                client.close()

    @classmethod
    def register_model(cls, model: type["Document"]) -> None:
        """注册模型"""
        cls._document_models.add(model)
