"""
Ana Menü Ekranı
"""
import customtkinter as ctk
from typing import Callable, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import THEME


class MainMenu(ctk.CTkFrame):
    """Ana menü ekranı"""
    
    def __init__(self, parent, 
                 on_bot_game: Optional[Callable] = None,
                 on_friend_game: Optional[Callable] = None,
                 on_analysis: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_bot_game = on_bot_game
        self.on_friend_game = on_friend_game
        self.on_analysis = on_analysis
        
        self.configure(fg_color=THEME["bg_primary"])
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        # Merkez container
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Başlık
        title_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 40))
        
        # Satranç sembolleri
        ctk.CTkLabel(
            title_frame,
            text="♔ SATRANÇ ♚",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Çevrimdışı Satranç Oyunu",
            font=ctk.CTkFont(size=16),
            text_color=THEME["text_secondary"]
        ).pack(pady=(5, 0))
        
        # Butonlar
        buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Botla Oyna
        self._create_menu_button(
            buttons_frame,
            text="🤖  Botla Oyna",
            subtitle="Stockfish motoruna karşı oyna",
            command=self._on_bot_click
        ).pack(pady=10)
        
        # Arkadaşla Oyna
        self._create_menu_button(
            buttons_frame,
            text="👥  Arkadaşla Oyna",
            subtitle="Aynı bilgisayarda 2 kişi oyna",
            command=self._on_friend_click
        ).pack(pady=10)
        
        # Analiz
        self._create_menu_button(
            buttons_frame,
            text="📊  Analiz Yap",
            subtitle="Oyunlarını analiz et",
            command=self._on_analysis_click
        ).pack(pady=10)
        
        # Alt bilgi
        footer = ctk.CTkLabel(
            self,
            text="Stockfish motoru ile güçlendirilmiştir",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        footer.place(relx=0.5, rely=0.95, anchor="center")
    
    def _create_menu_button(self, parent, text: str, subtitle: str, 
                           command: Callable) -> ctk.CTkFrame:
        """Menü butonu oluştur"""
        frame = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_secondary"],
            corner_radius=15,
            cursor="hand2"
        )
        frame.configure(width=350, height=80)
        frame.pack_propagate(False)
        
        # İçerik
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            content,
            text=text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            content,
            text=subtitle,
            font=ctk.CTkFont(size=12),
            text_color=THEME["text_secondary"],
            anchor="w"
        ).pack(fill="x")
        
        # Hover efektleri
        def on_enter(e):
            frame.configure(fg_color=THEME["button_hover"])
        
        def on_leave(e):
            frame.configure(fg_color=THEME["bg_secondary"])
        
        def on_click(e):
            command()
        
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        frame.bind("<Button-1>", on_click)
        
        # Alt widget'lara da bind et
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)
            for subchild in child.winfo_children():
                subchild.bind("<Enter>", on_enter)
                subchild.bind("<Leave>", on_leave)
                subchild.bind("<Button-1>", on_click)
        
        return frame
    
    def _on_bot_click(self):
        if self.on_bot_game:
            self.on_bot_game()
    
    def _on_friend_click(self):
        if self.on_friend_game:
            self.on_friend_game()
    
    def _on_analysis_click(self):
        if self.on_analysis:
            self.on_analysis()
