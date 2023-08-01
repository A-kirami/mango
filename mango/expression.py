from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from pydantic.fields import ModelField
from typing_extensions import Self

from mango.fields import FieldInfo

if TYPE_CHECKING:  # pragma: no cover
    from mango.models import Document


class Operators(Enum):
    EQ = auto()
    """等于"""
    NE = auto()
    """不等于"""
    LT = auto()
    """小于"""
    LTE = auto()
    """小于或等于"""
    GT = auto()
    """大于"""
    GTE = auto()
    """大于或等于"""
    OR = auto()
    """逻辑或"""
    AND = auto()
    """逻辑与"""
    NOR = auto()
    """逻辑非或"""
    IN = auto()
    """包含在"""
    NIN = auto()
    """不包含在"""
    REGEX = auto()
    """正则匹配"""

    def __str__(self) -> str:
        return f"${self.name.lower()}"


class ExpressionField:
    def __init__(
        self, field: ModelField, parents: list[tuple[str, "Document"]]
    ) -> None:
        self.field = field
        self.parents = parents

    def __eq__(self, other: Any) -> "Expression":
        return OPR(self).eq(other)

    def __ne__(self, other: Any) -> "Expression":
        return OPR(self).ne(other)

    def __lt__(self, other: Any) -> "Expression":
        return OPR(self).lt(other)

    def __le__(self, other: Any) -> "Expression":
        return OPR(self).lte(other)

    def __gt__(self, other: Any) -> "Expression":
        return OPR(self).gt(other)

    def __ge__(self, other: Any) -> "Expression":
        return OPR(self).gte(other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __repr__(self) -> str:
        return f"ExpressionField(name={self!s}, type={self.field._type_display()})"

    def __str__(self) -> str:
        names = [p[0] for p in self.parents]
        if isinstance(finfo := self.field.field_info, FieldInfo) and finfo.primary_key:
            names.append("_id")
        else:
            names.append(self.field.name)
        return ".".join(names)

    def __getattr__(self, name: str) -> Any:
        """内嵌查询反向查找分配父级"""
        attr = getattr(self.field.outer_type_, name)
        if isinstance(attr, self.__class__):
            new_parent = (self.field.name, self.field.outer_type_)
            if new_parent not in attr.parents:
                attr.parents.append(new_parent)
            if new_parents := list(set(self.parents) - set(attr.parents)):
                attr.parents = new_parents + attr.parents
        return attr


@dataclass
class Expression:
    key: ExpressionField | None
    operator: Operators
    value: Any

    def __or__(self, other: Self) -> Self:
        return OPR.or_(self, other)

    def __and__(self, other: Self) -> Self:
        return OPR.and_(self, other)

    def __repr__(self) -> str:
        return f"Expression({self.struct()})"

    def struct(self) -> dict[str, Any]:
        """转换为 MongoDB 查询结构"""
        value = {str(self.operator): self.unpack(self.value)}
        return {str(self.key): value} if self.key else value

    def unpack(self, value: Any) -> Any:
        # TODO: 将嵌入文档模型转换为 mongodb 文档形式
        return value

    def merge(self, operator: Operators) -> Any:
        return self.value if self.operator is operator else [self]


class OPR:
    def __init__(self, key: Any) -> None:
        if not isinstance(key, ExpressionField):
            raise TypeError("必须是有效的字段")
        self.key = key

    def eq(self, value: Any) -> Expression:
        return Expression(self.key, Operators.EQ, value)

    def ne(self, value: Any) -> Expression:
        return Expression(self.key, Operators.NE, value)

    def lt(self, value: Any) -> Expression:
        return Expression(self.key, Operators.LT, value)

    def lte(self, value: Any) -> Expression:
        return Expression(self.key, Operators.LTE, value)

    def gt(self, value: Any) -> Expression:
        return Expression(self.key, Operators.GT, value)

    def gte(self, value: Any) -> Expression:
        return Expression(self.key, Operators.GTE, value)

    def in_(self, *values: Any) -> Expression:
        """包含在"""
        return Expression(self.key, Operators.IN, values)

    def nin(self, *values: Any) -> Expression:
        """不包含在"""
        return Expression(self.key, Operators.NIN, values)

    def regex(self, values: str) -> Expression:
        """正则匹配"""
        return Expression(self.key, Operators.REGEX, values)

    @classmethod
    def or_(cls, *expressions: Expression | bool) -> Expression:
        merge = cls._merge(Operators.OR, expressions)
        return Expression(None, *merge)

    @classmethod
    def and_(cls, *expressions: Expression | bool) -> Expression:
        merge = cls._merge(Operators.AND, expressions)
        return Expression(None, *merge)

    @classmethod
    def nor(cls, *expressions: Expression | bool) -> Expression:
        """既不……也不……"""
        merge = cls._merge(Operators.NOR, expressions)
        return Expression(None, *merge)

    @classmethod
    def _merge(
        cls, operator: Operators, expressions: tuple[Expression | bool]
    ) -> tuple[Operators, list[Expression]]:
        merge_expr: list[Expression] = []
        for expression in expressions:
            if not isinstance(expression, Expression):
                raise TypeError("必须是有效的表达式")

            if expression.operator is operator:
                merge_expr.extend(expression.value)
            else:
                merge_expr.append(expression)

        return operator, merge_expr
