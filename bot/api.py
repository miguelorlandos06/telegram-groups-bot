"""
Endpoints JSON para la Mini App.
"""
from aiohttp import web
from bot import db, config


async def api_groups(request: web.Request) -> web.Response:
    """GET /api/groups?q=&country=&language=&category=&type=&page="""
    q = request.query.get("q", "").strip()
    country = request.query.get("country") or None
    language = request.query.get("language") or None
    category = request.query.get("category") or None
    tipo = request.query.get("type") or None
    members_range = request.query.get("members_range") or None
    show_adult = request.query.get("show_adult") == "1"

    try:
        page = int(request.query.get("page", "0"))
    except ValueError:
        page = 0

    min_members = None
    if members_range:
        min_members = config.MEMBERS_VALUES.get(members_range)

    filters = {
        "country": country,
        "language": language,
        "category": category,
        "type": tipo,
        "min_members": min_members,
        "is_adult": None if show_adult else False,
    }

    try:
        if q:
            total = await db.count_groups(query=q, filters=filters)
            items = await db.search_groups(q, filters, page=page)
        else:
            if tipo:
                total = await db.count_by_type(tipo, filters)
                items = await db.list_by_type(tipo, "recent", filters, page=page, per_page=10)
            else:
                total = await db.count_by_type("all", filters)
                items = await db.list_by_type("all", "recent", filters, page=page, per_page=10)
    except Exception as e:
        return web.json_response(
            {"error": str(e), "items": [], "total": 0},
            status=500
        )

    return web.json_response({
        "total": total,
        "page": page,
        "per_page": 10,
        "items": [_serialize(g) for g in items],
    })


async def api_meta(request: web.Request) -> web.Response:
    """GET /api/meta → categorías, países, idiomas"""
    return web.json_response({
        "categories": config.CATEGORIES,
        "countries": config.COUNTRIES,
        "languages": config.LANGUAGES,
        "members_ranges": config.MEMBERS_RANGES,
    })


async def api_stats(request: web.Request) -> web.Response:
    """GET /api/stats"""
    try:
        stats = await db.get_stats()
    except Exception as e:
        stats = {"error": str(e)}
    return web.json_response(stats)


def _serialize(g) -> dict:
    keys = g.keys()
    return {
        "id": g["id"],
        "link": g["link"],
        "title": g["title"],
        "description": g["description"] or "",
        "category": g["category"],
        "category_label": config.CATEGORIES.get(g["category"], g["category"]) if g["category"] else None,
        "country": g["country"],
        "country_label": config.COUNTRIES.get(g["country"], g["country"]) if g["country"] else None,
        "language": g["language"],
        "members_range": g["members_range"],
        "members_label": config.MEMBERS_RANGES.get(g["members_range"]) if g["members_range"] else None,
        "is_adult": g["is_adult"],
        "type": g["type"] if "type" in keys else "group",
        "views": g["views"],
        "tags": g["tags"] or "",
    }


def setup_api(app: web.Application):
    app.router.add_get("/api/groups", api_groups)
    app.router.add_get("/api/meta", api_meta)
    app.router.add_get("/api/stats", api_stats)
