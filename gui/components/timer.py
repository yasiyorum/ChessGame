"""
Satranç Zamanlayıcısı
"""
import customtkinter as ctk
from typing import Callable, Optional
import time
import threading


class ChessTimer(ctk.CTkFrame):
    """Satranç süresi widget'ı"""
    
    def __init__(self, parent, initial_time: int = 300, increment: int = 0,
                 on_timeout: Optional[Callable] = None, player_name: str = "Oyuncu",
                 **kwargs):
        """
        Args:
            parent: Parent widget
            initial_time: Başlangıç süresi (saniye)
            increment: Hamle başı ek süre (saniye)
            on_timeout: Süre bittiğinde çağrılacak fonksiyon
            player_name: Oyuncu ismi
        """
        super().__init__(parent, **kwargs)
        
        self.initial_time = initial_time
        self.remaining_time = initial_time
        self.increment = increment
        self.on_timeout = on_timeout
        self.player_name = player_name
        
        self.is_running = False
        self.is_unlimited = (initial_time <= 0)
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI oluştur"""
        self.configure(fg_color="#262421", corner_radius=10)
        
        # Oyuncu ismi
        self.name_label = ctk.CTkLabel(
            self,
            text=self.player_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#B0B0B0"
        )
        self.name_label.pack(pady=(10, 5), padx=15, anchor="w")
        
        # Süre göstergesi
        self.time_label = ctk.CTkLabel(
            self,
            text=self._format_time(),
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color="#FFFFFF"
        )
        self.time_label.pack(pady=(0, 10), padx=15)
        
    def _format_time(self) -> str:
        """Süreyi MM:SS formatında döndür"""
        if self.is_unlimited:
            return "∞"
        
        minutes = int(self.remaining_time // 60)
        seconds = int(self.remaining_time % 60)
        
        if self.remaining_time < 60:
            # Son dakikada ondalık saniye göster
            return f"{seconds}.{int((self.remaining_time % 1) * 10)}"
        
        return f"{minutes:02d}:{seconds:02d}"
    
    def start(self):
        """Zamanlayıcıyı başlat"""
        if self.is_unlimited or self.is_running:
            return
        
        self.is_running = True
        self._stop_event.clear()
        self._timer_thread = threading.Thread(target=self._countdown, daemon=True)
        self._timer_thread.start()
        
        # Aktif görünüm
        self.configure(fg_color="#3D3A37")
        self.time_label.configure(text_color="#81B64C")
        
    def stop(self):
        """Zamanlayıcıyı durdur"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        # Pasif görünüm
        self.configure(fg_color="#262421")
        self.time_label.configure(text_color="#FFFFFF")
        
    def add_increment(self):
        """Hamle sonu ek süre ekle"""
        if not self.is_unlimited and self.increment > 0:
            self.remaining_time += self.increment
            self._update_display()
    
    def _countdown(self):
        """Geri sayım döngüsü"""
        last_time = time.time()
        
        while self.is_running and self.remaining_time > 0:
            if self._stop_event.wait(0.1):
                break
            
            current_time = time.time()
            elapsed = current_time - last_time
            last_time = current_time
            
            self.remaining_time = max(0, self.remaining_time - elapsed)
            
            # UI güncelleme (thread-safe)
            try:
                self.after(0, self._update_display)
            except:
                break
        
        if self.remaining_time <= 0 and self.is_running:
            self.is_running = False
            self.after(0, self._handle_timeout)
    
    def _update_display(self):
        """Süre göstergesini güncelle"""
        self.time_label.configure(text=self._format_time())
        
        # Son 30 saniyede kırmızı
        if not self.is_unlimited and self.remaining_time < 30:
            self.time_label.configure(text_color="#E84545")
    
    def _handle_timeout(self):
        """Süre bittiğinde"""
        self.time_label.configure(text="0:00", text_color="#E84545")
        if self.on_timeout:
            self.on_timeout()
    
    def reset(self, initial_time: Optional[int] = None):
        """Zamanlayıcıyı sıfırla"""
        self.stop()
        if initial_time is not None:
            self.initial_time = initial_time
            self.is_unlimited = (initial_time <= 0)
        self.remaining_time = self.initial_time
        self._update_display()
        self.time_label.configure(text_color="#FFFFFF")
    
    def set_unlimited(self, unlimited: bool):
        """Süresiz mod ayarla"""
        self.is_unlimited = unlimited
        if unlimited:
            self.stop()
        self._update_display()
    
    def get_remaining(self) -> float:
        """Kalan süreyi döndür"""
        return self.remaining_time
    
    def is_timed_out(self) -> bool:
        """Süre bitti mi?"""
        return not self.is_unlimited and self.remaining_time <= 0
