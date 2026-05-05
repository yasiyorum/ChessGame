"""
Satranç Uygulaması Konfigürasyon Dosyası
Chess.com Kalitesinde Profesyonel Satranç
"""
import os
import sys

# PyInstaller ile paketlendiğinde base path değişir
def get_base_path():
    """Uygulama base path'ini döndür (PyInstaller uyumlu)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş
        return sys._MEIPASS
    else:
        # Normal Python çalıştırma
        return os.path.dirname(__file__)

BASE_PATH = get_base_path()

# Uygulama Ayarları
APP_NAME = "Satranç"
APP_VERSION = "2.0"
WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 850
MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 750

# Stockfish Ayarları
import utils
stockfish_dir = utils.sync_from_github("stockfish")
STOCKFISH_PATH = os.path.join(
    stockfish_dir, 
    "stockfish-windows-x86-64-avx2.exe"
)

# Performans Optimizasyonu
STOCKFISH_THREADS = 4
STOCKFISH_HASH = 64
ANALYSIS_WORKERS = 4

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
TIME_OPTIONS = [1, 2, 3, 5, 10, 15, 30, 45, 60, 90, 120]  # Dakika cinsinden
INCREMENT_OPTIONS = [0, 1, 2, 3, 5, 10, 15, 30, 45, 60, 90, 120]      # Saniye cinsinden

# Tahta Renkleri (varsayılan - tema tarafından override edilebilir)
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
    "best": "#8FB44E",        # Koyu yeşil - En iyi hamle
    "book": "#A88865",        # Kahverengi - Kitap hamlesi
    "good": "#FFFFFF",        # Beyaz - İyi hamle
    "normal": "#B0B0B0",      # Açık gri - Normal hamle
    "inaccuracy": "#F0D151",  # Sarı - Yanlışlık
    "mistake": "#E6912C",     # Turuncu - Hata
    "blunder": "#B33430",     # Kırmızı - Vahim Hata
    "miss": "#FF3B3F",        # Parlak Kırmızı - Kaçırılan Fırsat
}

# Hamle Sembolleri (Chess.com Stili)
MOVE_SYMBOLS = {
    "brilliant": "!!",
    "great": "!",
    "best": "★",
    "book": "📖",
    "good": "✓",
    "normal": "",
    "inaccuracy": "?!",
    "mistake": "?",
    "blunder": "??",
    "miss": "X",
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

# GUI Tema Renkleri (Chess.com Dark Theme)
THEME = {
    "bg_primary": "#302E2B",
    "bg_secondary": "#272522",
    "bg_tertiary": "#1E1D1B",
    "bg_elevated": "#3C3A38",
    "text_primary": "#FFFFFF",
    "text_secondary": "#9E9B98",
    "text_muted": "#6B6966",
    "accent": "#81B64C",
    "accent_hover": "#95CA5D",
    "accent_dark": "#629132",
    "danger": "#E84545",
    "danger_hover": "#C83030",
    "warning": "#F7C631",
    "success": "#81B64C",
    "button_bg": "#454341",
    "button_hover": "#555351",
    "button_active": "#656361",
    "panel_bg": "#262421",
    "panel_border": "#3A3835",
    "divider": "#3A3835",
    "timer_active_bg": "#454341",
    "timer_inactive_bg": "#262421",
    "timer_active_text": "#FFFFFF",
    "timer_warning": "#E84545",
    "move_list_bg": "#262421",
    "move_list_hover": "#3A3835",
    "move_list_selected": "#4A4745",
    "eval_white": "#FFFFFF",
    "eval_black": "#403D39",
    "eval_advantage": "#81B64C",
}

# Unicode Satranç Taşları (fallback)
PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

# Taş İsimleri (Türkçe)
PIECE_NAMES_TR = {
    'K': 'Şah', 'Q': 'Vezir', 'R': 'Kale', 'B': 'Fil', 'N': 'At', 'P': 'Piyon',
    'k': 'Şah', 'q': 'Vezir', 'r': 'Kale', 'b': 'Fil', 'n': 'At', 'p': 'Piyon'
}

# Taş Değerleri (materyal hesabı için)
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
    'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0
}
