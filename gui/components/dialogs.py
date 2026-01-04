"""
Diyalog Pencereleri
"""
import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    MIN_ELO, MAX_ELO, DEFAULT_ELO, 
    DEFAULT_TIME_MINUTES, DEFAULT_INCREMENT_SECONDS,
    TIME_OPTIONS, INCREMENT_OPTIONS, THEME
)


class SettingsDialog(ctk.CTkToplevel):
    """Oyun ayarları diyaloğu"""
    
    def __init__(self, parent, mode: str = "bot", on_start: Optional[Callable] = None):
        super().__init__(parent)
        
        self.mode = mode
        self.on_start = on_start
        self.result: Optional[Dict] = None
        
        # Pencere ayarları
        self.title("Oyun Ayarları")
        self.geometry("450x580")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # Ortala
        self.after(10, self._center_window)
    
    def _center_window(self):
        """Pencereyi ortala"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 580) // 2
        self.geometry(f"450x580+{x}+{y}")
    
    def _setup_ui(self):
        """UI oluştur"""
        # Başlık
        title = "🤖 Botla Oyna" if self.mode == "bot" else "👥 Arkadaşla Oyna"
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=20)
        
        # Bot ELO ayarı (sadece bot modunda)
        if self.mode == "bot":
            self._setup_elo_section()
        
        # Renk seçimi (sadece bot modunda)
        if self.mode == "bot":
            self._setup_color_section()
        
        # Süre ayarları
        self._setup_time_section()
        
        # Butonlar
        self._setup_buttons()
    
    def _setup_elo_section(self):
        """ELO ayar bölümü"""
        frame = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], corner_radius=10)
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Bot Seviyesi (ELO)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(15, 5), padx=15, anchor="w")
        
        # ELO göstergesi
        self.elo_label = ctk.CTkLabel(
            frame,
            text=str(DEFAULT_ELO),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=THEME["accent"]
        )
        self.elo_label.pack(pady=5)
        
        # Slider
        self.elo_slider = ctk.CTkSlider(
            frame,
            from_=MIN_ELO,
            to=MAX_ELO,
            number_of_steps=62,  # 50 ELO adımları
            command=self._on_elo_change,
            fg_color=THEME["bg_tertiary"],
            progress_color=THEME["accent"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent_hover"]
        )
        self.elo_slider.set(DEFAULT_ELO)
        self.elo_slider.pack(fill="x", padx=20, pady=(5, 15))
    
    def _setup_color_section(self):
        """Renk seçim bölümü"""
        frame = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], corner_radius=10)
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Taş Rengi",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        color_frame = ctk.CTkFrame(frame, fg_color="transparent")
        color_frame.pack(pady=(0, 15))
        
        self.color_var = ctk.StringVar(value="white")
        
        ctk.CTkRadioButton(
            color_frame,
            text="♔ Beyaz",
            variable=self.color_var,
            value="white",
            font=ctk.CTkFont(size=16),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"]
        ).pack(side="left", padx=20)
        
        ctk.CTkRadioButton(
            color_frame,
            text="♚ Siyah",
            variable=self.color_var,
            value="black",
            font=ctk.CTkFont(size=16),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"]
        ).pack(side="left", padx=20)
    
    def _setup_time_section(self):
        """Süre ayar bölümü"""
        frame = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], corner_radius=10)
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Süre Kontrolü",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Süresiz toggle
        self.unlimited_var = ctk.BooleanVar(value=False)
        self.unlimited_check = ctk.CTkSwitch(
            frame,
            text="Süresiz Oyun",
            variable=self.unlimited_var,
            command=self._toggle_time,
            font=ctk.CTkFont(size=13),
            fg_color=THEME["bg_tertiary"],
            progress_color=THEME["accent"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent_hover"]
        )
        self.unlimited_check.pack(pady=5, padx=15, anchor="w")
        
        # Süre seçimi
        time_frame = ctk.CTkFrame(frame, fg_color="transparent")
        time_frame.pack(fill="x", padx=15, pady=10)
        
        # Ana süre
        ctk.CTkLabel(
            time_frame,
            text="Süre (dk):",
            font=ctk.CTkFont(size=12),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        self.time_menu = ctk.CTkOptionMenu(
            time_frame,
            values=[str(t) for t in TIME_OPTIONS],
            fg_color=THEME["button_bg"],
            button_color=THEME["button_bg"],
            button_hover_color=THEME["button_hover"],
            dropdown_fg_color=THEME["bg_secondary"]
        )
        self.time_menu.set(str(DEFAULT_TIME_MINUTES))
        self.time_menu.pack(side="left", padx=(10, 30))
        
        # Ek süre
        ctk.CTkLabel(
            time_frame,
            text="Ek süre (sn):",
            font=ctk.CTkFont(size=12),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        self.increment_menu = ctk.CTkOptionMenu(
            time_frame,
            values=[str(i) for i in INCREMENT_OPTIONS],
            fg_color=THEME["button_bg"],
            button_color=THEME["button_bg"],
            button_hover_color=THEME["button_hover"],
            dropdown_fg_color=THEME["bg_secondary"]
        )
        self.increment_menu.set(str(DEFAULT_INCREMENT_SECONDS))
        self.increment_menu.pack(side="left", padx=10)
    
    def _setup_buttons(self):
        """Butonlar"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            font=ctk.CTkFont(size=14),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self.destroy,
            width=100
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Başla",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._on_start_click,
            width=150
        ).pack(side="right", padx=10)
    
    def _on_elo_change(self, value):
        """ELO değiştiğinde"""
        elo = int(round(value / 50) * 50)  # 50'nin katlarına yuvarla
        self.elo_label.configure(text=str(elo))
    
    def _toggle_time(self):
        """Süresiz modu aç/kapa"""
        state = "disabled" if self.unlimited_var.get() else "normal"
        self.time_menu.configure(state=state)
        self.increment_menu.configure(state=state)
    
    def _on_start_click(self):
        """Başla butonuna tıklandığında"""
        elo = DEFAULT_ELO
        if self.mode == "bot":
            elo = int(round(self.elo_slider.get() / 50) * 50)
        
        self.result = {
            "elo": elo,
            "color": self.color_var.get() if self.mode == "bot" else "white",
            "time_minutes": int(self.time_menu.get()) if not self.unlimited_var.get() else 0,
            "increment_seconds": int(self.increment_menu.get()) if not self.unlimited_var.get() else 0,
            "unlimited": self.unlimited_var.get()
        }
        
        if self.on_start:
            self.on_start(self.result)
        
        self.destroy()


class GameEndDialog(ctk.CTkToplevel):
    """Oyun sonu diyaloğu"""
    
    def __init__(self, parent, result: str, reason: str, pgn: str,
                 on_new_game: Optional[Callable] = None,
                 on_menu: Optional[Callable] = None):
        super().__init__(parent)
        
        self.pgn = pgn
        self.on_new_game = on_new_game
        self.on_menu = on_menu
        
        # Pencere ayarları
        # Pencere ayarları
        self.title("Oyun Bitti")
        self.geometry("450x500")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui(result, reason)
        
        # Ortala
        self.after(10, self._center_window)
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"450x500+{x}+{y}")
    
    def _setup_ui(self, result: str, reason: str):
        """UI oluştur"""
        # Sonuç ikonu
        icon = "🏆" if "Kazandı" in result else ("🤝" if "Berabere" in result else "😔")
        
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=72)
        ).pack(pady=(40, 10))
        
        # Sonuç
        ctk.CTkLabel(
            self,
            text=result,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=5)
        
        # Sebep
        ctk.CTkLabel(
            self,
            text=reason,
            font=ctk.CTkFont(size=16),
            text_color=THEME["text_secondary"]
        ).pack(pady=(0, 20))
        
        # Butonlar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Yeni Oyun",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._new_game
        ).pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🏠 Ana Menü",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._go_menu
        ).pack(fill="x", pady=10)
        
        # PGN Kopyala (text link gibi)
        ctk.CTkButton(
            self,
            text="📋 PGN Kopyala",
            font=ctk.CTkFont(size=14, underline=True),
            fg_color="transparent",
            text_color=THEME["text_secondary"],
            hover_color=THEME["bg_secondary"],
            command=self._copy_pgn,
            height=30
        ).pack(pady=10)
    
    def _copy_pgn(self):
        """PGN'i panoya kopyala"""
        self.clipboard_clear()
        self.clipboard_append(self.pgn)
        
        # Geri bildirim
        self.after(0, lambda: self._show_copied_feedback())
    
    def _show_copied_feedback(self):
        """Kopyalandı geri bildirimi"""
        label = ctk.CTkLabel(
            self,
            text="✓ Kopyalandı!",
            font=ctk.CTkFont(size=12),
            text_color=THEME["accent"]
        )
        label.pack()
        self.after(1500, label.destroy)
    
    def _new_game(self):
        """Yeni oyun"""
        if self.on_new_game:
            self.on_new_game()
        self.destroy()
    
    def _go_menu(self):
        """Ana menüye dön"""
        if self.on_menu:
            self.on_menu()
        self.destroy()


class PromotionDialog(ctk.CTkToplevel):
    """Piyon terfi diyaloğu"""
    
    def __init__(self, parent, color: str = "white", on_select: Optional[Callable] = None):
        super().__init__(parent)
        
        self.on_select = on_select
        self.color = color
        
        # Pencere ayarları
        self.title("Terfi")
        self.geometry("280x100")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # Ortala
        self.after(10, self._center_window)
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 280) // 2
        y = (self.winfo_screenheight() - 100) // 2
        self.geometry(f"280x100+{x}+{y}")
    
    def _setup_ui(self):
        """UI oluştur"""
        ctk.CTkLabel(
            self,
            text="Terfi seçin:",
            font=ctk.CTkFont(size=14),
            text_color=THEME["text_secondary"]
        ).pack(pady=10)
        
        pieces_frame = ctk.CTkFrame(self, fg_color="transparent")
        pieces_frame.pack(pady=10)
        
        pieces = ['Q', 'R', 'B', 'N']
        symbols = ['♕', '♖', '♗', '♘'] if self.color == "white" else ['♛', '♜', '♝', '♞']
        
        for piece, symbol in zip(pieces, symbols):
            btn = ctk.CTkButton(
                pieces_frame,
                text=symbol,
                font=ctk.CTkFont(size=32),
                fg_color=THEME["button_bg"],
                hover_color=THEME["button_hover"],
                command=lambda p=piece: self._select(p),
                width=50,
                height=50
            )
            btn.pack(side="left", padx=5)
    
    def _select(self, piece: str):
        """Taş seçildiğinde"""
        if self.on_select:
            self.on_select(piece)
        self.destroy()
