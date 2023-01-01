from importlib.metadata import version

from mango.expression import OPR
from mango.fields import Field
from mango.index import Attr, Index, Order
from mango.models import Document, EmbeddedDocument
from mango.source import Mango
from mango.stage import Pipeline

__version__ = version("mango-odm")

__all__ = [
    "OPR",
    "Field",
    "Attr",
    "Index",
    "Order",
    "Document",
    "EmbeddedDocument",
    "Mango",
    "Pipeline",
]
