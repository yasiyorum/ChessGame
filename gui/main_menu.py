"""
Ana Menü Ekranı - Chess.com Tarzı Premium Tasarım
"""
import customtkinter as ctk
from typing import Callable, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME, APP_VERSION
from theme_manager import ThemeManager


class MainMenu(ctk.CTkFrame):
    """Chess.com tarzı ana menü"""
    
    def __init__(self, parent, 
                 on_bot_game: Optional[Callable] = None,
                 on_friend_game: Optional[Callable] = None,
                 on_analysis: Optional[Callable] = None,
                 on_board_editor: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_bot_game = on_bot_game
        self.on_friend_game = on_friend_game
        self.on_analysis = on_analysis
        self.on_board_editor = on_board_editor
        
        self.configure(fg_color=THEME["bg_primary"])
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        # Ana konteyner
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # Sol panel - Logo ve bilgi
        left_panel = ctk.CTkFrame(main_container, fg_color=THEME["bg_secondary"], corner_radius=0)
        left_panel.pack(side="left", fill="y", ipadx=30)
        
        # Logo alanı
        logo_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(60, 30), padx=30)
        
        # Satranç logosu
        ctk.CTkLabel(
            logo_frame,
            text="♔",
            font=ctk.CTkFont(size=72),
            text_color=THEME["accent"]
        ).pack()
        
        ctk.CTkLabel(
            logo_frame,
            text="SATRANÇ",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=(5, 0))
        
        ctk.CTkLabel(
            logo_frame,
            text="Profesyonel Satranç Deneyimi",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=THEME["text_muted"]
        ).pack(pady=(2, 0))
        
        # Ayırıcı çizgi
        separator = ctk.CTkFrame(left_panel, fg_color=THEME["divider"], height=1)
        separator.pack(fill="x", padx=30, pady=15)
        
        # Ayarlar Butonu
        settings_btn = ctk.CTkButton(
            left_panel,
            text="⚙️ Uygulama Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            text_color=THEME["text_secondary"],
            command=self._open_settings,
            height=40
        )
        settings_btn.pack(fill="x", padx=30, pady=20)
        
        # Alt bilgi (versiyonlu)
        footer_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(
            footer_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_muted"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            footer_frame,
            text="Stockfish Destekli",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_muted"]
        ).pack(side="right")
        
        # Sağ panel - Oyun modları
        right_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Oyun modları başlığı
        header = ctk.CTkFrame(right_panel, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(60, 30))
        
        ctk.CTkLabel(
            header,
            text="Oyna",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text="Bir oyun modu seçin",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=THEME["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(2, 0))
        
        # Oyun modu kartları
        cards_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=50, pady=(0, 40))
        
        # Botla Oyna kartı
        self._create_game_card(
            cards_frame,
            icon="🤖",
            title="Botla Oyna",
            subtitle="Stockfish motoruna karşı oyna",
            accent_color=THEME["accent"],
            command=self._on_bot_click
        ).pack(fill="x", pady=8)
        
        # Arkadaşla Oyna kartı
        self._create_game_card(
            cards_frame,
            icon="👥",
            title="Arkadaşla Oyna",
            subtitle="Aynı bilgisayarda 2 kişi oyna",
            accent_color="#5C8BB0",
            command=self._on_friend_click
        ).pack(fill="x", pady=8)
        
        # Analiz kartı
        self._create_game_card(
            cards_frame,
            icon="📊",
            title="Oyun Analizi",
            subtitle="Oyunlarını analiz et",
            accent_color="#E6912C",
            command=self._on_analysis_click
        ).pack(fill="x", pady=8)
        
        # Pozisyon Kurma (Board Editor) kartı
        self._create_game_card(
            cards_frame,
            icon="✏️",
            title="Tahta Düzenleyici",
            subtitle="Özel pozisyon kur ve analiz et",
            accent_color="#9C59B6",
            command=self._on_board_editor_click
        ).pack(fill="x", pady=8)
    
    def _create_game_card(self, parent, icon: str, title: str, 
                          subtitle: str, accent_color: str, command: Callable) -> ctk.CTkFrame:
        """Chess.com tarzı oyun modu kartı"""
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["panel_border"],
            cursor="hand2"
        )
        card.configure(height=90)
        card.pack_propagate(False)
        
        # Sol renk çizgisi
        accent_bar = ctk.CTkFrame(
            card, fg_color=accent_color, width=4, corner_radius=2
        )
        accent_bar.pack(side="left", fill="y", padx=(12, 0), pady=12)
        
        # İkon
        icon_frame = ctk.CTkFrame(card, fg_color="transparent", width=55)
        icon_frame.pack(side="left", fill="y", padx=(10, 0))
        icon_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=ctk.CTkFont(size=32),
            anchor="center"
        ).pack(expand=True)
        
        # Metin
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(8, 15), pady=15)
        
        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        )
        title_label.pack(fill="x")
        
        subtitle_label = ctk.CTkLabel(
            text_frame,
            text=subtitle,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=THEME["text_secondary"],
            anchor="w"
        )
        subtitle_label.pack(fill="x")
        
        # Sağ ok ikonu
        arrow_label = ctk.CTkLabel(
            card,
            text="›",
            font=ctk.CTkFont(size=24),
            text_color=THEME["text_muted"],
            width=30
        )
        arrow_label.pack(side="right", padx=(0, 15))
        
        # Hover efektleri
        def on_enter(e):
            card.configure(fg_color=THEME["bg_elevated"], border_color=accent_color)
            arrow_label.configure(text_color=accent_color)
        
        def on_leave(e):
            card.configure(fg_color=THEME["bg_secondary"], border_color=THEME["panel_border"])
            arrow_label.configure(text_color=THEME["text_muted"])
        
        def on_click(e):
            command()
        
        # Tüm child widget'lara bind et
        for widget in [card, accent_bar, icon_frame, text_frame, 
                       title_label, subtitle_label, arrow_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            # Alt widget'lar
            for child in widget.winfo_children():
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)
                child.bind("<Button-1>", on_click)
        
        return card
    
    def _open_settings(self):
        """Uygulama ayarlarını aç"""
        from .components.dialogs import AppSettingsDialog
        theme_mgr = ThemeManager.get_instance()
        dialog = AppSettingsDialog(self, theme_mgr)
    
    def _on_bot_click(self):
        if self.on_bot_game:
            self.on_bot_game()
    
    def _on_friend_click(self):
        if self.on_friend_game:
            self.on_friend_game()
    
    def _on_analysis_click(self):
        if self.on_analysis:
            self.on_analysis()

    def _on_board_editor_click(self):
        if self.on_board_editor:
            self.on_board_editor()
