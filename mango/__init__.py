from importlib.metadata import version

from mango.drive import connect
from mango.expression import OPR
from mango.fields import Field
from mango.index import Attr, Index, Order
from mango.models import Model
from mango.stage import Pipeline

__version__ = version("mango-odm")

__all__ = ["connect", "OPR", "Field", "Attr", "Index", "Order", "Model", "Pipeline"]
