"""
Temel Oyun Ekranı (Base Class) - Chess.com Tarzı Layout
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
from .components.eval_bar import EvalBar
from .components.captured_pieces import CapturedPieces


class GameScreen(ctk.CTkFrame):
    """Chess.com tarzı oyun ekranı"""
    
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
        # Ana layout: Header + Content
        self._setup_header()
        
        # İçerik alanı
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Sol panel (eval bar + tahta + bilgiler)
        self._setup_board_panel(content)
        
        # Sağ panel (hamle listesi + kontroller)
        self._setup_info_panel(content)
    
    def _setup_header(self):
        """Üst bar - minimal chess.com tarzı"""
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=44, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Geri butonu
        back_btn = ctk.CTkButton(
            header,
            text="← Geri",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=THEME["button_hover"],
            text_color=THEME["text_secondary"],
            command=self._on_back_click,
            width=70,
            height=30
        )
        back_btn.pack(side="left", padx=10, pady=7)
        
        # Başlık
        self.title_label = ctk.CTkLabel(
            header,
            text=self.title_text,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.title_label.pack(side="left", padx=15)
        
        # Durum göstergesi
        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_muted"]
        )
        self.status_label.pack(side="right", padx=15)
    
    def _setup_board_panel(self, parent):
        """Tahta paneli - chess.com layout"""
        # Sol ana çerçeve
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Üst: Rakip bilgileri
        self.opponent_info = ctk.CTkFrame(left_frame, fg_color="transparent", height=50)
        self.opponent_info.pack(fill="x", padx=5, pady=(0, 4))
        self.opponent_info.pack_propagate(False)
        
        # Rakip ismi + timer (aynı satırda)
        opp_left = ctk.CTkFrame(self.opponent_info, fg_color="transparent")
        opp_left.pack(side="left", fill="both", expand=True)
        
        self.opponent_name_label = ctk.CTkLabel(
            opp_left,
            text="Rakip",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        )
        self.opponent_name_label.pack(fill="x", padx=5)
        
        # Rakip alınan taşlar
        self.opponent_captured = CapturedPieces(opp_left, color=chess.BLACK)
        self.opponent_captured.pack(fill="x", padx=5)
        
        # Rakip timer
        self.opponent_timer = ChessTimer(
            self.opponent_info,
            initial_time=300,
            player_name="",
            on_timeout=lambda: self._on_timeout("opponent")
        )
        self.opponent_timer.name_label.pack_forget()  # İsmi zaten üstte gösteriyoruz
        self.opponent_timer.pack(side="right", padx=5)
        
        # Tahta alanı (eval bar + tahta)
        board_area = ctk.CTkFrame(left_frame, fg_color="transparent")
        board_area.pack(fill="both", expand=True)
        
        # Eval bar (sol)
        self.eval_bar = EvalBar(board_area, height=480, width=26)
        
        from theme_manager import ThemeManager
        theme_mgr = ThemeManager.get_instance()
        if theme_mgr.settings.get("show_eval_bar", True):
            self.eval_bar.pack(side="left", fill="y", padx=(5, 4))
        
        # Tahta container
        self.board_container = ctk.CTkFrame(board_area, fg_color=THEME["bg_secondary"], corner_radius=4)
        self.board_container.pack(side="left", fill="both", expand=True)
        
        # Satranç tahtası
        self.chess_board = ChessBoard(
            self.board_container,
            size=480,
            on_move=self._on_player_move,
            on_promotion_needed=self._on_promotion_needed
        )
        self.chess_board.place(relx=0.5, rely=0.5, anchor="center")
        
        # Resize binding
        self.board_container.bind("<Configure>", self._on_board_container_resize)
        
        # Alt: Oyuncu bilgileri
        self.player_info = ctk.CTkFrame(left_frame, fg_color="transparent", height=50)
        self.player_info.pack(fill="x", padx=5, pady=(4, 0))
        self.player_info.pack_propagate(False)
        
        # Oyuncu ismi
        player_left = ctk.CTkFrame(self.player_info, fg_color="transparent")
        player_left.pack(side="left", fill="both", expand=True)
        
        self.player_name_label = ctk.CTkLabel(
            player_left,
            text="Sen",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        )
        self.player_name_label.pack(fill="x", padx=5)
        
        # Oyuncu alınan taşlar
        self.player_captured = CapturedPieces(player_left, color=chess.WHITE)
        self.player_captured.pack(fill="x", padx=5)
        
        # Oyuncu timer
        self.player_timer = ChessTimer(
            self.player_info,
            initial_time=300,
            player_name="",
            on_timeout=lambda: self._on_timeout("player")
        )
        self.player_timer.name_label.pack_forget()
        self.player_timer.pack(side="right", padx=5)
    
    def _on_board_container_resize(self, event):
        """Tahta container'ı yeniden boyutlandırıldığında"""
        available_size = min(event.width, event.height) - 8
        
        if available_size < 320:
            available_size = 320
        
        new_size = (available_size // 8) * 8
        
        if abs(new_size - self.chess_board.size) > 16:
            self.chess_board.size = new_size
            self.chess_board.total_size = new_size
            self.chess_board.square_size = new_size // 8
            self.chess_board.piece_font_size = int(self.chess_board.square_size * 0.75)
            self.chess_board.configure(width=new_size, height=new_size)
            # Eval bar yüksekliğini eşitle
            self.eval_bar.resize(new_size)
            self.chess_board.draw_board()
            
    def _update_eval_bar(self):
        """Asenkron eval bar güncellemesi"""
        if not hasattr(self, "eval_bar") or not self.eval_bar.winfo_ismapped():
            return
            
        def on_hint_ready(result):
            if result:
                _, score = result
                self.after(0, lambda: self.eval_bar.set_eval(score))
                
        # Mevcut get_hint_async metodunu eval hesaplamak için kullanıyoruz
        if hasattr(self, "stockfish") and self.stockfish:
            self.stockfish.get_hint_async(self.engine.board, on_hint_ready)
    def _setup_info_panel(self, parent):
        """Sağ bilgi paneli"""
        info_frame = ctk.CTkFrame(
            parent, 
            fg_color=THEME["bg_secondary"],
            corner_radius=8, 
            width=280,
            border_width=1,
            border_color=THEME["panel_border"]
        )
        info_frame.pack(side="right", fill="y", padx=(5, 0))
        info_frame.pack_propagate(False)
        
        # Hamle listesi
        self.move_list = MoveList(
            info_frame,
            fg_color=THEME["move_list_bg"],
            corner_radius=0
        )
        self.move_list.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Kontrol butonları
        self._setup_controls(info_frame)
    
    def _setup_controls(self, parent):
        """Alt kontrol butonları"""
        # Ayırıcı
        ctk.CTkFrame(parent, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        controls = ctk.CTkFrame(parent, fg_color=THEME["bg_tertiary"], corner_radius=0)
        controls.pack(fill="x", padx=0, pady=0)
        
        # Üst satır butonları
        row1 = ctk.CTkFrame(controls, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(8, 4))
        
        btn_style = {
            "font": ctk.CTkFont(family="Segoe UI", size=11),
            "fg_color": THEME["button_bg"],
            "hover_color": THEME["button_hover"],
            "corner_radius": 6,
            "height": 32,
            "border_width": 1,
            "border_color": THEME["panel_border"]
        }
        
        self.hint_btn = ctk.CTkButton(
            row1, text="💡 İpucu",
            command=self._on_hint_click,
            **btn_style
        )
        self.hint_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))
        
        self.undo_btn = ctk.CTkButton(
            row1, text="↩ Geri Al",
            command=self._on_undo_click,
            **btn_style
        )
        self.undo_btn.pack(side="left", fill="x", expand=True, padx=(3, 0))
        
        # Undo button durumu kontrolü
        from theme_manager import ThemeManager
        theme_mgr = ThemeManager.get_instance()
        mode_str = "bot" if "bot_game" in self.__module__ else "friend"
        allow = theme_mgr.settings.get(f"{mode_str}_allow_undo", True)
        if not allow:
            self.undo_btn.configure(state="disabled")
        
        # Alt satır butonları
        row2 = ctk.CTkFrame(controls, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=(0, 4))
        
        self.resign_btn = ctk.CTkButton(
            row2, text="🏳 Terk Et",
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=6,
            height=32,
            command=self._on_resign_click
        )
        self.resign_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))
        
        self.flip_btn = ctk.CTkButton(
            row2, text="🔄 Çevir",
            command=self._on_flip_click,
            **btn_style
        )
        self.flip_btn.pack(side="left", fill="x", expand=True, padx=(3, 0))
        
        # Kopyala butonu
        row3 = ctk.CTkFrame(controls, fg_color="transparent")
        row3.pack(fill="x", padx=8, pady=(0, 8))
        
        self.copy_btn = ctk.CTkButton(
            row3, text="📋 Hamleleri Kopyala",
            command=self._on_copy_click,
            **btn_style
        )
        self.copy_btn.pack(fill="x")
    
    def update_captured_pieces(self):
        """Alınan taşları güncelle"""
        if hasattr(self, 'chess_board') and self.chess_board.board:
            self.player_captured.update_captured(self.chess_board.board)
            self.opponent_captured.update_captured(self.chess_board.board)
    
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
    
    def _on_undo_click(self):
        """Hamle geri al butonu tıklandı - override edilecek"""
        pass
    
    def _on_flip_click(self):
        """Tahtayı çevir butonu tıklandı"""
        self.chess_board.set_flipped(not self.chess_board.flipped)
    
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
