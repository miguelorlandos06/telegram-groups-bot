from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot import db, config
from bot.keyboards import search_results_kb, filters_kb, filter_choice_kb, main_menu
from bot.states import SearchStates

router = Router()
SEP = "━━━━━━━━━━━━━━━━━━━━"


def _icon_for(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    if tipo == "channel":
        return "🔞📢" if g["is_adult"] else "📢"
    return "🔞" if g["is_adult"] else "📌"


def _format_item(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    icon = _icon_for(g)
    flag = ""
    if g["country"]:
        label = config.COUNTRIES.get(g["country"], "")
        flag = label.split()[0] if label else ""
    cat_icon = ""
    if g["category"]:
        cat_icon = config.CATEGORIES.get(g["category"], "").split()[0]
    members_txt = ""
    if g["members_range"]:
        members_txt = config.MEMBERS_RANGES.get(g["members_range"], "")

    line = f"{icon} <a href='{g['link']}'><b>{g['title']}</b></a> {flag}\n"
    details = []
    if cat_icon:
        details.append(cat_icon)
    if members_txt:
        details.append(f"👥 {members_txt}")
    if details:
        line += f"   <i>{'  ·  '.join(details)}</i>\n"
    return line


def _build_filters_sync(base, show_adult):
    f = dict(base or {})
    if not show_adult:
        f["is_adult"] = False
    min_members = None
    if f.get("members_range"):
        min_members = config.MEMBERS_VALUES.get(f["members_range"])
    f["min_members"] = min_members
    return f


async def _build_filters(user_id, base):
    user = await db.get_user(user_id)
    show_adult = bool(user and user["show_nsfw"])
    return _build_filters_sync(base, show_adult)


def _build_header(query, total, page, total_pages):
    return (
        f"╔════════════════════════╗\n"
        f"   🔍 RESULTADOS\n"
        f"╚════════════════════════╝\n\n"
        f"🔎 <b>Búsqueda:</b> {query}\n"
        f"📊 <b>Total:</b> {total}  ·  📄 <b>Pág:</b> {page+1}/{total_pages}\n\n"
        f"{SEP}\n\n"
    )


@router.message(Command("buscar"))
async def cmd_search(message: Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        await _run_search(message, parts[1], state, message.from_user.id)
    else:
        await state.set_state(SearchStates.waiting_query)
        await message.answer(
            "🔍 <b>¿Qué quieres buscar?</b>\n\n"
            "Escribe el nombre, categoría o etiqueta.",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "menu:search")
async def cb_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_query)
    await call.message.edit_text(
        "🔍 <b>¿Qué quieres buscar?</b>\n\n"
        "Escribe el nombre, categoría o etiqueta.",
        parse_mode="HTML"
    )
    await call.answer()


@router.message(SearchStates.waiting_query)
async def on_query(message: Message, state: FSMContext):
    await _run_search(message, message.text or "", state, message.from_user.id)


async def _run_search(message, query, state, user_id):
    data = await state.get_data()
    filters = await _build_filters(user_id, data.get("filters", {}))
    total = await db.count_groups(query=query, filters=filters)
    if total == 0:
        await message.answer(
            f"😕 <b>Sin resultados para:</b> <code>{query}</code>\n\n"
            "Prueba con otra palabra o revisa los filtros.",
            parse_mode="HTML"
        )
        return
    groups = await db.search_groups(query, filters, page=0)
    total_pages = max(1, (total + 9) // 10)

    text = _build_header(query, total, 0, total_pages)
    for g in groups:
        text += _format_item(g) + "\n"
    text = text.rstrip() + f"\n\n{SEP}"

    await state.update_data(
        last_query=query, last_filters=filters,
        last_page=0, last_total_pages=total_pages
    )
    await message.answer(
        text,
        reply_markup=search_results_kb(groups, 0, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )


async def show_browse(call, category, page=0):
    filters = await _build_filters(call.from_user.id, {})
    if category == "adult":
        user = await db.get_user(call.from_user.id)
        if not (user and user["show_nsfw"]):
            await call.answer("🔞 Activa el modo +18 primero.", show_alert=True)
            return
        filters["is_adult"] = True
    total = await db.count_groups(filters=filters, category=category)
    if total == 0:
        await call.message.edit_text(
            "😕 <b>No hay publicaciones en esta categoría</b>",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
        await call.answer()
        return
    groups = await db.browse_category(category, filters, page=page)
    total_pages = max(1, (total + 9) // 10)

    cat_label = config.CATEGORIES.get(category, category)
    header = (
        f"╔════════════════════════╗\n"
        f"   {cat_label}\n"
        f"╚════════════════════════╝\n\n"
        f"📊 <b>Total:</b> {total}  ·  📄 <b>Pág:</b> {page+1}/{total_pages}\n\n"
        f"{SEP}\n\n"
    )
    text = header
    for g in groups:
        text += _format_item(g) + "\n"
    text = text.rstrip() + f"\n\n{SEP}"

    await call.message.edit_text(
        text,
        reply_markup=search_results_kb(groups, page, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("page:"))
async def cb_page(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    query = data.get("last_query")
    if not query:
        await call.answer("Primero busca algo.", show_alert=True)
        return
    page = int(call.data.split(":")[1])
    filters = data.get("last_filters", {})
    groups = await db.search_groups(query, filters, page=page)
    total_pages = data.get("last_total_pages", 1)

    text = _build_header(query, "—", page, total_pages)
    for g in groups:
        text += _format_item(g) + "\n"
    text = text.rstrip() + f"\n\n{SEP}"

    await state.update_data(last_page=page)
    await call.message.edit_text(
        text,
        reply_markup=search_results_kb(groups, page, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data == "filters:open")
async def cb_filters_open(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.message.edit_reply_markup(
        reply_markup=filters_kb(data.get("last_filters", {}))
    )
    await call.answer()


@router.callback_query(F.data == "filter:back")
async def cb_filter_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    query = data.get("last_query")
    if not query:
        await call.message.edit_text("🏠 <b>Menú principal</b>",
                                      reply_markup=main_menu(), parse_mode="HTML")
        await call.answer()
        return
    page = data.get("last_page", 0)
    filters = data.get("last_filters", {})
    groups = await db.search_groups(query, filters, page=page)
    total_pages = data.get("last_total_pages", 1)
    text = _build_header(query, "—", page, total_pages)
    for g in groups:
        text += _format_item(g) + "\n"
    text = text.rstrip() + f"\n\n{SEP}"
    await call.message.edit_text(
        text,
        reply_markup=search_results_kb(groups, page, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "filter:clear")
async def cb_filter_clear(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    f = dict(data.get("last_filters", {}))
    for k in ("country", "language", "category", "members_range", "type"):
        f.pop(k, None)
    await state.update_data(last_filters=f)
    await call.message.edit_reply_markup(reply_markup=filters_kb(f))
    await call.answer("🔄 Filtros limpiados")


@router.callback_query(F.data == "filter:apply")
async def cb_filter_apply(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    query = data.get("last_query")
    if not query:
        await call.answer("Busca algo primero.", show_alert=True)
        return
    f = dict(data.get("last_filters", {}))
    min_members = config.MEMBERS_VALUES.get(f["members_range"]) if f.get("members_range") else None
    f["min_members"] = min_members
    total = await db.count_groups(query=query, filters=f)
    total_pages = max(1, (total + 9) // 10)
    groups = await db.search_groups(query, f, page=0)
    text = _build_header(query, total, 0, total_pages)
    for g in groups:
        text += _format_item(g) + "\n"
    text = text.rstrip() + f"\n\n{SEP}"
    await state.update_data(last_filters=f, last_page=0, last_total_pages=total_pages)
    await call.message.edit_text(
        text,
        reply_markup=search_results_kb(groups, 0, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "filter:adult")
async def cb_filter_adult(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    f = dict(data.get("last_filters", {}))
    f["is_adult"] = not f.get("is_adult", False)
    await state.update_data(last_filters=f)
    await call.message.edit_reply_markup(reply_markup=filters_kb(f))
    await call.answer()


@router.callback_query(F.data.startswith("filter:"))
async def cb_filter_choice(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[1]
    if kind in ("open", "apply", "clear", "back", "adult"):
        return
    data = await state.get_data()
    f = data.get("last_filters", {})
    key_map = {"country": "country", "lang": "language", "cat": "category",
               "members": "members_range", "type": "type"}
    current = f.get(key_map.get(kind))
    await call.message.edit_reply_markup(reply_markup=filter_choice_kb(kind, current))
    await call.answer()


@router.callback_query(F.data.startswith("fset:"))
async def cb_filter_set(call: CallbackQuery, state: FSMContext):
    _, kind, val = call.data.split(":")
    data = await state.get_data()
    f = dict(data.get("last_filters", {}))
    key_map = {"country": "country", "lang": "language", "cat": "category",
               "members": "members_range", "type": "type"}
    key = key_map[kind]
    if val == "none":
        f.pop(key, None)
    else:
        f[key] = val
    await state.update_data(last_filters=f)
    await call.message.edit_reply_markup(reply_markup=filters_kb(f))
    await call.answer()
