"""
Temel Oyun Ekranı (Base Class)
Bot ve Arkadaş oyunları için ortak arayüz
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME

from .chess_board import ChessBoard
from .components.timer import ChessTimer
from .components.move_list import MoveList


class GameScreen(ctk.CTkFrame):
    """Temel oyun ekranı"""
    
    def __init__(self, parent, 
                 on_back: Optional[Callable] = None,
                 title: str = "Oyun",
                 **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_back = on_back
        self.title_text = title
        
        self.configure(fg_color=THEME["bg_primary"])
        
        # Oyun durumu
        self.game_active = False
        self.current_turn = chess.WHITE
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        # Üst bar
        self._setup_header()
        
        # Ana içerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol panel (tahta)
        self._setup_board_panel(content)
        
        # Sağ panel (bilgiler)
        self._setup_info_panel(content)
        
        # Alt butonlar
        self._setup_footer()
    
    def _setup_header(self):
        """Üst bar"""
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Geri butonu
        back_btn = ctk.CTkButton(
            header,
            text="← Geri",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=THEME["button_hover"],
            command=self._on_back_click,
            width=80
        )
        back_btn.pack(side="left", padx=10, pady=10)
        
        # Başlık
        self.title_label = ctk.CTkLabel(
            header,
            text=self.title_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.title_label.pack(side="left", padx=20)
        
        # Durum göstergesi
        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=THEME["text_secondary"]
        )
        self.status_label.pack(side="right", padx=20)
    
    def _setup_board_panel(self, parent):
        """Tahta paneli"""
        board_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=15)
        board_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Tahta container (ortalama için)
        board_container = ctk.CTkFrame(board_frame, fg_color="transparent")
        board_container.pack(expand=True, pady=20)
        
        # Satranç tahtası
        self.chess_board = ChessBoard(
            board_container,
            size=480,
            on_move=self._on_player_move,
            on_promotion_needed=self._on_promotion_needed
        )
        self.chess_board.pack()
    
    def _setup_info_panel(self, parent):
        """Bilgi paneli"""
        info_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], 
                                  corner_radius=15, width=280)
        info_frame.pack(side="right", fill="y", padx=(10, 0))
        info_frame.pack_propagate(False)
        
        # Rakip timer
        self.opponent_timer = ChessTimer(
            info_frame,
            initial_time=300,
            player_name="Rakip",
            on_timeout=lambda: self._on_timeout("opponent")
        )
        self.opponent_timer.pack(fill="x", padx=10, pady=(15, 5))
        
        # Hamle listesi
        self.move_list = MoveList(
            info_frame,
            fg_color=THEME["bg_tertiary"],
            corner_radius=10,
            height=250
        )
        self.move_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Oyuncu timer
        self.player_timer = ChessTimer(
            info_frame,
            initial_time=300,
            player_name="Sen",
            on_timeout=lambda: self._on_timeout("player")
        )
        self.player_timer.pack(fill="x", padx=10, pady=(5, 15))
    
    def _setup_footer(self):
        """Alt butonlar"""
        footer = ctk.CTkFrame(self, fg_color="transparent", height=60)
        footer.pack(fill="x", padx=20, pady=(0, 15))
        footer.pack_propagate(False)
        
        # İpucu butonu
        self.hint_btn = ctk.CTkButton(
            footer,
            text="💡 İpucu",
            font=ctk.CTkFont(size=13),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._on_hint_click,
            width=100
        )
        self.hint_btn.pack(side="left", padx=5, pady=10)
        
        # Terk et butonu
        self.resign_btn = ctk.CTkButton(
            footer,
            text="🏳 Terk Et",
            font=ctk.CTkFont(size=13),
            fg_color=THEME["danger"],
            hover_color="#C83030",
            command=self._on_resign_click,
            width=100
        )
        self.resign_btn.pack(side="left", padx=5, pady=10)
        
        # Hamleleri kopyala butonu
        self.copy_btn = ctk.CTkButton(
            footer,
            text="📋 Hamleleri Kopyala",
            font=ctk.CTkFont(size=13),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._on_copy_click,
            width=150
        )
        self.copy_btn.pack(side="right", padx=5, pady=10)
    
    def set_status(self, text: str):
        """Durum metnini güncelle"""
        self.status_label.configure(text=text)
    
    def _on_back_click(self):
        """Geri butonuna tıklandı"""
        self._cleanup()
        if self.on_back:
            self.on_back()
    
    def _on_player_move(self, move: chess.Move):
        """Oyuncu hamle yaptı - override edilecek"""
        pass
    
    def _on_promotion_needed(self, from_sq: chess.Square, to_sq: chess.Square):
        """Terfi gerekli - override edilecek"""
        pass
    
    def _on_hint_click(self):
        """İpucu butonu tıklandı - override edilecek"""
        pass
    
    def _on_resign_click(self):
        """Terk et butonu tıklandı - override edilecek"""
        pass
    
    def _on_copy_click(self):
        """Hamleleri kopyala - override edilecek"""
        pass
    
    def _on_timeout(self, who: str):
        """Süre doldu - override edilecek"""
        pass
    
    def _cleanup(self):
        """Temizlik - override edilecek"""
        self.player_timer.stop()
        self.opponent_timer.stop()
