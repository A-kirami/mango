from collections.abc import Sequence
from typing import Any, ClassVar

from mango.drive import Database
from mango.encoder import EncodeType
from mango.index import Index, IndexTuple


class MetaConfig:
    name: ClassVar[str | None] = None
    database: ClassVar[Database | str | None] = None
    indexes: ClassVar[Sequence[str | Index | Sequence[IndexTuple]]] = []
    bson_encoders: ClassVar[EncodeType] = {}
    by_alias: ClassVar[bool] = False


def inherit_meta(
    self_config: type[MetaConfig] | None,
    parent_config: type[MetaConfig],
    **namespace: Any,
) -> type[MetaConfig]:
    if not self_config:
        base_classes = (parent_config,)
    elif self_config == parent_config:
        base_classes = (self_config,)
    else:
        base_classes = self_config, parent_config

    namespace["bson_encoders"] = {
        **getattr(parent_config, "bson_encoders", {}),
        **getattr(self_config, "bson_encoders", {}),
        **namespace.get("bson_encoders", {}),
    }

    return type("Meta", base_classes, namespace)
