# Lina v0.3.0-alpha Release Notes

## Sürüm

`v0.3.0-alpha`

## Durum

Alpha / Release Candidate

Bu sürüm, Lina’nın yerel çalışan masaüstü yapay zeka asistanı olma yolunda erken ama kullanılabilir bir alpha adımıdır. Sürüm; terminal, GUI, yerel Ollama entegrasyonu, proje farkındalığı ve güvenli araç temellerini bir araya getirir.

Bu sürüm production-ready değildir. Bilinen sınırlamalar ve sorunlar saklanmadan aşağıda listelenmiştir.

## Öne Çıkanlar

- Terminal üzerinden çalışan Lina CLI.
- Tkinter tabanlı ilk masaüstü GUI.
- Ollama üzerinden local model entegrasyonu.
- PromptBuilder ile merkezi prompt oluşturma.
- IntentAnalyzer ile minimal intent analizi.
- Bazı güvenli sorular için deterministic responses.
- Session history desteği.
- Runtime ContextManager.
- Project Awareness.
- Read-only Git context.
- Safe Tool Foundation.
- ToolExecutionService.
- Model diagnostics ve kullanıcıya daha anlaşılır bağlantı durumları.

## Mevcut Özellikler

- `python main.py` ile CLI başlatma.
- `python gui.py` ile masaüstü GUI başlatma.
- Ollama üzerinde yapılandırılmış local model ile sohbet.
- Basit intent analizi.
- Bazı kimlik, yardım ve güvenlik odaklı sorularda deterministik cevaplar.
- Çalışma zamanında sınırlı conversation history kullanımı.
- Proje dosyaları ve Git context’i için read-only farkındalık.
- Güvenli araç mimarisi temeli.
- ToolExecutionService ile kontrollü araç yürütme altyapısı.
- Model bağlantı durumunu teşhis eden diagnostics yapısı.

## Bilinen Sınırlamalar

- Lina henüz kalıcı memory sistemine sahip değildir.
- Speech, text-to-speech ve wake word desteği yoktur.
- Vision, screen understanding ve camera desteği yoktur.
- Browser automation ve Windows automation henüz yoktur.
- Lina henüz gerçek anlamda bilgisayarı kontrol etmez.
- Multi-agent yapı henüz uygulanmamıştır.
- GUI hâlâ erken alpha seviyesindedir.
- Tool sistemi güvenli temel seviyededir; geniş yetenek seti henüz eklenmemiştir.

## Bilinen Sorunlar

- GUI’de bazı gerçek kullanıcı akışlarında hâlâ `Lina:Lina:` çift etiket problemi görülebiliyor olabilir.
- Bazı LLM cevaplarında Türkçe kalite sorunu devam edebilir; bu davranış kullanılan yerel modele bağlıdır.
- “Bir gün bilgisayarımı yönetebilecek misin?” gibi gelecek capability soruları henüz deterministic cevaplanmamaktadır; LLM bazen fazla iddialı yanıt verebilir.
- Ollama timeout durumları kullanıcıya düzgün gösterilmektedir, ancak model performansı ve cevap süresi tamamen yerel modelin hızına bağlıdır.

## Çalıştırma

CLI:

```bash
python main.py
```

GUI:

```bash
python gui.py
```

## Test

```bash
python -m pytest
```

Bu sürüm hazırlanırken tam test paketi `224 passed` sonucu vermiştir.

## Sonraki Adımlar

1. GUI actual render path içinde çift etiket problemini kesin olarak düzeltmek.
2. Gelecek capability / bilgisayar kontrolü soruları için deterministic intent ve response eklemek.
3. Türkçe response reliability polish çalışmasını sürdürmek.
4. v0.3.1-alpha veya v0.3.0-alpha hotfix kararını manuel smoke test sonuçlarına göre vermek.
