"""
Satranç Uygulaması - Ana Giriş Noktası
Chess.com Kalitesinde Profesyonel Satranç Deneyimi
"""
import customtkinter as ctk
import sys
import os

# Path ayarları
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, THEME
from theme_manager import ThemeManager
from gui.main_menu import MainMenu
from gui.bot_game import BotGame
from gui.friend_game import FriendGame
from gui.analysis_screen import AnalysisScreen
from gui.board_editor import BoardEditorScreen


class SplashScreen(ctk.CTkFrame):
    """Açılış ekranı - Paket yükleme durumu için"""
    def __init__(self, parent, on_complete):
        super().__init__(parent, fg_color=THEME["bg_primary"])
        self.on_complete = on_complete
        
        # İçerik
        self.label = ctk.CTkLabel(self, text="Satranç Pro", font=ctk.CTkFont(size=40, weight="bold"))
        self.label.pack(pady=(WINDOW_HEIGHT//3, 20))
        
        self.status_label = ctk.CTkLabel(self, text="Başlatılıyor...", font=ctk.CTkFont(size=14), text_color=THEME["text_secondary"])
        self.status_label.pack(pady=10)
        
        self.progress = ctk.CTkProgressBar(self, width=400, progress_color=THEME["accent"])
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        self.start_sync()

    def start_sync(self):
        import threading
        import time
        from utils import sync_from_github
        
        def run():
            try:
                # 1. Temalar
                self.update_status("Gerekli paketler yükleniyor (Temalar)...", 0.3)
                sync_from_github("themes")
                
                # 2. Stockfish
                self.update_status("Gerekli paketler yükleniyor (Stockfish)...", 0.7)
                sync_from_github("stockfish")
                
                # 3. Tamamla
                self.update_status("Sistem hazır, başlatılıyor...", 1.0)
                time.sleep(0.8)
                self.after(0, self.on_complete)
            except Exception as e:
                print(f"Splash sync error: {e}")
                self.after(0, self.on_complete)

        threading.Thread(target=run, daemon=True).start()

    def update_status(self, text, val):
        self.after(0, lambda: self._update_ui(text, val))

    def _update_ui(self, text, val):
        self.status_label.configure(text=text)
        self.progress.set(val)


class ChessApp(ctk.CTk):
    """Ana uygulama penceresi - Chess.com tarzı"""
    
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
        
        # Pencere ikonunu ayarla
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # Mevcut ekran
        self.current_screen = None
        
        # Açılış ekranını göster
        self.show_splash()
        
        # Pencere kapatma eventi
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def show_splash(self):
        """Açılış ekranını göster"""
        self._clear_screen()
        self.current_screen = SplashScreen(self, on_complete=self.on_splash_complete)
        self.current_screen.pack(fill="both", expand=True)

    def on_splash_complete(self):
        """Yükleme tamamlandığında ana menüye geç"""
        # Tema yöneticisini şimdi başlat (senkronizasyon bittiği için hızlı olacak)
        self.theme_manager = ThemeManager.get_instance()
        self.show_main_menu()

    def show_main_menu(self):
        """Ana menüyü göster"""
        self._clear_screen()
        
        self.current_screen = MainMenu(
            self,
            on_bot_game=self.show_bot_game,
            on_friend_game=self.show_friend_game,
            on_analysis=self.show_analysis,
            on_board_editor=self.show_board_editor
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
    
    def show_analysis(self, pgn=None, fen=None):
        """Analiz ekranını göster"""
        self._clear_screen()
        
        self.current_screen = AnalysisScreen(
            self,
            on_back=self.show_main_menu,
            initial_pgn=pgn,
            initial_fen=fen
        )
        self.current_screen.pack(fill="both", expand=True)
        
    def show_board_editor(self):
        """Tahta düzenleyici ekranını göster"""
        self._clear_screen()
        
        self.current_screen = BoardEditorScreen(
            self,
            on_back=self.show_main_menu,
            on_analyze=lambda fen: self.show_analysis(fen=fen)
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
