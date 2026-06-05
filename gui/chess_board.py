"""
Satranç Tahtası Widget'ı - Chess.com Kalitesinde
Canvas tabanlı interaktif satranç tahtası - PNG taş resimleri
"""
import customtkinter as ctk
import chess
import math
from typing import Optional, Callable, List, Tuple, Set, Dict
from PIL import Image, ImageTk, ImageDraw
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
                 edit_mode: bool = False,
                 on_board_changed: Optional[Callable] = None,
                 on_square_click: Optional[Callable] = None,
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
        self.edit_mode = edit_mode
        self.on_board_changed = on_board_changed
        self.on_square_click = on_square_click
        
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
        
        # === Çizim / Annotasyon Sistemi (Chess.com tarzı) ===
        # Oklar: {(from_square, to_square): color_hex}
        self._arrows: Dict[Tuple[int, int], str] = {}
        # Kare vurguları: {square: color_hex}
        self._highlights: Dict[int, str] = {}
        # Çizim durumu
        self._drawing = False
        self._draw_start_square: Optional[int] = None
        self._draw_preview_end: Optional[Tuple[int, int]] = None  # (x, y) piksel
        self._draw_color = "#15781B"  # Varsayılan yeşil
        
        # Renk paleti (Chess.com tarzı)
        self._annotation_colors = {
            "default": "#15781B",   # Yeşil
            "ctrl": "#E84545",     # Kırmızı
            "alt": "#3B7DD8",      # Mavi
            "shift": "#F0D151",    # Sarı
        }
        
        # === Sürükle-Bırak (Drag & Drop) Sistemi ===
        self._dragging = False
        self._drag_piece: Optional[chess.Piece] = None
        self._drag_from_square: Optional[chess.Square] = None
        self._drag_pos: Optional[Tuple[int, int]] = None  # (x, y) fare pozisyonu
        self._drag_started = False  # Fare hareket etti mi (tıklama vs sürükleme ayrımı)
        
        # Event binding
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        # Sağ tık çizim eventleri
        self.bind("<Button-3>", self._on_right_click_press)
        self.bind("<B3-Motion>", self._on_right_click_drag)
        self.bind("<ButtonRelease-3>", self._on_right_click_release)
        
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
        self._arrows.clear()
        self._highlights.clear()
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
        
        # Kare vurgularını çiz (taşların altında)
        self._draw_highlights()
        
        # Koordinat etiketlerini kare içine çiz (chess.com gibi)
        self._draw_coordinates()
        
        # Taşları çiz (sürüklenen taş hariç)
        for square in chess.SQUARES:
            # Sürüklenen taşı kendi karesinde çizme
            if self._dragging and square == self._drag_from_square:
                continue
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(square, piece)
        
        # İpucu okunu çiz
        if self.hint_move:
            self._draw_hint_arrow(self.hint_move)
        
        # Kullanıcı oklarını çiz (taşların üstünde)
        self._draw_user_arrows()
        
        # Çizim önizlemesi (sağ tık sürükleme sırasında)
        if self._drawing and self._draw_start_square is not None and self._draw_preview_end:
            self._draw_preview_arrow()
        
        # Sürüklenen taşı fare pozisyonunda çiz (en üst katman)
        if self._dragging and self._drag_piece and self._drag_pos:
            self._draw_dragged_piece()
    
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
        """İpucu okunu PIL ile çiz (temiz, yarı-saydam)"""
        overlay = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        self._draw_arrow_on_pil(draw, move.from_square, move.to_square, 
                                 "#15781B", alpha=200)
        
        photo = ImageTk.PhotoImage(overlay)
        self.create_image(0, 0, image=photo, anchor="nw", tags="hint_arrow")
        self._piece_refs.append(photo)
    
    def _on_press(self, event):
        """Sol tık basıldı — taş seçimi veya sürükleme başlat"""
        # Çizimleri temizle
        if self._arrows or self._highlights:
            self._arrows.clear()
            self._highlights.clear()
            self.draw_board()
        
        if not self.interactive:
            return
        
        # Tahta dışı kontrolü
        if event.x < 0 or event.y < 0 or event.x >= self.size or event.y >= self.size:
            return
        
        col = event.x // self.square_size
        row = event.y // self.square_size
        if col < 0 or col > 7 or row < 0 or row > 7:
            return
        
        if self.flipped:
            square = chess.square(7 - col, row)
        else:
            square = chess.square(col, 7 - row)
        
        # Edit mode click handling
        if self.edit_mode:
            if self.on_square_click:
                handled = self.on_square_click(square)
                if handled:
                    self.draw_board()
                    return
            
            piece = self.board.piece_at(square)
            if piece:
                self._dragging = True
                self._drag_piece = piece
                self._drag_from_square = square
                self._drag_pos = (event.x, event.y)
                self._drag_started = False
                self.draw_board()
            return
            
        # Önce: Önceden seçili taş var ve geçerli kareye tıklandıysa hamle yap (tıklama modu)
        if self.selected_square is not None and self.selected_square != square:
            for move in self.legal_moves:
                if move.to_square == square:
                    if self._needs_promotion(self.selected_square, square):
                        if self.on_promotion_needed:
                            self.on_promotion_needed(self.selected_square, square)
                        return
                    self._make_move(move)
                    return
        
        # Taş seçimi ve sürükleme başlat
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.selected_square = square
            self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
            
            # Sürükleme hazırlığı
            self._dragging = True
            self._drag_piece = piece
            self._drag_from_square = square
            self._drag_pos = (event.x, event.y)
            self._drag_started = False  # Henüz hareket etmedi
            
            self.draw_board()
        else:
            self.selected_square = None
            self.legal_moves = []
            self._dragging = False
            self._drag_piece = None
            self._drag_from_square = None
            self.draw_board()
    
    def _on_drag(self, event):
        """Sol tık sürükleme — taşı fareyle taşı"""
        if not self._dragging or not self._drag_piece:
            return
        
        self._drag_started = True
        self._drag_pos = (event.x, event.y)
        self.draw_board()
    
    def _on_release(self, event):
        """Sol tık bırakıldı — taşı yerleştir veya geri al"""
        if not self._dragging or not self._drag_piece:
            return
        
        # Sürükleme başlamadıysa (sadece tıklama), taş seçimini koru
        if not self._drag_started:
            self._dragging = False
            self._drag_piece = None
            self._drag_pos = None
            # Seçim zaten _on_press'te yapıldı, tahtayı yeniden çiz
            self.draw_board()
            return
        
        # Bırakılan kareyi hesapla
        col = event.x // self.square_size
        row = event.y // self.square_size
        from_sq = self._drag_from_square
        
        if self.edit_mode:
            # Edit mode'da tahta dışına bırakılırsa sil, geçerli kareye bırakılırsa taşı
            if col < 0 or col > 7 or row < 0 or row > 7:
                self.board.remove_piece_at(from_sq)
            else:
                if self.flipped:
                    to_sq = chess.square(7 - col, row)
                else:
                    to_sq = chess.square(col, 7 - row)
                
                if to_sq != from_sq:
                    self.board.remove_piece_at(from_sq)
                    self.board.set_piece_at(to_sq, self._drag_piece)
            
            self._dragging = False
            self._drag_piece = None
            self._drag_from_square = None
            self._drag_pos = None
            
            self.draw_board()
            if self.on_board_changed:
                self.on_board_changed()
            return
            
        # Normal oyun modu sürükleme bırakma
        self._dragging = False
        self._drag_piece = None
        self._drag_from_square = None
        self._drag_pos = None
        
        # Tahta sınırları kontrolü
        if col < 0 or col > 7 or row < 0 or row > 7:
            self.draw_board()
            return
        
        if self.flipped:
            to_sq = chess.square(7 - col, row)
        else:
            to_sq = chess.square(col, 7 - row)
        
        # Aynı kareye bırakıldıysa — taş seçimini koru (tıklama modu)
        if to_sq == from_sq:
            self.draw_board()
            return
        
        # Geçerli hamle mi kontrol et
        valid_move = None
        for move in self.legal_moves:
            if move.from_square == from_sq and move.to_square == to_sq:
                valid_move = move
                break
        
        if valid_move:
            # Terfi kontrolü
            if self._needs_promotion(from_sq, to_sq):
                if self.on_promotion_needed:
                    self.on_promotion_needed(from_sq, to_sq)
                else:
                    self.draw_board()
                return
            
            self._make_move(valid_move)
        else:
            # Geçersiz hamle — taş geri döner
            self.selected_square = None
            self.legal_moves = []
            self.draw_board()
    
    def _draw_dragged_piece(self):
        """Sürüklenen taşı fare pozisyonunda çiz (büyütülmüş)"""
        if not self._drag_piece or not self._drag_pos:
            return
        
        x, y = self._drag_pos
        
        # PNG resim (biraz büyütülmüş — Chess.com efekti)
        piece_key = self.theme.get_piece_key(self._drag_piece)
        piece_size = int(self.square_size * 0.98)
        photo = self.theme.get_piece_image(piece_key, piece_size)
        
        if photo:
            self.create_image(x, y, image=photo, anchor="center", tags="drag_piece")
            self._piece_refs.append(photo)
        else:
            # Unicode fallback
            symbol = self._drag_piece.symbol()
            unicode_piece = PIECE_UNICODE.get(symbol, "?")
            text_color = "#FFFFFF" if self._drag_piece.color == chess.WHITE else "#000000"
            
            drag_font_size = int(self.piece_font_size * 1.1)
            
            # Gölge
            self.create_text(
                x + 3, y + 3,
                text=unicode_piece,
                font=("Segoe UI Symbol", drag_font_size),
                fill="#444444",
                tags="drag_piece"
            )
            self.create_text(
                x, y,
                text=unicode_piece,
                font=("Segoe UI Symbol", drag_font_size),
                fill=text_color,
                tags="drag_piece"
            )
    
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
            self._arrows.clear()
            self._highlights.clear()
            self.draw_board()
    
    def push_move(self, move: chess.Move):
        """Dışarıdan hamle yap (bot için)"""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self.legal_moves = []
            self._arrows.clear()
            self._highlights.clear()
            self.draw_board()
    
    def get_square_at(self, x: int, y: int) -> chess.Square:
        """Koordinattan kare hesapla"""
        col = x // self.square_size
        row = y // self.square_size
        
        if self.flipped:
            return chess.square(7 - col, row)
        else:
            return chess.square(col, 7 - row)
    
    # ==================== Çizim / Annotasyon Sistemi ====================
    
    def _get_annotation_color(self, event) -> str:
        """Modifier tuşlarına göre çizim rengini belirle"""
        if event.state & 0x4:   # Ctrl
            return self._annotation_colors["ctrl"]
        elif event.state & 0x20000 or event.state & 0x8:  # Alt
            return self._annotation_colors["alt"]
        elif event.state & 0x1:  # Shift
            return self._annotation_colors["shift"]
        return self._annotation_colors["default"]
    
    def _on_right_click_press(self, event):
        """Sağ tık basıldı — çizim başlat"""
        if event.x < 0 or event.y < 0 or event.x >= self.size or event.y >= self.size:
            return
        
        col = event.x // self.square_size
        row = event.y // self.square_size
        if col < 0 or col > 7 or row < 0 or row > 7:
            return
        
        if self.flipped:
            square = chess.square(7 - col, row)
        else:
            square = chess.square(col, 7 - row)
        
        self._drawing = True
        self._draw_start_square = square
        self._draw_preview_end = None
        self._draw_color = self._get_annotation_color(event)
    
    def _on_right_click_drag(self, event):
        """Sağ tık sürükleme — ok önizlemesi"""
        if not self._drawing or self._draw_start_square is None:
            return
        
        # Rengi güncelle (kullanıcı sürükleme sırasında modifier tuşu değiştirebilir)
        self._draw_color = self._get_annotation_color(event)
        self._draw_preview_end = (event.x, event.y)
        self.draw_board()
    
    def _on_right_click_release(self, event):
        """Sağ tık bırakıldı — çizimi tamamla"""
        if not self._drawing or self._draw_start_square is None:
            self._drawing = False
            return
        
        # Bitiş karesini hesapla
        col = max(0, min(7, event.x // self.square_size))
        row = max(0, min(7, event.y // self.square_size))
        
        if self.flipped:
            end_square = chess.square(7 - col, row)
        else:
            end_square = chess.square(col, 7 - row)
        
        color = self._get_annotation_color(event)
        
        if end_square == self._draw_start_square:
            # Aynı kareye tıklandı → kare vurgusu toggle
            if self._draw_start_square in self._highlights:
                # Aynı renk ise kaldır, farklı renk ise değiştir
                if self._highlights[self._draw_start_square] == color:
                    del self._highlights[self._draw_start_square]
                else:
                    self._highlights[self._draw_start_square] = color
            else:
                self._highlights[self._draw_start_square] = color
        else:
            # Farklı kare → ok çiz (toggle)
            arrow_key = (self._draw_start_square, end_square)
            if arrow_key in self._arrows:
                if self._arrows[arrow_key] == color:
                    del self._arrows[arrow_key]
                else:
                    self._arrows[arrow_key] = color
            else:
                self._arrows[arrow_key] = color
        
        self._drawing = False
        self._draw_start_square = None
        self._draw_preview_end = None
        self.draw_board()
    
    def _square_to_pixel_center(self, square: int) -> Tuple[int, int]:
        """Kare numarasından piksel merkezini hesapla"""
        col = chess.square_file(square)
        row = chess.square_rank(square)
        
        if self.flipped:
            px = (7 - col) * self.square_size + self.square_size // 2
            py = row * self.square_size + self.square_size // 2
        else:
            px = col * self.square_size + self.square_size // 2
            py = (7 - row) * self.square_size + self.square_size // 2
        
        return (px, py)
    
    def _hex_to_rgba(self, hex_color: str, alpha: int = 180) -> Tuple[int, int, int, int]:
        """Hex rengi RGBA tuple'a çevir"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)
    
    def _draw_highlights(self):
        """Vurgulanan kareleri PIL ile yarı-saydam çiz"""
        if not self._highlights:
            return
        
        for square, color in self._highlights.items():
            col = chess.square_file(square)
            row = chess.square_rank(square)
            
            if self.flipped:
                display_col = 7 - col
                display_row = row
            else:
                display_col = col
                display_row = 7 - row
            
            x1 = display_col * self.square_size
            y1 = display_row * self.square_size
            sq_size = self.square_size
            
            # PIL ile yarı-saydam kare oluştur
            overlay = Image.new("RGBA", (sq_size, sq_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            rgba = self._hex_to_rgba(color, alpha=140)
            draw.rectangle([0, 0, sq_size, sq_size], fill=rgba)
            
            # Arka plan rengini al (karenin orijinal rengi)
            is_light = (row + col) % 2 == 1
            bg_hex = self.theme.board_light if is_light else self.theme.board_dark
            bg_rgb = self._hex_to_rgba(bg_hex, 255)[:3]
            
            # Arka planla birleştir
            bg_img = Image.new("RGBA", (sq_size, sq_size), (*bg_rgb, 255))
            composited = Image.alpha_composite(bg_img, overlay)
            
            photo = ImageTk.PhotoImage(composited)
            self.create_image(x1, y1, image=photo, anchor="nw", tags="annotation")
            self._piece_refs.append(photo)
    
    def _draw_user_arrows(self):
        """Kullanıcının çizdiği okları PIL overlay ile render et"""
        if not self._arrows:
            return
        
        # Tüm okları tek bir şeffaf katmanda çiz
        overlay = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for (from_sq, to_sq), color in self._arrows.items():
            self._draw_arrow_on_pil(draw, from_sq, to_sq, color, alpha=200)
        
        photo = ImageTk.PhotoImage(overlay)
        self.create_image(0, 0, image=photo, anchor="nw", tags="user_arrow")
        self._piece_refs.append(photo)
    
    def _draw_arrow_on_pil(self, draw: ImageDraw.Draw, from_sq: int, to_sq: int, 
                            color: str, alpha: int = 200):
        """PIL ImageDraw üzerinde temiz ok çiz"""
        fx, fy = self._square_to_pixel_center(from_sq)
        tx, ty = self._square_to_pixel_center(to_sq)
        
        rgba = self._hex_to_rgba(color, alpha)
        
        # Ok boyutları
        line_width = max(10, int(self.square_size * 0.30))
        head_length = max(18, int(self.square_size * 0.45))
        head_width = max(14, int(self.square_size * 0.55))
        
        # Yön vektörü
        dx = tx - fx
        dy = ty - fy
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return
        
        ux = dx / length
        uy = dy / length
        
        # Dik vektör
        perp_x = -uy
        perp_y = ux
        
        # Başlangıç dairesi
        circle_r = max(8, int(self.square_size * 0.20))
        draw.ellipse(
            [fx - circle_r, fy - circle_r, fx + circle_r, fy + circle_r],
            fill=rgba
        )
        
        # Ok gövdesi (kalın dikdörtgen olarak çiz — daha temiz)
        half_w = line_width / 2
        
        # Gövde başlangıç ve bitiş (ok başının tabanına kadar)
        body_end_x = tx - ux * head_length
        body_end_y = ty - uy * head_length
        
        # Gövde köşeleri (4 köşe dikdörtgen)
        body_points = [
            (fx + perp_x * half_w, fy + perp_y * half_w),
            (body_end_x + perp_x * half_w, body_end_y + perp_y * half_w),
            (body_end_x - perp_x * half_w, body_end_y - perp_y * half_w),
            (fx - perp_x * half_w, fy - perp_y * half_w),
        ]
        draw.polygon(body_points, fill=rgba)
        
        # Ok başı (üçgen)
        tip_x = tx
        tip_y = ty
        
        base_x = tx - ux * head_length
        base_y = ty - uy * head_length
        
        head_points = [
            (tip_x, tip_y),
            (base_x + perp_x * head_width / 2, base_y + perp_y * head_width / 2),
            (base_x - perp_x * head_width / 2, base_y - perp_y * head_width / 2),
        ]
        draw.polygon(head_points, fill=rgba)
    
    def _draw_preview_arrow(self):
        """Sürükleme sırasında ok önizlemesi çiz (PIL ile)"""
        if self._draw_start_square is None or self._draw_preview_end is None:
            return
        
        fx, fy = self._square_to_pixel_center(self._draw_start_square)
        tx, ty = self._draw_preview_end
        
        tx = max(0, min(self.size - 1, tx))
        ty = max(0, min(self.size - 1, ty))
        
        dx = tx - fx
        dy = ty - fy
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < self.square_size * 0.4:
            # Çok yakın — kare vurgusu önizlemesi (PIL ile)
            col = chess.square_file(self._draw_start_square)
            row = chess.square_rank(self._draw_start_square)
            if self.flipped:
                dc = 7 - col
                dr = row
            else:
                dc = col
                dr = 7 - row
            
            x1 = dc * self.square_size
            y1 = dr * self.square_size
            sq_size = self.square_size
            
            is_light = (row + col) % 2 == 1
            bg_hex = self.theme.board_light if is_light else self.theme.board_dark
            bg_rgb = self._hex_to_rgba(bg_hex, 255)[:3]
            
            overlay = Image.new("RGBA", (sq_size, sq_size), (0, 0, 0, 0))
            d = ImageDraw.Draw(overlay)
            rgba = self._hex_to_rgba(self._draw_color, alpha=140)
            d.rectangle([0, 0, sq_size, sq_size], fill=rgba)
            
            bg_img = Image.new("RGBA", (sq_size, sq_size), (*bg_rgb, 255))
            composited = Image.alpha_composite(bg_img, overlay)
            
            photo = ImageTk.PhotoImage(composited)
            self.create_image(x1, y1, image=photo, anchor="nw", tags="preview")
            self._piece_refs.append(photo)
            return
        
        # Ok önizlemesi — snap to grid
        snap_col = max(0, min(7, tx // self.square_size))
        snap_row = max(0, min(7, ty // self.square_size))
        
        if self.flipped:
            end_sq = chess.square(7 - snap_col, snap_row)
        else:
            end_sq = chess.square(snap_col, 7 - snap_row)
        
        if end_sq != self._draw_start_square:
            overlay = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            self._draw_arrow_on_pil(draw, self._draw_start_square, end_sq, 
                                     self._draw_color, alpha=160)
            
            photo = ImageTk.PhotoImage(overlay)
            self.create_image(0, 0, image=photo, anchor="nw", tags="preview")
            self._piece_refs.append(photo)
    
    def clear_annotations(self):
        """Tüm çizimleri temizle"""
        self._arrows.clear()
        self._highlights.clear()
        self.draw_board()
    
    def add_arrow(self, from_sq: int, to_sq: int, color: str = "#15781B"):
        """Programatik olarak ok ekle"""
        self._arrows[(from_sq, to_sq)] = color
        self.draw_board()
    
    def add_highlight(self, square: int, color: str = "#15781B"):
        """Programatik olarak kare vurgusu ekle"""
        self._highlights[square] = color
        self.draw_board()
