"""
Hamle Listesi Widget'ı - Chess.com Tarzı
"""
import customtkinter as ctk
from typing import List, Dict, Optional, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import MOVE_COLORS, MOVE_SYMBOLS, THEME


class MoveList(ctk.CTkScrollableFrame):
    """Chess.com tarzı hamle listesi"""
    
    def __init__(self, parent, on_move_click: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_move_click = on_move_click
        self.moves: List[Dict] = []
        self.move_labels: List[ctk.CTkLabel] = []
        self.row_frames: List[ctk.CTkFrame] = []
        self.current_index = -1
        
        self.configure(fg_color=THEME["move_list_bg"])
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=28)
        header.pack(fill="x", padx=8, pady=(6, 2))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="Hamleler",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_muted"]
        ).pack(side="left")
        
        self.moves_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.moves_frame.pack(fill="both", expand=True, padx=4)
        
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
        """Tüm hamleleri ayarla"""
        self.moves = moves
        self._render_moves()
    
    def clear(self):
        """Hamle listesini temizle"""
        self.moves = []
        self.move_labels = []
        self.row_frames = []
        self.current_index = -1
        
        for widget in self.moves_frame.winfo_children():
            widget.destroy()
    
    def remove_last_move(self):
        """Son hamleyi kaldır"""
        if self.moves:
            self.moves.pop()
            self._render_moves()
    
    def _render_moves(self):
        """Hamleleri chess.com tarzında render et"""
        for widget in self.moves_frame.winfo_children():
            widget.destroy()
        self.move_labels = []
        self.row_frames = []
        
        row_frame = None
        
        for i, move in enumerate(self.moves):
            # Her 2 hamlede bir yeni satır
            if i % 2 == 0:
                row_frame = ctk.CTkFrame(
                    self.moves_frame, 
                    fg_color="transparent" if (i // 2) % 2 == 0 else THEME["bg_tertiary"],
                    corner_radius=0,
                    height=28
                )
                row_frame.pack(fill="x", pady=0)
                row_frame.pack_propagate(False)
                self.row_frames.append(row_frame)
                
                # Hamle numarası
                move_num = (i // 2) + 1
                num_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{move_num}.",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=THEME["text_muted"],
                    width=32,
                    anchor="e"
                )
                num_label.pack(side="left", padx=(4, 4))
            
            # Hamle etiketi
            classification = move.get("classification", "normal")
            color = MOVE_COLORS.get(classification, THEME["text_secondary"])
            symbol = MOVE_SYMBOLS.get(classification, "")
            
            san = move.get("san", "")
            display_text = f"{san}"
            if symbol and classification not in ("normal", "good"):
                display_text = f"{san} {symbol}"
            
            # Arka plan renkli gösterge (chess.com tarzı)
            move_frame = ctk.CTkFrame(row_frame, fg_color="transparent", corner_radius=4)
            move_frame.pack(side="left", padx=2, fill="y")
            
            # Sınıflandırma renk çizgisi (sol kenar)
            if classification not in ("normal", "good", "best"):
                indicator = ctk.CTkFrame(
                    move_frame, 
                    fg_color=color, 
                    width=3, 
                    corner_radius=1
                )
                indicator.pack(side="left", fill="y", padx=(0, 2))
            
            label = ctk.CTkLabel(
                move_frame,
                text=display_text,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color,
                width=70,
                anchor="w",
                cursor="hand2"
            )
            label.pack(side="left", padx=4, pady=2)
            
            # Tıklama ve hover eventleri
            move_index = i
            label.bind("<Button-1>", lambda e, idx=move_index: self._on_click(idx))
            
            def on_enter(e, mf=move_frame):
                mf.configure(fg_color=THEME["move_list_hover"])
            def on_leave(e, mf=move_frame):
                mf.configure(fg_color="transparent")
            
            label.bind("<Enter>", on_enter)
            label.bind("<Leave>", on_leave)
            move_frame.bind("<Enter>", on_enter)
            move_frame.bind("<Leave>", on_leave)
            move_frame.bind("<Button-1>", lambda e, idx=move_index: self._on_click(idx))
            
            self.move_labels.append((label, move_frame))
        
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
        
        for i, (label, move_frame) in enumerate(self.move_labels):
            if i == index:
                move_frame.configure(fg_color=THEME["move_list_selected"])
            else:
                move_frame.configure(fg_color="transparent")
    
    def _scroll_to_bottom(self):
        """En alta kaydır"""
        try:
            self._parent_canvas.yview_moveto(1.0)
        except:
            pass
    
    def get_moves_text(self) -> str:
        """Hamleleri PGN formatında döndür"""
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
