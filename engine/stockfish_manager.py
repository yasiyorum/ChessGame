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
        self.current_elo = 1600  # Varsayılan ELO
        import random
        self.random = random
        
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
        """
        Chess.com Resmi Win Probability Formülü: 
        WP = 1 / (1 + 10^(-cp/400))
        
        Not: Mat durumları (mate in X) CP olarak +-10000 veya +-32000 olarak gelir.
        Bu formül matlarda otomatik olarak 1.0 veya 0.0 üretir.
        """
        try:
            # Sınır değerleri kontrol et (aşırı büyük CP'lerde math.pow hata verebilir)
            if cp > 3000: return 1.0
            if cp < -3000: return 0.0
            
            return 1.0 / (1.0 + math.pow(10, -cp / 400.0))
        except:
            return 1.0 if cp > 0 else 0.0 if cp < 0 else 0.5

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
            
            # Zorunlu hamle kontrolü (Sadece bir legal hamle varsa)
            is_forced = (len(list(board_before.legal_moves)) == 1)

            res = {
                "index": idx,
                "san": board_before.san(moves[idx]),
                "eval": eval_after if (idx % 2 == 0) else -eval_after,  # Beyaz perspektifi
                "eval_loss": cp_loss,
                "classification": classification,
                "best_move": engine_best_move,
                "is_best": is_best,
                "is_forced": is_forced,
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
        """
        Chess.com CAPS 2.0 Formülü: 
        Accuracy = 103.1668 * exp(-0.04354 * (WinProbLoss * 100)) - 3.16681
        
        Kriterler:
        - Zorunlu hamleler (forced) ve açılış hamleleri (book) ortalamayı şişirmemesi için filtrelenir.
        - WinProbLoss 0-1 arasındadır, formülde 100 ile çarpılarak (0-100 aralığında) kullanılır.
        """
        
        def acc_from_result(r: Dict) -> Optional[float]:
            # Puan şişiren hamleleri filtrele (Book ve Forced hamleler analize dahil edilmez)
            if r.get("classification") == "book" or r.get("is_forced"):
                return None
                
            wp_loss = r.get("expected_score_loss", 0)
            
            # wp_loss_pct: 0 ile 100 arasında bir değer (Örn: %5 kayıp -> 5.0)
            wp_loss_pct = wp_loss * 100.0
            
            # CAPS 2.0 Formülü
            accuracy = 103.1668 * math.exp(-0.04354 * wp_loss_pct) - 3.16681
            
            # Sınıflandırma tabanlı manuel düzeltmeler (Chess.com'un CAPS 2.0 sonrası uyguladığı min-max sınırları)
            classification = r.get("classification", "normal")
            if classification == "brilliant": return 100.0
            if classification == "great": return max(accuracy, 95.0)
            if classification == "blunder": return min(accuracy, 30.0)
            
            return max(0.0, min(100.0, accuracy))
        
        def calculate_avg(scores: List[Optional[float]]) -> float:
            valid_scores = [s for s in scores if s is not None]
            return sum(valid_scores) / len(valid_scores) if valid_scores else 100.0

        w_scores = [acc_from_result(r) for r in results if r["index"] % 2 == 0]
        b_scores = [acc_from_result(r) for r in results if r["index"] % 2 != 0]
        
        return (calculate_avg(w_scores), calculate_avg(b_scores))

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
            (90.0,  2000),
            (85.0,  1700),
            (80.0,  1500),
            (75.0,  1350),
            (70.0,  1200),
            (60.0,   800),
            (50.0,   500),
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
        
        is_forced = (len(list(board_before.legal_moves)) == 1)
        
        return {
            "san": board_before.san(move),
            "eval": eval_after if board_before.turn == chess.WHITE else -eval_after,
            "eval_loss": cp_loss,
            "classification": classification,
            "best_move": engine_best_move,
            "is_best": is_best,
            "is_forced": is_forced
        }
        
    def analyze_single_move_async(self, board_before, move, depth=15, callback=None):
        def _task():
            res = self.analyze_single_move(board_before, move, depth)
            if callback: callback(res)
            return res
        return ThreadPoolExecutor(max_workers=1).submit(_task)

    def _pick_weak_move(self, board: chess.Board) -> chess.Move:
        """
        Gerçekçi ELO simülasyonu.
        
        Felsefe: Gerçek düşük ELO oyuncular tamamen rastgele oynamaz.
        Temel hamleleri bilirler ama taktik kaçırırlar, planları yoktur,
        ve arada büyük hatalar yaparlar.
        
        Katmanlar:
        - 100-200: Çok kötü, neredeyse her hamle hata ama yine de bir mantığı var
        - 200-400: Sık blunder, temel alımları göremez, gelişi güzel geliştirir
        - 400-600: Arada iyi hamle yapar ama taktik göremez, sık hata
        - 600-800: Çoğunlukla makul hamle yapar, ama önemli anlarda taktik kaçırır
        - 800-1000: İyi oynar ama hassas pozisyonlarda hata yapar
        - 1000-1200: Güçlü oynar, nadiren büyük hata
        """
        legal_moves = list(board.legal_moves)
        if len(legal_moves) == 0:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        elo = self.current_elo
        
        # Tüm hamleleri değerlendir (multipv ile)
        try:
            mv_count = min(len(legal_moves), 20)
            analysis_depth = self._get_analysis_depth(elo)
            
            with self._lock:
                info = self.engine.analyse(board, chess.engine.Limit(depth=analysis_depth), multipv=mv_count)
            
            ranked_moves = []
            for pv in info:
                m = pv.get("pv", [None])[0]
                score_obj = pv.get("score")
                cp = 0
                if score_obj:
                    cp = score_obj.relative.score(mate_score=10000)
                    if cp is None:
                        cp = 10000 if score_obj.relative.mate() > 0 else -10000
                if m:
                    ranked_moves.append((m, cp))
        except:
            return self.random.choice(legal_moves)
        
        if not ranked_moves:
            return self.random.choice(legal_moves)
        
        # Sıralamada olmayan hamleleri de ekle
        ranked_set = {m for m, _ in ranked_moves}
        worst_cp = ranked_moves[-1][1] if ranked_moves else 0
        for m in legal_moves:
            if m not in ranked_set:
                ranked_moves.append((m, worst_cp - 100))
        
        # En iyi hamle ve en kötü hamle
        best_cp = ranked_moves[0][1]
        
        # === ELO'ya göre hamle seçim stratejisi ===
        
        # 1. "Kabul edilebilir kayıp eşiği" — bu eşiğin altındaki hamleler "makul" sayılır
        #    Gerçek oyuncular genelde makul hamleler arasından seçer,
        #    ama bazen eşiğin dışına çıkarlar (blunder)
        acceptable_loss = self._get_acceptable_loss(elo)
        
        # 2. Blunder olasılığı — makul hamle yerine kötü hamle seçme şansı
        blunder_chance = self._get_blunder_chance(elo)
        
        # 3. En iyi hamleyi bulma olasılığı
        best_move_chance = self._get_best_move_chance(elo)
        
        # Hamleleri kategorilere ayır
        good_moves = []   # best_cp - acceptable_loss içinde
        okay_moves = []   # acceptable_loss - 2*acceptable_loss arası (hafif hata)
        bad_moves = []    # 2*acceptable_loss'tan fazla kayıp (blunder)
        
        for m, cp in ranked_moves:
            loss = best_cp - cp
            if loss <= acceptable_loss:
                good_moves.append((m, cp))
            elif loss <= acceptable_loss * 2.5:
                okay_moves.append((m, cp))
            else:
                bad_moves.append((m, cp))
        
        # Eğer iyi hamle yoksa (herşey eşit), hepsini iyi say
        if not good_moves:
            good_moves = ranked_moves[:max(1, len(ranked_moves)//2)]
        
        # === Hamle seçimi ===
        roll = self.random.random()
        
        # En iyi hamleyi tam olarak bul?
        if roll < best_move_chance:
            return ranked_moves[0][0]
        
        # Blunder yap?
        if roll < best_move_chance + blunder_chance:
            # Blunder: okay veya bad hamlelerden seç
            blunder_pool = okay_moves + bad_moves
            if blunder_pool:
                # Düşük ELO'da daha kötü blunder, yüksek ELO'da daha hafif
                if elo < 400 and bad_moves:
                    return self._weighted_pick(bad_moves, bias="random")
                elif okay_moves:
                    return self._weighted_pick(okay_moves, bias="random")
                else:
                    return self._weighted_pick(blunder_pool, bias="random")
        
        # Normal oyna: makul hamleler arasından seç (hafif rastgelelik ile)
        pool = good_moves if good_moves else ranked_moves[:5]
        return self._weighted_pick(pool, bias="top")
    
    def _weighted_pick(self, moves_with_cp, bias="top"):
        """
        Hamle listesinden ağırlıklı seçim.
        bias="top": iyi hamlelere eğilimli
        bias="random": eşit dağılım
        """
        if not moves_with_cp:
            return None
        if len(moves_with_cp) == 1:
            return moves_with_cp[0][0]
        
        moves = [m for m, _ in moves_with_cp]
        
        if bias == "random":
            return self.random.choice(moves)
        
        # "top" bias: sıralamaya göre azalan ağırlık
        n = len(moves)
        weights = [max(0.1, (n - i) / n) for i in range(n)]
        return self.random.choices(moves, weights=weights, k=1)[0]
    
    def _get_analysis_depth(self, elo):
        """ELO'ya göre analiz derinliği (düşük = daha zayıf değerlendirme)"""
        if elo < 200: return 3
        if elo < 400: return 5
        if elo < 600: return 7
        if elo < 800: return 9
        if elo < 1000: return 11
        return 13
    
    def _get_acceptable_loss(self, elo):
        """
        Kabul edilebilir centipawn kaybı.
        Bu eşiğin altındaki hamleler "normal/makul" sayılır.
        
        Düşük ELO: Büyük kayıpları bile fark etmez
        Yüksek ELO: Küçük kayıpları bile fark eder
        """
        if elo < 200: return 300   # 3 piyonluk kayıp bile "normal"
        if elo < 400: return 200   # 2 piyonluk kayıp fark edilmez
        if elo < 600: return 120   # ~1.2 piyon fark edilmez
        if elo < 800: return 80    # ~0.8 piyon kayıp kabul edilir
        if elo < 1000: return 50   # Yarım piyon
        return 30                   # Çok küçük hatalar
    
    def _get_blunder_chance(self, elo):
        """
        Her hamlede blunder yapma olasılığı.
        Gerçek verilere dayanır:
        - 100-200 ELO: ~%40-50 (neredeyse her hamle kötü)
        - 400 ELO: ~%25
        - 600 ELO: ~%12-15 (her 7-8 hamlede bir büyük hata)
        - 800 ELO: ~%8 (her 12 hamlede bir)
        - 1000 ELO: ~%4
        - 1200 ELO: ~%2
        """
        if elo < 200: return 0.45
        if elo < 300: return 0.35
        if elo < 400: return 0.25
        if elo < 500: return 0.18
        if elo < 600: return 0.13
        if elo < 700: return 0.10
        if elo < 800: return 0.08
        if elo < 900: return 0.06
        if elo < 1000: return 0.04
        if elo < 1100: return 0.03
        return 0.02
    
    def _get_best_move_chance(self, elo):
        """
        En iyi hamleyi tam olarak bulma olasılığı.
        - 100-200: %5 (şans eseri)
        - 400: %15
        - 600: %25
        - 800: %35
        - 1000: %50
        - 1200: %60
        """
        if elo < 200: return 0.05
        if elo < 300: return 0.10
        if elo < 400: return 0.15
        if elo < 500: return 0.20
        if elo < 600: return 0.25
        if elo < 700: return 0.30
        if elo < 800: return 0.35
        if elo < 900: return 0.42
        if elo < 1000: return 0.50
        if elo < 1100: return 0.55
        return 0.60

    def get_best_move(self, board, callback=None):
        if not self.engine: self.start()
        
        move = None
        
        # 1200 altı ELO'lar için özel zayıflatma sistemi
        if self.current_elo < 1200:
            move = self._pick_weak_move(board)
        
        # 1200+ veya fallback: Stockfish'in kendi Skill Level/UCI_Elo ayarları
        if not move:
            think_time = elo_to_think_time(self.current_elo) / 1000.0
            try:
                with self._lock:
                    res = self.engine.play(board, chess.engine.Limit(time=think_time))
                move = res.move
            except:
                legal_moves = list(board.legal_moves)
                move = self.random.choice(legal_moves) if legal_moves else None
            
        if callback: callback(move)
        return move

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
        """Botun gücünü ayarla
        
        ELO Katmanları:
        - 100-1200: Özel zayıflatma sistemi (_pick_weak_move) ile yönetilir.
                     Motor Skill Level 0'da tutulur, gerçek zayıflık yazılımsal.
        - 1200-3200: Stockfish'in kendi UCI_Elo ve Skill Level mekanizması.
        """
        self.current_elo = elo
        if not self.engine: self.start()
        
        # 1200 altı: Motor tam güçte tutulur ama _pick_weak_move hamle seçer
        # 1200 üstü: Stockfish'in Skill Level ve UCI_Elo mekanizması kullanılır
        if elo < 1200:
            # Düşük ELO'larda motorun kendi zayıflatmasına güvenmiyoruz
            # Skill Level 0 + UCI_LimitStrength kapalı
            # Asıl zayıflatma get_best_move -> _pick_weak_move içinde yapılır
            try:
                self.engine.configure({
                    "Skill Level": 0,
                    "UCI_LimitStrength": False
                })
            except:
                pass
            return
        
        # 1200+ ELO: Stockfish'in kendi mekanizması
        skill = elo_to_skill_level(elo)
        options = {"Skill Level": skill}
        
        try:
            if "UCI_Elo" in self.engine.options:
                uci_elo_option = self.engine.options["UCI_Elo"]
                min_elo = uci_elo_option.min
                max_elo = uci_elo_option.max
                
                if min_elo <= elo <= max_elo:
                    options["UCI_LimitStrength"] = True
                    options["UCI_Elo"] = elo
                else:
                    options["UCI_LimitStrength"] = False
            
            self.engine.configure(options)
        except Exception as e:
            try:
                self.engine.configure({"Skill Level": skill, "UCI_LimitStrength": False})
            except:
                pass
            print(f"ELO ayarlanırken hata (Hata toleransıyla geçiliyor): {e}")

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
