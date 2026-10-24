"""Language Matrix - Standalone Korean language tutor"""

__version__ = "0.1.0"
__author__ = "Language Matrix Team"

from .lesson_engine import LessonEngine
from .lesson_schema import LessonSchema
from .lesson_validator import LessonValidator
from .browser_gui import BrowserGUI

__all__ = [
    "LessonEngine",
    "LessonSchema",
    "LessonValidator",
    "BrowserGUI",
]
