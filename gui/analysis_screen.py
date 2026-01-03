"""
Analiz Ekranı
Chess.com tarzı oyun analizi
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable, List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME, MOVE_COLORS

from .chess_board import ChessBoard
from .components.move_list import MoveList
from engine.chess_engine import ChessEngine
from engine.stockfish_manager import StockfishManager


class AnalysisScreen(ctk.CTkFrame):
    """Analiz ekranı"""
    
    def __init__(self, parent, on_back: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_back = on_back
        
        self.configure(fg_color=THEME["bg_primary"])
        
        # Motor
        self.engine = ChessEngine()
        self.stockfish = StockfishManager()
        
        # Analiz durumu
        self.analysis_results: List[Dict] = []
        self.current_move_index = -1
        self.is_analyzing = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        # Üst bar
        self._setup_header()
        
        # Ana içerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol panel (tahta + kontroller)
        self._setup_left_panel(content)
        
        # Sağ panel (PGN input + hamle listesi)
        self._setup_right_panel(content)
    
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
        ctk.CTkLabel(
            header,
            text="📊 Oyun Analizi",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(side="left", padx=20)
        
        # Durum
        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=THEME["text_secondary"]
        )
        self.status_label.pack(side="right", padx=20)
    
    def _setup_left_panel(self, parent):
        """Sol panel (tahta + navigasyon)"""
        left_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], corner_radius=15)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Tahta container
        self.board_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.board_container.pack(fill="both", expand=True, pady=20, padx=20)
        
        # Satranç tahtası
        self.chess_board = ChessBoard(
            self.board_container,
            size=450,
            on_move=None  # Analiz modunda interaktif değil
        )
        self.chess_board.set_interactive(False)
        self.chess_board.place(relx=0.5, rely=0.5, anchor="center")
        
        # Pencere boyutu değiştiğinde tahtayı yeniden boyutlandır
        self.board_container.bind("<Configure>", self._on_board_container_resize)
        
        # Navigasyon butonları
        nav_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        nav_frame.pack(pady=(0, 20))
        
        nav_buttons = [
            ("⏮", self._go_start),
            ("◀", self._go_prev),
            ("▶", self._go_next),
            ("⏭", self._go_end),
        ]
        
        for text, command in nav_buttons:
            ctk.CTkButton(
                nav_frame,
                text=text,
                font=ctk.CTkFont(size=18),
                fg_color=THEME["button_bg"],
                hover_color=THEME["button_hover"],
                command=command,
                width=60,
                height=40
            ).pack(side="left", padx=5)
        
        # Değerlendirme çubuğu
        self.eval_frame = ctk.CTkFrame(left_frame, fg_color="transparent", height=40)
        self.eval_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.eval_label = ctk.CTkLabel(
            self.eval_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.eval_label.pack()
    
    def _on_board_container_resize(self, event):
        """Tahta container'ı yeniden boyutlandırıldığında"""
        # Kare boyutu hesapla (min width/height)
        available_size = min(event.width, event.height) - 40
        
        # Minimum boyut kontrolü
        if available_size < 320:
            available_size = 320
        
        # 8'e bölünebilir olmalı
        new_size = (available_size // 8) * 8
        
        # Sadece önemli değişikliklerde güncelle
        if abs(new_size - self.chess_board.size) > 16:
            self.chess_board.size = new_size
            self.chess_board.total_size = new_size + self.chess_board.COORD_MARGIN
            self.chess_board.square_size = new_size // 8
            self.chess_board.piece_font_size = int(self.chess_board.square_size * 0.8)
            self.chess_board.configure(width=self.chess_board.total_size, height=self.chess_board.total_size)
            self.chess_board.draw_board()
    
    def _setup_right_panel(self, parent):
        """Sağ panel (PGN + analiz sonuçları)"""
        right_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], 
                                   corner_radius=15, width=350)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # PGN Input bölümü
        input_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            input_frame,
            text="PGN veya Hamle Metni Yapıştır:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(10, 5), padx=10, anchor="w")
        
        self.pgn_input = ctk.CTkTextbox(
            input_frame,
            height=80,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=THEME["bg_primary"],
            text_color=THEME["text_primary"]
        )
        self.pgn_input.pack(fill="x", padx=10, pady=(0, 10))
        
        # Depth ayarı
        depth_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        depth_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            depth_frame,
            text="Analiz Derinliği:",
            font=ctk.CTkFont(size=12),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        self.depth_var = ctk.StringVar(value="18")
        self.depth_entry = ctk.CTkEntry(
            depth_frame,
            textvariable=self.depth_var,
            width=50,
            font=ctk.CTkFont(size=12),
            fg_color=THEME["bg_primary"]
        )
        self.depth_entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            depth_frame,
            text="(15-25 önerilir)",
            font=ctk.CTkFont(size=11),
            text_color=THEME["text_secondary"]
        ).pack(side="left")
        
        # Butonlar
        btn_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 Analiz Et",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._start_analysis,
            width=130
        )
        self.analyze_btn.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Temizle",
            font=ctk.CTkFont(size=13),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._clear_all,
            width=80
        ).pack(side="left")
        
        # Accuracy göstergeleri
        self.accuracy_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], corner_radius=10)
        self.accuracy_frame.pack(fill="x", padx=10, pady=5)
        
        acc_inner = ctk.CTkFrame(self.accuracy_frame, fg_color="transparent")
        acc_inner.pack(pady=10)
        
        # Beyaz accuracy
        white_frame = ctk.CTkFrame(acc_inner, fg_color="transparent")
        white_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            white_frame,
            text="♔ Beyaz",
            font=ctk.CTkFont(size=11),
            text_color=THEME["text_secondary"]
        ).pack()
        
        self.white_accuracy_label = ctk.CTkLabel(
            white_frame,
            text="--%",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        self.white_accuracy_label.pack()
        
        # Siyah accuracy
        black_frame = ctk.CTkFrame(acc_inner, fg_color="transparent")
        black_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            black_frame,
            text="♚ Siyah",
            font=ctk.CTkFont(size=11),
            text_color=THEME["text_secondary"]
        ).pack()
        
        self.black_accuracy_label = ctk.CTkLabel(
            black_frame,
            text="--%",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#000000"
        )
        self.black_accuracy_label.pack()
        
        # Hamle listesi
        self.move_list = MoveList(
            right_frame,
            fg_color=THEME["bg_tertiary"],
            corner_radius=10,
            on_move_click=self._on_move_click
        )
        self.move_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Progress bar
        self.progress_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=THEME["bg_tertiary"],
            progress_color=THEME["accent"]
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")
        self.progress_bar.pack_forget()  # Başta gizli
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=THEME["text_secondary"]
        )
        
        # Kopyalama butonu
        ctk.CTkButton(
            right_frame,
            text="📋 Hamleleri Kopyala (Chess.com uyumlu)",
            font=ctk.CTkFont(size=12),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._copy_moves
        ).pack(fill="x", padx=10, pady=(0, 15))
    
    def _start_analysis(self):
        """Analizi başlat"""
        pgn_text = self.pgn_input.get("1.0", "end").strip()
        
        if not pgn_text:
            self.status_label.configure(text="PGN veya hamle metni girin!")
            return
        
        # Depth ayarını oku
        try:
            depth = int(self.depth_var.get())
            depth = max(10, min(30, depth))  # 10-30 arası sınırla
        except:
            depth = 18
        
        # PGN yükle
        if not self.engine.load_pgn(pgn_text):
            self.status_label.configure(text="Geçersiz PGN formatı!")
            return
        
        if len(self.engine.move_history) == 0:
            self.status_label.configure(text="Hamle bulunamadı!")
            return
        
        # UI hazırla
        self.analyze_btn.configure(state="disabled", text="Analiz ediliyor...")
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_label.pack()
        self.progress_bar.set(0)
        
        self.move_list.clear()
        self.analysis_results = []
        self.is_analyzing = True
        
        # Stockfish başlat
        self.stockfish.start()
        
        # Analizi başlat (async) - depth parametresi ile
        self.stockfish.analyze_game_async(
            self.engine.move_history,
            depth=depth,
            progress_callback=self._on_progress,
            complete_callback=self._on_complete
        )
    
    def _on_progress(self, current: int, total: int, move_result: Dict):
        """Analiz ilerlemesi"""
        def update():
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Analiz ediliyor: {current}/{total}")
            
            # Anlık olarak hamleyi ekle
            self.move_list.add_move(
                move_result["san"], 
                move_result["classification"]
            )
        
        self.after(0, update)
    
    def _on_complete(self, results: List[Dict]):
        """Analiz tamamlandı"""
        def update():
            self.analysis_results = results
            self.is_analyzing = False
            
            # UI güncelle
            self.analyze_btn.configure(state="normal", text="🔍 Analiz Et")
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self.status_label.configure(text="Analiz tamamlandı!")
            
            # Accuracy hesapla
            white_acc, black_acc = self.stockfish.calculate_accuracy(results)
            self.white_accuracy_label.configure(text=f"{white_acc:.1f}%")
            self.black_accuracy_label.configure(text=f"{black_acc:.1f}%")
            
            # Accuracy renklerini ayarla
            self._set_accuracy_color(self.white_accuracy_label, white_acc)
            self._set_accuracy_color(self.black_accuracy_label, black_acc)
            
            # Hamle listesini güncelle (renkli)
            self.move_list.clear()
            for result in results:
                self.move_list.add_move(result["san"], result["classification"])
            
            # Başlangıç pozisyonuna git
            self._go_start()
        
        self.after(0, update)
    
    def _set_accuracy_color(self, label, accuracy: float):
        """Accuracy değerine göre renk ayarla"""
        if accuracy >= 90:
            color = MOVE_COLORS["best"]
        elif accuracy >= 80:
            color = MOVE_COLORS["good"]
        elif accuracy >= 70:
            color = "#FFFFFF"
        elif accuracy >= 50:
            color = MOVE_COLORS["inaccuracy"]
        else:
            color = MOVE_COLORS["mistake"]
        
        label.configure(text_color=color)
    
    def _on_move_click(self, index: int):
        """Hamle tıklandığında"""
        self._go_to_move(index)
    
    def _go_to_move(self, index: int):
        """Belirli bir hamleye git"""
        if not self.analysis_results:
            return
        
        if index < -1:
            index = -1
        if index >= len(self.analysis_results):
            index = len(self.analysis_results) - 1
        
        self.current_move_index = index
        
        # Tahtayı güncelle
        self.engine.go_to_move(index + 1)  # 0 = başlangıç, 1 = ilk hamle sonrası
        self.chess_board.set_board(self.engine.board)
        
        # Son hamleyi vurgula
        if index >= 0 and index < len(self.engine.move_history):
            self.chess_board.set_last_move(self.engine.move_history[index])
        else:
            self.chess_board.set_last_move(None)
        
        # Hamle listesinde vurgula
        self.move_list.highlight_move(index)
        
        # Değerlendirme göster
        if index >= 0 and index < len(self.analysis_results):
            result = self.analysis_results[index]
            eval_score = result.get("eval", 0)
            classification = result.get("classification", "normal")
            
            # Değerlendirme metni
            if eval_score >= 0:
                eval_text = f"+{eval_score / 100:.2f}"
            else:
                eval_text = f"{eval_score / 100:.2f}"
            
            color = MOVE_COLORS.get(classification, "#FFFFFF")
            
            # Sınıflandırma Türkçe
            class_names = {
                "brilliant": "Efsane",
                "great": "Harika",
                "best": "En İyi",
                "good": "İyi",
                "book": "Kitap",
                "normal": "Normal",
                "inaccuracy": "Hatasız",
                "mistake": "Hata",
                "blunder": "Vahim"
            }
            class_name = class_names.get(classification, "")
            
            self.eval_label.configure(
                text=f"{eval_text}  •  {class_name}",
                text_color=color
            )
        else:
            self.eval_label.configure(text="Başlangıç pozisyonu", text_color=THEME["text_secondary"])
    
    def _go_start(self):
        """Başlangıca git"""
        self._go_to_move(-1)
    
    def _go_prev(self):
        """Önceki hamle"""
        self._go_to_move(self.current_move_index - 1)
    
    def _go_next(self):
        """Sonraki hamle"""
        self._go_to_move(self.current_move_index + 1)
    
    def _go_end(self):
        """Sona git"""
        if self.analysis_results:
            self._go_to_move(len(self.analysis_results) - 1)
    
    def _copy_moves(self):
        """Hamleleri Chess.com uyumlu formatta kopyala"""
        if not self.engine.move_history:
            return
        
        pgn = self.engine.get_pgn()
        self.clipboard_clear()
        self.clipboard_append(pgn)
        
        self.status_label.configure(text="✓ Kopyalandı!")
        self.after(1500, lambda: self.status_label.configure(text=""))
    
    def _clear_all(self):
        """Her şeyi temizle"""
        self.pgn_input.delete("1.0", "end")
        self.move_list.clear()
        self.analysis_results = []
        self.current_move_index = -1
        
        self.engine.reset()
        self.chess_board.set_board(self.engine.board)
        
        self.white_accuracy_label.configure(text="--%", text_color="#FFFFFF")
        self.black_accuracy_label.configure(text="--%", text_color="#000000")
        self.eval_label.configure(text="")
        self.status_label.configure(text="")
    
    def _on_back_click(self):
        """Geri butonu"""
        if self.is_analyzing:
            self.stockfish.stop_analysis()
        
        self.stockfish.stop()
        
        if self.on_back:
            self.on_back()
