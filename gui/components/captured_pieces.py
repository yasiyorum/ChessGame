"""
Alınan Taşlar Göstergesi - Chess.com Tarzı
"""
import customtkinter as ctk
import chess
from typing import List, Optional
from PIL import Image, ImageTk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import THEME, PIECE_VALUES
from theme_manager import ThemeManager


class CapturedPieces(ctk.CTkFrame):
    """Chess.com tarzı alınan taşlar göstergesi"""
    
    PIECE_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
    
    def __init__(self, parent, color: chess.Color = chess.WHITE, **kwargs):
        super().__init__(parent, fg_color="transparent", height=24, **kwargs)
        self.pack_propagate(False)
        
        self.color = color  # Bu oyuncunun rengi (alınan taşlar karşı renkten)
        self.theme = ThemeManager.get_instance()
        self._piece_refs = []
        
        # İçerik canvas
        self.canvas = ctk.CTkCanvas(
            self, height=22, highlightthickness=0,
            bg=THEME["bg_secondary"]
        )
        self.canvas.pack(fill="x", expand=True)
    
    def update_captured(self, board: chess.Board):
        """Tahtadaki duruma göre alınan taşları güncelle"""
        self.canvas.delete("all")
        self._piece_refs = []
        
        # Karşı tarafın alınan taşlarını hesapla
        opponent_color = not self.color
        
        # Başlangıçtaki taş sayıları
        initial_counts = {
            chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
            chess.ROOK: 2, chess.QUEEN: 1
        }
        
        # Mevcut taş sayıları
        current_counts = {}
        for piece_type in self.PIECE_ORDER:
            current_counts[piece_type] = len(board.pieces(piece_type, opponent_color))
        
        # Alınan taşlar (başlangıç - mevcut)
        captured = {}
        for piece_type in self.PIECE_ORDER:
            diff = initial_counts[piece_type] - current_counts[piece_type]
            if diff > 0:
                captured[piece_type] = diff
        
        # Materyal avantajı hesapla
        my_material = sum(
            len(board.pieces(pt, self.color)) * v 
            for pt, v in [(chess.PAWN, 1), (chess.KNIGHT, 3), (chess.BISHOP, 3), 
                          (chess.ROOK, 5), (chess.QUEEN, 9)]
        )
        opp_material = sum(
            len(board.pieces(pt, opponent_color)) * v 
            for pt, v in [(chess.PAWN, 1), (chess.KNIGHT, 3), (chess.BISHOP, 3), 
                          (chess.ROOK, 5), (chess.QUEEN, 9)]
        )
        advantage = my_material - opp_material
        
        # Taşları çiz
        x = 4
        piece_size = 16
        
        for piece_type in self.PIECE_ORDER:
            count = captured.get(piece_type, 0)
            for _ in range(count):
                # PNG resim dene
                prefix = 'b' if opponent_color == chess.BLACK else 'w'
                piece_map = {
                    chess.KING: 'K', chess.QUEEN: 'Q', chess.ROOK: 'R',
                    chess.BISHOP: 'B', chess.KNIGHT: 'N', chess.PAWN: 'P'
                }
                piece_key = f"{prefix}{piece_map[piece_type]}"
                photo = self.theme.get_piece_image(piece_key, piece_size)
                
                if photo:
                    self.canvas.create_image(x + piece_size // 2, 11, image=photo, anchor="center")
                    self._piece_refs.append(photo)
                else:
                    # Unicode fallback
                    unicode_map = {
                        chess.QUEEN: '♛' if opponent_color == chess.BLACK else '♕',
                        chess.ROOK: '♜' if opponent_color == chess.BLACK else '♖',
                        chess.BISHOP: '♝' if opponent_color == chess.BLACK else '♗',
                        chess.KNIGHT: '♞' if opponent_color == chess.BLACK else '♘',
                        chess.PAWN: '♟' if opponent_color == chess.BLACK else '♙',
                    }
                    self.canvas.create_text(
                        x + piece_size // 2, 11,
                        text=unicode_map.get(piece_type, "?"),
                        font=("Segoe UI Symbol", 12),
                        fill="#9E9B98",
                        anchor="center"
                    )
                
                x += piece_size - 2  # Hafif overlap
        
        # Materyal avantajı göster
        if advantage > 0:
            self.canvas.create_text(
                x + 8, 11,
                text=f"+{advantage}",
                font=("Segoe UI", 10, "bold"),
                fill="#9E9B98",
                anchor="w"
            )
