"""
Maç Geçmişi Yöneticisi
JSON tabanlı oyun geçmişi kayıt ve yükleme sistemi
"""
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

from utils import get_appdata_dir

def get_history_path():
    """Geçmiş dosyası yolu"""
    base = get_appdata_dir()
    return os.path.join(base, "game_history.json")


class GameHistory:
    """Maç geçmişi yöneticisi"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.games: List[Dict] = []
        self._load()
    
    def _load(self):
        """Geçmişi dosyadan yükle"""
        path = get_history_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.games = json.load(f)
            except:
                self.games = []
    
    def _save(self):
        """Geçmişi dosyaya kaydet"""
        path = get_history_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Geçmiş kayıt hatası: {e}")
    
    def add_game(self, white_name: str, black_name: str, result: str,
                 move_count: int, pgn: str, mode: str = "bot",
                 white_name_custom: str = "", black_name_custom: str = ""):
        """Yeni oyun kaydet"""
        game = {
            "id": len(self.games) + 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "white": white_name,
            "black": black_name,
            "white_custom": white_name_custom,
            "black_custom": black_name_custom,
            "result": result,
            "move_count": move_count,
            "mode": mode,
            "pgn": pgn
        }
        self.games.insert(0, game)  # En yeni başa
        
        # Maksimum 200 maç tut
        if len(self.games) > 200:
            self.games = self.games[:200]
        
        self._save()
        return game
    
    def get_games(self, limit: int = 50) -> List[Dict]:
        """Son N maçı getir"""
        return self.games[:limit]
    
    def get_game_by_id(self, game_id: int) -> Optional[Dict]:
        """ID ile maç getir"""
        for g in self.games:
            if g.get("id") == game_id:
                return g
        return None
    
    def clear_history(self):
        """Tüm geçmişi sil"""
        self.games = []
        self._save()
    
    def get_result_text(self, game: Dict) -> str:
        """Sonuç metnini döndür"""
        result = game.get("result", "*")
        if result == "1-0":
            return f"⬜ {game.get('white', 'Beyaz')} kazandı"
        elif result == "0-1":
            return f"⬛ {game.get('black', 'Siyah')} kazandı"
        elif result == "1/2-1/2":
            return "🤝 Berabere"
        return "Devam ediyor"
