"""
Satranç Uygulaması - Ana Giriş Noktası
Çevrimdışı satranç oyunu: Botla Oyna, Arkadaşla Oyna, Analiz
"""
import customtkinter as ctk
import sys
import os

# Path ayarları
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, THEME
from gui.main_menu import MainMenu
from gui.bot_game import BotGame
from gui.friend_game import FriendGame
from gui.analysis_screen import AnalysisScreen


class ChessApp(ctk.CTk):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        
        # Pencere ayarları
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Arka plan rengi
        self.configure(fg_color=THEME["bg_primary"])
        
        # Mevcut ekran
        self.current_screen = None
        
        # Ana menüyü göster
        self.show_main_menu()
        
        # Pencere kapatma eventi
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def show_main_menu(self):
        """Ana menüyü göster"""
        self._clear_screen()
        
        self.current_screen = MainMenu(
            self,
            on_bot_game=self.show_bot_game,
            on_friend_game=self.show_friend_game,
            on_analysis=self.show_analysis
        )
        self.current_screen.pack(fill="both", expand=True)
    
    def show_bot_game(self):
        """Botla oyna ekranını göster"""
        self._clear_screen()
        
        self.current_screen = BotGame(
            self,
            on_back=self.show_main_menu
        )
        self.current_screen.pack(fill="both", expand=True)
    
    def show_friend_game(self):
        """Arkadaşla oyna ekranını göster"""
        self._clear_screen()
        
        self.current_screen = FriendGame(
            self,
            on_back=self.show_main_menu
        )
        self.current_screen.pack(fill="both", expand=True)
    
    def show_analysis(self):
        """Analiz ekranını göster"""
        self._clear_screen()
        
        self.current_screen = AnalysisScreen(
            self,
            on_back=self.show_main_menu
        )
        self.current_screen.pack(fill="both", expand=True)
    
    def _clear_screen(self):
        """Mevcut ekranı temizle"""
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None
    
    def _on_close(self):
        """Pencere kapatılırken"""
        self._clear_screen()
        self.quit()
        self.destroy()


def main():
    """Uygulamayı başlat"""
    app = ChessApp()
    app.mainloop()


if __name__ == "__main__":
    main()
