from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot import db
from bot.keyboards import main_menu, categories_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 ¡Hola {message.from_user.first_name}!\n\n"
        "Bienvenido al directorio de grupos y canales de Telegram.",
        reply_markup=main_menu()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 Menú principal", reply_markup=main_menu())


@router.callback_query(F.data == "menu:main")
async def cb_main(call: CallbackQuery):
    await call.message.edit_text("🏠 Menú principal", reply_markup=main_menu())
    await call.answer()


@router.callback_query(F.data == "menu:cats")
async def cb_cats(call: CallbackQuery):
    await call.message.edit_text("📂 Elige una categoría:", reply_markup=categories_kb("browse"))
    await call.answer()


@router.callback_query(F.data.startswith("browse:"))
async def cb_browse(call: CallbackQuery):
    from bot.handlers.search import show_browse
    cat = call.data.split(":")[1]
    await show_browse(call, cat, page=0)


@router.message(Command("misgrupos"))
async def cmd_mine(message: Message):
    await _show_mine(message.from_user.id, message)


@router.callback_query(F.data == "menu:mine")
async def cb_mine(call: CallbackQuery):
    await _show_mine(call.from_user.id, call.message, edit=True, call=call)


async def _show_mine(user_id, message, edit=False, call=None):
    groups = await db.my_groups(user_id)
    if not groups:
        text = "😕 Aún no has publicado nada."
        if edit:
            await message.edit_text(text, reply_markup=main_menu())
            await call.answer()
        else:
            await message.answer(text)
        return

    text = "⭐ <b>Tus publicaciones:</b>\n\n"
    for g in groups:
        tipo = g["type"] if "type" in g.keys() else "group"
        icon = ("🔞📢" if g["is_adult"] else "📢") if tipo == "channel" else ("🔞" if g["is_adult"] else "📌")
        text += f"{icon} <a href='{g['link']}'>{g['title']}</a>\n"

    if edit:
        await message.edit_text(text, disable_web_page_preview=True, reply_markup=main_menu())
        await call.answer()
    else:
        await message.answer(text, disable_web_page_preview=True)


@router.message(Command("todos"))
async def cmd_all(message: Message):
    from bot.keyboards import all_groups_order_kb
    await message.answer("📚 <b>Todos</b>\n\n¿Cómo quieres ordenarlos?",
                         reply_markup=all_groups_order_kb())


@router.message(Command("tendencias"))
async def cmd_trending(message: Message):
    from bot.keyboards import trending_kb
    user = await db.get_user(message.from_user.id)
    show_adult = bool(user and user["show_nsfw"])
    filters = {} if show_adult else {"is_adult": False}
    groups = await db.get_top_groups(limit=10, filters=filters)
    if not groups:
        await message.answer("🔥 No hay publicaciones todavía.", reply_markup=main_menu())
        return
    text = "🔥 <b>Top 10 más vistos</b>\n\n"
    for i, g in enumerate(groups, 1):
        tipo = g["type"] if "type" in g.keys() else "group"
        icon = ("🔞📢" if g["is_adult"] else "📢") if tipo == "channel" else ("🔞" if g["is_adult"] else "📌")
        text += f"{i}. {icon} <a href='{g['link']}'>{g['title']}</a> — 👁️ {g['views']}\n"
    await message.answer(text, reply_markup=trending_kb(groups), disable_web_page_preview=True)
