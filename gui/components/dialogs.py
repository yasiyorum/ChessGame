"""
Diyalog Pencereleri - Chess.com Tarzı
"""
import customtkinter as ctk
from typing import Callable, Optional, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    MIN_ELO, MAX_ELO, DEFAULT_ELO, 
    DEFAULT_TIME_MINUTES, DEFAULT_INCREMENT_SECONDS,
    TIME_OPTIONS, INCREMENT_OPTIONS, THEME
)


class SettingsDialog(ctk.CTkToplevel):
    """Oyun ayarları diyaloğu - scroll yok, her şey tek sayfada"""
    
    def __init__(self, parent, mode: str = "bot", on_start: Optional[Callable] = None):
        super().__init__(parent)
        
        self.mode = mode
        self.on_start = on_start
        self.result: Optional[Dict] = None
        
        # Pencere boyutu - bot modunda daha uzun
        if mode == "bot":
            self.win_w, self.win_h = 500, 580
        else:
            self.win_w, self.win_h = 500, 340
        
        self.title("Oyun Ayarlari")
        self.geometry(f"{self.win_w}x{self.win_h}")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self.after(10, self._center_window)
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.win_w) // 2
        y = (self.winfo_screenheight() - self.win_h) // 2
        self.geometry(f"{self.win_w}x{self.win_h}+{x}+{y}")
    
    def _setup_ui(self):
        """Tüm UI - scroll yok"""
        # Başlık
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title = "Botla Oyna" if self.mode == "bot" else "Arkadasla Oyna"
        ctk.CTkLabel(
            header, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(expand=True)
        
        # İçerik - normal frame (scroll yok!)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=12)
        
        # Bot ELO ayarı
        if self.mode == "bot":
            self._setup_elo_section(content)
            self._setup_color_section(content)
        
        # Süre ayarları
        self._setup_time_section(content)
        
        # Butonlar (alt kısım)
        self._setup_buttons()
    
    def _setup_elo_section(self, parent):
        """ELO ayar bölümü"""
        frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=10,
                             border_width=1, border_color=THEME["panel_border"])
        frame.pack(fill="x", pady=(0, 10))
        
        # Başlık + ELO değeri aynı satırda
        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 0))
        
        ctk.CTkLabel(
            top_row, text="Bot Seviyesi",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        self.elo_level_label = ctk.CTkLabel(
            top_row, text=self._get_elo_level_name(DEFAULT_ELO),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=THEME["text_muted"]
        )
        self.elo_level_label.pack(side="right")
        
        # ELO büyük göstergesi
        self.elo_label = ctk.CTkLabel(
            frame, text=str(DEFAULT_ELO),
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=THEME["accent"]
        )
        self.elo_label.pack(padx=16, pady=(2, 0))
        
        # Slider
        self.elo_slider = ctk.CTkSlider(
            frame, from_=MIN_ELO, to=MAX_ELO,
            number_of_steps=62, command=self._on_elo_change,
            fg_color=THEME["bg_tertiary"],
            progress_color=THEME["accent"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent_hover"],
            height=20
        )
        self.elo_slider.set(DEFAULT_ELO)
        self.elo_slider.pack(fill="x", padx=16, pady=(8, 14))
    
    def _get_elo_level_name(self, elo: int) -> str:
        if elo < 400: return "Yeni Baslayan"
        elif elo < 800: return "Baslangic"
        elif elo < 1200: return "Orta"
        elif elo < 1600: return "Ileri"
        elif elo < 2000: return "Uzman"
        elif elo < 2400: return "Usta"
        elif elo < 2800: return "Buyukusta"
        else: return "Super GM"
    
    def _setup_color_section(self, parent):
        """Renk seçim bölümü - kompakt"""
        frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=10,
                             border_width=1, border_color=THEME["panel_border"])
        frame.pack(fill="x", pady=(0, 10))
        
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        
        ctk.CTkLabel(
            inner, text="Tas Rengi",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        # Radio butonları sağa
        self.color_var = ctk.StringVar(value="white")
        
        radio_frame = ctk.CTkFrame(inner, fg_color="transparent")
        radio_frame.pack(side="right")
        
        ctk.CTkRadioButton(
            radio_frame, text="Siyah", variable=self.color_var, value="black",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            border_color=THEME["text_muted"]
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkRadioButton(
            radio_frame, text="Beyaz", variable=self.color_var, value="white",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            border_color=THEME["text_muted"]
        ).pack(side="right")
    
    def _setup_time_section(self, parent):
        """Süre ayar bölümü - kompakt"""
        frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=10,
                             border_width=1, border_color=THEME["panel_border"])
        frame.pack(fill="x", pady=(0, 10))
        
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        
        # Başlık + süresiz switch aynı satırda
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            top_row, text="Sure Kontrolu",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        self.unlimited_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            top_row, text="Suresiz", variable=self.unlimited_var,
            command=self._toggle_time,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=THEME["bg_tertiary"],
            progress_color=THEME["accent"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent_hover"]
        ).pack(side="right")
        
        # Süre + Ek süre yan yana
        time_row = ctk.CTkFrame(inner, fg_color="transparent")
        time_row.pack(fill="x")
        
        # Sol: Ana süre
        left = ctk.CTkFrame(time_row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkLabel(
            left, text="Sure (dk)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=THEME["text_muted"]
        ).pack(anchor="w")
        
        self.time_menu = ctk.CTkOptionMenu(
            left, values=[str(t) for t in TIME_OPTIONS],
            fg_color=THEME["button_bg"], button_color=THEME["button_bg"],
            button_hover_color=THEME["button_hover"],
            dropdown_fg_color=THEME["bg_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=32
        )
        self.time_menu.set(str(DEFAULT_TIME_MINUTES))
        self.time_menu.pack(fill="x", pady=(3, 0))
        
        # Sağ: Ek süre
        right = ctk.CTkFrame(time_row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        ctk.CTkLabel(
            right, text="Ek sure (sn)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=THEME["text_muted"]
        ).pack(anchor="w")
        
        self.increment_menu = ctk.CTkOptionMenu(
            right, values=[str(i) for i in INCREMENT_OPTIONS],
            fg_color=THEME["button_bg"], button_color=THEME["button_bg"],
            button_hover_color=THEME["button_hover"],
            dropdown_fg_color=THEME["bg_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=32
        )
        self.increment_menu.set(str(DEFAULT_INCREMENT_SECONDS))
        self.increment_menu.pack(fill="x", pady=(3, 0))
    
    def _setup_buttons(self):
        """Alt butonlar"""
        btn_frame = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=65, corner_radius=0)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)
        
        inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner.pack(expand=True, padx=24)
        
        ctk.CTkButton(
            inner, text="Iptal",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=THEME["button_bg"], hover_color=THEME["button_hover"],
            command=self.destroy, width=100, height=40, corner_radius=8
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            inner, text="Oyunu Baslat",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            command=self._on_start_click, width=200, height=40, corner_radius=8
        ).pack(side="right", padx=5)
    
    def _on_elo_change(self, value):
        elo = int(round(value / 50) * 50)
        self.elo_label.configure(text=str(elo))
        self.elo_level_label.configure(text=self._get_elo_level_name(elo))
    
    def _toggle_time(self):
        state = "disabled" if self.unlimited_var.get() else "normal"
        self.time_menu.configure(state=state)
        self.increment_menu.configure(state=state)
    
    def _on_start_click(self):
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
        
        self.title("Oyun Bitti")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui(result, reason)
        self.after(10, self._center_window)
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 440) // 2
        y = (self.winfo_screenheight() - 420) // 2
        self.geometry(f"440x420+{x}+{y}")
    
    def _setup_ui(self, result: str, reason: str):
        is_win = "Kazan" in result
        is_draw = "Berabere" in result
        
        stripe_color = THEME["accent"] if is_win else (THEME["warning"] if is_draw else THEME["danger"])
        
        ctk.CTkFrame(self, fg_color=stripe_color, height=4, corner_radius=0).pack(fill="x")
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30)
        
        # Sonuç ikonu
        icon = "🏆" if is_win else ("🤝" if is_draw else "")
        if icon:
            ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=64)).pack(pady=(30, 10))
        else:
            ctk.CTkFrame(content, fg_color="transparent", height=30).pack()
        
        ctk.CTkLabel(
            content, text=result,
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=5)
        
        ctk.CTkLabel(
            content, text=reason,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=THEME["text_secondary"]
        ).pack(pady=(0, 25))
        
        ctk.CTkButton(
            content, text="Yeni Oyun",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=48, fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            corner_radius=8, command=self._new_game
        ).pack(fill="x", pady=5)
        
        ctk.CTkButton(
            content, text="Ana Menu",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=48, fg_color=THEME["button_bg"], hover_color=THEME["button_hover"],
            corner_radius=8, command=self._go_menu
        ).pack(fill="x", pady=5)
        
        ctk.CTkButton(
            content, text="PGN Kopyala",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent", text_color=THEME["text_muted"],
            hover_color=THEME["bg_secondary"],
            command=self._copy_pgn, height=30
        ).pack(pady=(10, 5))
    
    def _copy_pgn(self):
        self.clipboard_clear()
        self.clipboard_append(self.pgn)
    
    def _new_game(self):
        if self.on_new_game:
            self.on_new_game()
        self.destroy()
    
    def _go_menu(self):
        if self.on_menu:
            self.on_menu()
        self.destroy()


class PromotionDialog(ctk.CTkToplevel):
    """Terfi diyaloğu"""
    
    def __init__(self, parent, color: str = "white", on_select: Optional[Callable] = None):
        super().__init__(parent)
        
        self.on_select = on_select
        self.color = color
        
        self.title("Terfi")
        self.geometry("320x130")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self.after(10, self._center_window)
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 320) // 2
        y = (self.winfo_screenheight() - 130) // 2
        self.geometry(f"320x130+{x}+{y}")
    
    def _setup_ui(self):
        ctk.CTkLabel(
            self, text="Terfi secin",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(12, 8))
        
        pieces_frame = ctk.CTkFrame(self, fg_color="transparent")
        pieces_frame.pack(pady=5)
        
        pieces = ['Q', 'R', 'B', 'N']
        symbols = ['♕', '♖', '♗', '♘'] if self.color == "white" else ['♛', '♜', '♝', '♞']
        
        for piece, symbol in zip(pieces, symbols):
            ctk.CTkButton(
                pieces_frame, text=symbol,
                font=ctk.CTkFont(size=34),
                fg_color=THEME["button_bg"], hover_color=THEME["accent"],
                command=lambda p=piece: self._select(p),
                width=60, height=60, corner_radius=8,
                border_width=1, border_color=THEME["panel_border"]
            ).pack(side="left", padx=4)
    
    def _select(self, piece: str):
        if self.on_select:
            self.on_select(piece)
        self.destroy()

class AppSettingsDialog(ctk.CTkToplevel):
    """Genel Uygulama Ayarları"""
    
    def __init__(self, parent, theme_mgr):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        
        self.title("Uygulama Ayarları")
        self.geometry("450x600")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self.after(10, self._center_window)
        
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"450x600+{x}+{y}")
        
    def _setup_ui(self):
        # Başlık
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, text="⚙️ Uygulama Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(side="left", padx=20)
        
        # İçerik
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # --- TEMA ---
        theme_frame = ctk.CTkFrame(content, fg_color=THEME["bg_secondary"], corner_radius=8)
        theme_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(theme_frame, text="🎨 Tema", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        themes = self.theme_mgr.get_available_themes()
        self.theme_var = ctk.StringVar(value=self.theme_mgr.current_theme_name)
        
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame, values=themes, variable=self.theme_var,
            command=self._on_theme_change, width=200
        )
        self.theme_menu.pack(anchor="w", padx=15, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=15, pady=(0, 5))
        
        ctk.CTkButton(
            btn_frame, text="📁 Özel Klasör Seç",
            command=self._select_theme_folder, fg_color=THEME["bg_tertiary"],
            text_color=THEME["text_secondary"], hover_color=THEME["button_bg"],
            width=120
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame, text="📂 Klasörü Aç",
            command=self._open_theme_folder, fg_color=THEME["bg_tertiary"],
            text_color=THEME["text_secondary"], hover_color=THEME["button_bg"],
            width=100
        ).pack(side="left")
        
        self.folder_label = ctk.CTkLabel(
            theme_frame, text=self.theme_mgr.get_themes_dir() or "Yok",
            font=ctk.CTkFont(size=11), text_color=THEME["text_muted"]
        )
        self.folder_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # --- TAHTA ---
        board_frame = ctk.CTkFrame(content, fg_color=THEME["bg_secondary"], corner_radius=8)
        board_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(board_frame, text="♟️ Tahta Ayarları", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(board_frame, text="Koordinatlar", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
        self.coords_var = ctk.StringVar(value=self.theme_mgr.settings.get("coords_style", "inside"))
        coords_menu = ctk.CTkOptionMenu(
            board_frame, variable=self.coords_var,
            values=["İçinde", "Kapalı"],
            command=self._save_settings
        )
        coords_menu.pack(anchor="w", padx=15, pady=(5, 15))
        if self.coords_var.get() == "inside" or self.coords_var.get() == "outside": self.coords_var.set("İçinde")
        elif self.coords_var.get() == "off": self.coords_var.set("Kapalı")
        
        # --- OYUN İÇİ ---
        game_frame = ctk.CTkFrame(content, fg_color=THEME["bg_secondary"], corner_radius=8)
        game_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(game_frame, text="🎮 Oyun İçi", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.eval_var = ctk.BooleanVar(value=self.theme_mgr.settings.get("show_eval_bar", True))
        ctk.CTkSwitch(game_frame, text="Değerlendirme (Eval) Çubuğu", variable=self.eval_var, command=self._save_settings).pack(anchor="w", padx=15, pady=5)
        
        self.bot_undo_var = ctk.BooleanVar(value=self.theme_mgr.settings.get("bot_allow_undo", True))
        ctk.CTkSwitch(game_frame, text="Bot Maçında Geri Al", variable=self.bot_undo_var, command=self._save_settings).pack(anchor="w", padx=15, pady=5)
        
        self.friend_undo_var = ctk.BooleanVar(value=self.theme_mgr.settings.get("friend_allow_undo", True))
        ctk.CTkSwitch(game_frame, text="Arkadaş Maçında Geri Al", variable=self.friend_undo_var, command=self._save_settings).pack(anchor="w", padx=15, pady=(5, 15))
        
        # --- MAÇ GEÇMİŞİ ---
        hist_frame = ctk.CTkFrame(content, fg_color=THEME["bg_secondary"], corner_radius=8)
        hist_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(hist_frame, text="📜 Maç Geçmişi", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        hist_btns = ctk.CTkFrame(hist_frame, fg_color="transparent")
        hist_btns.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkButton(
            hist_btns, text="📋 Geçmişi Göster", command=self._show_history,
            fg_color=THEME["button_bg"], hover_color=THEME["button_hover"], height=30
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            hist_btns, text="🗑 Geçmişi Sil", command=self._clear_history,
            fg_color=THEME["danger"], hover_color=THEME["danger_hover"], height=30
        ).pack(side="left")
        
        # Kapat Butonu
        ctk.CTkButton(
            self, text="Tamam", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            command=self.destroy, height=40
        ).pack(fill="x", padx=20, pady=15)
        
    def _save_settings(self, *args):
        val = self.coords_var.get()
        if val == "İçinde": c_val = "inside"
        else: c_val = "off"
        
        self.theme_mgr.settings["coords_style"] = c_val
        self.theme_mgr.settings["show_eval_bar"] = self.eval_var.get()
        self.theme_mgr.settings["bot_allow_undo"] = self.bot_undo_var.get()
        self.theme_mgr.settings["friend_allow_undo"] = self.friend_undo_var.get()
        self.theme_mgr._save_settings()
        
    def _on_theme_change(self, theme_name: str):
        self.theme_mgr.load_theme(theme_name)
        
    def _select_theme_folder(self):
        from customtkinter import filedialog
        folder = filedialog.askdirectory(title="Özel Tema Klasörünü Seçin")
        if folder:
            self.theme_mgr.set_themes_dir(folder)
            self.folder_label.configure(text=folder)
            themes = self.theme_mgr.get_available_themes()
            self.theme_menu.configure(values=themes)
            if self.theme_mgr.current_theme_name not in themes:
                self.theme_mgr.load_theme("default")
                self.theme_var.set("default")
                
    def _open_theme_folder(self):
        """Tema klasörünü dosya gezgininde aç"""
        folder = self.theme_mgr.get_themes_dir()
        if folder and os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                print(f"Klasör açılamadı: {e}")
    
    def _show_history(self):
        """Maç geçmişini göster"""
        GameHistoryDialog(self, on_load=self._on_load_game)
        
    def _on_load_game(self, pgn: str):
        """Geçmiş maçı analize yükle"""
        self.destroy()
        if hasattr(self.master, "on_analysis") and self.master.on_analysis:
            self.master.on_analysis(pgn)
    
    def _clear_history(self):
        """Geçmişi sil"""
        from game_history import GameHistory
        GameHistory.get_instance().clear_history()


class GameHistoryDialog(ctk.CTkToplevel):
    """Maç Geçmişi Listesi"""
    
    def __init__(self, parent, on_load=None):
        super().__init__(parent)
        self.on_load = on_load
        
        self.title("Maç Geçmişi")
        self.geometry("550x500")
        self.resizable(False, True)
        self.configure(fg_color=THEME["bg_primary"])
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self.after(10, self._center)
    
    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 550) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"550x500+{x}+{y}")
    
    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=45, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="📜 Maç Geçmişi", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=15)
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        from game_history import GameHistory
        history = GameHistory.get_instance()
        games = history.get_games(50)
        
        if not games:
            ctk.CTkLabel(scroll, text="Henüz maç geçmişi yok.", text_color=THEME["text_muted"]).pack(pady=30)
            return
        
        for game in games:
            self._create_game_row(scroll, game, history)
    
    def _create_game_row(self, parent, game, history):
        row = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=6, height=60)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Sol: Sonuç
        result_text = history.get_result_text(game)
        result_color = THEME["accent"] if "kazandı" in result_text else THEME["text_muted"]
        
        ctk.CTkLabel(inner, text=result_text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=result_color, anchor="w").pack(fill="x")
        
        # Alt satır: tarih, hamle
        info = f"{game.get('date', '')} • {game.get('move_count', 0)} hamle • {game.get('mode', 'bot')}"
        ctk.CTkLabel(inner, text=info, font=ctk.CTkFont(size=10),
                     text_color=THEME["text_muted"], anchor="w").pack(fill="x")
        
        # PGN kopyala butonu
        def copy_pgn(pgn=game.get("pgn", "")):
            self.clipboard_clear()
            self.clipboard_append(pgn)
            
        def load_pgn(pgn=game.get("pgn", "")):
            if self.on_load:
                self.on_load(pgn)
                self.destroy()
                
        ctk.CTkButton(row, text="🔍 İncele", width=65, height=30, command=load_pgn,
                      fg_color=THEME["accent"], hover_color=THEME["accent_hover"]
                      ).pack(side="right", padx=5)
        
        ctk.CTkButton(row, text="📋", width=35, height=30, command=copy_pgn,
                      fg_color=THEME["button_bg"], hover_color=THEME["button_hover"]
                      ).pack(side="right")

