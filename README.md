# ♔ Satranç Pro - Professional Chess Application

Modern, Chess.com tarzı, profesyonel analiz özelliklerine sahip masaüstü satranç uygulaması. Stockfish motoru ile güçlendirilmiş, yüksek doğrulukta analiz ve performans odaklı bir deneyim sunar.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 🎮 Temel Özellikler

### 🤖 Botla Oyna (Professional Engine)
- **Hassas ELO Ayarı**: 100 ile 3200 ELO arası her seviyede rakip.
- **Dinamik Süre Kontrolü**: Bullet, Blitz ve Rapid formatları (1, 3, 5, 10, 30, 60 dk).
- **Artırmalı Süre (Increment)**: Hamle başına ek süre desteği.
- **Görsel İpucu Sistemi**: En iyi hamleleri tahta üzerinde yeşil oklar ile görme.

### 👥 Yerel Çok Oyunculu
- Aynı bilgisayar üzerinden arkadaşınızla profesyonel süre kontrolü eşliğinde maç yapın.

### 📊 Gelişmiş Analiz Ekranı (Chess.com Standartlarında)
- **İnteraktif Tahta**: Analiz sırasında taşları serbestçe hareket ettirin, varyasyonları keşfedin.
- **Top 3 Hamle Önerisi**: Stockfish Multipv analizi ile o anki konumun en iyi 3 devam yolunu görün.
- **Canlı Ok Yardımı**: En iyi hamleyi tahta üzerinde anlık ok ile takip edin.
- **CAPS 2.0 Doğruluk Hesaplaması**: Chess.com'un resmi $103.1668 \times e^{-0.04354 \times \text{wp\_loss\%}} - 3.1668$ formülü ile maç sonu analiz.
- **Performans ELO Tahmini**: Maç performansınıza göre tahmini ELO seviyeniz.
- **Brilliant (!!) Sistemi**: Gerçek feda gerektiren efsanevi hamlelerin tespiti.

### 📜 Maç Geçmişi & Senkronizasyon
- **Kalıcı Geçmiş**: Oynadığınız tüm maçlar otomatik kaydedilir, istediğiniz zaman analiz edilebilir.
- **Bulut Senkronizasyonu**: Temalar ve Stockfish motoru otomatik olarak GitHub üzerinden %APPDATA% klasörüne senkronize edilir.

## 🎨 Hamle Sınıflandırma Sistemi

| Hamle Tipi | Sembol | Renk | Açıklama |
|------------|--------|------|----------|
| **Brilliant** | !! | 🔵 Camgöbeği | Materyal feda ederek üstünlük sağlayan efsane hamle |
| **Great** | ! | 💙 Mavi | Pozisyonu ciddi şekilde iyileştiren hamle |
| **Best** | ★ | 💚 Koyu Yeşil | Motorun birinci sıradaki tercihi |
| **Book** | 📖 | 🟫 Kahverengi | Açılış teorisi hamlesi |
| **Good** | ✓ | ⚪ Beyaz | Pozisyonu koruyan sağlam hamle |
| **Inaccuracy** | ?! | 💛 Sarı | Avantajı hafifçe azaltan yanlışlık |
| **Mistake** | ? | 🟠 Turuncu | Avantajı ciddi şekilde kaybettiren hata |
| **Blunder** | ?? | 🔴 Kırmızı | Oyunu kaybettirebilecek vahim hata |
| **Miss** | X | 🔴 Parlak Kırmızı | Galibiyeti veya büyük avantajı kaçıran hamle |

## 📦 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.10 veya üzeri
- `requests`, `customtkinter`, `python-chess`, `Pillow` kütüphaneleri

### Hızlı Başlangıç
1. **Repoyu Klonlayın**:
   ```bash
   git clone https://github.com/yasiyorum/ChessGame
   cd ChessGame
   ```
2. **Bağımlılıkları Yükleyin**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Uygulamayı Başlatın**:
   ```bash
   python main.py
   ```

## 📁 Dosya Yapısı
- `AppData/Roaming/ChessPro`: Tüm kullanıcı ayarları, temalar ve maç geçmişi burada güvenle saklanır.
- `themes/`: Kendi özel taş resimlerinizi ve tahta renklerinizi ekleyebileceğiniz tema klasörü.

## 🤝 Katkıda Bulunma
Feature branch'ler açarak veya issue bildirerek projeye katkıda bulunabilirsiniz.

---
⭐ **Emeğe saygı için yıldız vermeyi unutmayın!**
