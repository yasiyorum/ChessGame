"""
Botla Oyna Modu
Stockfish motoruna karşı oyun
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


class BotGame(GameScreen):
    """Botla oyna modu"""
    
    def __init__(self, parent, on_back: Optional[Callable] = None, **kwargs):
        super().__init__(parent, on_back=on_back, title="🤖 Botla Oyna", **kwargs)
        
        # Motor
        self.engine = ChessEngine()
        self.stockfish = StockfishManager()
        
        # Oyun ayarları
        self.player_color = chess.WHITE
        self.bot_elo = 1200
        self.time_minutes = 5
        self.increment_seconds = 0
        self.unlimited = False
        
        # Stockfish'i arka planda önceden başlat (donmayı önlemek için)
        import threading
        threading.Thread(target=self._preload_stockfish, daemon=True).start()
        
        # Ayarlar diyaloğunu göster
        self.after(100, self._show_settings)
    
    def _preload_stockfish(self):
        """Stockfish'i arka planda başlat"""
        self.stockfish.start()
    
    def _show_settings(self):
        """Ayarlar diyaloğunu göster"""
        SettingsDialog(
            self,
            mode="bot",
            on_start=self._start_game
        )
    
    def _start_game(self, settings: dict):
        """Oyunu başlat"""
        self.bot_elo = settings["elo"]
        self.player_color = chess.WHITE if settings["color"] == "white" else chess.BLACK
        self.time_minutes = settings["time_minutes"]
        self.increment_seconds = settings["increment_seconds"]
        self.unlimited = settings["unlimited"]
        
        # Stockfish ELO ayarı (zaten arka planda başlatılmış)
        self.stockfish.set_elo(self.bot_elo)
        
        # Motor sıfırla
        self.engine.reset()
        self.engine.set_players(
            "Sen" if self.player_color == chess.WHITE else f"Stockfish ({self.bot_elo})",
            f"Stockfish ({self.bot_elo})" if self.player_color == chess.WHITE else "Sen"
        )
        
        # Tahta ayarları
        self.chess_board.set_board(self.engine.board)
        self.chess_board.set_flipped(self.player_color == chess.BLACK)
        self.chess_board.set_interactive(True)
        
        # Timer ayarları
        initial_time = self.time_minutes * 60 if not self.unlimited else 0
        
        self.player_timer.reset(initial_time)
        self.player_timer.increment = self.increment_seconds
        self.player_timer.set_unlimited(self.unlimited)
        self.player_timer.name_label.configure(text="Sen")
        
        self.opponent_timer.reset(initial_time)
        self.opponent_timer.increment = self.increment_seconds
        self.opponent_timer.set_unlimited(self.unlimited)
        self.opponent_timer.name_label.configure(text=f"Stockfish ({self.bot_elo})")
        
        # Hamle listesi temizle
        self.move_list.clear()
        
        # Oyun aktif
        self.game_active = True
        self.set_status(f"ELO: {self.bot_elo}")
        
        # Siyah seçildiyse bot ilk hamleyi yapar
        if self.player_color == chess.BLACK:
            self.chess_board.set_interactive(False)
            self._bot_move()
        else:
            if not self.unlimited:
                self.player_timer.start()
    
    def _on_player_move(self, move: chess.Move):
        """Oyuncu hamle yaptı"""
        if not self.game_active:
            return
        
        # Hamleyi kaydet
        san = self.engine.board.san(move)
        self.engine.make_move(move)
        
        # Hamle listesine ekle
        self.move_list.add_move(san)
        
        # Timer
        if not self.unlimited:
            self.player_timer.stop()
            self.player_timer.add_increment()
        
        # Oyun bitti mi?
        if self.engine.game_over:
            self._handle_game_over()
            return
        
        # Bot sırası
        self.chess_board.set_interactive(False)
        self.set_status("Bot düşünüyor...")
        
        if not self.unlimited:
            self.opponent_timer.start()
        
        # Bot hamlesini hesapla (async)
        self.after(100, self._bot_move)
    
    def _bot_move(self):
        """Bot hamle yapar"""
        def on_move_ready(move):
            if move and self.game_active:
                self.after(0, lambda: self._execute_bot_move(move))
        
        self.stockfish.get_best_move_async(self.engine.board, on_move_ready)
    
    def _execute_bot_move(self, move: chess.Move):
        """Bot hamlesini uygula"""
        if not self.game_active:
            return
        
        # Hamleyi kaydet
        san = self.engine.board.san(move)
        self.engine.make_move(move)
        
        # Tahtayı güncelle (board referansı paylaşılıyor, sadece görsel güncelleme gerek)
        self.chess_board.set_last_move(move)
        
        # Hamle listesine ekle
        self.move_list.add_move(san)
        
        # Timer
        if not self.unlimited:
            self.opponent_timer.stop()
            self.opponent_timer.add_increment()
        
        # Oyun bitti mi?
        if self.engine.game_over:
            self._handle_game_over()
            return
        
        # Oyuncu sırası
        self.chess_board.set_interactive(True)
        self.set_status(f"ELO: {self.bot_elo}")
        
        if not self.unlimited:
            self.player_timer.start()
    
    def _on_promotion_needed(self, from_sq: chess.Square, to_sq: chess.Square):
        """Terfi gerekli"""
        color = "white" if self.player_color == chess.WHITE else "black"
        
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
            
            # 3 saniye sonra ipucunu kaldır
            self.after(3000, self.chess_board.clear_hint)
    
    def _on_undo_click(self):
        """Hamle geri al - Botla oynarken 2 hamle geri al (kendi ve botun hamlesi)"""
        if not self.game_active:
            return
        
        # En az 2 hamle olmalı (bizim ve botun hamlesi)
        if len(self.engine.move_history) < 2:
            if len(self.engine.move_history) == 1:
                # Sadece 1 hamle varsa (ilk hamle) onu geri al
                self.engine.undo_move()
                self.move_list.remove_last_move()
            return
        
        # Botun hamlesini geri al
        self.engine.undo_move()
        self.move_list.remove_last_move()
        
        # Kendi hamlemizi geri al
        self.engine.undo_move()
        self.move_list.remove_last_move()
        
        # Tahtayı güncelle
        self.chess_board.set_board(self.engine.board)
        if self.engine.move_history:
            self.chess_board.set_last_move(self.engine.move_history[-1])
        else:
            self.chess_board.set_last_move(None)
        
        # Sıra bizde olmalı
        self.chess_board.set_interactive(True)
        self.set_status(f"ELO: {self.bot_elo}")
    
    def _on_resign_click(self):
        """Terk et"""
        if not self.game_active:
            return
        
        self.engine.resign(self.player_color)
        self._handle_game_over()
    
    def _on_copy_click(self):
        """Hamleleri kopyala (Chess.com uyumlu)"""
        pgn = self.engine.get_pgn()
        self.clipboard_clear()
        self.clipboard_append(pgn)
        
        # Geri bildirim
        self.copy_btn.configure(text="✓ Kopyalandı!")
        self.after(1500, lambda: self.copy_btn.configure(text="📋 Hamleleri Kopyala"))
    
    def _on_timeout(self, who: str):
        """Süre doldu"""
        if not self.game_active:
            return
        
        if who == "player":
            self.engine.resign(self.player_color)
        else:
            opponent_color = chess.BLACK if self.player_color == chess.WHITE else chess.WHITE
            self.engine.resign(opponent_color)
        
        self._handle_game_over()
    
    def _handle_game_over(self):
        """Oyun bitti"""
        self.game_active = False
        self.chess_board.set_interactive(False)
        self.player_timer.stop()
        self.opponent_timer.stop()
        
        # Sonuç belirleme
        result = self.engine.result
        
        if result == "1-0":
            if self.player_color == chess.WHITE:
                result_text = "Kazandın! 🏆"
            else:
                result_text = "Kaybettin"
        elif result == "0-1":
            if self.player_color == chess.BLACK:
                result_text = "Kazandın! 🏆"
            else:
                result_text = "Kaybettin"
        else:
            result_text = "Berabere 🤝"
        
        # Sebep
        if self.engine.board.is_checkmate():
            reason = "Şah mat!"
        elif self.engine.board.is_stalemate():
            reason = "Pat"
        elif self.engine.board.is_insufficient_material():
            reason = "Yetersiz materyal"
        elif self.player_timer.is_timed_out():
            reason = "Süre doldu"
        elif self.opponent_timer.is_timed_out():
            reason = "Rakibin süresi doldu"
        else:
            reason = "Oyun terk edildi"
        
        # Diyalog göster
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
