"""
Arkadaşla Oyna Modu - Chess.com Tarzı
Aynı bilgisayarda 2 kişilik oyun
"""
import customtkinter as ctk
import chess
from typing import Optional, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME

from .game_screen import GameScreen
from .components.dialogs import SettingsDialog, GameEndDialog, PromotionDialog
from engine.chess_engine import ChessEngine
from engine.stockfish_manager import StockfishManager


class FriendGame(GameScreen):
    """Arkadaşla oyna modu"""
    
    def __init__(self, parent, on_back: Optional[Callable] = None, **kwargs):
        super().__init__(parent, on_back=on_back, title="👥 Arkadaşla Oyna", **kwargs)
        
        # Motor
        self.engine = ChessEngine()
        self.stockfish = StockfishManager()  # Sadece ipucu için
        
        # Oyun ayarları
        self.time_minutes = 5
        self.increment_seconds = 0
        self.unlimited = False
        
        # İsimler
        self.player_name_label.configure(text="Beyaz ♔")
        self.opponent_name_label.configure(text="Siyah ♚")
        
        # Captured pieces renkleri
        self.player_captured.color = chess.WHITE
        self.opponent_captured.color = chess.BLACK
        
        # Ayarlar diyaloğunu göster
        self.after(100, self._show_settings)
    
    def _show_settings(self):
        """Ayarlar diyaloğunu göster"""
        SettingsDialog(
            self,
            mode="friend",
            on_start=self._start_game
        )
    
    def _start_game(self, settings: dict):
        """Oyunu başlat"""
        self.time_minutes = settings["time_minutes"]
        self.increment_seconds = settings["increment_seconds"]
        self.unlimited = settings["unlimited"]
        
        # Motor sıfırla
        self.engine.reset()
        self.engine.set_players("Beyaz", "Siyah")
        
        # Tahta ayarları
        self.chess_board.set_board(self.engine.board)
        self.chess_board.set_flipped(False)
        self.chess_board.set_interactive(True)
        
        # Timer ayarları
        initial_time = self.time_minutes * 60 if not self.unlimited else 0
        
        self.player_timer.reset(initial_time)
        self.player_timer.increment = self.increment_seconds
        self.player_timer.set_unlimited(self.unlimited)
        
        self.opponent_timer.reset(initial_time)
        self.opponent_timer.increment = self.increment_seconds
        self.opponent_timer.set_unlimited(self.unlimited)
        
        # Hamle listesi temizle
        self.move_list.clear()
        
        # Eval bar sıfırla
        self.eval_bar.set_eval(0)
        
        # Stockfish başlat (ipucu için)
        self.stockfish.start()
        
        # Oyun aktif
        self.game_active = True
        self._update_turn_display()
        
        # Alınan taşları sıfırla
        self.update_captured_pieces()
        
        # Beyaz başlar
        if not self.unlimited:
            self.player_timer.start()
    
    def _update_turn_display(self):
        """Sıra göstergesini güncelle"""
        if self.engine.board.turn == chess.WHITE:
            self.set_status("Sıra: Beyaz ♔")
        else:
            self.set_status("Sıra: Siyah ♚")
    
    def _on_player_move(self, move: chess.Move):
        """Hamle yapıldı"""
        if not self.game_active:
            return
        
        current_turn = self.engine.board.turn
        
        # Hamleyi kaydet
        san = self.engine.board.san(move)
        self.engine.make_move(move)
        
        # Hamle listesine ekle
        self.move_list.add_move(san)
        
        # Alınan taşları güncelle
        self.update_captured_pieces()
        self._update_eval_bar()
        
        # Timer değiştir
        if not self.unlimited:
            if current_turn == chess.WHITE:
                self.player_timer.stop()
                self.player_timer.add_increment()
                self.opponent_timer.start()
            else:
                self.opponent_timer.stop()
                self.opponent_timer.add_increment()
                self.player_timer.start()
        
        # Oyun bitti mi?
        if self.engine.game_over:
            self._handle_game_over()
            return
        
        # Sıra göstergesini güncelle
        self._update_turn_display()
        
        # Tahtayı güncelle
        self.chess_board.set_last_move(move)
    
    def _on_promotion_needed(self, from_sq: chess.Square, to_sq: chess.Square):
        """Terfi gerekli"""
        color = "white" if self.engine.board.turn == chess.WHITE else "black"
        
        def on_select(piece):
            self.chess_board.make_promotion_move(from_sq, to_sq, piece)
        
        PromotionDialog(self, color=color, on_select=on_select)
    
    def _on_hint_click(self):
        """İpucu butonu"""
        if not self.game_active:
            return
        
        self.hint_btn.configure(state="disabled", text="Düşünüyor...")
        
        def on_hint_ready(result):
            self.after(0, lambda: self._show_hint(result))
        
        self.stockfish.get_hint_async(self.engine.board, on_hint_ready)
    
    def _show_hint(self, result):
        """İpucunu göster"""
        self.hint_btn.configure(state="normal", text="💡 İpucu")
        
        if result:
            move, score = result
            self.chess_board.show_hint(move)
            self.after(3000, self.chess_board.clear_hint)
    
    def _on_undo_click(self):
        """Hamle geri al"""
        if not self.game_active:
            return
        
        if not self.engine.move_history:
            return
        
        self.engine.undo_move()
        self.move_list.remove_last_move()
        
        self.chess_board.set_board(self.engine.board)
        if self.engine.move_history:
            self.chess_board.set_last_move(self.engine.move_history[-1])
        else:
            self.chess_board.set_last_move(None)
        
        # Alınan taşları güncelle
        self.update_captured_pieces()
        self._update_eval_bar()
        
        self._update_turn_display()
    
    def _on_resign_click(self):
        """Terk et"""
        if not self.game_active:
            return
        
        self.engine.resign(self.engine.board.turn)
        self._handle_game_over()
    
    def _on_copy_click(self):
        """Hamleleri kopyala"""
        pgn = self.engine.get_pgn()
        self.clipboard_clear()
        self.clipboard_append(pgn)
        
        self.copy_btn.configure(text="✓ Kopyalandı!")
        self.after(1500, lambda: self.copy_btn.configure(text="📋 Hamleleri Kopyala"))
    
    def _on_timeout(self, who: str):
        """Süre doldu"""
        if not self.game_active:
            return
        
        if who == "player":
            self.engine.resign(chess.WHITE)
        else:
            self.engine.resign(chess.BLACK)
        
        self._handle_game_over()
    
    def _handle_game_over(self):
        """Oyun bitti"""
        self.game_active = False
        self.chess_board.set_interactive(False)
        self.player_timer.stop()
        self.opponent_timer.stop()
        
        result = self.engine.result
        
        if result == "1-0":
            result_text = "Beyaz Kazandı! ♔"
        elif result == "0-1":
            result_text = "Siyah Kazandı! ♚"
        else:
            result_text = "Berabere 🤝"
        
        if self.engine.board.is_checkmate():
            reason = "Şah mat!"
        elif self.engine.board.is_stalemate():
            reason = "Pat"
        elif self.engine.board.is_insufficient_material():
            reason = "Yetersiz materyal"
        elif self.player_timer.is_timed_out():
            reason = "Beyazın süresi doldu"
        elif self.opponent_timer.is_timed_out():
            reason = "Siyahın süresi doldu"
        else:
            reason = "Oyun terk edildi"
        
        # Maç geçmişine kaydet
        from game_history import GameHistory
        history = GameHistory.get_instance()
        history.add_game(
            white_name=self.engine.white_player,
            black_name=self.engine.black_player,
            result=self.engine.result or "*",
            move_count=len(self.engine.move_history),
            pgn=self.engine.get_pgn(),
            mode="friend"
        )
        
        GameEndDialog(
            self,
            result=result_text,
            reason=reason,
            pgn=self.engine.get_pgn(),
            on_new_game=self._new_game,
            on_menu=self._go_menu
        )
    
    def _new_game(self):
        """Yeni oyun"""
        self._show_settings()
    
    def _go_menu(self):
        """Ana menüye dön"""
        self._cleanup()
        if self.on_back:
            self.on_back()
    
    def _cleanup(self):
        """Temizlik"""
        super()._cleanup()
        self.game_active = False
        self.stockfish.stop()
