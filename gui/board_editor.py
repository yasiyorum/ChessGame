"""
Tahta Düzenleyici Ekranı (Position Setup) - Chess.com Tarzı
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable
import sys
import os
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME, PIECE_UNICODE
from theme_manager import ThemeManager
from .chess_board import ChessBoard


class BoardEditorScreen(ctk.CTkFrame):
    """Satranç tahtası düzenleyicisi (Position Setup)"""
    
    def __init__(self, parent, on_back: Optional[Callable] = None, on_analyze: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_back = on_back
        self.on_analyze = on_analyze
        self.configure(fg_color=THEME["bg_primary"])
        
        self.theme = ThemeManager.get_instance()
        self.selected_palette_item = None  # None = seçili yok, 'trash' = silici, veya chess.Piece
        
        self._setup_ui()
        self._update_fen()

    def _setup_ui(self):
        """UI oluştur"""
        # Üst bar
        self._setup_header()
        
        # Ana içerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        # Sol panel (Tahta)
        self._setup_left_panel(content)
        
        # Sağ panel (Palet ve Ayarlar)
        self._setup_right_panel(content)

    def _setup_header(self):
        """Üst bar"""
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], height=44, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
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
        
        ctk.CTkLabel(
            header,
            text="✏️ Tahta Düzenleyici",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(side="left", padx=15)
        
    def _on_back_click(self):
        if self.on_back:
            self.on_back()

    def _setup_left_panel(self, parent):
        """Sol panel (Tahta)"""
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        board_container = ctk.CTkFrame(left_frame, fg_color=THEME["bg_secondary"], corner_radius=4)
        board_container.pack(fill="both", expand=True)
        
        self.chess_board = ChessBoard(
            board_container,
            size=480,
            edit_mode=True,
            on_board_changed=self._on_board_changed,
            on_square_click=self._on_square_click
        )
        self.chess_board.place(relx=0.5, rely=0.5, anchor="center")
        board_container.bind("<Configure>", self._on_board_container_resize)

    def _on_board_container_resize(self, event):
        """Tahta boyutu değiştiğinde"""
        available_size = min(event.width, event.height) - 16
        if available_size < 320:
            available_size = 320
        
        new_size = (available_size // 8) * 8
        if abs(new_size - self.chess_board.size) > 16:
            self.chess_board.size = new_size
            self.chess_board.total_size = new_size
            self.chess_board.square_size = new_size // 8
            self.chess_board.piece_font_size = int(self.chess_board.square_size * 0.75)
            self.chess_board.configure(width=new_size, height=new_size)
            self.chess_board.draw_board()

    def _setup_right_panel(self, parent):
        """Sağ panel (Palet, FEN, Ayarlar)"""
        right_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], 
                                    corner_radius=8, width=350,
                                    border_width=1, border_color=THEME["panel_border"])
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)
        
        # Palet başlığı
        ctk.CTkLabel(
            right_frame,
            text="Taş Paleti",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.palette_buttons = []
        
        # Siyah Taşlar
        black_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        black_frame.pack(fill="x", padx=15, pady=5)
        self._add_palette_pieces(black_frame, chess.BLACK)
        
        # Beyaz Taşlar
        white_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        white_frame.pack(fill="x", padx=15, pady=5)
        self._add_palette_pieces(white_frame, chess.WHITE)
        
        # Kontroller (Çöp Kutusu vs)
        control_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=15, pady=5)
        
        self.trash_btn = ctk.CTkButton(
            control_frame, text="🗑️ Silici", width=80, height=36,
            fg_color=THEME["bg_tertiary"], hover_color=THEME["button_hover"],
            text_color=THEME["text_secondary"],
            command=lambda: self._select_palette_item('trash')
        )
        self.trash_btn.pack(side="left", padx=2)
        self.palette_buttons.append(('trash', self.trash_btn))
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x", pady=15)
        
        # Tahta kontrolleri
        board_ctrl_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        board_ctrl_frame.pack(fill="x", padx=15)
        
        ctk.CTkButton(
            board_ctrl_frame, text="Başlangıç Dizilimi",
            fg_color=THEME["button_bg"], hover_color=THEME["button_hover"],
            command=self._set_starting_position
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            board_ctrl_frame, text="Tahtayı Temizle",
            fg_color=THEME["button_bg"], hover_color=THEME["button_hover"],
            command=self._clear_board
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x", pady=15)
        
        # Detaylı Ayarlar (Sıra kimde, Rok vb.)
        settings_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=15)
        
        # Hamle sırası
        ctk.CTkLabel(settings_frame, text="Sıra Kimde:", text_color=THEME["text_secondary"]).pack(anchor="w")
        self.turn_var = ctk.StringVar(value="Beyaz")
        turn_combo = ctk.CTkSegmentedButton(
            settings_frame, values=["Beyaz", "Siyah"],
            variable=self.turn_var,
            command=self._on_turn_change
        )
        turn_combo.pack(fill="x", pady=(5, 15))
        turn_combo.set("Beyaz")
        
        # Rok Hakları
        ctk.CTkLabel(settings_frame, text="Rok Hakları:", text_color=THEME["text_secondary"]).pack(anchor="w")
        castling_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        castling_frame.pack(fill="x", pady=(5, 15))
        
        self.castle_vars = {
            "K": ctk.BooleanVar(value=True),
            "Q": ctk.BooleanVar(value=True),
            "k": ctk.BooleanVar(value=True),
            "q": ctk.BooleanVar(value=True)
        }
        
        col1 = ctk.CTkFrame(castling_frame, fg_color="transparent")
        col1.pack(side="left", expand=True)
        ctk.CTkCheckBox(col1, text="Beyaz O-O", variable=self.castle_vars["K"], command=self._update_fen).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(col1, text="Beyaz O-O-O", variable=self.castle_vars["Q"], command=self._update_fen).pack(anchor="w", pady=2)
        
        col2 = ctk.CTkFrame(castling_frame, fg_color="transparent")
        col2.pack(side="left", expand=True)
        ctk.CTkCheckBox(col2, text="Siyah O-O", variable=self.castle_vars["k"], command=self._update_fen).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(col2, text="Siyah O-O-O", variable=self.castle_vars["q"], command=self._update_fen).pack(anchor="w", pady=2)
        
        # FEN Input
        ctk.CTkLabel(right_frame, text="FEN Dizgesi:", text_color=THEME["text_secondary"]).pack(anchor="w", padx=15)
        self.fen_entry = ctk.CTkEntry(right_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.fen_entry.pack(fill="x", padx=15, pady=5)
        self.fen_entry.bind("<Return>", self._on_fen_entered)
        self.fen_entry.bind("<FocusOut>", self._on_fen_entered)
        
        # Alt Boşluk ve Analiz Butonu
        ctk.CTkFrame(right_frame, fg_color="transparent").pack(fill="both", expand=True)
        
        self.analyze_btn = ctk.CTkButton(
            right_frame,
            text="🔍 Analiz Et",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._analyze_position,
            height=45
        )
        self.analyze_btn.pack(fill="x", padx=15, pady=15)

    def _add_palette_pieces(self, parent, color):
        """Palete taş butonlarını ekle"""
        pieces = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
        
        for p_type in pieces:
            piece = chess.Piece(p_type, color)
            
            # Text based symbol
            symbol = PIECE_UNICODE.get(piece.symbol(), "?")
            text_color = "#FFFFFF" if color == chess.WHITE else "#000000"
            
            btn = ctk.CTkButton(
                parent, text=symbol, font=ctk.CTkFont(size=24),
                width=40, height=40,
                fg_color=THEME["bg_tertiary"], hover_color=THEME["button_hover"],
                text_color=text_color,
                command=lambda p=piece: self._select_palette_item(p)
            )
            btn.pack(side="left", padx=2)
            self.palette_buttons.append((piece, btn))

    def _select_palette_item(self, item):
        """Palette bir seçim yapıldığında"""
        self.selected_palette_item = item
        
        # Seçili butonu vurgula
        for p, btn in self.palette_buttons:
            if p == item:
                btn.configure(fg_color=THEME["button_hover"])
            else:
                btn.configure(fg_color=THEME["bg_tertiary"])

    def _on_square_click(self, square: chess.Square) -> bool:
        """Kareye tıklandığında paletten taş yerleştir veya sil"""
        if self.selected_palette_item is None:
            return False  # Drag & drop normal çalışsın
            
        if self.selected_palette_item == 'trash':
            self.chess_board.board.remove_piece_at(square)
        else:
            self.chess_board.board.set_piece_at(square, self.selected_palette_item)
            
        self._on_board_changed()
        return True  # Olayı biz işledik, sürükleme başlatma

    def _on_board_changed(self):
        """Tahta sürüklendiğinde FEN'i güncelle"""
        self._update_fen()

    def _set_starting_position(self):
        """Başlangıç pozisyonunu kur"""
        self.chess_board.board.set_fen(chess.STARTING_FEN)
        self.chess_board.draw_board()
        self.turn_var.set("Beyaz")
        for k in self.castle_vars:
            self.castle_vars[k].set(True)
        self._update_fen()

    def _clear_board(self):
        """Tahtayı temizle"""
        self.chess_board.board.clear_board()
        self.chess_board.draw_board()
        for k in self.castle_vars:
            self.castle_vars[k].set(False)
        self._update_fen()

    def _on_turn_change(self, value):
        self._update_fen()

    def _update_fen(self, *args):
        """UI'daki ayarlara göre FEN üretip textbox'a yaz"""
        # Tahtadaki taşlar
        fen = self.chess_board.board.board_fen()
        
        # Hamle sırası
        turn = 'w' if self.turn_var.get() == "Beyaz" else 'b'
        
        # Rok Hakları
        castling = ""
        if self.castle_vars["K"].get(): castling += "K"
        if self.castle_vars["Q"].get(): castling += "Q"
        if self.castle_vars["k"].get(): castling += "k"
        if self.castle_vars["q"].get(): castling += "q"
        if not castling: castling = "-"
        
        # En passant vs standart - şimdilik yok
        full_fen = f"{fen} {turn} {castling} - 0 1"
        
        # Engine tahtasını güncelle
        try:
            self.chess_board.board.set_fen(full_fen)
        except ValueError:
            pass # Geçersiz rok hakları falan olabilir (örneğin şah yokken rok)
            
        # Entry güncelle
        self.fen_entry.delete(0, "end")
        self.fen_entry.insert(0, full_fen)

    def _on_fen_entered(self, event=None):
        """FEN textbox'ına girildiğinde tahtayı güncelle"""
        fen = self.fen_entry.get()
        try:
            self.chess_board.board.set_fen(fen)
            self.chess_board.draw_board()
            
            # UI güncellemeleri
            turn = fen.split()[1]
            self.turn_var.set("Beyaz" if turn == 'w' else "Siyah")
            
            castling = fen.split()[2]
            for k in self.castle_vars:
                self.castle_vars[k].set(k in castling)
                
        except ValueError:
            pass # Hatalı FEN

    def _analyze_position(self):
        """Analiz ekranına geçiş"""
        if self.on_analyze:
            fen = self.fen_entry.get()
            self.on_analyze(fen)
