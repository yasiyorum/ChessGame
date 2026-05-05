"""
Stockfish Yöneticisi - Chess.com %100 Uyumlu Analiz Sistemi
"""
import chess
import chess.engine
import threading
import subprocess
import math
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Optional, Tuple, List, Dict, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    STOCKFISH_PATH, STOCKFISH_THREADS, STOCKFISH_HASH, ANALYSIS_WORKERS,
    elo_to_skill_level, elo_to_think_time
)

class StockfishManager:
    def __init__(self):
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.Lock()
        self.is_analyzing = False
        self._engine_started = False
        
    def start(self) -> bool:
        try:
            with self._lock:
                if self.engine is None:
                    popen_args = {}
                    if sys.platform == "win32":
                        popen_args["creationflags"] = subprocess.CREATE_NO_WINDOW
                    
                    self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH, **popen_args)
                    self.engine.configure({
                        "Threads": STOCKFISH_THREADS,
                        "Hash": STOCKFISH_HASH
                    })
                    self._engine_started = True
                return True
        except Exception as e:
            print(f"Stockfish başlatma hatası: {e}")
            return False

    def stop(self):
        with self._lock:
            if self.engine:
                try: self.engine.quit()
                except: pass
                self.engine = None
        self.executor.shutdown(wait=False)

    # ==================== Chess.com Win Probability ====================
    
    def _cp_to_win_prob(self, cp: int) -> float:
        """Chess.com Resmi Formülü: 1 / (1 + 10^(-cp/400))"""
        try:
            return 1.0 / (1.0 + math.pow(10, -cp / 400.0))
        except:
            return 0.5

    # ==================== ANALİZ ====================

    def analyze_position(self, board: chess.Board, depth: int) -> Dict:
        if not self.engine: self.start()
        try:
            with self._lock:
                # Daha derin analiz = daha doğru sonuç
                info = self.engine.analyse(board, chess.engine.Limit(depth=depth))
                score = info.get("score")
                cp = 0
                if score:
                    cp = score.relative.score(mate_score=10000)
                    if cp is None: 
                        cp = 10000 if score.relative.mate() > 0 else -10000
                
                return {
                    "score": cp,
                    "best_move": info.get("pv", [None])[0] if "pv" in info else None,
                }
        except:
            return {"score": 0, "best_move": None}

    def analyze_game(self, moves: List[chess.Move], callback: Optional[Callable] = None, depth: int = 20) -> List[Dict]:
        """Chess.com tarzı oyun analizi"""
        self.is_analyzing = True
        results = [None] * len(moves)
        
        # Tüm pozisyonların FEN'lerini önceden hazırla
        fens = []
        temp_board = chess.Board()
        fens.append(temp_board.fen())
        for m in moves:
            temp_board.push(m)
            fens.append(temp_board.fen())

        def worker(idx: int):
            if not self.is_analyzing: return None
            
            # Hamle öncesi ve sonrası pozisyonlar
            board_before = chess.Board(fens[idx])
            board_after = chess.Board(fens[idx + 1])
            
            # Hamle öncesi en iyi hamleyi bul
            pre_eval = self.analyze_position(board_before, depth)
            engine_best_move = pre_eval["best_move"]
            eval_before = pre_eval["score"]  # Oyuncu perspektifinden
            
            # Hamle sonrası değerlendirme
            post_eval = self.analyze_position(board_after, depth)
            eval_after = -post_eval["score"]  # Perspektif değişti, çevir
            
            # En iyi hamle yapılsaydı ne olurdu?
            if engine_best_move and engine_best_move in board_before.legal_moves:
                board_best = board_before.copy()
                board_best.push(engine_best_move)
                best_eval_result = self.analyze_position(board_best, depth)
                best_eval_after = -best_eval_result["score"]
            else:
                best_eval_after = eval_before  # Eğer best move yoksa (garip durum)
            
            # Win Probability Loss hesapla
            win_prob_best = self._cp_to_win_prob(best_eval_after)
            win_prob_actual = self._cp_to_win_prob(eval_after)
            win_prob_loss = max(0, win_prob_best - win_prob_actual)
            
            # CP Loss
            cp_loss = max(0, best_eval_after - eval_after)
            
            # Sınıflandırma
            is_best = (moves[idx] == engine_best_move)
            classification = self._classify_move(
                win_prob_loss, is_best, idx + 1, 
                eval_before, eval_after, best_eval_after,
                moves[idx], board_before
            )

            res = {
                "index": idx,
                "san": board_before.san(moves[idx]),
                "eval": eval_after if (idx % 2 == 0) else -eval_after,  # Beyaz perspektifi
                "eval_loss": cp_loss,
                "classification": classification,
                "best_move": engine_best_move,
                "is_best": is_best,
                "expected_score_loss": win_prob_loss
            }
            
            if callback: callback(idx + 1, len(moves), res)
            return res

        # Paralel analiz
        with ThreadPoolExecutor(max_workers=ANALYSIS_WORKERS) as executor:
            futures = [executor.submit(worker, i) for i in range(len(moves))]
            for future in as_completed(futures):
                if not self.is_analyzing: break
                r = future.result()
                if r: results[r["index"]] = r

        self.is_analyzing = False
        return [r for r in results if r is not None]

    def _classify_move(self, wp_loss: float, is_best: bool, move_num: int,
                       eval_before: int, eval_after: int, best_eval_after: int,
                       move: chess.Move, board: chess.Board) -> str:
        """Chess.com Sınıflandırma Mantığı (Ultra Sert)"""
        from config import EVAL_THRESHOLDS

        # 1. Book / Teori
        if move_num <= 10 and is_best and wp_loss < 0.001:
            return "book"

        # 2. Miss (Kaçırma) - Büyük kazancı elden bırakmak
        if best_eval_after > 200 and eval_after < 50:
            return "miss"

        # 3. Brilliant (Efsane)
        if is_best and eval_after > -80:
            if self._is_brilliant_sacrifice(move, board, eval_before, eval_after):
                return "brilliant"

        # 4. Great (Mükemmel)
        if is_best:
            if (eval_before < -200 and eval_after > -50) or (eval_before < 50 and eval_after > 250):
                return "great"
            return "best"

        # 5. Config bazlı Sıkı Eşikler (wp_loss bazlı)
        t = EVAL_THRESHOLDS
        # Eşikleri centipawn'dan win prob kaybına kabaca çeviriyoruz (normal_threshold: 42 -> 0.0042)
        if wp_loss <= t["good_threshold"] / 1000.0: return "good"
        if wp_loss <= t["inaccuracy_threshold"] / 1000.0: return "inaccuracy"
        if wp_loss <= t["mistake_threshold"] / 1000.0: return "mistake"
        return "blunder"

    def _is_brilliant_sacrifice(self, move: chess.Move, board: chess.Board, 
                                 eval_before: int, eval_after: int) -> bool:
        """Chess.com tarzı Brilliant kontrolü - SADECE gerçek fedalarda"""
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type in [chess.PAWN, chess.KING]:
            return False  # Piyon ve Şah brilliant olamaz
        
        # Feda: Taşı rakibin vurduğu bir kareye mi bıraktık?
        board_next = board.copy()
        board_next.push(move)
        attackers = board_next.attackers(board_next.turn, move.to_square)
        if not attackers:
            return False  # Rakip vuramıyorsa feda değil
        
        # Değer farkı: Giden taş, alınan taştan en az 2 puan değerli olmalı
        captured = board.piece_at(move.to_square)
        vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        piece_val = vals.get(piece.piece_type, 0)
        captured_val = vals.get(captured.piece_type, 0) if captured else 0
        sacrifice_value = piece_val - captured_val
        
        if sacrifice_value < 2:
            return False  # Yeterli materyal farkı yok
        
        # Pozisyon iyileşmeli veya en azından kötüleşmemeli
        if eval_after < eval_before - 50:
            return False
            
        return True

    def calculate_accuracy(self, results: List[Dict]) -> Tuple[float, float]:
        """Chess.com CAPS 2.0 - Yaklaşık Formül
        
        Chess.com'un gerçek formülü:
        accuracy = 103.1668 * exp(-0.04354 * (win_prob_loss * 100)) - 3.1668
        Sınırlar: [0, 100]
        """
        
        def acc_from_result(r: Dict) -> float:
            wp_loss = r.get("expected_score_loss", 0)
            classification = r.get("classification", "normal")
            
            # Chess.com CAPS 2.0 yaklaşık formül
            # wp_loss 0-1 arasında, yüzdeye çevir
            wp_loss_pct = wp_loss * 100.0
            
            # Temel accuracy: 103.1668 * exp(-0.04354 * wp_loss_pct) - 3.1668
            raw_accuracy = 103.1668 * math.exp(-0.04354 * wp_loss_pct) - 3.1668
            
            # Daha yumuşak sınıflandırma sınırları (Asıl işi formülün kendisine bırak)
            if classification == "brilliant":
                raw_accuracy = 100.0
            elif classification == "great":
                raw_accuracy = max(raw_accuracy, 95.0)
            elif classification == "best":
                raw_accuracy = max(raw_accuracy, 90.0)
            elif classification == "book":
                raw_accuracy = 100.0
            elif classification == "blunder":
                raw_accuracy = min(raw_accuracy, 40.0)
            elif classification == "miss":
                raw_accuracy = min(raw_accuracy, 50.0)
            
            return max(0.0, min(100.0, raw_accuracy))
        
        w_scores = [acc_from_result(r) for r in results if r["index"] % 2 == 0]
        b_scores = [acc_from_result(r) for r in results if r["index"] % 2 != 0]
        
        return (
            sum(w_scores) / len(w_scores) if w_scores else 0,
            sum(b_scores) / len(b_scores) if b_scores else 0
        )

    def analyze_game_async(self, moves, depth=20, progress_callback=None, complete_callback=None):
        def _task():
            res = self.analyze_game(moves, progress_callback, depth)
            if complete_callback: complete_callback(res)
            return res
        return ThreadPoolExecutor(max_workers=1).submit(_task)

    def stop_analysis(self):
        self.is_analyzing = False
        
    def estimate_elo(self, accuracy: float) -> int:
        """Accuracy değerine göre tahmini ELO hesapla (Referans Tablosu / İnterpolasyon)"""
        # (Accuracy, ELO) referans noktaları
        ref_points = [
            (100.0, 3200),
            (95.0,  2500),
            (90.0,  2100),
            (85.0,  1800),
            (80.0,  1500),
            (75.0,  1350),
            (70.0,  1200),
            (60.0,   900),
            (50.0,   600),
            (40.0,   400),
            (0.0,    100)
        ]
        
        if accuracy >= 100: return 3200
        if accuracy <= 0: return 100
        
        # Hangi aralığa düştüğünü bul ve lineer interpolasyon yap
        for i in range(len(ref_points) - 1):
            acc_high, elo_high = ref_points[i]
            acc_low, elo_low = ref_points[i+1]
            
            if acc_low <= accuracy <= acc_high:
                oran = (accuracy - acc_low) / (acc_high - acc_low)
                return int(elo_low + oran * (elo_high - elo_low))
                
        return 100

    def get_top_moves(self, board, num_moves=3, depth=15):
        if not self.engine: self.start()
        try:
            info = self.engine.analyse(board, chess.engine.Limit(depth=depth), multipv=num_moves)
            # info bir liste döner multipv>1 ise
            results = []
            for pv in info:
                move = pv.get("pv", [None])[0]
                if not move: continue
                score_obj = pv.get("score")
                cp = 0
                if score_obj:
                    cp = score_obj.white().score(mate_score=10000)
                    if cp is None:
                        cp = 10000 if score_obj.white().mate() > 0 else -10000
                results.append((move, cp))
            return results
        except Exception as e:
            print("Top moves hatası:", e)
            return []
            
    def get_top_moves_async(self, board, num_moves=3, depth=15, callback=None):
        def _task():
            res = self.get_top_moves(board, num_moves, depth)
            if callback: callback(res)
            return res
        return ThreadPoolExecutor(max_workers=1).submit(_task)

    def analyze_single_move(self, board_before, move, depth=15):
        """Kullanıcının yaptığı tek hamleyi anlık analiz et"""
        if not self.engine: self.start()
        
        pre_eval = self.analyze_position(board_before, depth)
        engine_best_move = pre_eval["best_move"]
        eval_before = pre_eval["score"]
        
        board_after = board_before.copy()
        board_after.push(move)
        post_eval = self.analyze_position(board_after, depth)
        eval_after = -post_eval["score"]
        
        if engine_best_move and engine_best_move in board_before.legal_moves:
            board_best = board_before.copy()
            board_best.push(engine_best_move)
            best_eval_result = self.analyze_position(board_best, depth)
            best_eval_after = -best_eval_result["score"]
        else:
            best_eval_after = eval_before
            
        win_prob_best = self._cp_to_win_prob(best_eval_after)
        win_prob_actual = self._cp_to_win_prob(eval_after)
        win_prob_loss = max(0, win_prob_best - win_prob_actual)
        
        cp_loss = max(0, best_eval_after - eval_after)
        is_best = (move == engine_best_move)
        
        classification = self._classify_move(
            win_prob_loss, is_best, board_before.fullmove_number * 2, 
            eval_before, eval_after, best_eval_after,
            move, board_before
        )
        
        return {
            "san": board_before.san(move),
            "eval": eval_after if board_before.turn == chess.WHITE else -eval_after,
            "eval_loss": cp_loss,
            "classification": classification,
            "best_move": engine_best_move,
            "is_best": is_best
        }
        
    def analyze_single_move_async(self, board_before, move, depth=15, callback=None):
        def _task():
            res = self.analyze_single_move(board_before, move, depth)
            if callback: callback(res)
            return res
        return ThreadPoolExecutor(max_workers=1).submit(_task)
    def get_best_move(self, board, callback=None):
        if not self.engine: self.start()
        res = self.engine.play(board, chess.engine.Limit(time=0.5))
        if callback: callback(res.move)
        return res.move

    def get_hint(self, board):
        if not self.engine: self.start()
        info = self.engine.analyse(board, chess.engine.Limit(time=0.5))
        score_obj = info.get("score")
        cp = 0
        if score_obj:
            cp = score_obj.white().score(mate_score=10000)
            if cp is None:
                cp = 10000 if score_obj.white().mate() > 0 else -10000
        return (info.get("pv", [None])[0], cp)

    def set_elo(self, elo: int):
        """Botun gücünü ayarla"""
        if not self.engine: self.start()
        
        # Skill Level (0-20)
        skill = elo_to_skill_level(elo)
        
        options = {}
        options["Skill Level"] = skill
        
        # UCI_Elo ayarını kontrol et
        use_uci_elo = False
        if "UCI_Elo" in self.engine.options:
            uci_elo_option = self.engine.options["UCI_Elo"]
            min_elo = uci_elo_option.min
            
            # Eğer istenen ELO, motorun desteklediği minimumdan büyükse UCI_Elo kullan
            # Değilse sadece Skill Level kullan (bu sayede 100 ELO da mümkün olur)
            if elo >= min_elo:
                use_uci_elo = True
                options["UCI_LimitStrength"] = True
                options["UCI_Elo"] = elo
            else:
                # Düşük ELO modu: UCI_LimitStrength kapat, motoru Skill Level ile kısıtla
                options["UCI_LimitStrength"] = False
        
        # UCI ayarlarını güncelle
        try:
            self.engine.configure(options)
        except Exception as e:
            print(f"ELO ayarlanırken hata (görmezden geliniyor): {e}")

    def get_best_move_async(self, board, callback):
        """Asenkron en iyi hamle (Bot oyunu için)"""
        def _task():
            # ELO'ya göre düşünme süresi
            # Basitçe sabit bir süre veya ELO'ya bağlı min süre verebiliriz
            # Şimdilik 0.5 - 2 saniye arası
            move = self.get_best_move(board)
            if callback: callback(move)
        
        threading.Thread(target=_task, daemon=True).start()

    def get_hint_async(self, board, callback):
        """Asenkron ipucu"""
        def _task():
            res = self.get_hint(board)
            if callback: callback(res)
        
        threading.Thread(target=_task, daemon=True).start()
