from .appointments import UserAppointmentsPlugin
from .links import CMSLinkPlugin, LinkPlugin
from .tasks import TasksPlugin
from .text import TextPlugin
from .userfeed import UserFeedPlugin
from .videoplayer import VideoPlayerPlugin

__all__ = [
    "UserAppointmentsPlugin",
    "UserFeedPlugin",
    "TasksPlugin",
    "TextPlugin",
    "VideoPlayerPlugin",
    "CMSLinkPlugin",
    "LinkPlugin",
]
