from aiogram import Router
from . import start, add_group, search, settings, all_groups, trending


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(add_group.router)
    router.include_router(search.router)
    router.include_router(settings.router)
    router.include_router(all_groups.router)
    router.include_router(trending.router)
    return router
