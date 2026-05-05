"""
Değerlendirme Çubuğu - Chess.com Tarzı Dikey Eval Bar
"""
import customtkinter as ctk
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import THEME


class EvalBar(ctk.CTkCanvas):
    """Chess.com tarzı dikey değerlendirme çubuğu"""
    
    def __init__(self, parent, height: int = 480, width: int = 28, **kwargs):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, bg=THEME["bg_primary"], **kwargs)
        
        self.bar_width = width
        self.bar_height = height
        self.eval_score = 0  # Centipawn (beyaz perspektifinden)
        self.is_mate = False
        self.mate_in = 0
        
        self.draw()
    
    def set_eval(self, cp_score: int, is_mate: bool = False, mate_in: int = 0):
        """Değerlendirmeyi ayarla (beyaz perspektifinden centipawn)"""
        self.eval_score = cp_score
        self.is_mate = is_mate
        self.mate_in = mate_in
        self.draw()
    
    def draw(self):
        """Çubuğu çiz"""
        self.delete("all")
        
        w = self.bar_width
        h = self.bar_height
        
        # Score'u 0-1 arasına normalize et (0.5 = eşit)
        if self.is_mate:
            if self.mate_in > 0:
                white_ratio = 1.0  # Beyaz mat yapıyor
            else:
                white_ratio = 0.0  # Siyah mat yapıyor
        else:
            # Sigmoid fonksiyonu ile normalize
            # chess.com'daki gibi -1000'den +1000'e smooth geçiş
            cp = max(-1000, min(1000, self.eval_score))
            white_ratio = 1.0 / (1.0 + math.exp(-cp / 200.0))
        
        # Beyaz ve siyah bölüm yükseklikleri
        white_height = int(h * white_ratio)
        black_height = h - white_height
        
        # Siyah bölüm (üst)
        if black_height > 0:
            self.create_rectangle(0, 0, w, black_height,
                                fill="#403D39", outline="")
        
        # Beyaz bölüm (alt)
        if white_height > 0:
            self.create_rectangle(0, black_height, w, h,
                                fill="#FFFFFF", outline="")
        
        # Ortadaki çizgi (eşit pozisyon referansı)
        mid_y = h // 2
        self.create_line(0, mid_y, w, mid_y, fill="#8B8987", width=1)
        
        # Eval text
        if self.is_mate:
            if self.mate_in > 0:
                text = f"M{abs(self.mate_in)}"
                text_y = h - 14
                text_color = "#403D39"
            else:
                text = f"M{abs(self.mate_in)}"
                text_y = 14
                text_color = "#FFFFFF"
        else:
            cp = self.eval_score
            if abs(cp) < 10:
                text = "0.0"
            elif cp > 0:
                text = f"+{cp / 100:.1f}"
            else:
                text = f"{cp / 100:.1f}"
            
            # Metni avantajlı tarafın bölümüne koy
            if cp >= 0:
                text_y = h - 14
                text_color = "#403D39"
            else:
                text_y = 14
                text_color = "#FFFFFF"
        
        font_size = max(8, w // 3)
        self.create_text(
            w // 2, text_y,
            text=text,
            font=("Segoe UI", font_size, "bold"),
            fill=text_color,
            anchor="center"
        )
    
    def resize(self, height: int):
        """Yüksekliği güncelle"""
        self.bar_height = height
        self.configure(height=height)
        self.draw()
