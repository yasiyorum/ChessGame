"""
Satranç Tahtası Widget'ı - Chess.com Kalitesinde
Canvas tabanlı interaktif satranç tahtası - PNG taş resimleri
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable, List, Tuple
from PIL import Image, ImageTk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import PIECE_UNICODE, THEME
from theme_manager import ThemeManager


class ChessBoard(ctk.CTkCanvas):
    """Interaktif satranç tahtası - Chess.com tarzı"""
    
    # Koordinat etiketi karelerin içinde (chess.com gibi)
    COORD_MARGIN = 0  # Artık dışarıda değil, karelerin içinde
    
    def __init__(self, parent, size: int = 480, flipped: bool = False,
                 on_move: Optional[Callable] = None,
                 on_promotion_needed: Optional[Callable] = None,
                 **kwargs):
        total_size = size
        super().__init__(parent, width=total_size, height=total_size, 
                        highlightthickness=0, bg=THEME["bg_primary"], **kwargs)
        
        self.total_size = total_size
        self.size = size
        self.square_size = size // 8
        self.flipped = flipped
        self.on_move = on_move
        self.on_promotion_needed = on_promotion_needed
        
        # Tema
        self.theme = ThemeManager.get_instance()
        
        # Oyun durumu
        self.board = chess.Board()
        self.selected_square: Optional[chess.Square] = None
        self.legal_moves: List[chess.Move] = []
        self.last_move: Optional[chess.Move] = None
        self.hint_move: Optional[chess.Move] = None
        self.interactive = True
        
        # Taş resimleri referansları (garbage collection önlemi)
        self._piece_refs = []
        
        # Taş fontları (fallback)
        self.piece_font_size = int(self.square_size * 0.75)
        
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
            self.total_size = new_size
            self.square_size = new_size // 8
            self.piece_font_size = int(self.square_size * 0.75)
            self.configure(width=new_size, height=new_size)
            self.theme.clear_cache()  # Boyut değişince cache temizle
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
        self._piece_refs = []
        
        # Kareleri çiz
        for row in range(8):
            for col in range(8):
                self._draw_square(row, col)
        
        # Koordinat etiketlerini kare içine çiz (chess.com gibi)
        self._draw_coordinates()
        
        # Taşları çiz
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(square, piece)
        
        # İpucu okunu çiz
        if self.hint_move:
            self._draw_hint_arrow(self.hint_move)
    
    def _get_square_color(self, row: int, col: int) -> str:
        """Kare rengini belirle"""
        square = chess.square(col, row)
        is_light = (row + col) % 2 == 1
        
        # Varsayılan renk
        color = self.theme.board_light if is_light else self.theme.board_dark
        
        # Son hamle vurgusu
        if self.last_move:
            if square in (self.last_move.from_square, self.last_move.to_square):
                color = self.theme.board_last_move_light if is_light else self.theme.board_last_move_dark
        
        # Seçili kare
        if square == self.selected_square:
            color = self.theme.board_selected
        
        # Şah durumu - gradient kırmızı
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if square == king_square:
                color = self.theme.board_check
        
        return color
    
    def _draw_square(self, row: int, col: int):
        """Tek bir kareyi çiz"""
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
        
        square = chess.square(col, row)
        color = self._get_square_color(row, col)
        
        self.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # Geçerli hamle göstergeleri
        if self.selected_square is not None:
            for move in self.legal_moves:
                if move.to_square == square:
                    if self.board.piece_at(square):
                        self._draw_capture_ring(x1, y1, x2, y2)
                    else:
                        self._draw_move_dot(x1, y1)
    
    def _draw_move_dot(self, x1: int, y1: int):
        """Chess.com tarzı hamle noktası (yarı-şeffaf daire)"""
        center_x = x1 + self.square_size // 2
        center_y = y1 + self.square_size // 2
        radius = self.square_size // 6
        
        self.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill="#14120F", outline="", stipple="gray50"
        )
    
    def _draw_capture_ring(self, x1: int, y1: int, x2: int, y2: int):
        """Chess.com tarzı yeme göstergesi (halka)"""
        padding = self.square_size // 12
        ring_width = self.square_size // 7
        
        # Dış halka
        self.create_oval(
            x1 + padding, y1 + padding,
            x2 - padding, y2 - padding,
            fill="", outline="#14120F", width=ring_width,
            stipple="gray50"
        )
    
    def _draw_coordinates(self):
        """Chess.com tarzı koordinatlar"""
        style = self.theme.settings.get("coords_style", "inside")
        if style == "off":
            return
            
        coord_font_size = max(9, int(self.square_size * 0.18))
        
        for i in range(8):
            # Sütun harfleri (alttaki satırın sağ alt köşesi)
            if self.flipped:
                file_char = chr(ord('h') - i)
                bottom_row = 0
            else:
                file_char = chr(ord('a') + i)
                bottom_row = 7
            
            is_light_square_file = (bottom_row + i) % 2 == 0
            # Kontrast için ters renk
            file_color = self.theme.board_dark if is_light_square_file else self.theme.board_light
            
            if style == "outside":
                # Şimdilik outside desteği tam yok, köşeye yakın çizelim
                x = i * self.square_size + self.square_size // 2
                y = self.size - coord_font_size // 2
                anchor = "s"
                file_color = self.theme.board_coords_color
            else:
                x = i * self.square_size + self.square_size - 3
                y = self.size - 3
                anchor = "se"
            
            self.create_text(
                x, y,
                text=file_char,
                font=("Segoe UI", coord_font_size, "bold"),
                fill=file_color,
                anchor=anchor
            )
            
            # Satır numaraları (sol taraftaki sütunun sol üst köşesi)
            if self.flipped:
                rank = i + 1
                left_col = 7
            else:
                rank = 8 - i
                left_col = 0
                
            is_light_square_rank = (i + left_col) % 2 == 0
            rank_color = self.theme.board_dark if is_light_square_rank else self.theme.board_light
            
            if style == "outside":
                x = coord_font_size // 2
                y = i * self.square_size + self.square_size // 2
                anchor = "w"
                rank_color = self.theme.board_coords_color
            else:
                x = 4
                y = i * self.square_size + 4
                anchor = "nw"
            
            self.create_text(
                x, y,
                text=str(rank),
                font=("Segoe UI", coord_font_size, "bold"),
                fill=rank_color,
                anchor=anchor
            )
    
    def _draw_piece(self, square: chess.Square, piece: chess.Piece):
        """Taş çiz (PNG resim veya Unicode fallback)"""
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
        
        # PNG resim dene
        piece_key = self.theme.get_piece_key(piece)
        piece_size = int(self.square_size * 0.88)
        photo = self.theme.get_piece_image(piece_key, piece_size)
        
        if photo:
            self.create_image(x, y, image=photo, anchor="center")
            self._piece_refs.append(photo)
        else:
            # Unicode fallback
            symbol = piece.symbol()
            unicode_piece = PIECE_UNICODE.get(symbol, "?")
            
            text_color = "#FFFFFF" if piece.color == chess.WHITE else "#000000"
            outline_color = "#000000" if piece.color == chess.WHITE else "#FFFFFF"
            
            # Gölge
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
        
        # Yarı-şeffaf ok
        arrow_color = "#15781B"
        self.create_line(
            from_x, from_y, to_x, to_y,
            fill=arrow_color, width=max(8, self.square_size // 6),
            arrow="last", arrowshape=(20, 25, 8),
            stipple="gray75"
        )
        
        # Başlangıç dairesi
        radius = max(10, self.square_size // 5)
        self.create_oval(
            from_x - radius, from_y - radius,
            from_x + radius, from_y + radius,
            fill=arrow_color, outline="", stipple="gray75"
        )
    
    def _on_click(self, event):
        """Tıklama eventi"""
        if not self.interactive:
            return
        
        # Tahta dışı tıklamaları yok say
        if event.x < 0 or event.y < 0:
            return
        if event.x >= self.size or event.y >= self.size:
            return
        
        # Tıklanan kareyi bul
        col = event.x // self.square_size
        row = event.y // self.square_size
        
        # Sınır kontrolü
        if col < 0 or col > 7 or row < 0 or row > 7:
            return
        
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
        """Hamle yap"""
        if move in self.board.legal_moves:
            if self.on_move:
                self.on_move(move)
            
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
