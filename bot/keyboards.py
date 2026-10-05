from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot import config


def _icon_for(g):
    tipo = g["type"] if "type" in g.keys() else "group"
    if tipo == "channel":
        return "🔞📢" if g["is_adult"] else "📢"
    return "🔞" if g["is_adult"] else "📌"


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Buscar", callback_data="menu:search")],
        [InlineKeyboardButton(
            text="🌐 Abrir App",
            web_app=WebAppInfo(url=f"{config.WEBHOOK_URL}/app")
        )],
        [InlineKeyboardButton(text="👥 Grupos", callback_data="menu:all:group"),
         InlineKeyboardButton(text="📢 Canales", callback_data="menu:all:channel")],
        [InlineKeyboardButton(text="📚 Todos", callback_data="menu:all:all")],
        [InlineKeyboardButton(text="➕ Agregar", callback_data="menu:add")],
        [InlineKeyboardButton(text="📂 Categorías", callback_data="menu:cats")],
        [InlineKeyboardButton(text="🔥 Tendencias", callback_data="menu:trending")],
        [InlineKeyboardButton(text="⭐ Mis Publicaciones", callback_data="menu:mine")],
        [InlineKeyboardButton(text="⚙️ Ajustes", callback_data="menu:settings")],
    ])


def type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Grupo", callback_data="pick_type:group"),
         InlineKeyboardButton(text="📢 Canal", callback_data="pick_type:channel")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="menu:main")],
    ])


def categories_kb(prefix="pick_cat"):
    b = InlineKeyboardBuilder()
    for key, label in config.CATEGORIES.items():
        b.button(text=label, callback_data=f"{prefix}:{key}")
    b.adjust(2, 2, 2, 2)
    b.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:main"))
    return b.as_markup()


def countries_kb(prefix="pick_country"):
    b = InlineKeyboardBuilder()
    for code, label in config.COUNTRIES.items():
        b.button(text=label, callback_data=f"{prefix}:{code}")
    b.adjust(2, 2, 2, 2, 2)
    b.row(InlineKeyboardButton(text="⏭️ Saltar", callback_data=f"{prefix}:skip"))
    return b.as_markup()


def languages_kb(prefix="pick_lang"):
    b = InlineKeyboardBuilder()
    for code, label in config.LANGUAGES.items():
        b.button(text=label, callback_data=f"{prefix}:{code}")
    b.adjust(3)
    b.row(InlineKeyboardButton(text="⏭️ Saltar", callback_data=f"{prefix}:skip"))
    return b.as_markup()


def members_kb(prefix="pick_members"):
    b = InlineKeyboardBuilder()
    for key, label in config.MEMBERS_RANGES.items():
        b.button(text=label, callback_data=f"{prefix}:{key}")
    b.adjust(2, 2)
    b.row(InlineKeyboardButton(text="⏭️ Saltar", callback_data=f"{prefix}:skip"))
    return b.as_markup()


def adult_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Sí, es +18", callback_data="adult:yes")],
        [InlineKeyboardButton(text="❌ No", callback_data="adult:no")],
    ])


def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Publicar", callback_data="confirm:yes")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="confirm:no")],
    ])


def search_results_kb(groups, page, total_pages):
    b = InlineKeyboardBuilder()
    for g in groups:
        icon = _icon_for(g)
        flag = ""
        if g["country"]:
            label = config.COUNTRIES.get(g["country"], "")
            flag = label.split()[0] if label else ""
        b.row(InlineKeyboardButton(
            text=f"{icon} {g['title'][:38]} {flag}", url=g["link"]
        ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{max(total_pages,1)}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"page:{page+1}"))
    b.row(*nav)
    b.row(InlineKeyboardButton(text="🔎 Filtros", callback_data="filters:open"))
    b.row(InlineKeyboardButton(text="🏠 Menú", callback_data="menu:main"))
    return b.as_markup()


def filters_kb(f):
    country = config.COUNTRIES.get(f.get("country"), "Todos") if f.get("country") else "Todos"
    language = config.LANGUAGES.get(f.get("language"), "Todos") if f.get("language") else "Todos"
    category = config.CATEGORIES.get(f.get("category"), "Todas") if f.get("category") else "Todas"
    members = config.MEMBERS_RANGES.get(f.get("members_range"), "Todos") if f.get("members_range") else "Todos"
    adult = "🔞 Incluir" if f.get("is_adult") else "🚫 Ocultar"
    tipo = {"group": "👥 Grupos", "channel": "📢 Canales"}.get(f.get("type"), "Todos")

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌍 País: {country}", callback_data="filter:country")],
        [InlineKeyboardButton(text=f"🗣️ Idioma: {language}", callback_data="filter:lang")],
        [InlineKeyboardButton(text=f"📂 Categoría: {category}", callback_data="filter:cat")],
        [InlineKeyboardButton(text=f"👥 Miembros: {members}", callback_data="filter:members")],
        [InlineKeyboardButton(text=f"📌 Tipo: {tipo}", callback_data="filter:type")],
        [InlineKeyboardButton(text=f"🔞 +18: {adult}", callback_data="filter:adult")],
        [InlineKeyboardButton(text="🔄 Limpiar", callback_data="filter:clear"),
         InlineKeyboardButton(text="✅ Aplicar", callback_data="filter:apply")],
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="filter:back")],
    ])


def filter_choice_kb(kind, current=None):
    if kind == "country":
        opts = config.COUNTRIES
    elif kind == "lang":
        opts = config.LANGUAGES
    elif kind == "cat":
        opts = config.CATEGORIES
    elif kind == "members":
        opts = config.MEMBERS_RANGES
    elif kind == "type":
        opts = {"group": "👥 Grupos", "channel": "📢 Canales"}
    else:
        opts = {}

    b = InlineKeyboardBuilder()
    for key, label in opts.items():
        mark = "✅ " if current == key else ""
        b.button(text=f"{mark}{label}", callback_data=f"fset:{kind}:{key}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="🗑️ Quitar", callback_data=f"fset:{kind}:none"))
    b.row(InlineKeyboardButton(text="⬅️ Volver", callback_data="filters:open"))
    return b.as_markup()


def all_groups_order_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 A-Z", callback_data="all:order:asc"),
         InlineKeyboardButton(text="🔤 Z-A", callback_data="all:order:desc")],
        [InlineKeyboardButton(text="👥 Más miembros", callback_data="all:order:members"),
         InlineKeyboardButton(text="📅 Recientes", callback_data="all:order:recent")],
        [InlineKeyboardButton(text="🔥 Más vistos", callback_data="all:order:views")],
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:main")],
    ])


def all_groups_results_kb(groups, page, total_pages):
    b = InlineKeyboardBuilder()
    for g in groups:
        icon = _icon_for(g)
        flag = ""
        if g["country"]:
            label = config.COUNTRIES.get(g["country"], "")
            flag = label.split()[0] if label else ""
        b.row(InlineKeyboardButton(
            text=f"{icon} {g['title'][:36]} {flag}", url=g["link"]
        ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"all:page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{max(total_pages,1)}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"all:page:{page+1}"))
    b.row(*nav)
    b.row(InlineKeyboardButton(text="🔄 Cambiar orden", callback_data="all:change_order"))
    b.row(InlineKeyboardButton(text="🏠 Menú", callback_data="menu:main"))
    return b.as_markup()


def trending_kb(groups):
    b = InlineKeyboardBuilder()
    for g in groups:
        icon = _icon_for(g)
        b.row(InlineKeyboardButton(
            text=f"{icon} {g['title'][:40]} · 👁️ {g['views']}", url=g["link"]
        ))
    b.row(InlineKeyboardButton(text="🏠 Menú", callback_data="menu:main"))
    return b.as_markup()
