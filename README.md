# ♔ Satranç Pro - Professional Chess Application

Modern, Chess.com tarzı, profesyonel analiz özelliklerine sahip masaüstü satranç uygulaması. Stockfish motoru ile güçlendirilmiş, yüksek doğrulukta analiz ve performans odaklı bir deneyim sunar.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 🎮 Temel Özellikler

### 🤖 Botla Oyna (Professional Engine)
- **Hassas ELO Ayarı**: 100 ile 3200 ELO arası her seviyede rakip.
- **Gerçekçi ELO Simülasyonu**: 4 katmanlı zayıflatma sistemi — 100 ELO gerçekten acemi gibi oynar.
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

## ✏️ Tahta Üzerinde Çizim (Chess.com Tarzı)

Sağ tık basılı tutarak tahta üzerinde ok ve kare vurguları çizebilirsiniz.

| Eylem | Sonuç |
|-------|-------|
| **Sağ tık + sürükle** | İki kare arasında ok çizer |
| **Sağ tık** (tek kare) | Kareyi renkli vurgular |
| **Sol tık** | Tüm çizimleri temizler |

### Renk Kısayolları

| Tuş Kombinasyonu | Renk |
|-------------------|------|
| Sağ tık | 🟢 Yeşil |
| **Ctrl** + Sağ tık | 🔴 Kırmızı |
| **Alt** + Sağ tık | 🔵 Mavi |
| **Shift** + Sağ tık | 🟡 Sarı |

> Oklar ve vurgular hamle yapılana kadar kalıcıdır. Aynı oku tekrar çizerseniz silinir (toggle).

## 🧠 ELO Simülasyon Sistemi

Stockfish'in varsayılan zayıflatması düşük ELO'larda yetersiz kaldığı için **100–1200 arası** her ELO dilimi için özel bir simülasyon sistemi geliştirilmiştir. 1200 üstü Stockfish'in kendi `UCI_Elo` mekanizmasını kullanır.

### Genel Davranış

| ELO Aralığı | Davranış |
|-------------|----------|
| **100–200** | Çok kötü, neredeyse her hamle hata ama bir mantığı var |
| **200–400** | Sık blunder, temel taktikleri göremez |
| **400–600** | Arada iyi hamle yapar ama taktik göremez |
| **600–800** | Çoğunlukla makul hamle, ama önemli anlarda taktik kaçırır |
| **800–1200** | İyi oynar ama hassas pozisyonlarda hata yapar |
| **1200–3200** | Stockfish'in kendi Skill Level ve UCI_Elo mekanizması |

### Detaylı Parametreler

Her hamle için 3 parametre kontrol edilir:

| ELO | Blunder Şansı | En İyi Hamle Şansı | Kabul Edilebilir Kayıp | Analiz Derinliği |
|-----|--------------|--------------------|-----------------------|-----------------|
| 100 | %45 | %5 | 300cp (3 piyon) | 3 |
| 200 | %35 | %10 | 300cp | 3 |
| 300 | %25 | %10 | 200cp | 5 |
| 400 | %18 | %15 | 200cp | 5 |
| 500 | %13 | %20 | 120cp | 7 |
| 600 | %10 | %25 | 120cp | 7 |
| 700 | %8 | %30 | 80cp | 9 |
| 800 | %6 | %35 | 80cp | 9 |
| 900 | %4 | %42 | 50cp | 11 |
| 1000 | %3 | %50 | 50cp | 11 |
| 1100 | %2 | %55 | 30cp | 13 |

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
