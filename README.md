# ♔ Satranç - Çevrimdışı Satranç Oyunu

Modern, Chess.com tarzı çevrimdışı satranç uygulaması. Stockfish motoru ile güçlendirilmiştir.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 🎮 Özellikler

### 🤖 Botla Oyna
- **ELO Ayarı**: 100-3200 arası bot seviyesi
- **Süre Kontrolü**: Farklı zaman formatları (1, 2, 3, 5, 10, 15, 30, 60 dakika)
- **Hamle Başı Ek Süre**: 0-10 saniye increment
- **Süresiz Mod**: Zaman baskısı olmadan oyna
- **İpucu Sistemi**: En iyi hamleyi yeşil ok ile göster
- **Renk Seçimi**: Beyaz veya siyah taşlarla oyna

### 👥 Arkadaşla Oyna
- Aynı bilgisayarda 2 kişilik oyun
- Her iki taraf için ayrı süre sayacı
- İpucu sistemi (sırası gelen için)
- Tüm süre kontrol seçenekleri

### 📊 Analiz Modu
- **PGN Import**: Chess.com'dan kopyala-yapıştır
- **Hamle Sınıflandırma**: Chess.com tarzı renkli değerlendirme
- **Accuracy Hesaplama**: Her iki taraf için % doğruluk
- **Hamle Navigasyonu**: İleri/Geri butonları ile analiz

## 🎨 Hamle Renk Kodları

| Hamle Tipi | Renk | Sembol |
|------------|------|--------|
| Efsane (Brilliant) | 🔵 Camgöbeği | !! |
| Harika (Great) | 💙 Mavi | ! |
| İyi (Good) | 💚 Yeşil | |
| Normal | ⚪ Gri | |
| Hatasız (Inaccuracy) | 💛 Sarı | ?! |
| Hata (Mistake) | 🟠 Turuncu | ? |
| Vahim (Blunder) | 🔴 Kırmızı | ?? |

## 📦 Kurulum

### Gereksinimler
- Python 3.10 veya üzeri
- Windows işletim sistemi

### Adımlar

1. **Repoyu klonla**
```bash
git clone https://github.com/kullanici/chess.git
cd chess
```

2. **Sanal ortam oluştur**
```bash
python -m venv env
```

3. **Sanal ortamı aktifle**
```bash
# Windows
.\env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

4. **Bağımlılıkları yükle**
```bash
pip install -r requirements.txt
```

5. **Stockfish motorunu indir**
   - [Stockfish resmi sitesi](https://stockfishchess.org/download/) adresinden Windows sürümünü indir
   - `stockfish-windows-x86-64-avx2.exe` dosyasını `stockfish/` klasörüne koy

6. **Uygulamayı çalıştır**
```bash
python main.py
```

Veya Windows'ta:
```bash
run.bat
```

## 📁 Proje Yapısı

```
chess/
├── main.py                    # Ana uygulama
├── config.py                  # Ayarlar ve sabitler
├── requirements.txt           # Python bağımlılıkları
├── run.bat                    # Windows başlatıcı
├── engine/
│   ├── chess_engine.py        # Satranç mantığı
│   └── stockfish_manager.py   # Stockfish iletişimi
├── gui/
│   ├── main_menu.py           # Ana menü
│   ├── chess_board.py         # Tahta widget'ı
│   ├── game_screen.py         # Oyun ekranı (base)
│   ├── bot_game.py            # Bot modu
│   ├── friend_game.py         # Arkadaş modu
│   ├── analysis_screen.py     # Analiz modu
│   └── components/
│       ├── timer.py           # Süre sayacı
│       ├── move_list.py       # Hamle listesi
│       └── dialogs.py         # Diyalog pencereleri
└── stockfish/
    └── stockfish-windows-x86-64-avx2.exe  # (Manuel indirilmeli)
```

## 🔧 Yapılandırma

`config.py` dosyasından aşağıdaki ayarları değiştirebilirsiniz:

- `STOCKFISH_THREADS`: CPU thread sayısı (varsayılan: 1)
- `STOCKFISH_HASH`: Hash tablosu boyutu MB (varsayılan: 64)
- `MIN_ELO` / `MAX_ELO`: Bot ELO aralığı
- Tahta ve tema renkleri

## 📋 Chess.com Uyumluluğu

### PGN Export
Oyun sonunda "Hamleleri Kopyala" butonuna tıklayarak Chess.com uyumlu PGN alabilirsiniz:

```
[Event "Çevrimdışı Oyun"]
[Site "Çevrimdışı"]
[Date "2026.01.02"]
[White "Sen"]
[Black "Stockfish (1200)"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O 1-0
```

### PGN Import
Analiz modunda Chess.com'dan kopyaladığınız PGN'i doğrudan yapıştırabilirsiniz.

## 🛠️ Teknolojiler

- **Python 3**: Ana programlama dili
- **CustomTkinter**: Modern GUI framework
- **python-chess**: Satranç kuralları ve PGN
- **Stockfish**: Satranç motoru
- **Pillow**: Görsel işleme

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

## 📞 İletişim

Sorularınız için issue açabilirsiniz.

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
