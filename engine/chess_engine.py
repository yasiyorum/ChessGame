"""
Satranç Motoru - python-chess wrapper
Oyun mantığı, hamle validasyonu ve PGN işlemleri
"""
import chess
import chess.pgn
import io
from datetime import datetime
from typing import List, Optional, Tuple, Dict


class ChessEngine:
    """Satranç oyunu yönetim sınıfı"""
    
    def __init__(self):
        self.board = chess.Board()
        self.move_history: List[chess.Move] = []
        self.position_history: List[str] = [self.board.fen()]
        self.game_started = False
        self.game_over = False
        self.result = None
        self.white_player = "Beyaz"
        self.black_player = "Siyah"
        self.event = "Çevrimdışı Oyun"
        
    def reset(self):
        """Oyunu sıfırla"""
        self.board = chess.Board()
        self.move_history = []
        self.position_history = [self.board.fen()]
        self.game_started = False
        self.game_over = False
        self.result = None
        
    def set_players(self, white: str, black: str):
        """Oyuncu isimlerini ayarla"""
        self.white_player = white
        self.black_player = black
        
    def get_legal_moves(self) -> List[chess.Move]:
        """Geçerli hamleleri döndür"""
        return list(self.board.legal_moves)
    
    def get_legal_moves_for_square(self, square: chess.Square) -> List[chess.Move]:
        """Belirli bir kare için geçerli hamleleri döndür"""
        return [move for move in self.board.legal_moves if move.from_square == square]
    
    def is_legal_move(self, from_sq: chess.Square, to_sq: chess.Square, promotion: Optional[chess.PieceType] = None) -> bool:
        """Hamlenin geçerli olup olmadığını kontrol et"""
        move = chess.Move(from_sq, to_sq, promotion=promotion)
        return move in self.board.legal_moves
    
    def make_move(self, move: chess.Move) -> bool:
        """Hamle yap"""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            self.position_history.append(self.board.fen())
            self.game_started = True
            self._check_game_over()
            return True
        return False
    
    def make_move_uci(self, uci: str) -> bool:
        """UCI formatında hamle yap (örn: 'e2e4')"""
        try:
            move = chess.Move.from_uci(uci)
            return self.make_move(move)
        except:
            return False
    
    def make_move_san(self, san: str) -> bool:
        """SAN formatında hamle yap (örn: 'e4', 'Nf3')"""
        try:
            move = self.board.parse_san(san)
            return self.make_move(move)
        except:
            return False
    
    def undo_move(self) -> Optional[chess.Move]:
        """Son hamleyi geri al"""
        if self.move_history:
            move = self.move_history.pop()
            self.position_history.pop()
            self.board.pop()
            self.game_over = False
            self.result = None
            return move
        return None
    
    def _check_game_over(self):
        """Oyun bitip bitmediğini kontrol et"""
        if self.board.is_checkmate():
            self.game_over = True
            self.result = "0-1" if self.board.turn == chess.WHITE else "1-0"
        elif self.board.is_stalemate():
            self.game_over = True
            self.result = "1/2-1/2"
        elif self.board.is_insufficient_material():
            self.game_over = True
            self.result = "1/2-1/2"
        elif self.board.is_fifty_moves():
            self.game_over = True
            self.result = "1/2-1/2"
        elif self.board.is_repetition(3):
            self.game_over = True
            self.result = "1/2-1/2"
    
    def resign(self, color: chess.Color):
        """Terk et"""
        self.game_over = True
        self.result = "0-1" if color == chess.WHITE else "1-0"
    
    def is_check(self) -> bool:
        """Şah durumunda mı?"""
        return self.board.is_check()
    
    def get_turn(self) -> chess.Color:
        """Sıra kimde?"""
        return self.board.turn
    
    def get_turn_str(self) -> str:
        """Sıra kimde? (string)"""
        return "white" if self.board.turn == chess.WHITE else "black"
    
    def get_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        """Belirli bir karedeki taşı döndür"""
        return self.board.piece_at(square)
    
    def get_fen(self) -> str:
        """Mevcut pozisyonun FEN notasyonunu döndür"""
        return self.board.fen()
    
    def set_fen(self, fen: str) -> bool:
        """FEN'den pozisyon yükle"""
        try:
            self.board.set_fen(fen)
            self.move_history = []
            self.position_history = [fen]
            return True
        except:
            return False
    
    def get_pgn(self) -> str:
        """
        Chess.com uyumlu PGN formatında oyunu döndür
        """
        game = chess.pgn.Game()
        
        # Header bilgileri
        game.headers["Event"] = self.event
        game.headers["Site"] = "Çevrimdışı"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = "1"
        game.headers["White"] = self.white_player
        game.headers["Black"] = self.black_player
        game.headers["Result"] = self.result if self.result else "*"
        
        # Hamleleri ekle
        node = game
        temp_board = chess.Board()
        for move in self.move_history:
            node = node.add_variation(move)
            temp_board.push(move)
        
        # PGN string olarak döndür
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return game.accept(exporter)
    
    def get_moves_text(self) -> str:
        """Hamleleri sadece metin olarak döndür (Chess.com paste için)"""
        moves = []
        temp_board = chess.Board()
        
        for i, move in enumerate(self.move_history):
            san = temp_board.san(move)
            if i % 2 == 0:
                move_num = (i // 2) + 1
                moves.append(f"{move_num}. {san}")
            else:
                moves[-1] += f" {san}"
            temp_board.push(move)
        
        return " ".join(moves)
    
    def load_pgn(self, pgn_text: str) -> bool:
        """
        PGN'den oyun yükle (Chess.com uyumlu)
        """
        try:
            pgn_io = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn_io)
            
            if game is None:
                # PGN header yoksa sadece hamleleri parse et
                return self._load_moves_only(pgn_text)
            
            self.reset()
            
            # Header bilgilerini al
            if "White" in game.headers:
                self.white_player = game.headers["White"]
            if "Black" in game.headers:
                self.black_player = game.headers["Black"]
            if "Event" in game.headers:
                self.event = game.headers["Event"]
            if "Result" in game.headers and game.headers["Result"] != "*":
                self.result = game.headers["Result"]
            
            # Hamleleri yükle
            for move in game.mainline_moves():
                self.make_move(move)
            
            return True
        except Exception as e:
            print(f"PGN yükleme hatası: {e}")
            return False
    
    def _load_moves_only(self, moves_text: str) -> bool:
        """Sadece hamle metninden yükle (1. e4 e5 2. Nf3 ...)"""
        try:
            self.reset()
            
            # Temizlik
            text = moves_text.strip()
            # Sonuç gösterimini kaldır
            for result in ["1-0", "0-1", "1/2-1/2", "*"]:
                text = text.replace(result, "")
            
            # Hamle numaralarını ve noktaları kaldır
            import re
            # "1." veya "1..." gibi numaraları kaldır
            text = re.sub(r'\d+\.+\s*', ' ', text)
            
            # Hamleleri ayır
            moves = text.split()
            
            for san in moves:
                san = san.strip()
                if san and not san.isdigit():
                    if not self.make_move_san(san):
                        print(f"Geçersiz hamle: {san}")
                        return False
            
            return True
        except Exception as e:
            print(f"Hamle yükleme hatası: {e}")
            return False
    
    def get_move_count(self) -> int:
        """Toplam hamle sayısı"""
        return len(self.move_history)
    
    def get_fullmove_number(self) -> int:
        """Tam hamle numarası (1, 2, 3...)"""
        return self.board.fullmove_number
    
    def get_king_square(self, color: chess.Color) -> chess.Square:
        """Şahın karesini döndür"""
        return self.board.king(color)
    
    def needs_promotion(self, from_sq: chess.Square, to_sq: chess.Square) -> bool:
        """Terfi gerekli mi?"""
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(to_sq)
            if (piece.color == chess.WHITE and to_rank == 7) or \
               (piece.color == chess.BLACK and to_rank == 0):
                return True
        return False
    
    def get_last_move(self) -> Optional[chess.Move]:
        """Son hamleyi döndür"""
        if self.move_history:
            return self.move_history[-1]
        return None
    
    def get_position_at_move(self, move_index: int) -> str:
        """Belirli bir hamledeki pozisyonu FEN olarak döndür"""
        if 0 <= move_index < len(self.position_history):
            return self.position_history[move_index]
        return self.board.fen()
    
    def go_to_move(self, move_index: int):
        """Belirli bir hamleye git (analiz için)"""
        if 0 <= move_index <= len(self.move_history):
            # Tahtayı baştan kur
            self.board = chess.Board()
            for i in range(move_index):
                self.board.push(self.move_history[i])
