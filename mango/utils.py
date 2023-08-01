import re
from collections.abc import Callable, Generator, Iterable, Sequence
from types import UnionType
from typing import TYPE_CHECKING, Any

import pydantic
from pydantic.fields import ModelField

from mango.fields import FieldInfo
from mango.index import Index, IndexType

if TYPE_CHECKING:  # pragma: no cover
    from mango.models import Document


def to_snake_case(string: str) -> str:
    """将字符串转换为蛇形命名法"""
    tmp = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", tmp).lower()


def all_check(
    iter_obj: Iterable[object],
    type_or_func: type
    | UnionType
    | Callable
    | tuple[type | UnionType | tuple[Any, ...], ...],
) -> bool:
    """
    如果可迭代对象中的所有元素为指定类型，则返回True。
    如果可迭代对象为空，则返回True。
    """
    if isinstance(type_or_func, Callable):
        return all(type_or_func(obj) for obj in iter_obj)
    return all(isinstance(obj, type_or_func) for obj in iter_obj)


def any_check(
    iter_obj: Iterable[object],
    type_or_func: type
    | UnionType
    | Callable
    | tuple[type | UnionType | tuple[Any, ...], ...],
) -> bool:
    """
    如果可迭代对象中的任意元素为指定类型，则返回True。
    如果可迭代对象为空，则返回False。
    """
    if isinstance(type_or_func, Callable):
        return any(type_or_func(obj) for obj in iter_obj)
    return any(isinstance(obj, type_or_func) for obj in iter_obj)


def is_sequence(
    iter_obj: Sequence[object],
) -> bool:
    """判断是否为非字符串的序列对象"""
    return isinstance(iter_obj, Sequence) and not isinstance(iter_obj, bytes | str)


def validate_fields(
    model: type["Document"], input_data: dict[str, Any]
) -> dict[str, Any]:
    """验证模型的指定字段"""
    if miss := set(input_data) - set(model.__fields__):
        raise ValueError(f"这些字段在 {model.__name__} 中不存在: {miss}")

    fields = {
        k: (v.outer_type_, v.field_info)
        for k, v in model.__fields__.items()
        if k in input_data
    }
    new_model = pydantic.create_model(model.__name__, **fields)
    values, _, validation_error = pydantic.validate_model(new_model, input_data)

    if validation_error:
        raise validation_error

    return values


def add_fields(model: type["Document"], **field_definitions: Any) -> None:
    """动态添加字段

    来源见: https://github.com/pydantic/pydantic/issues/1937
    """
    new_fields: dict[str, ModelField] = {}
    new_annotations: dict[str, type | None] = {}

    for f_name, f_def in field_definitions.items():
        if isinstance(f_def, tuple):
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise ValueError(
                    "field definitions should either be a tuple of (<type>, <default>) "
                    "or just a default value, unfortunately this means tuples as "
                    "default values are not allowed"
                ) from e
        else:
            f_annotation, f_value = None, f_def

        if f_annotation:
            new_annotations[f_name] = f_annotation

        new_fields[f_name] = ModelField.infer(
            name=f_name,
            value=f_value,
            annotation=f_annotation,
            class_validators=None,
            config=model.__config__,
        )

    model.__fields__.update(new_fields)
    model.__annotations__.update(new_annotations)


def get_indexes(model: type["Document"]) -> Generator[Index, None, None]:
    """获取模型中定义的索引, 包括字段与元配置"""
    for name, field in model.__fields__.items():
        finfo = field.field_info
        if isinstance(finfo, FieldInfo):
            if index := finfo.index:
                if index is True:
                    yield Index(name)
                elif isinstance(index, IndexType):
                    yield Index((name, index))
                else:
                    yield index
            elif expire := finfo.expire:
                yield Index(name, expireAfterSeconds=expire)

    for index in model.__meta__.indexes:
        if isinstance(index, str):
            yield Index(index)
        elif isinstance(index, Sequence):
            yield Index(*index)
        else:
            yield index
