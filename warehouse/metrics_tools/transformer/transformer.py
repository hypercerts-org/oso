import typing as t
from dataclasses import dataclass

from metrics_tools.transformer.base import Transform
from metrics_tools.transformer.qualify import QualifyTransform
from sqlglot import exp
from sqlmesh.core.dialect import parse


@dataclass(kw_only=True)
class SQLTransformer:
    """The sql transformer.

    This defines a process for sql transformation. Given an ordered list of Transforms
    """

    transforms: t.List[Transform]

    def transform(self, query: str | t.List[exp.Expression]):
        if isinstance(query, str):
            transformed = parse(query)
        else:
            transformed = query
        # Qualify all
        # transformed = list(map(qualify, transformed))
        transformed = QualifyTransform()(transformed)

        for transform in self.transforms:
            transformed = transform(transformed)
        return transformed
