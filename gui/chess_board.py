"""
Satranç Tahtası Widget'ı
Canvas tabanlı interaktif satranç tahtası
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable, List, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    BOARD_LIGHT_COLOR, BOARD_DARK_COLOR, BOARD_HIGHLIGHT_COLOR,
    BOARD_SELECTED_COLOR, BOARD_LAST_MOVE_COLOR, BOARD_HINT_COLOR,
    BOARD_CHECK_COLOR, PIECE_UNICODE
)


class ChessBoard(ctk.CTkCanvas):
    """Interaktif satranç tahtası"""
    
    def __init__(self, parent, size: int = 480, flipped: bool = False,
                 on_move: Optional[Callable] = None,
                 on_promotion_needed: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, width=size, height=size, 
                        highlightthickness=0, **kwargs)
        
        self.size = size
        self.square_size = size // 8
        self.flipped = flipped
        self.on_move = on_move
        self.on_promotion_needed = on_promotion_needed
        
        # Oyun durumu
        self.board = chess.Board()
        self.selected_square: Optional[chess.Square] = None
        self.legal_moves: List[chess.Move] = []
        self.last_move: Optional[chess.Move] = None
        self.hint_move: Optional[chess.Move] = None
        self.interactive = True
        
        # Taş fontları
        self.piece_font_size = int(self.square_size * 0.8)
        
        # Event binding
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)
        
        # İlk çizim
        self.draw_board()
    
    def _on_resize(self, event):
        """Yeniden boyutlandırma"""
        new_size = min(event.width, event.height)
        if new_size != self.size and new_size > 100:
            self.size = new_size
            self.square_size = new_size // 8
            self.piece_font_size = int(self.square_size * 0.8)
            self.configure(width=new_size, height=new_size)
            self.draw_board()
    
    def set_board(self, board: chess.Board):
        """Tahtayı ayarla"""
        self.board = board
        self.selected_square = None
        self.legal_moves = []
        self.draw_board()
    
    def set_position(self, fen: str):
        """FEN'den pozisyon yükle"""
        try:
            self.board.set_fen(fen)
            self.selected_square = None
            self.legal_moves = []
            self.last_move = None
            self.draw_board()
        except:
            pass
    
    def set_flipped(self, flipped: bool):
        """Tahtayı çevir"""
        self.flipped = flipped
        self.draw_board()
    
    def set_interactive(self, interactive: bool):
        """İnteraktiviteyi aç/kapa"""
        self.interactive = interactive
    
    def show_hint(self, move: Optional[chess.Move]):
        """İpucu hamlesini göster"""
        self.hint_move = move
        self.draw_board()
    
    def clear_hint(self):
        """İpucunu temizle"""
        self.hint_move = None
        self.draw_board()
    
    def set_last_move(self, move: Optional[chess.Move]):
        """Son hamleyi ayarla"""
        self.last_move = move
        self.draw_board()
    
    def draw_board(self):
        """Tahtayı çiz"""
        self.delete("all")
        
        # Kareleri çiz
        for row in range(8):
            for col in range(8):
                self._draw_square(row, col)
        
        # Etiketleri çiz
        self._draw_labels()
        
        # Taşları çiz
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(square, piece)
        
        # İpucu okunu çiz
        if self.hint_move:
            self._draw_hint_arrow(self.hint_move)
    
    def _draw_square(self, row: int, col: int):
        """Tek bir kareyi çiz"""
        # Koordinatları hesapla (flipped durumuna göre)
        if self.flipped:
            display_row = row
            display_col = 7 - col
        else:
            display_row = 7 - row
            display_col = col
        
        x1 = display_col * self.square_size
        y1 = display_row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        
        # Kare rengi
        square = chess.square(col, row)
        is_light = (row + col) % 2 == 1
        color = BOARD_LIGHT_COLOR if is_light else BOARD_DARK_COLOR
        
        # Son hamle vurgusu
        if self.last_move:
            if square in (self.last_move.from_square, self.last_move.to_square):
                color = BOARD_LAST_MOVE_COLOR
        
        # Seçili kare
        if square == self.selected_square:
            color = BOARD_SELECTED_COLOR
        
        # Geçerli hamleler
        if self.selected_square is not None:
            for move in self.legal_moves:
                if move.to_square == square:
                    color = BOARD_HIGHLIGHT_COLOR
        
        # Şah durumu
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if square == king_square:
                color = BOARD_CHECK_COLOR
        
        self.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # Geçerli hamle noktaları
        if self.selected_square is not None:
            for move in self.legal_moves:
                if move.to_square == square:
                    # Hedef karede taş varsa çerçeve, yoksa nokta
                    if self.board.piece_at(square):
                        self._draw_capture_indicator(x1, y1, x2, y2)
                    else:
                        self._draw_move_dot(x1, y1)
    
    def _draw_move_dot(self, x1: int, y1: int):
        """Geçerli hamle noktası çiz"""
        center_x = x1 + self.square_size // 2
        center_y = y1 + self.square_size // 2
        radius = self.square_size // 6
        
        self.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill="#666666", outline=""
        )
    
    def _draw_capture_indicator(self, x1: int, y1: int, x2: int, y2: int):
        """Yeme göstergesi çiz"""
        # Köşe üçgenleri
        corner_size = self.square_size // 4
        color = "#666666"
        
        # Sol üst
        self.create_polygon(
            x1, y1, x1 + corner_size, y1, x1, y1 + corner_size,
            fill=color, outline=""
        )
        # Sağ üst
        self.create_polygon(
            x2, y1, x2 - corner_size, y1, x2, y1 + corner_size,
            fill=color, outline=""
        )
        # Sol alt
        self.create_polygon(
            x1, y2, x1 + corner_size, y2, x1, y2 - corner_size,
            fill=color, outline=""
        )
        # Sağ alt
        self.create_polygon(
            x2, y2, x2 - corner_size, y2, x2, y2 - corner_size,
            fill=color, outline=""
        )
    
    def _draw_labels(self):
        """Sütun ve satır etiketleri"""
        font_size = int(self.square_size * 0.2)
        
        for i in range(8):
            # Sütun etiketleri (a-h)
            col = 7 - i if self.flipped else i
            x = i * self.square_size + self.square_size - 5
            y = self.size - 5
            is_light = (7 + i) % 2 == 1
            color = BOARD_DARK_COLOR if is_light else BOARD_LIGHT_COLOR
            
            self.create_text(
                x, y,
                text=chr(ord('a') + col),
                font=("Arial", font_size, "bold"),
                fill=color,
                anchor="se"
            )
            
            # Satır etiketleri (1-8)
            row = i if self.flipped else 7 - i
            x = 5
            y = i * self.square_size + 5
            is_light = (i) % 2 == 1
            color = BOARD_DARK_COLOR if is_light else BOARD_LIGHT_COLOR
            
            self.create_text(
                x, y,
                text=str(row + 1),
                font=("Arial", font_size, "bold"),
                fill=color,
                anchor="nw"
            )
    
    def _draw_piece(self, square: chess.Square, piece: chess.Piece):
        """Taş çiz"""
        # Koordinatları hesapla
        col = chess.square_file(square)
        row = chess.square_rank(square)
        
        if self.flipped:
            display_row = row
            display_col = 7 - col
        else:
            display_row = 7 - row
            display_col = col
        
        x = display_col * self.square_size + self.square_size // 2
        y = display_row * self.square_size + self.square_size // 2
        
        # Unicode sembolü
        symbol = piece.symbol()
        unicode_piece = PIECE_UNICODE.get(symbol, "?")
        
        # Renk
        text_color = "#FFFFFF" if piece.color == chess.WHITE else "#000000"
        outline_color = "#000000" if piece.color == chess.WHITE else "#FFFFFF"
        
        # Gölge efekti
        self.create_text(
            x + 2, y + 2,
            text=unicode_piece,
            font=("Segoe UI Symbol", self.piece_font_size),
            fill="#444444"
        )
        
        # Ana taş
        self.create_text(
            x, y,
            text=unicode_piece,
            font=("Segoe UI Symbol", self.piece_font_size),
            fill=text_color
        )
    
    def _draw_hint_arrow(self, move: chess.Move):
        """İpucu okunu çiz"""
        from_sq = move.from_square
        to_sq = move.to_square
        
        # Koordinatları hesapla
        from_col = chess.square_file(from_sq)
        from_row = chess.square_rank(from_sq)
        to_col = chess.square_file(to_sq)
        to_row = chess.square_rank(to_sq)
        
        if self.flipped:
            from_x = (7 - from_col) * self.square_size + self.square_size // 2
            from_y = from_row * self.square_size + self.square_size // 2
            to_x = (7 - to_col) * self.square_size + self.square_size // 2
            to_y = to_row * self.square_size + self.square_size // 2
        else:
            from_x = from_col * self.square_size + self.square_size // 2
            from_y = (7 - from_row) * self.square_size + self.square_size // 2
            to_x = to_col * self.square_size + self.square_size // 2
            to_y = (7 - to_row) * self.square_size + self.square_size // 2
        
        # Ok çiz
        arrow_color = BOARD_HINT_COLOR
        self.create_line(
            from_x, from_y, to_x, to_y,
            fill=arrow_color, width=8,
            arrow="last", arrowshape=(20, 25, 8)
        )
        
        # Başlangıç noktası
        radius = 12
        self.create_oval(
            from_x - radius, from_y - radius,
            from_x + radius, from_y + radius,
            fill=arrow_color, outline=""
        )
    
    def _on_click(self, event):
        """Tıklama eventi"""
        if not self.interactive:
            return
        
        # Tıklanan kareyi bul
        col = event.x // self.square_size
        row = event.y // self.square_size
        
        if self.flipped:
            square = chess.square(7 - col, row)
        else:
            square = chess.square(col, 7 - row)
        
        # Geçerli hamleye tıklandı mı?
        if self.selected_square is not None:
            for move in self.legal_moves:
                if move.to_square == square:
                    # Terfi kontrolü
                    if self._needs_promotion(self.selected_square, square):
                        if self.on_promotion_needed:
                            self.on_promotion_needed(self.selected_square, square)
                        return
                    
                    # Hamleyi yap
                    self._make_move(move)
                    return
        
        # Yeni taş seçimi
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.selected_square = square
            self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
        else:
            self.selected_square = None
            self.legal_moves = []
        
        self.draw_board()
    
    def _needs_promotion(self, from_sq: chess.Square, to_sq: chess.Square) -> bool:
        """Terfi gerekli mi?"""
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(to_sq)
            if (piece.color == chess.WHITE and to_rank == 7) or \
               (piece.color == chess.BLACK and to_rank == 0):
                return True
        return False
    
    def make_promotion_move(self, from_sq: chess.Square, to_sq: chess.Square, promotion: str):
        """Terfi hamlesi yap"""
        promotion_piece = {'Q': chess.QUEEN, 'R': chess.ROOK, 
                          'B': chess.BISHOP, 'N': chess.KNIGHT}.get(promotion, chess.QUEEN)
        move = chess.Move(from_sq, to_sq, promotion=promotion_piece)
        self._make_move(move)
    
    def _make_move(self, move: chess.Move):
        """Hamle yap - callback hamleyi board'da yapar, biz sadece görsel güncelleme yaparız"""
        if move in self.board.legal_moves:
            # Callback'i çağır - callback board'a push yapacak
            if self.on_move:
                self.on_move(move)
            
            # Görsel güncelleme
            self.last_move = move
            self.selected_square = None
            self.legal_moves = []
            self.hint_move = None
            self.draw_board()
    
    def push_move(self, move: chess.Move):
        """Dışarıdan hamle yap (bot için)"""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self.legal_moves = []
            self.draw_board()
    
    def get_square_at(self, x: int, y: int) -> chess.Square:
        """Koordinattan kare hesapla"""
        col = x // self.square_size
        row = y // self.square_size
        
        if self.flipped:
            return chess.square(7 - col, row)
        else:
            return chess.square(col, 7 - row)
