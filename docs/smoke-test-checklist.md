# Lina Smoke Test Checklist

Bu doküman `v0.3.0-alpha` öncesi manuel doğrulama adımlarını tanımlar.

## Ön Koşullar

- Python sanal ortamı aktif olmalı.
- Geliştirme bağımlılıkları kurulmuş olmalı.
- Normal sohbet testi için Ollama çalışıyor olmalı.
- `config/default.toml` içinde tanımlı model yerelde yüklü olmalı.

## Otomatik Test

```powershell
python -m pytest
```

Beklenen sonuç:

- Tüm testler başarılı olmalı.

## CLI Smoke Test

```powershell
python main.py
```

Kontroller:

- CLI banner görünür.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina` normal chat olarak Ollama'ya gider.
- `exit` veya `quit` uygulamayı kapatır.

## GUI Smoke Test

```powershell
python gui.py
```

Kontroller:

- Lina penceresi açılır. Özel header ("Lina", "Personal AI Assistant") ve sağ alt köşede status bar ("Bağlanıyor...", "Bağlı") görünür.
- Input alanı focus alır.
- Üstte "Clear Chat" ve "Copy Last Response" butonları mevcuttur.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina bugün nasılsın?` normal chat olarak Ollama'ya gider.
- Cevap beklenirken input alanı disable olur, status bar "Düşünüyor..." veya benzeri durumu yansıtır.
- Cevap gelince input tekrar aktif olur.
- Yeni mesajlarda sohbet alanı aşağı kayar.
- "Copy Last Response" butonuna basıldığında son asistan cevabı panoya kopyalanır.
- "Clear Chat" butonuna basıldığında sohbet geçmişi temizlenir.

## Ollama Kapalıyken Davranış

Ollama kapalıyken GUI başlat.

Beklenen sonuç:

- Sağ alt status bar "Ulaşılamıyor" (Kırmızı) durumuna geçer.
- Ollama kapalıyken mesaj atıldığında uygulama çökmez.
- Traceback gösterilmez.
- Kullanıcıya kısa Türkçe hata mesajı gösterilir.

## Project Awareness Smoke Test

CLI veya GUI içinde şu mesajları dene:

```text
Lina projesinin durumu ne?
Şu an hangi branch üzerindeyim ve working tree nasıl?
Bugün Lina projesinde ne yaptık?
Son sprintlerde ne eklendi?
```

Beklenen sonuç:

- Lina, izinli proje dokümanlarına ve aktif okunabilir Git verisine (branch, status, log) dayalı cevap verir.
- Sahte GitHub URL, sahte commit veya sahte dosya uydurmaz.
- Bilmediği noktaları dürüstçe sınırlar.

## Safe Tool Smoke Test

```text
Saat kaç?
```

Beklenen sonuç:

- Cevap Brain/Ollama'ya gitmeden SAFE tool akışı üzerinden üretilir.
- Shell, dosya sistemi veya tehlikeli işlem çalışmaz.

## Bilinen Sınırlar

- Bu checklist otomatik release testi değildir.
- GUI görsel doğrulaması manuel yapılır.
- Ollama model kalitesi yerel modele bağlıdır.
