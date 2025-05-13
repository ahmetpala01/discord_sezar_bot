# Discord Bot Kelime Oyunu - Türkçe

## İçindekiler
- [Discord Bot Kelime Oyunu - Türkçe](#discord-bot-kelime-oyunu---türkçe)
  - [İçindekiler](#i̇çindekiler)
  - [Giriş](#giriş)
  - [Türkçe Kelime Kuralları](#türkçe-kelime-kuralları)
  - [Geliştirme Durumu](#geliştirme-durumu)
  - [Nasıl Kullanılır](#nasıl-kullanılır)
  - [Katkıda Bulunma](#katkıda-bulunma)
  - [Kelime Listesi](#kelime-listesi)
  - [Not](#not)

## Giriş
Bu Discord botu, Türkçe kelimelere dayalı bir kelime oyunu oynamanızı sağlar. Oyunda, bir kullanıcı bir kelime yazar ve sonraki kullanıcı o kelimenin son harfiyle başlayan yeni bir kelime yazmak zorundadır. Ancak, yalnızca Türkçe kelimeler kabul edilir ve belirli Türkçe dil kurallarına uymalıdır.

## Türkçe Kelime Kuralları
Bir kelimenin oyun için geçerli olabilmesi için aşağıdaki kurallara uyması gerekir:

1. **Kelime Listesi**: Kelime, `word.txt` dosyasında bulunmalıdır. Bu dosya, Türkçe kelimelerin bir listesini içerir.
2. **Hece Kuralı**: Bir kelimenin ilk hecesi dışındaki hecelerde 'o' veya 'ö' olmamalıdır. Bu, kelimenin aslen Türkçe olduğunu garanti etmek için kullanılan bir kuraldır.
3. **Uzun Ünlüler**: Kelime, 'â', 'î', 'û' gibi uzun ünlüler içermemelidir. Bu ünlüler genellikle Arapça veya Farsça ödünç kelimelerde bulunur.
4. **Büyük-Küçük Harf Duyarlılığı**: Kelimeler büyük-küçük harf duyarlılığı gözetilmeksizin kontrol edilir, yani tüm kelimeler küçük harfe çevrilir.

## Geliştirme Durumu
Bu bot hala geliştirme aşamasındadır ve hatalar içerebilir. Özellikle, heceleme algoritması basittir ve her zaman doğru olmayabilir. Ayrıca, kelime listesi kapsamlı değildir ve daha fazla kelime eklenebilir.

## Nasıl Kullanılır
- Botu sunuya eklemek için, Discord Developer Portal'dan bir bot oluşturun ve token'ını alın.
- `main.py` dosyasındaki `YOUR_BOT_TOKEN` yerine bot token'ınızı yerleştirin.
- Botu çalıştırmak için `python main.py` komutunu kullanın.
- Oyunu başlatmak için `/kelimeoyunu` komutunu kullanın.
- Oyunu bitirmek için `/bitir` komutunu kullanın.
- Oyun sırasında, geçerli Türkçe kelimeler yazarak oynayabilirsiniz.

## Katkıda Bulunma
Bu proje açık kaynaklıdır ve katkılarınızı bekliyoruz. Eğer hata bulduysanız veya yeni özellikler eklemek istiyorsanız, lütfen GitHub üzerinden pull request gönderin.

## Kelime Listesi
- `word.txt` dosyası, oyun için geçerli kelimeleri içerir.
- Bu dosyaya yeni kelimeler eklemek mümkündür, ancak eklenen kelimelerin Türkçe olmasını sağlamalısınız.

## Not
Bu bot, geliştirici tarafından hala geliştirilmekte olup, hatalar içerebilir. Eğer herhangi bir sorunla karşılaşırsanız, lütfen geliştiriciye bildirin veya katkıda bulunarak yardımcı olun.