"""
Hamle Listesi Widget'ı
"""
import customtkinter as ctk
from typing import List, Dict, Optional, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import MOVE_COLORS, MOVE_SYMBOLS


class MoveList(ctk.CTkScrollableFrame):
    """Hamle listesi widget'ı - Chess.com tarzı"""
    
    def __init__(self, parent, on_move_click: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_move_click = on_move_click
        self.moves: List[Dict] = []
        self.move_labels: List[ctk.CTkLabel] = []
        self.current_index = -1
        
        self.configure(fg_color="#262421")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text="Hamleler",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#B0B0B0"
        ).pack(side="left")
        
        self.moves_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.moves_frame.pack(fill="both", expand=True, padx=5)
        
    def add_move(self, san: str, classification: str = "normal"):
        """Hamle ekle"""
        move_data = {
            "san": san,
            "classification": classification,
            "index": len(self.moves)
        }
        self.moves.append(move_data)
        
        # Görsel güncelle
        self._render_moves()
        
        # Son hamleyi görünür yap
        self.after(10, self._scroll_to_bottom)
    
    def set_moves(self, moves: List[Dict]):
        """Tüm hamleleri ayarla (analiz için)"""
        self.moves = moves
        self._render_moves()
    
    def clear(self):
        """Hamle listesini temizle"""
        self.moves = []
        self.move_labels = []
        self.current_index = -1
        
        for widget in self.moves_frame.winfo_children():
            widget.destroy()
    
    def _render_moves(self):
        """Hamleleri render et"""
        # Mevcut widget'ları temizle
        for widget in self.moves_frame.winfo_children():
            widget.destroy()
        self.move_labels = []
        
        # Satır satır hamleler
        row_frame = None
        
        for i, move in enumerate(self.moves):
            # Yeni satır (her 2 hamlede bir)
            if i % 2 == 0:
                row_frame = ctk.CTkFrame(self.moves_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                
                # Hamle numarası
                move_num = (i // 2) + 1
                num_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{move_num}.",
                    font=ctk.CTkFont(size=13),
                    text_color="#808080",
                    width=30
                )
                num_label.pack(side="left", padx=(5, 5))
            
            # Hamle etiketi
            classification = move.get("classification", "normal")
            color = MOVE_COLORS.get(classification, "#D0D0D0")
            symbol = MOVE_SYMBOLS.get(classification, "")
            
            san = move.get("san", "")
            display_text = f"{san}{symbol}"
            
            label = ctk.CTkLabel(
                row_frame,
                text=display_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color,
                width=70,
                cursor="hand2"
            )
            label.pack(side="left", padx=5)
            
            # Tıklama eventi
            move_index = i
            label.bind("<Button-1>", lambda e, idx=move_index: self._on_click(idx))
            label.bind("<Enter>", lambda e, lbl=label: lbl.configure(fg_color="#3D3A37"))
            label.bind("<Leave>", lambda e, lbl=label: lbl.configure(fg_color="transparent"))
            
            self.move_labels.append(label)
        
        # Mevcut hamleyi vurgula
        self.highlight_move(self.current_index)
    
    def _on_click(self, index: int):
        """Hamle tıklandığında"""
        self.highlight_move(index)
        if self.on_move_click:
            self.on_move_click(index)
    
    def highlight_move(self, index: int):
        """Hamleyi vurgula"""
        self.current_index = index
        
        for i, label in enumerate(self.move_labels):
            if i == index:
                label.configure(fg_color="#4A4745")
            else:
                label.configure(fg_color="transparent")
    
    def _scroll_to_bottom(self):
        """En alta kaydır"""
        self._parent_canvas.yview_moveto(1.0)
    
    def get_moves_text(self) -> str:
        """Hamleleri metin olarak döndür (PGN format)"""
        lines = []
        
        for i in range(0, len(self.moves), 2):
            move_num = (i // 2) + 1
            white_move = self.moves[i].get("san", "")
            
            if i + 1 < len(self.moves):
                black_move = self.moves[i + 1].get("san", "")
                lines.append(f"{move_num}. {white_move} {black_move}")
            else:
                lines.append(f"{move_num}. {white_move}")
        
        return " ".join(lines)
