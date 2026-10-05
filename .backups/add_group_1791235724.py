from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot import db, config
from bot.keyboards import (type_kb, categories_kb, countries_kb, languages_kb,
                            members_kb, adult_kb, confirm_kb, main_menu)
from bot.states import AddItemStates

router = Router()
SEP = "━━━━━━━━━━━━━━━━━━━━"


@router.message(Command("publicar"))
async def cmd_add(message: Message, state: FSMContext):
    await db.upsert_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await state.set_state(AddItemStates.choosing_type)

    text = (
        f"╔════════════════════════╗\n"
        f"   ➕ NUEVA PUBLICACIÓN\n"
        f"╚════════════════════════╝\n\n"
        f"📌 <b>¿Qué quieres publicar?</b>"
    )
    await message.answer(text, reply_markup=type_kb(), parse_mode="HTML")


@router.callback_query(F.data == "menu:add")
async def cb_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddItemStates.choosing_type)
    text = (
        f"╔════════════════════════╗\n"
        f"   ➕ NUEVA PUBLICACIÓN\n"
        f"╚════════════════════════╝\n\n"
        f"📌 <b>¿Qué quieres publicar?</b>"
    )
    await call.message.edit_text(text, reply_markup=type_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.choosing_type, F.data.startswith("pick_type:"))
async def step_type(call: CallbackQuery, state: FSMContext):
    tipo = call.data.split(":")[1]
    await state.update_data(type=tipo)
    await state.set_state(AddItemStates.link)
    label = "grupo" if tipo == "group" else "canal"
    icon = "👥" if tipo == "group" else "📢"
    text = (
        f"{icon} <b>Nuevo {label}</b>\n\n"
        f"📎 Envíame el enlace del {label}.\n"
        f"<i>Ejemplo: https://t.me/mi{label}</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


@router.message(AddItemStates.link)
async def step_link(message: Message, state: FSMContext):
    link = (message.text or "").strip()
    if link.startswith("@"):
        link = f"https://t.me/{link[1:]}"
    if not link.startswith("https://t.me/"):
        await message.answer("❌ <b>Enlace inválido.</b> Usa https://t.me/xxx o @xxx",
                              parse_mode="HTML")
        return
    if await db.group_exists(link):
        await message.answer("❌ <b>Esa publicación ya está registrada.</b>",
                              parse_mode="HTML")
        return
    await state.update_data(link=link)
    await state.set_state(AddItemStates.title)
    text = (
        f"✏️ <b>Título</b>\n\n"
        f"Envíame el título (3-60 caracteres)."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(AddItemStates.title)
async def step_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not (3 <= len(title) <= 60):
        await message.answer("❌ Debe tener entre 3 y 60 caracteres.", parse_mode="HTML")
        return
    await state.update_data(title=title)
    await state.set_state(AddItemStates.description)
    text = (
        f"📝 <b>Descripción</b>\n\n"
        f"Envíame una descripción (hasta 300 caracteres).\n"
        f"<i>Explica de qué trata tu grupo o canal.</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(AddItemStates.description)
async def step_desc(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    if len(desc) > 300:
        await message.answer("❌ Máximo 300 caracteres.", parse_mode="HTML")
        return
    await state.update_data(description=desc)
    await state.set_state(AddItemStates.category)
    text = (
        f"📂 <b>Categoría</b>\n\n"
        f"Elige la categoría:"
    )
    await message.answer(text, reply_markup=categories_kb("pick_cat"), parse_mode="HTML")


@router.callback_query(AddItemStates.category, F.data.startswith("pick_cat:"))
async def step_cat(call: CallbackQuery, state: FSMContext):
    cat = call.data.split(":")[1]
    await state.update_data(category=cat)
    await state.set_state(AddItemStates.country)
    text = (
        f"🌍 <b>País</b>\n\n"
        f"¿De qué país es?"
    )
    await call.message.edit_text(text, reply_markup=countries_kb("pick_country"),
                                  parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.country, F.data.startswith("pick_country:"))
async def step_country(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    country = None if val == "skip" else val
    await state.update_data(country=country)
    await state.set_state(AddItemStates.language)
    text = (
        f"🗣️ <b>Idioma principal</b>\n\n"
        f"Elige el idioma:"
    )
    await call.message.edit_text(text, reply_markup=languages_kb("pick_lang"),
                                  parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.language, F.data.startswith("pick_lang:"))
async def step_lang(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    lang = None if val == "skip" else val
    await state.update_data(language=lang)
    await state.set_state(AddItemStates.members)
    text = (
        f"👥 <b>Tamaño</b>\n\n"
        f"¿Cuántos miembros aprox.?"
    )
    await call.message.edit_text(text, reply_markup=members_kb("pick_members"),
                                  parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.members, F.data.startswith("pick_members:"))
async def step_members(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    if val == "skip":
        members_range, members_est = None, 0
    else:
        members_range = val
        members_est = config.MEMBERS_VALUES.get(val, 0)
    await state.update_data(members_range=members_range, members_estimate=members_est)
    await state.set_state(AddItemStates.tags)
    text = (
        f"🏷️ <b>Etiquetas</b>\n\n"
        f"Envíamelas separadas por coma.\n"
        f"<i>Ejemplo: python, backend, latam</i>\n\n"
        f"O escribe /skip para saltar."
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


@router.message(AddItemStates.tags, Command("skip"))
async def step_tags_skip(message: Message, state: FSMContext):
    await state.update_data(tags=None)
    await state.set_state(AddItemStates.adult)
    text = (
        f"🔞 <b>Contenido +18</b>\n\n"
        f"¿Es contenido para adultos?"
    )
    await message.answer(text, reply_markup=adult_kb(), parse_mode="HTML")


@router.message(AddItemStates.tags)
async def step_tags(message: Message, state: FSMContext):
    tags = (message.text or "").strip()
    if len(tags) > 100:
        await message.answer("❌ Máximo 100 caracteres.", parse_mode="HTML")
        return
    await state.update_data(tags=tags)
    await state.set_state(AddItemStates.adult)
    text = (
        f"🔞 <b>Contenido +18</b>\n\n"
        f"¿Es contenido para adultos?"
    )
    await message.answer(text, reply_markup=adult_kb(), parse_mode="HTML")


@router.callback_query(AddItemStates.adult, F.data.startswith("adult:"))
async def step_adult(call: CallbackQuery, state: FSMContext):
    is_adult = call.data.split(":")[1] == "yes"
    await state.update_data(is_adult=is_adult)
    await state.set_state(AddItemStates.confirm)
    data = await state.get_data()
    text = _format_preview(data)
    await call.message.edit_text(text, reply_markup=confirm_kb(),
                                  disable_web_page_preview=True, parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.confirm, F.data == "confirm:no")
async def step_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ <b>Publicación cancelada.</b>",
                                  reply_markup=main_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(AddItemStates.confirm, F.data == "confirm:yes")
async def step_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["owner_id"] = call.from_user.id
    group_id = await db.add_group(data)
    await state.clear()

    tipo = data.get("type", "group")
    label = "Grupo" if tipo == "group" else "Canal"
    icon = "👥" if tipo == "group" else "📢"

    text = (
        f"╔════════════════════════╗\n"
        f"   ✅ ¡PUBLICADO!\n"
        f"╚════════════════════════╝\n\n"
        f"{icon} <b>{data['title']}</b>\n"
        f"🔗 {data['link']}\n"
        f"🆔 <code>#{group_id}</code>\n\n"
        f"Tu {label.lower()} ya está disponible en el directorio. 🎉"
    )
    await call.message.edit_text(text, reply_markup=main_menu(),
                                  disable_web_page_preview=True, parse_mode="HTML")
    await call.answer("✅ Publicado")


def _format_preview(data):
    tipo = data.get("type", "group")
    tipo_icon = "📢" if tipo == "channel" else "👥"
    tipo_label = "CANAL" if tipo == "channel" else "GRUPO"
    icon = "🔞" if data.get("is_adult") else tipo_icon
    country = config.COUNTRIES.get(data.get("country"), "—") if data.get("country") else "—"
    lang = config.LANGUAGES.get(data.get("language"), "—") if data.get("language") else "—"
    cat = config.CATEGORIES.get(data.get("category"), "—")
    members = config.MEMBERS_RANGES.get(data.get("members_range"), "—") if data.get("members_range") else "—"
    tags = data.get("tags") or "—"

    return (
        f"╔════════════════════════╗\n"
        f"   👁️ VISTA PREVIA\n"
        f"╚════════════════════════╝\n\n"
        f"{icon} <b>{data['title']}</b>\n"
        f"<i>{tipo_label}</i>\n\n"
        f"📝 {data['description']}\n\n"
        f"{SEP}\n\n"
        f"📂 {cat}\n"
        f"🌍 {country}\n"
        f"🗣️ {lang}\n"
        f"👥 {members}\n"
        f"🏷️ {tags}\n"
        f"🔗 {data['link']}\n\n"
        f"{SEP}\n\n"
        f"¿Todo correcto?"
    )
