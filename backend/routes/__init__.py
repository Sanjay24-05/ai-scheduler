"""Routes package."""
from routes.auth import router as auth_router
from routes.tasks import router as tasks_router
from routes.schedule import router as schedule_router
from routes.calendar import router as calendar_router
from routes.settings import router as settings_router
from routes.ai import router as ai_router

__all__ = [
    "auth_router",
    "tasks_router",
    "schedule_router",
    "calendar_router",
    "settings_router",
    "ai_router",
]
