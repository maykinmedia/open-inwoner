from .bericht_detail import (
    BerichtDetailView,
    BerichtDownloadView,
    MarkBerichtUnreadView,
)
from .bericht_list import BerichtListView

__all__ = [
    "BerichtDetailView",
    "BerichtListView",
    "MarkBerichtUnreadView",
    "BerichtDownloadView",
]
