"""Road Hawk — fleet and driver operations for trucking."""

from .branding import (
    BRAND,
    BRAND_ASSETS_SOURCE,
    COMPANY_LEGAL,
    COMPANY_SHORT,
    COPYRIGHT_NOTICE,
    PRODUCT,
)
from .version import package_version

__version__ = package_version()
__all__ = [
    "BRAND",
    "BRAND_ASSETS_SOURCE",
    "COMPANY_LEGAL",
    "COMPANY_SHORT",
    "COPYRIGHT_NOTICE",
    "PRODUCT",
    "__version__",
]