from collections.abc import Callable
from enum import Enum
from typing import Any, ClassVar, TypeAlias

from bson.codec_options import CodecOptions, TypeRegistry

EncodeType: TypeAlias = dict[type[Any] | tuple[type[Any], ...], Callable[..., Any]]


class Encoder:
    default_encode_type: ClassVar[EncodeType] = {
        set: list,
        Enum: lambda e: e.value,
    }

    @classmethod
    def create(
        cls,
        encode_type: EncodeType | None = None,
    ) -> CodecOptions:
        """创建一个编码器"""
        encode_type = encode_type or {}

        def encoder(value: Any) -> Any:
            for type_, encoder in (encode_type | cls.default_encode_type).items():
                if isinstance(value, type_):
                    return encoder(value)
            raise TypeError(f"无法编码 {type(value)} 类型的对象: {value}")

        return CodecOptions(type_registry=TypeRegistry(fallback_encoder=encoder))

    @classmethod
    def add_encode_type(cls, encode_type: EncodeType) -> None:
        """添加新的编码类型"""
        cls.default_encode_type |= encode_type
