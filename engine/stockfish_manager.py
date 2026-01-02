"""
Stockfish Yöneticisi
Stockfish motoru ile iletişim ve performans optimizasyonu
"""
import chess
import chess.engine
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Tuple, List, Dict, Callable
import sys
import os

# Config'i import et
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    STOCKFISH_PATH, STOCKFISH_THREADS, STOCKFISH_HASH,
    elo_to_skill_level, elo_to_think_time
)


class StockfishManager:
    """
    Stockfish motoru yönetim sınıfı
    Thread-safe ve performans optimize edilmiş
    """
    
    def __init__(self):
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.Lock()
        self.elo = 1200
        self.skill_level = 10
        self.think_time = 200  # ms
        self.is_analyzing = False
        
    def start(self) -> bool:
        """Stockfish motorunu başlat"""
        try:
            with self._lock:
                if self.engine is None:
                    self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
                    # Performans optimizasyonu
                    self.engine.configure({
                        "Threads": STOCKFISH_THREADS,
                        "Hash": STOCKFISH_HASH,
                        "Skill Level": self.skill_level
                    })
                return True
        except Exception as e:
            print(f"Stockfish başlatma hatası: {e}")
            return False
    
    def stop(self):
        """Stockfish motorunu durdur"""
        with self._lock:
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
                self.engine = None
        self.executor.shutdown(wait=False)
    
    def set_elo(self, elo: int):
        """Bot ELO değerini ayarla"""
        self.elo = elo
        self.skill_level = elo_to_skill_level(elo)
        self.think_time = elo_to_think_time(elo)
        
        with self._lock:
            if self.engine:
                self.engine.configure({"Skill Level": self.skill_level})
    
    def get_best_move(self, board: chess.Board, callback: Optional[Callable] = None) -> Optional[chess.Move]:
        """
        En iyi hamleyi hesapla (senkron)
        """
        if not self.engine:
            if not self.start():
                return None
        
        try:
            with self._lock:
                result = self.engine.play(
                    board, 
                    chess.engine.Limit(time=self.think_time / 1000.0)
                )
                return result.move
        except Exception as e:
            print(f"Hamle hesaplama hatası: {e}")
            return None
    
    def get_best_move_async(self, board: chess.Board, callback: Callable[[Optional[chess.Move]], None]) -> Future:
        """
        En iyi hamleyi asenkron hesapla (UI donmaz)
        """
        def _calculate():
            move = self.get_best_move(board)
            callback(move)
            return move
        
        return self.executor.submit(_calculate)
    
    def get_hint(self, board: chess.Board) -> Optional[Tuple[chess.Move, int]]:
        """
        İpucu için en iyi hamleyi ve değerlendirmesini döndür
        """
        if not self.engine:
            if not self.start():
                return None
        
        try:
            with self._lock:
                # Daha derin analiz (ipucu için)
                info = self.engine.analyse(
                    board, 
                    chess.engine.Limit(time=0.5),
                    info=chess.engine.INFO_ALL
                )
                
                best_move = info.get("pv", [None])[0]
                score = info.get("score")
                
                if score:
                    cp = score.relative.score(mate_score=10000)
                    if cp is None:
                        cp = 0
                    return (best_move, cp)
                
                return (best_move, 0) if best_move else None
                
        except Exception as e:
            print(f"İpucu hesaplama hatası: {e}")
            return None
    
    def get_hint_async(self, board: chess.Board, callback: Callable[[Optional[Tuple[chess.Move, int]]], None]) -> Future:
        """İpucu asenkron hesapla"""
        def _calculate():
            result = self.get_hint(board)
            callback(result)
            return result
        
        return self.executor.submit(_calculate)
    
    def analyze_position(self, board: chess.Board, depth: int = 15) -> Dict:
        """
        Pozisyonu analiz et ve detaylı bilgi döndür
        """
        if not self.engine:
            if not self.start():
                return {}
        
        try:
            with self._lock:
                info = self.engine.analyse(
                    board,
                    chess.engine.Limit(depth=depth),
                    info=chess.engine.INFO_ALL
                )
                
                result = {
                    "best_move": info.get("pv", [None])[0],
                    "pv": info.get("pv", []),
                    "depth": info.get("depth", 0),
                }
                
                score = info.get("score")
                if score:
                    cp = score.relative.score(mate_score=10000)
                    result["score"] = cp if cp is not None else 0
                    result["mate"] = score.relative.mate()
                else:
                    result["score"] = 0
                    result["mate"] = None
                
                return result
                
        except Exception as e:
            print(f"Analiz hatası: {e}")
            return {}
    
    def analyze_game(self, moves: List[chess.Move], callback: Optional[Callable] = None) -> List[Dict]:
        """
        Tüm oyunu analiz et ve her hamle için değerlendirme döndür
        Chess.com tarzı analiz
        """
        self.is_analyzing = True
        results = []
        board = chess.Board()
        
        # Başlangıç pozisyonu değerlendirmesi
        prev_eval = 0
        
        try:
            for i, move in enumerate(moves):
                if not self.is_analyzing:
                    break
                
                # Hamle öncesi pozisyon analizi (en iyi hamle neydi?)
                pre_analysis = self.analyze_position(board, depth=12)
                best_move = pre_analysis.get("best_move")
                
                # Hamleyi yap
                san = board.san(move)
                board.push(move)
                
                # Hamle sonrası değerlendirme
                post_analysis = self.analyze_position(board, depth=12)
                current_eval = post_analysis.get("score", 0)
                
                # Siyah için değerlendirmeyi ters çevir
                if i % 2 == 1:  # Siyah hamlesi
                    current_eval = -current_eval
                    prev_eval = -prev_eval
                
                # Hamle kalitesini belirle
                is_best = (move == best_move)
                eval_loss = prev_eval - current_eval
                
                classification = self._classify_move(eval_loss, is_best, pre_analysis)
                
                results.append({
                    "move": move,
                    "san": san,
                    "eval": current_eval,
                    "eval_loss": eval_loss,
                    "classification": classification,
                    "best_move": best_move,
                    "is_best": is_best,
                })
                
                # Callback ile progress bildir
                if callback:
                    callback(i + 1, len(moves), results[-1])
                
                # Bir sonraki hamle için mevcut eval'i kaydet
                prev_eval = -current_eval  # Taraf değişiyor
                
        except Exception as e:
            print(f"Oyun analiz hatası: {e}")
        
        self.is_analyzing = False
        return results
    
    def analyze_game_async(self, moves: List[chess.Move], 
                          progress_callback: Optional[Callable] = None,
                          complete_callback: Optional[Callable] = None) -> Future:
        """Oyunu asenkron analiz et"""
        def _analyze():
            results = self.analyze_game(moves, progress_callback)
            if complete_callback:
                complete_callback(results)
            return results
        
        return self.executor.submit(_analyze)
    
    def stop_analysis(self):
        """Devam eden analizi durdur"""
        self.is_analyzing = False
    
    def _classify_move(self, eval_loss: int, is_best: bool, analysis: Dict) -> str:
        """
        Hamleyi sınıflandır (Chess.com tarzı)
        """
        # Mat durumları
        if analysis.get("mate") is not None:
            if is_best:
                return "best"
        
        # Değerlendirme kaybına göre sınıflandır
        if eval_loss <= 0:
            if is_best:
                # Zor pozisyonda en iyi hamleyi bulmak "brilliant"
                if self._is_difficult_position(analysis):
                    return "brilliant"
                return "great"
            return "best"
        elif eval_loss < 25:
            return "good"
        elif eval_loss < 50:
            return "normal"
        elif eval_loss < 100:
            return "inaccuracy"
        elif eval_loss < 200:
            return "mistake"
        else:
            return "blunder"
    
    def _is_difficult_position(self, analysis: Dict) -> bool:
        """Pozisyonun zor olup olmadığını belirle"""
        pv = analysis.get("pv", [])
        # PV derinse veya değerlendirme keskinse zor pozisyon
        return len(pv) >= 5
    
    def calculate_accuracy(self, analysis_results: List[Dict]) -> Tuple[float, float]:
        """
        Her iki taraf için accuracy yüzdesini hesapla
        Chess.com formülü kullanılır
        """
        white_moves = []
        black_moves = []
        
        for i, result in enumerate(analysis_results):
            eval_loss = abs(result.get("eval_loss", 0))
            if i % 2 == 0:
                white_moves.append(eval_loss)
            else:
                black_moves.append(eval_loss)
        
        def calc_accuracy(losses):
            if not losses:
                return 100.0
            
            # Chess.com benzeri accuracy formülü
            total_accuracy = 0
            for loss in losses:
                # Her hamle için accuracy
                if loss <= 0:
                    acc = 100
                elif loss < 25:
                    acc = 100 - (loss * 0.4)
                elif loss < 50:
                    acc = 90 - ((loss - 25) * 0.8)
                elif loss < 100:
                    acc = 70 - ((loss - 50) * 0.6)
                elif loss < 200:
                    acc = 40 - ((loss - 100) * 0.3)
                else:
                    acc = max(0, 10 - ((loss - 200) * 0.05))
                
                total_accuracy += max(0, min(100, acc))
            
            return total_accuracy / len(losses)
        
        white_accuracy = calc_accuracy(white_moves)
        black_accuracy = calc_accuracy(black_moves)
        
        return (white_accuracy, black_accuracy)
    
    def __del__(self):
        self.stop()
