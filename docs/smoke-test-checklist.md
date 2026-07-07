# Lina Smoke Test Checklist

Bu doküman `v0.2.0-alpha` öncesi manuel doğrulama adımlarını tanımlar.

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

- Lina penceresi açılır.
- Input alanı focus alır.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina bugün nasılsın?` normal chat olarak Ollama'ya gider.
- Cevap beklenirken input ve gönder butonu disable olur.
- Cevap gelince input tekrar aktif olur.
- Yeni mesajlarda sohbet alanı aşağı kayar.

## Ollama Kapalıyken Davranış

Ollama kapalıyken GUI üzerinden normal chat mesajı gönder.

Beklenen sonuç:

- Uygulama çökmez.
- Traceback gösterilmez.
- Kullanıcıya kısa Türkçe hata mesajı gösterilir.

## Project Awareness Smoke Test

CLI veya GUI içinde şu mesajları dene:

```text
Lina projesinin durumu ne?
Bugün Lina projesinde ne yaptık?
Son sprintlerde ne eklendi?
```

Beklenen sonuç:

- Lina izinli proje dokümanlarına dayalı cevap verir.
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
