"""
Endpoints JSON para la Mini App.
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from aiohttp import web
from bot import db, config


async def api_groups(request: web.Request) -> web.Response:
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
    return web.json_response({
        "categories": config.CATEGORIES,
        "countries": config.COUNTRIES,
        "languages": config.LANGUAGES,
        "members_ranges": config.MEMBERS_RANGES,
    })


async def api_stats(request: web.Request) -> web.Response:
    try:
        stats = await db.get_stats()
    except Exception as e:
        stats = {"error": str(e)}
    return web.json_response(stats)


async def api_photo(request: web.Request) -> web.Response:
    file_id = request.match_info.get("file_id")
    if not file_id:
        return web.Response(status=400)
    try:
        from bot.main import get_bot
        bot = get_bot()
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        data = file_bytes.read() if hasattr(file_bytes, 'read') else bytes(file_bytes)
        return web.Response(
            body=data,
            content_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        return web.Response(status=404, text=str(e))


def _validate_init_data(init_data: str, bot_token: str):
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None
        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])
        return parsed
    except Exception:
        return None


async def api_delete_group(request: web.Request) -> web.Response:
    try:
        group_id = int(request.match_info.get("group_id"))
    except (ValueError, TypeError):
        return web.json_response({"error": "invalid_id"}, status=400)

    init_data = request.headers.get("X-Init-Data", "")
    if not init_data:
        return web.json_response({"error": "no_auth"}, status=401)

    parsed = _validate_init_data(init_data, config.BOT_TOKEN)
    if not parsed or "user" not in parsed:
        return web.json_response({"error": "invalid_auth"}, status=401)

    user_id = parsed["user"]["id"]

    group = await db.get_group_by_id(group_id)
    if not group:
        return web.json_response({"error": "not_found"}, status=404)

    if group["owner_id"] != user_id:
        return web.json_response({"error": "not_owner"}, status=403)

    ok = await db.delete_group(group_id, user_id)
    if not ok:
        return web.json_response({"error": "delete_failed"}, status=500)

    return web.json_response({"ok": True, "deleted_id": group_id})


async def api_my_groups(request: web.Request) -> web.Response:
    init_data = request.headers.get("X-Init-Data", "")
    if not init_data:
        return web.json_response({"error": "no_auth", "items": []}, status=401)

    parsed = _validate_init_data(init_data, config.BOT_TOKEN)
    if not parsed or "user" not in parsed:
        return web.json_response({"error": "invalid_auth", "items": []}, status=401)

    user_id = parsed["user"]["id"]
    items = await db.my_groups(user_id)

    return web.json_response({
        "total": len(items),
        "items": [_serialize(g) for g in items],
    })


def _serialize(g) -> dict:
    keys = g.keys()
    photo = g["photo_url"] if "photo_url" in keys else None
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
        "photo_url": f"/api/photo/{photo}" if photo else None,
    }


def setup_api(app: web.Application):
    app.router.add_get("/api/groups", api_groups)
    app.router.add_get("/api/meta", api_meta)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/photo/{file_id}", api_photo)
    app.router.add_get("/api/my-groups", api_my_groups)
    app.router.add_delete("/api/groups/{group_id}", api_delete_group)
