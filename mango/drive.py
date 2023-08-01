import os
from collections.abc import Iterator
from typing import Any, ClassVar

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from typing_extensions import Self

DEFAULT_CONNECT_URI = os.getenv("MANGO_URI") or "mongodb://localhost:27017"
DEFAULT_DATABASE_NAME = "test"


class Collection:
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    def __getattr__(self, name: str) -> Any:
        return getattr(self.collection, name)

    def __repr__(self) -> str:
        return f"Collection(name={self.name}, db={self.full_name.split('.')[0]})"

    @property
    def name(self) -> str:
        return self.collection.name

    @property
    def full_name(self) -> str:
        return self.collection.full_name


class Database:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.collections: dict[str, Collection] = {}

    def __getattr__(self, name: str) -> Collection:
        try:
            return self.collections[name]
        except KeyError:
            collection: AsyncIOMotorCollection = self.db.get_collection(name)
            self.collections[name] = Collection(collection)
            return self.collections[name]

    def __getitem__(self, name: str) -> Collection:
        return self.__getattr__(name)

    def __iter__(self) -> Iterator[Collection]:
        return iter(self.collections.values())

    def __repr__(self) -> str:
        return (
            f"Database(name={self.name}, "
            f"host={self.client.HOST}, "
            f"port={self.client.PORT})"
        )

    async def drop_collection(self, collection: str | Collection) -> None:
        """删除集合"""
        name = collection if isinstance(collection, str) else collection.name
        await self.db.drop_collection(name)
        self.collections.pop(name, None)

    @property
    def name(self) -> str:
        return self.db.name

    @property
    def client(self) -> AsyncIOMotorClient:
        return self.db.client


class Client:
    _clients: ClassVar[set[Self]] = set()

    def __init__(self, uri: str = DEFAULT_CONNECT_URI, **kwargs: Any) -> None:
        kwargs.setdefault("host", uri)
        self.client = AsyncIOMotorClient(**kwargs)
        self.databases: dict[str, Database] = {}
        self.__class__._clients.add(self)

    def __getattr__(self, name: str) -> Database:
        try:
            return self.databases[name]
        except KeyError:
            db: AsyncIOMotorDatabase = self.client.get_database(name)
            self.databases[name] = Database(db)
            return self.databases[name]

    def __getitem__(self, name: str) -> Database:
        return self.__getattr__(name)

    def __iter__(self) -> Iterator[Database]:
        return iter(self.databases.values())

    def __repr__(self) -> str:
        return f"Client(host={self.host}, port={self.port})"

    def close(self) -> None:
        """关闭连接"""
        self.client.close()
        self.__class__._clients.remove(self)

    async def drop_database(self, database: str | Database) -> None:
        """删除数据库"""
        name = database if isinstance(database, str) else database.name
        await self.client.drop_database(name)
        self.databases.pop(name, None)

    @classmethod
    def get_database(cls, db: Database | str | None = None) -> Database:
        """获取数据库"""
        try:
            client = next(iter(cls._clients))
        except StopIteration:
            client = cls()

        if isinstance(db, Database):
            return db
        return client[db] if isinstance(db, str) else client.default_database

    @property
    def default_database(self) -> Database:
        """默认为首次调用的数据库, 如果不存在, 则创建 test 数据库"""
        try:
            return next(iter(self.databases.values()))
        except StopIteration:
            ddb = self.client.get_default_database(DEFAULT_DATABASE_NAME)
            return self[ddb.name]

    @property
    def host(self) -> str:
        return self.client.HOST

    @property
    def port(self) -> int:
        return self.client.PORT

    @property
    def address(self) -> tuple[str, int]:
        return self.client.address
