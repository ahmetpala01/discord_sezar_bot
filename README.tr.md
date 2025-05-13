# Sezar Bot

Müzik, Sohbet ve Araçlar sunan çok amaçlı Discord botu.

<div align="center">

![Discord Bot Durumu](https://img.shields.io/badge/durum-çevrimiçi-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)  
![Docker](https://img.shields.io/badge/docker-supported-blue)

</div>

## 🌟 Özellikler

- 🎵 **Müzik Çalma**: YouTube'dan müzik çalma, durdurma, duraklatma
- 💬 **Sohbet**: Sorulara cevap veren yapay zeka sohbet özelliği
- 🎮 **Steam Profili**: Steam kullanıcı bilgilerini görüntüleme
- 📊 **Hız Testi**: Sunucunun internet hızını test etme
- 🎲 **Kelime Oyunu**: Özel dilbilim kuralları ile Türkçe kelime oyunu
- 🔧 **Moderasyon**: Sunucu yönetimi için temel moderasyon araçları
- 📈 **İstatistikler**: Mesaj istatistikleri ve kullanıcı aktivitelerini takip etme

## 📋 Komutlar

### 🎵 Müzik Komutları
| Komut | Açıklama |
|-------|----------|
| `/play <şarkı adı veya URL>` | YouTube'dan müzik çalar |
| `/pause` | Müziği duraklatır |
| `/resume` | Müziği devam ettirir |
| `/stop` | Müziği durdurur |
| `/join` | Ses kanalına katılır |
| `/leave` | Ses kanalından ayrılır |

### 💬 Sohbet Komutları
| Komut | Açıklama |
|-------|----------|
| `/sorusor <soru>` | Bota soru sorarsınız |
| `/sohbet <mesaj>` | Botla sohbet edersiniz |
| `@Sezar Bot <mesaj>` | Botu etiketleyerek konuşmaya başlayın |

### 🛠️ Araç Komutları
| Komut | Açıklama |
|-------|----------|
| `/steamprofil <kullanıcı adı>` | Steam profil bilgilerini gösterir |
| `/speedtest` | İnternet hız testi yapar |
| `/sunucubilgi` | Sunucu hakkında bilgi verir |
| `/botbilgi` | Bot hakkında teknik bilgileri gösterir |
| `/help [komut]` | Tüm komutlar veya belirli bir komut hakkında yardım gösterir |

### 🎲 Kelime Oyunu Komutları
| Komut | Açıklama |
|-------|----------|
| `/kelimeoyunu` | Türkçe kelime oyununu başlatır |
| `/bitir` | Aktif kelime oyununu sonlandırır |

### 🔒 Moderasyon Komutları
| Komut | Açıklama |
|-------|----------|
| `/warn <üye> <sebep>` | Sunucu üyesini uyarır |
| `/warnings <üye>` | Sunucu üyesinin uyarılarını gösterir |

## 💻 Kendi Sunucunuzda Çalıştırma

### Gereksinimler
- Python 3.11 veya daha yüksek
- Discord Bot Token
- Steam API Anahtarı (Steam özellikleri için)
- FFmpeg (ses desteği için)

### Kurulum

1. Repository'i klonlayın:
   ```bash
   git clone https://github.com/kullanıcıadınız/discord_sezar_bot.git
   cd discord_sezar_bot
   ```

2. Çevre değişkenleri dosyası oluşturun:
   ```bash
   echo "DISCORD_BOT_TOKEN=token_buraya" > .env
   echo "STEAM_API_KEY=api_anahtarı_buraya" >> .env
   ```

3. Gerekli paketleri kurun:
   ```bash
   pip install -r requirements.txt
   ```

4. Botu çalıştırın:
   ```bash
   python main.py
   ```

### Docker Desteği

Botu Docker kullanarak da çalıştırabilirsiniz:

```bash
docker-compose up -d
```

Disk alanını boşaltmak gerektiğinde:
```bash
bash docker-cleanup.sh
```

## 🎮 Durum Bildirimleri

Sezar Bot, durumunu düzenli olarak değiştirerek farklı özelliklerini vurgular:
- 🎵 "Müzik | /play" dinliyor
- 🎮 "Steam bilgisi | /steamprofil" oynuyor
- 👀 "Sorularınızı | /sorusor" izliyor
- 🏆 "En hızlı bot | /speedtest" yarışıyor

## 🔗 Davet Et

[Buraya tıklayarak](https://discord.com/oauth2/authorize?client_id=1369772830937317437) Sezar Bot'u sunucunuza ekleyin!

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! İyileştirme veya yeni özellik önerileriniz varsa, sorun bildirimi açabilir veya pull request gönderebilirsiniz.

## 📜 Lisans

Bu proje açık kaynaklıdır. Forkladığınızda veya değiştirdiğinizde lütfen uygun atıfları ekleyin.