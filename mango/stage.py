from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeAlias

from typing_extensions import Self

from mango.index import Order

SortOrder: TypeAlias = Order | Literal[1, -1]


class Pipeline(list[Mapping[str, Any]]):
    """聚合管道阶段"""

    def __init__(self, *stages: Mapping[str, Any]) -> None:
        super().__init__(stages)

    def stage(self, key: str, value: Any) -> Self:
        """添加一个阶段"""
        key = key if key.startswith("$") else f"${key}"
        self.append({key: value})
        return self

    def bucket(
        self,
        group_by: Any,
        boundaries: Sequence[int | float],
        default: str | None = None,
        output: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> Self:
        """
        根据指定的表达式和存储桶边界将传入文档分类到称为存储桶的组中，并为每个存储桶输出一个文档。

        group_by: 对文档进行分组的表达式。若要指定字段路径，请在字段名前面加上符号 `$` 。
        boundaries: 基于 `group_by` 表达式的值数组，用于指定每个桶的边界。每对相邻的值作为桶的包含下边界和独占上边界。
        default: 指定一个附加桶的 `_id`，该桶包含 `group_by` 表达式结果中，不属于边界指定的桶的所有文档。
        output: 指定输出文档中除 `_id` 字段外还要包含的字段。如果未指定文档，则操作返回包含文档数的字段在每个存储桶中。

        [$bucket (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/bucket/)
        """
        if len(boundaries) < 2:  # noqa: PLR2004
            raise ValueError("必须至少指定两个边界值")
        if sorted(boundaries) != boundaries:
            raise ValueError("指定的值必须以升序排列")
        struct = {
            "groupBy": group_by,
            "boundaries": boundaries,
        }
        if default:
            struct["default"] = default
        if output:
            struct["output"] = output
        return self.stage("bucket", struct)

    def count(self, field: str) -> Self:
        """
        将文档传递到下一阶段，该阶段包含输入到该阶段的文档数量的计数。

        field : 输出字段的名称，其值为计数结果。必须是非空字符串，不能以 `$` 开头，也不能包含 `.` 字符。

        [$count (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/count/)
        """
        if not field or field.startswith("$") or "." in field:
            raise ValueError("必须是非空字符串, 不能以 `$` 开头，也不能包含 `.` 字符。")
        return self.stage("count", field)

    def documents(self, expression: Any) -> Self:
        """
        从输入值返回原始文档。

        expression: 接受任何解析为映射数组的有效表达式。

        [$documents (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/documents/)
        """
        return self.stage("documents", expression)

    def facet(self, **fields: Self | Sequence[Mapping[str, Any]]) -> Self:
        """
        在同一组输入文档的单个阶段内处理多个聚合管道。每个子管道在输出文档中都有自己的字段，其结果存储为一个文档数组。
        输入文档只被传递到 `$facet` 阶段一次。`$facet` 支持对同一组输入文档进行各种聚合，无需多次检索输入文档。

        fields: 参数名为子管道输出的字段名, 参数为需要运行的子管道。

        [$facet (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/facet/)
        """
        return self.stage("facet", fields)

    def fill(
        self,
        output: Mapping[str, Any],
        partition_by: Any = None,
        partition_by_fields: Sequence[str] | None = None,
        sort_by: Mapping[str, SortOrder] | None = None,
    ) -> Self:
        """
        填充文档中的空值和缺少的字段值。

        output: 指定一个字典，该字典包含要填充缺失值的每个字段输出对象的字典。对象名称是要填充的字段的名称，对象值指定如何填充该字段。
        partition_by: 指定用于对文档进行分组的表达式。`partition_by` 和 `partition_by_fields` 是互斥的。
        partition_by_fields: 指定字段数组，以作为文档分组的复合键。`partition_by` 和 `partition_by_fields` 是互斥的。
        sort_by: 指定用于对每个分区内的文档进行排序的字段。

        [$fill (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/fill/)
        """
        struct: dict[str, Any] = {
            "output": output,
        }
        if partition_by:
            struct["partitionBy"] = partition_by
        elif partition_by_fields:
            if isinstance(partition_by_fields, str):
                raise TypeError("partition_by_fields 不能为字符串")
            struct["partitionByFields"] = partition_by_fields
        if sort_by:
            struct["sortBy"] = sort_by
        return self.stage("fill", struct)

    def group(self, id: Any, **fields: Mapping[str, Any]) -> Self:
        """
        `$group` 阶段根据“组键”将文档分成多个组。
        组键通常是一个字段或一组字段。组键也可以是表达式的结果。
        在 `$group` 阶段的输出中，`_id` 字段被设置为该文档的组键。
        每个输出文档的字段都包含唯一的按值分组。输出文档还可以包含包含某些累加器表达式值的计算字段。

        id: 可以接受任何有效的表达式。如果指定 `id` 为 `None` 或任何其他常数值，那么此 `$group` 阶段将整体计算所有输入文档的累积值。
        fields: 参数名为额外添加的字段, 参数为累加器表达式。

        [$group (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/group/)
        """
        return self.stage("group", {"_id": id, **fields})

    def limit(self, integer: int) -> Self:
        """
        限制传递到管道中下一阶段的文档数。

        integer: 指定要传递的文档的最大数量。

        [$limit (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/limit/)
        """
        return self.stage("limit", integer)

    def lookup(
        self,
        from_: str | None = None,
        local_field: str | None = None,
        foreign_field: str | None = None,
        let: Mapping[str, Any] | None = None,
        pipeline: Self | Sequence[Mapping[str, Any]] | None = None,
        as_: str | None = None,
    ) -> Self:
        """
        对同一数据库中的集合执行左外联接，以从“联接”集合中筛选文档进行处理。
        此 `$lookup` 阶段为每个输入文档添加一个新的数组字段，新的数组字段包含“联接”集合中的匹配文档，并将这些重新成形的文档传递到下一阶段。

        from_: 指定同一数据库中要联接到当前集合的外部集合。
        local_field: 指定当前集合的文档中的字段。
        foreign_field: 指定外部集合的文档中的字段。
        let: 指定要在管道阶段中使用的变量。使用变量表达式访问输入到管道的文档字段。
        pipeline: 指定要在已联接集合上运行的管道。管道从已联接的集合中确定结果文档。若要返回所有文档，请指定空管道。
        as_: 指定要添加到输出文档的新数组字段的名称。新的数组字段包含来自 `from_` 集合的匹配文档。如果指定的名称已经存在于输出文档中，则覆盖现有字段。

        [$lookup (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/lookup/)
        """
        return self.stage(
            "lookup",
            {
                k: v
                for k, v in {
                    "from": from_,
                    "localField": local_field,
                    "foreignField": foreign_field,
                    "let": let,
                    "pipeline": pipeline,
                    "as": as_,
                }.items()
                if v is None
            },
        )

    def match(self, query: Mapping[str, Any]) -> Self:
        """
        筛选文档流，仅将匹配指定条件的文档传递到下一个管道阶段。

        query: 指定查询条件。

        [$match (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/match/)
        """
        return self.stage("match", query)

    def merge(
        self,
        collection: str,
        database: str | None = None,
        let: Mapping[str, Any] | None = None,
        on: str | Sequence[str] | None = None,
        matched: Literal["replace", "keepExisting", "merge", "fail"]
        | Self
        | Sequence[Mapping[str, Any]] = "merge",
        not_matched: Literal["insert", "discard", "fail"] = "insert",
    ) -> None:
        """
        将聚合管道的结果写入指定的集合。`$merge` 操作符必须是管道中的最后一个阶段。

        collection: 输出到指定集合。如果输出集合不存在，将会创建集合。
        database: 输出到指定数据库，不指定则默认输出到运行聚合管道的同一数据库。
        let: 指定在 `matched` 管道中使用的变量。
        on: 作为文档唯一标识符的一个或多个字段。该标识符用于确定结果文档是否与输出集合中的现有文档匹配。
        matched: 如果结果文档和输出集合中的现有文档对于字段上指定的值相同，则 `$merge` 的行为。
        not_matched: 如果结果文档与输出集合中的现有文档不匹配，则 `$merge` 的行为。

        [$merge (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/merge/)
        """
        struct = {
            "into": {"db": database, "coll": collection} if database else collection,
            "whenMatched": matched,
            "whenNotMatched": not_matched,
        }
        if let:
            struct["let"] = let
        if on:
            struct["on"] = on
        self.stage("merge", struct)

    def out(self, collection: str, database: str | None = None) -> Self:
        """
        获取聚合管道返回的文档并将它们写入指定的集合。

        database: 输出数据库名称。
        collection: 输出集合名称。

        [$out (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/out/)
        """
        return self.stage(
            "out", {"db": database, "coll": collection} if database else collection
        )

    def project(self, **fields: bool | Mapping[str, Any]) -> Self:
        """
        将带有指定字段的文档传递到管道中的下一阶段。指定的字段可以是输入文档中的现有字段或新计算的字段。

        fields: 参数名为指定传递的字段。参数如果为布尔值，则可以包含或排除字段；如果为表达式，则可以添加新字段或重置现有字段的值。

        [$project (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/project/)
        """
        return self.stage("project", fields)

    def redact(self, expression: Any) -> Self:
        """
        根据存储在文档本身中的信息限制文档的内容。

        expression: 可以是任何有效的表达式，只要它解析为 `$$DESCEND`、`$$PRUNE` 或 `$$KEEP` 系统变量。

        [$redact (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/redact/)
        """
        return self.stage("redact", expression)

    def replace(self, replacement: Any) -> Self:
        """
        用指定的文档替换输入文档。该操作将替换输入文档中的所有现有字段，包括 `_id` 字段。

        replacement: 可以是解析为文档的任何有效表达式。

        [$replaceWith (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/replaceWith/)
        """
        return self.stage("replaceWith", replacement)

    def sample(self, size: int) -> Self:
        """
        从输入文档中随机选择指定数量的文档。

        size: 随机选择的文档数量。

        [$sample (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/sample/)
        """
        return self.stage("sample", {"size": size})

    def set(self, **fields: Any) -> Self:
        """
        向文档中添加新字段。输出包含来自输入文档的所有现有字段和新添加的字段的文档。

        field: 参数名为需要添加的每个字段的名称，参数为聚合表达式。如果新字段的名称与现有字段名称(包括 `_id`)相同，`$set` 将使用指定表达式的值覆盖该字段的现有值。

        [$set (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/set/)
        """
        return self.stage("set", fields)

    def skip(self, integer: int) -> Self:
        """
        跳过传递到该阶段的指定数量的文档，并将其余文档传递到管道中的下一个阶段。

        integer: 指定要跳过的文档的最大数量。

        [$skip (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/skip/)
        """
        return self.stage("skip", integer)

    def sort(self, **fields: SortOrder) -> Self:
        """
        对所有输入文档进行排序，并按排序顺序将它们返回给管道。

        field: 参数名为指定要排序的字段，参数为字段的排序顺序。最多可以按32个字段进行排序。

        [$sort (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/sort/)
        """
        return self.stage("sort", fields)

    def union(
        self,
        collection: str,
        pipeline: Self | Sequence[Mapping[str, Any]] | None = None,
    ) -> Self:
        """
        执行两个集合的联合。
        将来自两个集合的管道结果合并为一个结果集，将组合的结果集(包括重复的)输出到下一阶段

        collection: 希望在结果集中包含其管道结果的集合。
        pipeline: 应用于指定的集合的聚合管道。

        [$unionWith (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/unionWith/)
        """
        return self.stage(
            "unionWith",
            {"coll": collection, "pipeline": pipeline} if pipeline else collection,
        )

    def unset(self, *fields: str) -> Self:
        """
        从文档中移除/排除字段。

        field: 指定要删除的字段。

        [$unset (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/unset/)
        """
        return self.stage("unset", fields)

    def unwind(
        self, path: str, index_field: str | None = None, preserve_empty: bool = False
    ) -> Self:
        """
        从输入文档中解构数组字段以输出每个元素的文档。每个输出文档都是输入文档，数组字段的值由元素替换。

        path: 数组字段的字段路径。若要指定字段路径，请在字段名开头加上符号 `$`。
        index_field: 保存元素数组索引的新字段的名称。名称不能以符号 `$` 开头。
        preserve_empty: 在文档中的指定字段路径为 null、不存在或为空数组的情况下，如果该值为 `True`，则 `$unwind` 将输出文档，否则不会输出文档。

        [$unwind (aggregation)](https://www.mongodb.com/docs/manual/reference/operator/aggregation/unwind/#mongodb-pipeline-pipe.-unwind)
        """
        struct = {
            "path": path,
            "preserveNullAndEmptyArrays": preserve_empty,
        }
        if index_field:
            struct["includeArrayIndex"] = index_field
        return self.stage("unwind", struct)
