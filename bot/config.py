# ============================================
# CONFIGURACIÓN - EDITA AQUÍ
# ============================================

BOT_TOKEN = "TU_TOKEN_AQUI"
WEBHOOK_URL = "https://TU-APP.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "cambia_esto_123"
PORT = 10000
DATABASE_URL = "postgresql://usuario:password@host:5432/dbname"
ADMIN_ID = 0

CATEGORIES = {
    "tech":    "💻 Tecnología",
    "gaming":  "🎮 Gaming",
    "edu":     "📚 Educación",
    "biz":     "💰 Negocios",
    "art":     "🎨 Arte",
    "music":   "🎵 Música",
    "lang":    "🌍 Idiomas",
    "adult":   "🔞 Adultos",
}

COUNTRIES = {
    "CU":   "🇨🇺 Cuba",
    "MX":   "🇲🇽 México",
    "AR":   "🇦🇷 Argentina",
    "CO":   "🇨🇴 Colombia",
    "CL":   "🇨🇱 Chile",
    "PE":   "🇵🇪 Perú",
    "VE":   "🇻🇪 Venezuela",
    "ES":   "🇪🇸 España",
    "US":   "🇺🇸 USA",
    "OTRO": "🌐 Otro",
}

LANGUAGES = {
    "es": "🇪🇸 Español",
    "en": "🇬🇧 English",
    "pt": "🇧🇷 Português",
}

MEMBERS_RANGES = {
    "<100":   "< 100",
    "100-1k": "100 – 1k",
    "1k-10k": "1k – 10k",
    "10k+":   "+ 10k",
}

MEMBERS_VALUES = {
    "<100":   0,
    "100-1k": 100,
    "1k-10k": 1000,
    "10k+":   10000,
}
