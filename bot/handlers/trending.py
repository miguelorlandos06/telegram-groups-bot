from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot import db
from bot.keyboards import trending_kb, main_menu

router = Router()


@router.callback_query(F.data == "menu:trending")
async def cb_trending(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    show_adult = bool(user and user["show_nsfw"])
    filters = {} if show_adult else {"is_adult": False}
    groups = await db.get_top_groups(limit=10, filters=filters)
    if not groups:
        await call.message.edit_text("🔥 No hay publicaciones todavía.", reply_markup=main_menu())
        await call.answer()
        return
    text = "🔥 <b>Top 10 más vistos</b>\n\n"
    for i, g in enumerate(groups, 1):
        tipo = g["type"] if "type" in g.keys() else "group"
        icon = ("🔞📢" if g["is_adult"] else "📢") if tipo == "channel" else ("🔞" if g["is_adult"] else "📌")
        text += f"{i}. {icon} <a href='{g['link']}'>{g['title']}</a> — 👁️ {g['views']}\n"
    await call.message.edit_text(text, reply_markup=trending_kb(groups),
                                  disable_web_page_preview=True)
    await call.answer()
