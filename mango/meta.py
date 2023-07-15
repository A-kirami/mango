from typing import Any, Mapping, Optional, Sequence, Tuple, Type, Union

from mango.drive import Database
from mango.encoder import EncodeType
from mango.index import Attr, Index, Order

MetaConfigType = Type["MetaConfig"]


class MetaConfig:
    name: Optional[str] = None
    database: Optional[Union[Database, str]] = None
    indexes: Sequence[
        Union[str, Index, Sequence[Tuple[Union[str, Order, Attr, Mapping[str, Any]]]]]
    ] = []
    bson_encoders: EncodeType = {}
    by_alias: bool = False


def inherit_meta(
    self_config: Union[MetaConfigType, None],
    parent_config: MetaConfigType,
    **namespace: Any,
) -> MetaConfigType:
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
