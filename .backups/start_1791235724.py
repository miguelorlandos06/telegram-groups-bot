from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot import db
from bot.keyboards import main_menu, categories_kb

router = Router()
SEP = "━━━━━━━━━━━━━━━━━━━━"


def _icon_for(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    if tipo == "channel":
        return "🔞📢" if g["is_adult"] else "📢"
    return "🔞" if g["is_adult"] else "📌"


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.upsert_user(message.from_user.id, message.from_user.username)

    text = (
        f"╔════════════════════════╗\n"
        f"   🤖 DIRECTORIO TELEGRAM\n"
        f"╚════════════════════════╝\n\n"
        f"👋 ¡Hola <b>{message.from_user.first_name}</b>!\n\n"
        f"Bienvenido al directorio de grupos y canales.\n"
        f"Encuentra comunidades o publica la tuya gratis.\n\n"
        f"{SEP}\n\n"
        f"📚 <b>¿Qué puedes hacer?</b>\n"
        f"  • 🔍 Buscar por nombre, categoría o país\n"
        f"  • 👥 Ver todos los grupos\n"
        f"  • 📢 Ver todos los canales\n"
        f"  • ➕ Publicar el tuyo\n"
        f"  • 🔥 Ver los más populares\n\n"
        f"{SEP}"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 <b>Menú principal</b>",
                         reply_markup=main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "menu:main")
async def cb_main(call: CallbackQuery):
    text = (
        f"╔════════════════════════╗\n"
        f"   🏠 MENÚ PRINCIPAL\n"
        f"╚════════════════════════╝\n\n"
        f"Elige una opción:"
    )
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "menu:cats")
async def cb_cats(call: CallbackQuery):
    text = (
        f"╔════════════════════════╗\n"
        f"   📂 CATEGORÍAS\n"
        f"╚════════════════════════╝\n\n"
        f"Elige una categoría:"
    )
    await call.message.edit_text(text, reply_markup=categories_kb("browse"), parse_mode="HTML")
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
        text = (
            "😕 <b>Aún no has publicado nada</b>\n\n"
            "Pulsa ➕ en el menú para añadir tu primer grupo o canal."
        )
        if edit:
            await message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")
            await call.answer()
        else:
            await message.answer(text, parse_mode="HTML")
        return

    header = (
        f"╔════════════════════════╗\n"
        f"   ⭐ TUS PUBLICACIONES\n"
        f"╚════════════════════════╝\n\n"
        f"📊 <b>Total:</b> {len(groups)}\n\n"
        f"{SEP}\n\n"
    )
    body = ""
    for g in groups:
        icon = _icon_for(g)
        flag = ""
        if g["country"]:
            from bot import config
            label = config.COUNTRIES.get(g["country"], "")
            flag = label.split()[0] if label else ""
        body += f"{icon} <a href='{g['link']}'><b>{g['title']}</b></a> {flag}\n"
    text = header + body.rstrip() + f"\n\n{SEP}"

    if edit:
        await message.edit_text(text, disable_web_page_preview=True,
                                 reply_markup=main_menu(), parse_mode="HTML")
        await call.answer()
    else:
        await message.answer(text, disable_web_page_preview=True, parse_mode="HTML")


@router.message(Command("todos"))
async def cmd_all(message: Message):
    from bot.keyboards import all_groups_order_kb
    text = (
        f"╔════════════════════════╗\n"
        f"   📚 TODOS\n"
        f"╚════════════════════════╝\n\n"
        f"¿Cómo quieres ordenarlos?"
    )
    await message.answer(text, reply_markup=all_groups_order_kb(), parse_mode="HTML")


@router.message(Command("tendencias"))
async def cmd_trending(message: Message):
    from bot.keyboards import trending_kb
    from bot import config
    user = await db.get_user(message.from_user.id)
    show_adult = bool(user and user["show_nsfw"])
    filters = {} if show_adult else {"is_adult": False}
    groups = await db.get_top_groups(limit=10, filters=filters)
    if not groups:
        await message.answer("🔥 <b>No hay publicaciones todavía.</b>",
                              reply_markup=main_menu(), parse_mode="HTML")
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

    await message.answer(text, reply_markup=trending_kb(groups),
                         disable_web_page_preview=True, parse_mode="HTML")
