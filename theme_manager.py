"""
Tema Yöneticisi - Özelleştirme Sistemi
Taş resimleri, tahta renkleri ve genel görünüm özelleştirmesi
"""
import os
import sys
import json
from typing import Dict, Optional
from PIL import Image, ImageTk
from utils import sync_from_github, get_appdata_dir, get_base_path

def get_settings_path():
    """Ayar dosyası yolu (kullanıcı tercihleri)"""
    return os.path.join(get_appdata_dir(), "settings.json")


class ThemeManager:
    """Tema yönetim sınıfı"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.current_theme_name = "default"
        self.theme_data: Dict = {}
        self.piece_images: Dict[str, Dict[int, ImageTk.PhotoImage]] = {}
        self._raw_images: Dict[str, Image.Image] = {}
        self._custom_themes_dir: Optional[str] = None
        
        # Genel Uygulama Ayarları
        self.settings = {
            "coords_style": "inside",  # inside, outside, off
            "show_eval_bar": True,
            "bot_allow_undo": True,
            "friend_allow_undo": True
        }
        
        # Ayarları yükle (tema klasörü yolu)
        self._load_settings()
        
        # Eğer özel klasör seçilmemişse AppData'daki klasörü kullan
        if not self._custom_themes_dir:
            self._custom_themes_dir = os.path.join(get_appdata_dir(), "themes")
            
        # Varsayılan temayı yükle
        self.load_theme(self.current_theme_name)
    
    def _load_settings(self):
        """Kullanıcı ayarlarını yükle"""
        path = get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._custom_themes_dir = data.get("themes_dir", None)
                self.current_theme_name = data.get("current_theme", "default")
                
                # Ayarları birleştir
                saved_settings = data.get("settings", {})
                for k, v in saved_settings.items():
                    if k in self.settings:
                        self.settings[k] = v
            except:
                pass
    
    def _save_settings(self):
        """Kullanıcı ayarlarını kaydet"""
        path = get_settings_path()
        try:
            data = {
                "themes_dir": self._custom_themes_dir,
                "current_theme": self.current_theme_name,
                "settings": self.settings
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def set_themes_dir(self, path: str):
        """Tema klasörü yolunu ayarla"""
        if path and os.path.isdir(path):
            self._custom_themes_dir = path
            self._save_settings()
            return True
        elif not path:
            self._custom_themes_dir = None
            self._save_settings()
            return True
        return False
    
    def get_themes_dir(self) -> Optional[str]:
        """Mevcut tema klasörü yolunu döndür"""
        return self._custom_themes_dir
    
    def get_available_themes(self):
        """Mevcut temaları listele"""
        themes = set(["default"])
        
        # Özel tema klasörü (Örn: AppData içindeki)
        if self._custom_themes_dir and os.path.isdir(self._custom_themes_dir):
            for name in os.listdir(self._custom_themes_dir):
                theme_path = os.path.join(self._custom_themes_dir, name)
                if os.path.isdir(theme_path) and os.path.exists(os.path.join(theme_path, "theme.json")):
                    themes.add(name)
                    
        # Uygulama içindeki base klasör (varsa)
        base_themes = os.path.join(get_base_path(), "themes")
        if os.path.isdir(base_themes):
            for name in os.listdir(base_themes):
                theme_path = os.path.join(base_themes, name)
                if os.path.isdir(theme_path) and os.path.exists(os.path.join(theme_path, "theme.json")):
                    themes.add(name)
        
        return sorted(list(themes))
    
    def _find_theme_path(self, theme_name: str) -> Optional[str]:
        """Tema klasörünü bul"""
        if theme_name == "default":
            return None  # Default = Unicode, dosya yok
        
        # Özel tema klasöründe ara
        if self._custom_themes_dir and os.path.isdir(self._custom_themes_dir):
            path = os.path.join(self._custom_themes_dir, theme_name)
            if os.path.exists(path) and os.path.exists(os.path.join(path, "theme.json")):
                return path
        
        return None
    
    def load_theme(self, theme_name: str) -> bool:
        """Tema yükle"""
        self.current_theme_name = theme_name
        
        if theme_name == "default":
            # Default: Unicode kullan, PNG yükleme
            self.theme_data = self._get_default_theme_data()
            self._raw_images = {}
            self.piece_images = {}
            self._save_settings()
            return True
        
        theme_path = self._find_theme_path(theme_name)
        
        if not theme_path:
            self.theme_data = self._get_default_theme_data()
            self.current_theme_name = "default"
            self._raw_images = {}
            self.piece_images = {}
            self._save_settings()
            return False
        
        try:
            with open(os.path.join(theme_path, "theme.json"), "r", encoding="utf-8") as f:
                self.theme_data = json.load(f)
            
            # Taş resimlerini yükle (sadece özel temalarda)
            self._load_piece_images(theme_path)
            self._save_settings()
            return True
        except Exception as e:
            print(f"Tema yukleme hatasi: {e}")
            self.theme_data = self._get_default_theme_data()
            self.current_theme_name = "default"
            self._save_settings()
            return False
    
    def _get_default_theme_data(self) -> Dict:
        """Varsayılan tema verisi"""
        return {
            "name": "Varsayilan",
            "board": {
                "light_color": "#EEEED2",
                "dark_color": "#769656",
                "highlight_color": "#BACA44",
                "selected_color": "#F6F669",
                "last_move_light": "#F6F680",
                "last_move_dark": "#BACA44",
                "check_color": "#E84545",
                "hint_color": "#5DAD5D",
                "coordinates_color": "#B0B0B0"
            },
            "pieces": {
                "style": "unicode",
                "directory": "pieces"
            }
        }
    
    def _load_piece_images(self, theme_path: str):
        """Taş resimlerini yükle"""
        self._raw_images = {}
        self.piece_images = {}
        
        pieces_dir = os.path.join(theme_path, 
                                   self.theme_data.get("pieces", {}).get("directory", "pieces"))
        
        if not os.path.exists(pieces_dir):
            return
        
        piece_names = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 
                        'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']
        
        for name in piece_names:
            filepath = os.path.join(pieces_dir, f"{name}.png")
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath).convert("RGBA")
                    self._raw_images[name] = img
                except:
                    pass
    
    def get_piece_image(self, piece_key: str, size: int) -> Optional[ImageTk.PhotoImage]:
        """Belirli boyutta taş resmi döndür (cache'li)"""
        if piece_key not in self._raw_images:
            return None
        
        if piece_key not in self.piece_images:
            self.piece_images[piece_key] = {}
        
        if size not in self.piece_images[piece_key]:
            try:
                raw = self._raw_images[piece_key]
                resized = raw.resize((size, size), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                self.piece_images[piece_key][size] = photo
            except:
                return None
        
        return self.piece_images[piece_key].get(size)
    
    def clear_cache(self):
        """Resim cache'ini temizle"""
        self.piece_images = {}
    
    def has_piece_images(self) -> bool:
        """Taş resimleri yüklü mü?"""
        return len(self._raw_images) > 0
    
    # Board renkleri için kısayollar
    @property
    def board_light(self) -> str:
        return self.theme_data.get("board", {}).get("light_color", "#EEEED2")
    
    @property
    def board_dark(self) -> str:
        return self.theme_data.get("board", {}).get("dark_color", "#769656")
    
    @property
    def board_highlight(self) -> str:
        return self.theme_data.get("board", {}).get("highlight_color", "#BACA44")
    
    @property
    def board_selected(self) -> str:
        return self.theme_data.get("board", {}).get("selected_color", "#F6F669")
    
    @property
    def board_last_move_light(self) -> str:
        return self.theme_data.get("board", {}).get("last_move_light", "#F6F680")
    
    @property
    def board_last_move_dark(self) -> str:
        return self.theme_data.get("board", {}).get("last_move_dark", "#BACA44")
    
    @property
    def board_check(self) -> str:
        return self.theme_data.get("board", {}).get("check_color", "#E84545")
    
    @property
    def board_hint(self) -> str:
        return self.theme_data.get("board", {}).get("hint_color", "#5DAD5D")
    
    @property
    def board_coords_color(self) -> str:
        return self.theme_data.get("board", {}).get("coordinates_color", "#B0B0B0")
    
    def get_piece_key(self, piece) -> str:
        """python-chess Piece objesinden tema key'i oluştur"""
        import chess
        color_prefix = 'w' if piece.color == chess.WHITE else 'b'
        piece_map = {
            chess.KING: 'K', chess.QUEEN: 'Q', chess.ROOK: 'R',
            chess.BISHOP: 'B', chess.KNIGHT: 'N', chess.PAWN: 'P'
        }
        piece_char = piece_map.get(piece.piece_type, 'P')
        return f"{color_prefix}{piece_char}"
