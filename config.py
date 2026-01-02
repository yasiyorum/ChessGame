"""
Satranç Uygulaması Konfigürasyon Dosyası
"""
import os

# Uygulama Ayarları
APP_NAME = "Satranç"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# Stockfish Ayarları
STOCKFISH_PATH = os.path.join(
    os.path.dirname(__file__), 
    "stockfish", 
    "stockfish-windows-x86-64-avx2.exe"
)

# Performans Optimizasyonu
STOCKFISH_THREADS = 1  # Tek çekirdek kullanarak CPU yükünü azalt
STOCKFISH_HASH = 64    # MB cinsinden hash tablosu boyutu

# ELO Ayarları
MIN_ELO = 100
MAX_ELO = 3200
DEFAULT_ELO = 1200

# ELO -> Skill Level (0-20) dönüşüm tablosu
# Stockfish Skill Level 0-20 arası, ELO yaklaşık 800-3200+
def elo_to_skill_level(elo: int) -> int:
    """ELO değerini Stockfish Skill Level'a çevirir"""
    if elo < 800:
        return max(0, (elo - 100) // 70)
    else:
        return min(20, 10 + (elo - 800) // 120)

def elo_to_think_time(elo: int) -> int:
    """ELO değerine göre düşünme süresini milisaniye cinsinden döndürür"""
    if elo < 600:
        return 50
    elif elo < 1000:
        return 100
    elif elo < 1500:
        return 200
    elif elo < 2000:
        return 400
    elif elo < 2500:
        return 700
    else:
        return 1000

# Zaman Kontrolü Varsayılanları
DEFAULT_TIME_MINUTES = 5
DEFAULT_INCREMENT_SECONDS = 0
TIME_OPTIONS = [1, 2, 3, 5, 10, 15, 30, 60]  # Dakika cinsinden
INCREMENT_OPTIONS = [0, 1, 2, 3, 5, 10]      # Saniye cinsinden

# Tahta Renkleri
BOARD_LIGHT_COLOR = "#EEEED2"
BOARD_DARK_COLOR = "#769656"
BOARD_HIGHLIGHT_COLOR = "#BACA44"
BOARD_SELECTED_COLOR = "#F6F669"
BOARD_LAST_MOVE_COLOR = "#CDD26A"
BOARD_HINT_COLOR = "#5DAD5D"
BOARD_CHECK_COLOR = "#E84545"

# Hamle Değerlendirme Renkleri (Chess.com Stili)
MOVE_COLORS = {
    "brilliant": "#1BACA6",   # Camgöbeği - Efsane hamle
    "great": "#5C8BB0",       # Mavi - Harika hamle
    "best": "#96BC4B",        # Yeşil - En iyi hamle
    "good": "#96BC4B",        # Yeşil - İyi hamle
    "book": "#A88865",        # Kahverengi - Kitap hamlesi
    "normal": "#D0D0D0",      # Gri - Normal hamle
    "inaccuracy": "#F7C631",  # Sarı - Hatasız (küçük hata)
    "mistake": "#FFA459",     # Turuncu - Hata
    "blunder": "#CA3431",     # Kırmızı - Vahim hata
    "miss": "#DBAC16",        # Altın - Kaçırılan fırsat
}

# Hamle Sembolleri (Chess.com Stili)
MOVE_SYMBOLS = {
    "brilliant": "!!",
    "great": "!",
    "best": "",
    "good": "",
    "book": "",
    "normal": "",
    "inaccuracy": "?!",
    "mistake": "?",
    "blunder": "??",
    "miss": "",
}

# Değerlendirme Eşikleri (centipawn cinsinden)
EVAL_THRESHOLDS = {
    "brilliant_threshold": 0,      # En iyi hamle ve zor pozisyon
    "great_threshold": 10,         # 0-10 cp kayıp
    "good_threshold": 25,          # 10-25 cp kayıp
    "normal_threshold": 50,        # 25-50 cp kayıp
    "inaccuracy_threshold": 100,   # 50-100 cp kayıp
    "mistake_threshold": 200,      # 100-200 cp kayıp
    "blunder_threshold": 300,      # 200+ cp kayıp
}

# GUI Tema Renkleri
THEME = {
    "bg_primary": "#312E2B",
    "bg_secondary": "#272522",
    "bg_tertiary": "#21201D",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "accent": "#81B64C",
    "accent_hover": "#9BCF5C",
    "danger": "#E84545",
    "warning": "#F7C631",
    "button_bg": "#454341",
    "button_hover": "#555351",
    "panel_bg": "#262421",
}

# Unicode Satranç Taşları
PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

# Taş İsimleri (Türkçe)
PIECE_NAMES_TR = {
    'K': 'Şah', 'Q': 'Vezir', 'R': 'Kale', 'B': 'Fil', 'N': 'At', 'P': 'Piyon',
    'k': 'Şah', 'q': 'Vezir', 'r': 'Kale', 'b': 'Fil', 'n': 'At', 'p': 'Piyon'
}
