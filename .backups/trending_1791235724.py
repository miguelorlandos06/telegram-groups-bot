from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot import db, config
from bot.keyboards import trending_kb, main_menu

router = Router()
SEP = "━━━━━━━━━━━━━━━━━━━━"


def _icon_for(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    if tipo == "channel":
        return "🔞📢" if g["is_adult"] else "📢"
    return "🔞" if g["is_adult"] else "📌"


@router.callback_query(F.data == "menu:trending")
async def cb_trending(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    show_adult = bool(user and user["show_nsfw"])
    filters = {} if show_adult else {"is_adult": False}
    groups = await db.get_top_groups(limit=10, filters=filters)
    if not groups:
        await call.message.edit_text(
            "🔥 <b>No hay publicaciones todavía.</b>",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
        await call.answer()
        return

    text = (
        f"╔════════════════════════╗\n"
        f"   🔥 TOP 10 TENDENCIAS\n"
        f"╚════════════════════════╝\n\n"
        f"{SEP}\n\n"
    )
    for i, g in enumerate(groups, 1):
        icon = _icon_for(g)
        flag = ""
        if g["country"]:
            label = config.COUNTRIES.get(g["country"], "")
            flag = label.split()[0] if label else ""
        text += f"<b>{i}.</b> {icon} <a href='{g['link']}'>{g['title']}</a> {flag}\n"
        text += f"   <i>👁️ {g['views']} vistas</i>\n\n"
    text = text.rstrip() + f"\n\n{SEP}"

    await call.message.edit_text(
        text,
        reply_markup=trending_kb(groups),
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
    await call.answer()
