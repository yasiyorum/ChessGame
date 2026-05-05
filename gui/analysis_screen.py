"""
Analiz Ekranı - Chess.com Tarzı Profesyonel Analiz
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
from .components.eval_bar import EvalBar
from engine.chess_engine import ChessEngine
from engine.stockfish_manager import StockfishManager


class AnalysisScreen(ctk.CTkFrame):
    """Chess.com tarzı analiz ekranı"""
    
    def __init__(self, parent, on_back: Optional[Callable] = None, initial_pgn: Optional[str] = None, **kwargs):
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
        self.original_pgn_history = []  # Ana PGN varyasyonu için
        self.is_custom_line = False
        
        self._setup_ui()
        
        if initial_pgn:
            self.pgn_input.insert("1.0", initial_pgn)
            self.after(100, self._start_analysis)
    
    def _setup_ui(self):
        """UI oluştur"""
        # Üst bar
        self._setup_header()
        
        # Ana içerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Sol panel (eval bar + tahta + navigasyon)
        self._setup_left_panel(content)
        
        # Sağ panel (PGN input + sonuçlar)
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
            text="📊 Oyun Analizi",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(side="left", padx=15)
        
        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_muted"]
        )
        self.status_label.pack(side="right", padx=15)
    
    def _setup_left_panel(self, parent):
        """Sol panel"""
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Tahta alanı (eval bar + tahta)
        board_area = ctk.CTkFrame(left_frame, fg_color="transparent")
        board_area.pack(fill="both", expand=True)
        
        # Eval bar
        self.eval_bar = EvalBar(board_area, height=450, width=26)
        self.eval_bar.pack(side="left", fill="y", padx=(5, 4))
        
        # Tahta container
        board_outer = ctk.CTkFrame(board_area, fg_color="transparent")
        board_outer.pack(side="left", fill="both", expand=True)
        
        self.board_container = ctk.CTkFrame(board_outer, fg_color=THEME["bg_secondary"], corner_radius=4)
        self.board_container.pack(fill="both", expand=True)
        
        self.chess_board = ChessBoard(
            self.board_container,
            size=450,
            on_move=self._on_board_move
        )
        self.chess_board.set_interactive(True)
        self.chess_board.place(relx=0.5, rely=0.5, anchor="center")
        
        self.board_container.bind("<Configure>", self._on_board_container_resize)
        
        # Navigasyon + eval gösterge
        nav_area = ctk.CTkFrame(left_frame, fg_color="transparent")
        nav_area.pack(fill="x", pady=(8, 0))
        
        # Navigasyon butonları
        nav_frame = ctk.CTkFrame(nav_area, fg_color="transparent")
        nav_frame.pack(side="left")
        
        btn_style = {
            "font": ctk.CTkFont(family="Segoe UI", size=16),
            "fg_color": THEME["button_bg"],
            "hover_color": THEME["button_hover"],
            "width": 50,
            "height": 36,
            "corner_radius": 6,
            "border_width": 1,
            "border_color": THEME["panel_border"]
        }
        
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
                command=command,
                **btn_style
            ).pack(side="left", padx=2)
        
        # Detaylı hamle değerlendirme paneli (Sol alt)
        self.move_detail_frame = ctk.CTkFrame(
            nav_area,
            fg_color=THEME["bg_secondary"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["panel_border"],
            height=50
        )
        self.move_detail_frame.pack(side="right", fill="both", expand=True, padx=(15, 0))
        self.move_detail_frame.pack_propagate(False)
        
        # İçerik
        detail_inner = ctk.CTkFrame(self.move_detail_frame, fg_color="transparent")
        detail_inner.pack(fill="both", expand=True, padx=12, pady=5)
        
        # Sol taraf (İkon ve Sınıflandırma)
        class_frame = ctk.CTkFrame(detail_inner, fg_color="transparent")
        class_frame.pack(side="left", fill="y")
        
        self.detail_icon = ctk.CTkLabel(
            class_frame, text="",
            font=ctk.CTkFont(size=20)
        )
        self.detail_icon.pack(side="left", padx=(0, 5))
        
        self.detail_title = ctk.CTkLabel(
            class_frame, text="Başlangıç",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_muted"]
        )
        self.detail_title.pack(side="left")
        
        # Eval Skoru
        self.detail_eval = ctk.CTkLabel(
            detail_inner, text="",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.detail_eval.pack(side="right")
        
        # Alt açıklama (Örn: En iyi hamle)
        self.detail_desc = ctk.CTkLabel(
            detail_inner, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"]
        )
        self.detail_desc.pack(side="left", padx=15, pady=(2, 0))
    
    def _on_board_container_resize(self, event):
        """Tahta boyutu değiştiğinde"""
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
            self.eval_bar.resize(new_size)
            self.chess_board.draw_board()
    
    def _setup_right_panel(self, parent):
        """Sağ panel"""
        right_frame = ctk.CTkFrame(parent, fg_color=THEME["bg_secondary"], 
                                    corner_radius=8, width=350,
                                    border_width=1, border_color=THEME["panel_border"])
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # PGN Input
        input_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], corner_radius=0)
        input_frame.pack(fill="x")
        
        ctk.CTkLabel(
            input_frame,
            text="PGN veya Hamle Metni",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(pady=(10, 3), padx=12, anchor="w")
        
        self.pgn_input = ctk.CTkTextbox(
            input_frame,
            height=70,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=THEME["bg_primary"],
            text_color=THEME["text_primary"],
            corner_radius=6
        )
        self.pgn_input.pack(fill="x", padx=12, pady=(0, 8))
        
        # Depth + Butonlar
        ctrl_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        ctk.CTkLabel(
            ctrl_frame,
            text="Derinlik:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"]
        ).pack(side="left")
        
        self.depth_var = ctk.StringVar(value="18")
        self.depth_entry = ctk.CTkEntry(
            ctrl_frame,
            textvariable=self.depth_var,
            width=40,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=THEME["bg_primary"],
            corner_radius=4
        )
        self.depth_entry.pack(side="left", padx=5)
        
        self.analyze_btn = ctk.CTkButton(
            ctrl_frame,
            text="🔍 Analiz Et",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._start_analysis,
            width=100,
            height=28,
            corner_radius=6
        )
        self.analyze_btn.pack(side="right")
        
        ctk.CTkButton(
            ctrl_frame,
            text="Sıfırla",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._reset_board,
            width=50,
            height=28,
            corner_radius=6
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            ctrl_frame,
            text="Temizle",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._clear_all,
            width=50,
            height=28,
            corner_radius=6
        ).pack(side="right")
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        # Accuracy ve ELO göstergeleri
        self.accuracy_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], 
                                            corner_radius=0, height=85)
        self.accuracy_frame.pack(fill="x")
        self.accuracy_frame.pack_propagate(False)
        
        acc_inner = ctk.CTkFrame(self.accuracy_frame, fg_color="transparent")
        acc_inner.pack(expand=True)
        
        # Beyaz accuracy
        white_frame = ctk.CTkFrame(acc_inner, fg_color="transparent")
        white_frame.pack(side="left", padx=30)
        
        ctk.CTkLabel(
            white_frame,
            text="♔ Beyaz",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"]
        ).pack()
        
        self.white_accuracy_label = ctk.CTkLabel(
            white_frame,
            text="--%",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#FFFFFF"
        )
        self.white_accuracy_label.pack()
        
        self.white_elo_label = ctk.CTkLabel(
            white_frame,
            text="ELO: --",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_muted"]
        )
        self.white_elo_label.pack()
        
        # Ayırıcı
        ctk.CTkFrame(acc_inner, fg_color=THEME["divider"], width=1, height=40).pack(side="left")
        
        # Siyah accuracy
        black_frame = ctk.CTkFrame(acc_inner, fg_color="transparent")
        black_frame.pack(side="left", padx=30)
        
        ctk.CTkLabel(
            black_frame,
            text="♚ Siyah",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"]
        ).pack()
        
        self.black_accuracy_label = ctk.CTkLabel(
            black_frame,
            text="--%",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#B0B0B0"
        )
        self.black_accuracy_label.pack()
        
        self.black_elo_label = ctk.CTkLabel(
            black_frame,
            text="ELO: --",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_muted"]
        )
        self.black_elo_label.pack()
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        # Hamle İstatistikleri (Move Stats)
        self.stats_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], 
                                         corner_radius=0)
        self.stats_frame.pack(fill="x")
        
        self.stats_labels = {}
        
        # İstatistik satırları
        stat_types = [
            ("brilliant", "Efsane", "!!"),
            ("great", "Harika", "!"),
            ("best", "En İyi", "★"),
            ("good", "İyi", "✓"),
            ("inaccuracy", "Yanlış", "?!"),
            ("mistake", "Hata", "?"),
            ("blunder", "Vahim", "??")
        ]
        
        for key, name, icon in stat_types:
            row = ctk.CTkFrame(self.stats_frame, fg_color="transparent", height=22)
            row.pack(fill="x", padx=15, pady=1)
            row.pack_propagate(False)
            
            color = MOVE_COLORS.get(key, "#FFFFFF")
            
            # İkon
            ctk.CTkLabel(
                row, text=icon, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color, width=20, anchor="center"
            ).pack(side="left")
            
            # İsim
            ctk.CTkLabel(
                row, text=name, font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME["text_secondary"]
            ).pack(side="left", padx=5)
            
            # Beyaz Skor
            w_lbl = ctk.CTkLabel(
                row, text="-", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#FFFFFF"
            )
            w_lbl.pack(side="right", padx=(5, 10))
            
            # Siyah Skor
            b_lbl = ctk.CTkLabel(
                row, text="-", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#B0B0B0"
            )
            b_lbl.pack(side="right")
            
            self.stats_labels[key] = {"w": w_lbl, "b": b_lbl}
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        # Hamle listesi
        self.move_list = MoveList(
            right_frame,
            fg_color=THEME["move_list_bg"],
            corner_radius=0,
            on_move_click=self._on_move_click
        )
        self.move_list.pack(fill="both", expand=True)
        
        # Progress bar
        self.progress_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], 
                                            corner_radius=0, height=40)
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=THEME["bg_primary"],
            progress_color=THEME["accent"],
            height=6,
            corner_radius=3
        )
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_muted"]
        )
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        # Top 3 Hamle Önerisi
        self.top_moves_frame = ctk.CTkFrame(right_frame, fg_color=THEME["bg_tertiary"], corner_radius=0)
        self.top_moves_frame.pack(fill="x")
        
        ctk.CTkLabel(self.top_moves_frame, text="💡 Önerilen Hamleler", 
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=THEME["text_secondary"]).pack(anchor="w", padx=12, pady=(8, 2))
        
        self.top_move_labels = []
        for i in range(3):
            lbl = ctk.CTkLabel(self.top_moves_frame, text="", 
                               font=ctk.CTkFont(family="Segoe UI", size=11),
                               text_color=THEME["text_muted"])
            lbl.pack(anchor="w", padx=15, pady=1)
            self.top_move_labels.append(lbl)
            
        ctk.CTkFrame(self.top_moves_frame, fg_color="transparent", height=5).pack()
        
        # Ayırıcı
        ctk.CTkFrame(right_frame, fg_color=THEME["divider"], height=1).pack(fill="x")
        
        # Kopyala butonu
        ctk.CTkButton(
            right_frame,
            text="📋 PGN Kopyala",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=THEME["button_bg"],
            hover_color=THEME["button_hover"],
            command=self._copy_moves,
            height=32,
            corner_radius=0
        ).pack(fill="x")
    
    def _start_analysis(self):
        """Analizi başlat"""
        pgn_text = self.pgn_input.get("1.0", "end").strip()
        
        if not pgn_text:
            self.status_label.configure(text="PGN veya hamle metni girin!")
            return
        
        try:
            depth = int(self.depth_var.get())
            depth = max(10, min(30, depth))
        except:
            depth = 18
        
        if not self.engine.load_pgn(pgn_text):
            self.status_label.configure(text="Geçersiz PGN formatı!")
            return
        
        if len(self.engine.move_history) == 0:
            self.status_label.configure(text="Hamle bulunamadı!")
            return
        
        # UI hazırla
        self.analyze_btn.configure(state="disabled", text="Analiz ediliyor...")
        self.move_list.pack_forget()
        self.progress_frame.pack(fill="x")
        self.move_list.pack(fill="both", expand=True)
        
        self.progress_bar.pack(fill="x", padx=10, pady=(8, 2))
        self.progress_label.pack(padx=10, pady=(0, 5))
        self.progress_bar.set(0)
        
        self.move_list.clear()
        self.analysis_results = []
        self.is_analyzing = True
        
        self.stockfish.start()
        
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
            
            self.analyze_btn.configure(state="normal", text="🔍 Analiz Et")
            self.progress_frame.pack_forget()
            self.status_label.configure(text="Analiz tamamlandı!")
            
            # Accuracy hesapla
            white_acc, black_acc = self.stockfish.calculate_accuracy(results)
            self.white_accuracy_label.configure(text=f"{white_acc:.1f}%")
            self.black_accuracy_label.configure(text=f"{black_acc:.1f}%")
            
            self._set_accuracy_color(self.white_accuracy_label, white_acc)
            self._set_accuracy_color(self.black_accuracy_label, black_acc)
            
            # Tahmini ELO
            w_elo = self.stockfish.estimate_elo(white_acc)
            b_elo = self.stockfish.estimate_elo(black_acc)
            self.white_elo_label.configure(text=f"Tahmini ELO: {w_elo}")
            self.black_elo_label.configure(text=f"Tahmini ELO: {b_elo}")
            
            # Orijinal PGN'i kaydet
            self.original_pgn_history = list(self.engine.move_history)
            self.is_custom_line = False
            
            # İstatistikleri hesapla
            stats_w = {k: 0 for k in self.stats_labels.keys()}
            stats_b = {k: 0 for k in self.stats_labels.keys()}
            
            for r in results:
                cls = r.get("classification", "normal")
                if cls in self.stats_labels:
                    if r["index"] % 2 == 0:
                        stats_w[cls] += 1
                    else:
                        stats_b[cls] += 1
            
            # İstatistikleri UI'a yansıt
            for key in self.stats_labels:
                self.stats_labels[key]["w"].configure(text=str(stats_w[key]) if stats_w[key] > 0 else "-")
                self.stats_labels[key]["b"].configure(text=str(stats_b[key]) if stats_b[key] > 0 else "-")
            
            # Hamle listesini güncelle
            self.move_list.clear()
            for result in results:
                self.move_list.add_move(result["san"], result["classification"])
            
            self._go_start()
        
        self.after(0, update)
    
    def _set_accuracy_color(self, label, accuracy: float):
        """Accuracy rengini ayarla"""
        if accuracy >= 90:
            color = MOVE_COLORS["best"]
        elif accuracy >= 80:
            color = "#FFFFFF"
        elif accuracy >= 70:
            color = MOVE_COLORS["inaccuracy"]
        elif accuracy >= 50:
            color = MOVE_COLORS["mistake"]
        else:
            color = MOVE_COLORS["blunder"]
        
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
        
        self.engine.go_to_move(index + 1)
        self.chess_board.set_board(self.engine.board)
        
        if index >= 0 and index < len(self.engine.move_history):
            self.chess_board.set_last_move(self.engine.move_history[index])
        else:
            self.chess_board.set_last_move(None)
        
        self.move_list.highlight_move(index)
        
        if index >= 0 and index < len(self.analysis_results):
            result = self.analysis_results[index]
            eval_score = result.get("eval", 0)
            classification = result.get("classification", "normal")
            
            # Eval bar güncelle
            self.eval_bar.set_eval(eval_score)
            
            # Değerlendirme metni
            if eval_score >= 0:
                eval_text = f"+{eval_score / 100:.2f}"
            else:
                eval_text = f"{eval_score / 100:.2f}"
            
            color = MOVE_COLORS.get(classification, "#FFFFFF")
            
            class_names = {
                "brilliant": "Efsane Hamle",
                "great": "Harika Hamle",
                "best": "En İyi Hamle",
                "good": "İyi Hamle",
                "book": "Kitap Hamlesi",
                "normal": "Normal Hamle",
                "inaccuracy": "Yanlışlık",
                "mistake": "Hata",
                "blunder": "Vahim Hata",
                "miss": "Kaçırılan Fırsat"
            }
            class_icons = {
                "brilliant": "!!", "great": "!", "best": "★", "good": "✓",
                "book": "📚", "normal": "", "inaccuracy": "?!", "mistake": "?",
                "blunder": "??", "miss": "✖"
            }
            
            class_name = class_names.get(classification, "Bilinmeyen")
            icon = class_icons.get(classification, "")
            
            self.detail_icon.configure(text=icon, text_color=color)
            self.detail_title.configure(text=class_name, text_color=color)
            self.detail_eval.configure(text=eval_text)
            
            # Best move description
            if classification in ["inaccuracy", "mistake", "blunder", "miss"]:
                best_move = result.get("best_move")
                if best_move:
                    board_before = self.engine.board.copy()
                    board_before.pop() # Undo to get board state before the move
                    try:
                        best_san = board_before.san(best_move)
                        self.detail_desc.configure(text=f"En iyi hamle: {best_san}")
                    except:
                        self.detail_desc.configure(text="")
                else:
                    self.detail_desc.configure(text="")
            else:
                self.detail_desc.configure(text="")
                
        else:
            self.eval_bar.set_eval(0)
            self.detail_icon.configure(text="")
            self.detail_title.configure(text="Başlangıç Pozisyonu", text_color=THEME["text_muted"])
            self.detail_eval.configure(text="")
            self.detail_desc.configure(text="")
            
        # Top 3 hamleyi güncelle
        self._update_top_moves()
    
    def _go_start(self):
        self._go_to_move(-1)
    
    def _go_prev(self):
        self._go_to_move(self.current_move_index - 1)
    
    def _go_next(self):
        self._go_to_move(self.current_move_index + 1)
    
    def _go_end(self):
        if self.analysis_results:
            self._go_to_move(len(self.analysis_results) - 1)
    
    def _copy_moves(self):
        """PGN kopyala"""
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
        self.original_pgn_history = []
        self.is_custom_line = False
        self.current_move_index = -1
        
        self.engine.reset()
        self.chess_board.set_board(self.engine.board)
        self.eval_bar.set_eval(0)
        
        self.white_accuracy_label.configure(text="--%", text_color="#FFFFFF")
        self.black_accuracy_label.configure(text="--%", text_color="#B0B0B0")
        self.white_elo_label.configure(text="ELO: --")
        self.black_elo_label.configure(text="ELO: --")
        
        for key in self.stats_labels:
            self.stats_labels[key]["w"].configure(text="-")
            self.stats_labels[key]["b"].configure(text="-")
            
        self.detail_icon.configure(text="")
        self.detail_title.configure(text="Başlangıç Pozisyonu", text_color=THEME["text_muted"])
        self.detail_eval.configure(text="")
        self.detail_desc.configure(text="")
        self.status_label.configure(text="")
        
        for lbl in self.top_move_labels:
            lbl.configure(text="")
            
    def _reset_board(self):
        """Tahtayı orijinal varyasyona döndür"""
        if not self.original_pgn_history:
            return
            
        self.is_custom_line = False
        self.pgn_input.delete("1.0", "end")
        
        # PGN input'a orijinal hamleleri koy ve yeniden analiz başlat
        temp_board = chess.Board()
        moves = []
        for i, m in enumerate(self.original_pgn_history):
            san = temp_board.san(m)
            if i % 2 == 0:
                moves.append(f"{(i//2)+1}. {san}")
            else:
                moves[-1] += f" {san}"
            temp_board.push(m)
            
        self.pgn_input.insert("end", " ".join(moves))
        self._start_analysis()
        
    def _update_top_moves(self):
        """Top 3 hamleyi güncelle ve ok ile göster"""
        if self.is_analyzing or self.engine.board.is_game_over():
            for lbl in self.top_move_labels: lbl.configure(text="")
            self.chess_board.hint_move = None
            self.chess_board.draw_board()
            return
            
        for lbl in self.top_move_labels:
            lbl.configure(text="Düşünüyor...")
        
        def on_ready(results):
            def update_ui():
                # En iyi hamleyi tahtada okla göster
                if results and not self.is_analyzing:
                    best_move = results[0][0]
                    self.chess_board.hint_move = best_move
                    self.chess_board.draw_board()
                else:
                    self.chess_board.hint_move = None
                    self.chess_board.draw_board()
                    
                for i, lbl in enumerate(self.top_move_labels):
                    if i < len(results):
                        move, score = results[i]
                        try:
                            san = self.engine.board.san(move)
                            eval_text = f"+{score / 100:.2f}" if score >= 0 else f"{score / 100:.2f}"
                            lbl.configure(text=f"{i+1}. {san} ({eval_text})")
                        except:
                            lbl.configure(text="")
                    else:
                        lbl.configure(text="")
            self.after(0, update_ui)
            
        self.stockfish.get_top_moves_async(self.engine.board, num_moves=3, callback=on_ready)

    def _on_board_move(self, move: chess.Move):
        """Kullanıcı tahtada serbest hamle yaptı"""
        if self.is_analyzing:
            return
            
        board_before = self.engine.board.copy()
        
        # Orijinal çizgiden çıkış
        if not self.is_custom_line:
            self.engine.move_history = self.engine.move_history[:self.current_move_index + 1]
            self.engine.position_history = self.engine.position_history[:self.current_move_index + 2]
            self.analysis_results = self.analysis_results[:self.current_move_index + 1]
            self.move_list.clear()
            for r in self.analysis_results:
                self.move_list.add_move(r["san"], r["classification"])
            self.is_custom_line = True
            self.status_label.configure(text="Serbest Analiz Modu")
            
        san = board_before.san(move)
        self.engine.make_move(move)
        idx = len(self.engine.move_history) - 1
        
        self.chess_board.set_last_move(move)
        self.current_move_index = idx
        
        self.move_list.add_move(san, "normal")
        self.move_list.highlight_move(idx)
        
        self.detail_icon.configure(text="⏳")
        self.detail_title.configure(text="Analiz ediliyor...", text_color=THEME["text_muted"])
        self.detail_desc.configure(text="")
        
        # Anlık analiz
        def on_analyzed(result):
            result["index"] = idx
            
            # Eğer o sırada başka hamle yapıldıysa eskiyi umursama
            if len(self.analysis_results) == idx:
                self.analysis_results.append(result)
            elif len(self.analysis_results) > idx:
                self.analysis_results[idx] = result
                
            def update_ui():
                if self.current_move_index == idx:
                    self._go_to_move(idx)
            self.after(0, update_ui)
            
        self.stockfish.analyze_single_move_async(board_before, move, callback=on_analyzed)
    
    def _on_back_click(self):
        """Geri butonu"""
        if self.is_analyzing:
            self.stockfish.stop_analysis()
        
        self.stockfish.stop()
        
        if self.on_back:
            self.on_back()
