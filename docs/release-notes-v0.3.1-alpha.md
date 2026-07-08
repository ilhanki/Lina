# Lina v0.3.1-alpha Release Notes

## Sürüm

`v0.3.1-alpha`

## Durum

Stabilization Hotfix Adayı

Bu sürüm, `v0.3.0-alpha` sonrasında görülen küçük ama önemli güvenilirlik ve konuşma kalitesi sorunlarını kapatmak için hazırlanmıştır. Yeni büyük capability içermez.

## Öne Çıkanlar

- GUI typing placeholder silme akışı düzeltildi.
- GUI label duplication riskine karşı gerçek render path testleri güçlendirildi.
- Türkçe konuşma kalitesi prompt seviyesinde iyileştirildi.
- Basit selamlaşmalar için deterministic `CASUAL_GREETING` intent eklendi.
- Bilgisayar kontrolü ve gelecek capability soruları için güvenli deterministic status cevabı eklendi.

## Stabilization Gate Durumu

- GUI label duplication: Regresyon testleri mevcut.
- Typing placeholder: Gerçek cevap gelince tamamen siliniyor.
- Casual greeting: `selam`, `naber`, `nasılsın` gibi mesajlar LLM'e gitmeden cevaplanıyor.
- Capabilities cevabı: Mevcut yetenekleri ve eksikleri dürüstçe listeliyor.
- Computer control status: LLM'e gitmeden güvenli ve dürüst cevaplanıyor.
- Ollama yokken deterministic intent'ler çalışmaya devam ediyor.
- Tam test paketi geçiyor.

## Bilinen Sınırlamalar

- Kalıcı Memory henüz yoktur.
- Files capability henüz yoktur.
- Speech, Vision, Camera, Browser Automation ve Windows Automation henüz yoktur.
- Lina henüz gerçek anlamda bilgisayarı kontrol etmez.
- LLM kullanılan serbest chat cevaplarında kalite kullanılan yerel modele bağlıdır.

## Test

```bash
python -m pytest
```

Bu stabilization çalışması sırasında tam test paketi `250 passed` sonucu vermiştir.

## Sonraki Ana Milestone

Bir sonraki ana geliştirme hattı `v0.4.0-alpha - Memory Capability v1` olacaktır.
