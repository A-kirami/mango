import re
from collections.abc import Callable, Iterable, Sequence
from types import UnionType
from typing import TYPE_CHECKING, Any, Type

import pydantic

if TYPE_CHECKING:  # pragma: no cover
    from mango.models import Model


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
    else:
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
    else:
        return any(isinstance(obj, type_or_func) for obj in iter_obj)


def is_sequence(
    iter_obj: Sequence[object],
) -> bool:
    """判断是否为非字符串的序列对象"""
    return isinstance(iter_obj, Sequence) and not isinstance(iter_obj, bytes | str)


def field_validate(model: Type["Model"], input_data: dict[str, Any]) -> dict[str, Any]:
    """验证模型的指定字段"""
    if miss := set(input_data) - set(model.__fields__):
        raise ValueError(f"这些字段在 {model.__name__} 中不存在: {miss}")

    fields = {
        k: (v.type_, v.field_info)
        for k, v in model.__fields__.items()
        if k in input_data
    }
    new_model = pydantic.create_model(model.__name__, **fields)
    values, _, validation_error = pydantic.validate_model(new_model, input_data)

    if validation_error:
        raise validation_error

    return values
