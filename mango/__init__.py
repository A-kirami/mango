from mango.drive import connect
from mango.expression import OPR
from mango.fields import Field
from mango.index import Attr, Index, Order
from mango.models import Model

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # pragma: no cover
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__)

__all__ = ["connect", "OPR", "Field", "Attr", "Index", "Order", "Model"]
