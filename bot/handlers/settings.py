from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot import db

router = Router()


def _settings_kb(show_nsfw):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔞 Mostrar +18: {'✅ Activado' if show_nsfw else '❌ Desactivado'}",
            callback_data="settings:toggle_nsfw"
        )],
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:main")],
    ])


@router.callback_query(F.data == "menu:settings")
async def cb_settings(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    show_nsfw = bool(user and user["show_nsfw"])

    text = (
        f"╔════════════════════════╗\n"
        f"   ⚙️ AJUSTES\n"
        f"╚════════════════════════╝\n\n"
        f"Personaliza tu experiencia:\n\n"
        f"🔞 <b>Modo +18:</b> {'✅ Activado' if show_nsfw else '❌ Desactivado'}\n"
        f"<i>Actívalo para ver grupos y canales para adultos</i>"
    )
    await call.message.edit_text(text, reply_markup=_settings_kb(show_nsfw),
                                  parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "settings:toggle_nsfw")
async def cb_toggle_nsfw(call: CallbackQuery):
    new_value = await db.toggle_nsfw(call.from_user.id)

    text = (
        f"╔════════════════════════╗\n"
        f"   ⚙️ AJUSTES\n"
        f"╚════════════════════════╝\n\n"
        f"Personaliza tu experiencia:\n\n"
        f"🔞 <b>Modo +18:</b> {'✅ Activado' if new_value else '❌ Desactivado'}\n"
        f"<i>Actívalo para ver grupos y canales para adultos</i>"
    )
    await call.message.edit_text(text, reply_markup=_settings_kb(new_value),
                                  parse_mode="HTML")
    await call.answer("✅ Activado" if new_value else "❌ Desactivado")
