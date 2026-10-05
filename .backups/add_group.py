from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot import db, config
from bot.keyboards import (type_kb, categories_kb, countries_kb, languages_kb,
                            members_kb, adult_kb, confirm_kb, main_menu)
from bot.states import AddItemStates

router = Router()


@router.message(Command("publicar"))
async def cmd_add(message: Message, state: FSMContext):
    await db.upsert_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await state.set_state(AddItemStates.choosing_type)
    await message.answer("📌 ¿Qué quieres publicar?", reply_markup=type_kb())


@router.callback_query(F.data == "menu:add")
async def cb_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddItemStates.choosing_type)
    await call.message.edit_text("📌 ¿Qué quieres publicar?", reply_markup=type_kb())
    await call.answer()


@router.callback_query(AddItemStates.choosing_type, F.data.startswith("pick_type:"))
async def step_type(call: CallbackQuery, state: FSMContext):
    tipo = call.data.split(":")[1]
    await state.update_data(type=tipo)
    await state.set_state(AddItemStates.link)
    label = "grupo" if tipo == "group" else "canal"
    await call.message.edit_text(f"📎 Envíame el enlace del {label}.\nEj: https://t.me/mi{label}")
    await call.answer()


@router.message(AddItemStates.link)
async def step_link(message: Message, state: FSMContext):
    link = (message.text or "").strip()
    if link.startswith("@"):
        link = f"https://t.me/{link[1:]}"
    if not link.startswith("https://t.me/"):
        await message.answer("❌ Enlace inválido.")
        return
    if await db.group_exists(link):
        await message.answer("❌ Ya está registrado.")
        return
    await state.update_data(link=link)
    await state.set_state(AddItemStates.title)
    await message.answer("✏️ Envíame el título (3-60 caracteres).")


@router.message(AddItemStates.title)
async def step_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not (3 <= len(title) <= 60):
        await message.answer("❌ Debe tener entre 3 y 60 caracteres.")
        return
    await state.update_data(title=title)
    await state.set_state(AddItemStates.description)
    await message.answer("📝 Envíame una descripción (hasta 300 caracteres).")


@router.message(AddItemStates.description)
async def step_desc(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    if len(desc) > 300:
        await message.answer("❌ Máximo 300 caracteres.")
        return
    await state.update_data(description=desc)
    await state.set_state(AddItemStates.category)
    await message.answer("📂 Elige la categoría:", reply_markup=categories_kb("pick_cat"))


@router.callback_query(AddItemStates.category, F.data.startswith("pick_cat:"))
async def step_cat(call: CallbackQuery, state: FSMContext):
    cat = call.data.split(":")[1]
    await state.update_data(category=cat)
    await state.set_state(AddItemStates.country)
    await call.message.edit_text("🌍 ¿De qué país es?", reply_markup=countries_kb("pick_country"))
    await call.answer()


@router.callback_query(AddItemStates.country, F.data.startswith("pick_country:"))
async def step_country(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    country = None if val == "skip" else val
    await state.update_data(country=country)
    await state.set_state(AddItemStates.language)
    await call.message.edit_text("🗣️ ¿Idioma principal?", reply_markup=languages_kb("pick_lang"))
    await call.answer()


@router.callback_query(AddItemStates.language, F.data.startswith("pick_lang:"))
async def step_lang(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    lang = None if val == "skip" else val
    await state.update_data(language=lang)
    await state.set_state(AddItemStates.members)
    await call.message.edit_text("👥 ¿Cuántos miembros aprox.?", reply_markup=members_kb("pick_members"))
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
    await call.message.edit_text("🏷️ Etiquetas separadas por coma.\nO escribe /skip para saltar.")
    await call.answer()


@router.message(AddItemStates.tags, Command("skip"))
async def step_tags_skip(message: Message, state: FSMContext):
    await state.update_data(tags=None)
    await state.set_state(AddItemStates.adult)
    await message.answer("🔞 ¿Es contenido +18?", reply_markup=adult_kb())


@router.message(AddItemStates.tags)
async def step_tags(message: Message, state: FSMContext):
    tags = (message.text or "").strip()
    if len(tags) > 100:
        await message.answer("❌ Máximo 100 caracteres.")
        return
    await state.update_data(tags=tags)
    await state.set_state(AddItemStates.adult)
    await message.answer("🔞 ¿Es contenido +18?", reply_markup=adult_kb())


@router.callback_query(AddItemStates.adult, F.data.startswith("adult:"))
async def step_adult(call: CallbackQuery, state: FSMContext):
    is_adult = call.data.split(":")[1] == "yes"
    await state.update_data(is_adult=is_adult)
    await state.set_state(AddItemStates.confirm)
    data = await state.get_data()
    text = _format_preview(data)
    await call.message.edit_text(text, reply_markup=confirm_kb(), disable_web_page_preview=True)
    await call.answer()


@router.callback_query(AddItemStates.confirm, F.data == "confirm:no")
async def step_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Publicación cancelada.", reply_markup=main_menu())
    await call.answer()


@router.callback_query(AddItemStates.confirm, F.data == "confirm:yes")
async def step_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["owner_id"] = call.from_user.id
    group_id = await db.add_group(data)
    await state.clear()
    tipo = data.get("type", "group")
    label = "Grupo" if tipo == "group" else "Canal"
    await call.message.edit_text(
        f"✅ ¡{label} publicado!\n\n📌 {data['title']}\n🔗 {data['link']}\n🆔 ID: #{group_id}",
        reply_markup=main_menu(), disable_web_page_preview=True
    )
    await call.answer("✅ Publicado")


def _format_preview(data):
    tipo = data.get("type", "group")
    tipo_icon = "📢" if tipo == "channel" else "📌"
    tipo_label = "Canal" if tipo == "channel" else "Grupo"
    icon = "🔞" if data.get("is_adult") else tipo_icon
    country = config.COUNTRIES.get(data.get("country"), "—") if data.get("country") else "—"
    lang = config.LANGUAGES.get(data.get("language"), "—") if data.get("language") else "—"
    cat = config.CATEGORIES.get(data.get("category"), "—")
    members = config.MEMBERS_RANGES.get(data.get("members_range"), "—") if data.get("members_range") else "—"
    tags = data.get("tags") or "—"
    return (f"{icon} <b>Vista previa</b> ({tipo_label})\n\n"
            f"📌 <b>{data['title']}</b>\n📝 {data['description']}\n\n"
            f"📂 {cat}\n🌍 {country}\n🗣️ {lang}\n👥 {members}\n🏷️ {tags}\n🔗 {data['link']}\n\n"
            f"¿Publicar?")
