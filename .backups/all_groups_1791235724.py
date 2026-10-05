from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot import db, config
from bot.keyboards import all_groups_order_kb, all_groups_results_kb, main_menu

router = Router()
PER_PAGE = 20
SEP = "━━━━━━━━━━━━━━━━━━━━"


def _type_label(t):
    return {
        "group":   "👥 GRUPOS DE TELEGRAM",
        "channel": "📢 CANALES DE TELEGRAM",
        "all":     "📚 TODOS",
    }.get(t, "📚 TODOS")


def _icon_for(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    if tipo == "channel":
        return "🔞📢" if g["is_adult"] else "📢"
    return "🔞" if g["is_adult"] else "📌"


def _type_short(tipo):
    return "📢" if tipo == "channel" else "📌"


def _format_item(g):
    """Formato visual de un grupo/canal."""
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

    # Primera línea con título
    line = f"{icon} <a href='{g['link']}'><b>{g['title']}</b></a> {flag}\n"

    # Segunda línea con detalles
    details = []
    if cat_icon:
        details.append(cat_icon)
    if members_txt:
        details.append(f"👥 {members_txt}")
    if g["views"]:
        details.append(f"👁️ {g['views']}")

    if details:
        line += f"   <i>{'  ·  '.join(details)}</i>\n"

    return line


async def _build_filters(user_id):
    user = await db.get_user(user_id)
    show_adult = bool(user and user["show_nsfw"])
    filters = {}
    if not show_adult:
        filters["is_adult"] = False
    return filters


async def _show_list(call, state, group_type, order, page=0):
    filters = await _build_filters(call.from_user.id)
    total = await db.count_by_type(group_type, filters)

    if total == 0:
        await call.message.edit_text(
            f"📭 <b>No hay {_type_label(group_type).lower()}</b>\n\n"
            "Vuelve más tarde o añade tú el primero con ➕",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
        await call.answer()
        return

    groups = await db.list_by_type(group_type, order, filters, page=page, per_page=PER_PAGE)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    order_label = {
        "asc": "A-Z", "desc": "Z-A",
        "members": "Más miembros",
        "recent": "Recientes",
        "views": "Más vistos",
    }.get(order, "A-Z")

    # Cabecera
    header = (
        f"╔════════════════════════╗\n"
        f"   {_type_label(group_type)}\n"
        f"╚════════════════════════╝\n\n"
        f"🔤 <b>Orden:</b> {order_label}\n"
        f"📊 <b>Total:</b> {total}  ·  📄 <b>Pág:</b> {page+1}/{total_pages}\n\n"
        f"{SEP}\n\n"
    )

    # Lista
    body = ""
    for g in groups:
        body += _format_item(g) + "\n"

    text = header + body.rstrip() + f"\n\n{SEP}"

    await state.update_data(
        all_type=group_type, all_order=order,
        all_page=page, all_total_pages=total_pages
    )

    await call.message.edit_text(
        text,
        reply_markup=all_groups_results_kb(groups, page, total_pages),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.in_({"menu:all:group", "menu:all:channel", "menu:all:all"}))
async def cb_menu_all_type(call: CallbackQuery, state: FSMContext):
    group_type = call.data.split(":")[2]
    await state.update_data(all_type=group_type)

    text = (
        f"{_type_label(group_type)}\n\n"
        f"¿Cómo quieres ordenarlos?"
    )
    await call.message.edit_text(
        text,
        reply_markup=all_groups_order_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("all:order:"))
async def cb_order(call: CallbackQuery, state: FSMContext):
    order = call.data.split(":")[2]
    data = await state.get_data()
    await _show_list(call, state, data.get("all_type", "all"), order, page=0)


@router.callback_query(F.data.startswith("all:page:"))
async def cb_page(call: CallbackQuery, state: FSMContext):
    page = int(call.data.split(":")[2])
    data = await state.get_data()
    await _show_list(call, state, data.get("all_type", "all"),
                     data.get("all_order", "asc"), page=page)


@router.callback_query(F.data == "all:change_order")
async def cb_change_order(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_type = data.get("all_type", "all")
    text = f"{_type_label(group_type)}\n\n¿Cómo quieres ordenarlos?"
    await call.message.edit_text(text, reply_markup=all_groups_order_kb(), parse_mode="HTML")
    await call.answer()
