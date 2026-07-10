# Lina Speech Architecture v1

## Amaç

Bu doküman, Lina'nın `v0.6.0-alpha` Speech Capability v1 geliştirmesine başlamadan önce konuşma mimarisini, güvenlik sınırlarını, kullanıcı deneyimini ve uygulama planını netleştirir.

Bu bir implementation dokümanı değildir. Bu doküman, speech capability geliştirilirken hangi davranışların güvenli kabul edileceğini, hangi sınırların aşılmayacağını ve ilk sürümün hangi kapsamda tutulacağını tanımlar.

Speech özelliği Lina için önemlidir; çünkü masaüstü asistan deneyimi yalnızca yazılı sohbetten ibaret kalmamalıdır. Ancak ses, kullanıcı mahremiyeti açısından yüksek hassasiyet taşır. Bu nedenle speech geliştirmesi etkileyici görünmek için değil, kontrollü, açık ve test edilebilir davranışlarla başlatılmalıdır.

## Kapsam

Speech Capability v1 uzun vadede iki ana yeteneği kapsayabilir:

- STT: Kullanıcının sesini metne dönüştürme.
- TTS: Lina'nın yazılı cevabını sesli okuması.

`v0.6.0-alpha` için hedef, bu iki alanı aynı anda tam üretim kalitesinde çözmek değildir. İlk hedef, güvenli ve küçük bir speech temelini kurmak, GUI'deki Mic butonunun gelecekte nasıl davranacağını netleştirmek ve gerçek implementation başlamadan önce test edilebilir sınırları belirlemektir.

## Kapsam Dışı

Bu plan sprintinde ve ilk mimari dokümanda aşağıdakiler kapsam dışıdır:

- Gerçek mikrofon erişimi.
- Ses kaydı alma.
- Ses dosyası kaydetme.
- STT engine implementation.
- TTS engine implementation.
- Wake word.
- Always-on listening.
- Background recording.
- Cloud speech servisi entegrasyonu.
- Yeni dependency ekleme.
- Speech üzerinden Windows automation tetikleme.
- Speech üzerinden shell command execution.
- Kullanıcı onayı olmadan otomatik mesaj gönderme.

Bu sınırlar özellikle erken aşamada önemlidir. Speech capability, doğrudan bilgisayar mikrofonu ve kişisel konuşma verisiyle ilişkili olduğu için güvenlik ve mahremiyet tasarımı implementation'dan önce gelmelidir.

## Güvenlik İlkeleri

### 1. No Always-On Listening

Lina arka planda sürekli dinlememelidir.

Sürekli dinleme, kullanıcı farkındalığını azaltır ve güven ilişkisini zedeler. Lina'nın kişisel asistan olması, kullanıcının bilgisayarında görünmez şekilde dinleme hakkı olduğu anlamına gelmez.

### 2. Explicit User Action

Ses dinleme yalnızca kullanıcı açıkça Mic butonuna bastığında başlamalıdır.

Bu ilke hem kullanıcı deneyimi hem de mahremiyet açısından temel sınırdır. Lina, kullanıcının açık eylemi olmadan mikrofonu başlatmamalıdır.

### 3. Local-First

Ses verisi mümkün olduğunca yerel işlenmelidir.

Lina'nın genel felsefesi local-first olduğu için speech capability de bu çizgiyi korumalıdır. Cloud tabanlı speech servisleri ancak ayrı bir mimari değerlendirme, açık kullanıcı onayı ve güçlü gerekçeyle ele alınabilir.

### 4. No Audio Persistence By Default

Ses kayıtları varsayılan olarak kaydedilmemelidir.

STT için geçici audio buffer gerekirse bu veri işlem tamamlandıktan sonra tutulmamalıdır. Kalıcı ses kaydı ancak kullanıcı açıkça isterse ve ayrı bir güvenlik tasarımı yapılırsa değerlendirilebilir.

### 5. No Background Recording

Kullanıcı bilmeden kayıt yoktur.

Bu ilke, teknik davranış kadar ürün kimliği açısından da önemlidir. Lina güvenilir bir kişisel asistan olmalı, görünmez bir kayıt sistemi olmamalıdır.

### 6. Visual Status

Mikrofon aktifken GUI'de net ve görünür bir durum gösterilmelidir.

Örnek durumlar:

- `Dinliyorum...`
- `Metne dönüştürülüyor...`
- `Mikrofon hazır değil`

Kullanıcı, Lina'nın ne zaman dinlediğini ve ne zaman dinlemediğini her an anlayabilmelidir.

### 7. Graceful Fallback

Speech engine yoksa Lina bunu açıkça söylemelidir.

Örneğin Mic butonuna basıldığında engine hazır değilse Lina şu tür kısa bir mesaj verebilir:

`Mikrofon motoru henüz hazır değil İlhan.`

Bu davranış sessiz başarısızlıktan veya sahte başarıdan daha güvenilirdir.

### 8. Permission Clarity

Mikrofon erişimi kullanıcı eylemiyle ilişkilendirilmelidir.

İşletim sistemi izin penceresi çıkarsa, bu izin Mic butonuna basma gibi açık bir eylemin sonucu olmalıdır. Lina arka planda izin istememelidir.

### 9. Testable Interfaces

Speech akışı gerçek mikrofon olmadan test edilebilir olmalıdır.

Fake speech service, fake STT provider ve fake TTS provider ile GUI, ConversationService ve speech state davranışları test edilebilmelidir. Testler gerçek cihaz, driver veya mikrofon iznine bağlı olmamalıdır.

### 10. No Autonomous Speech Actions

Lina kendi kendine dinleme başlatmamalıdır.

Speech capability, agent veya background task altyapısı büyüse bile bu ilkeyi korumalıdır. Kullanıcı eylemi olmadan mikrofon açmak release blocker kabul edilmelidir.

## STT ve TTS Öncelik Değerlendirmesi

### Seçenek A: TTS First

TTS-first yaklaşımında Lina yazılı cevabını sesli okuyabilir.

Artıları:

- Mikrofon erişimi gerekmez.
- Mahremiyet riski daha düşüktür.
- Kullanıcıya hızlı bir sesli asistan hissi verir.
- Test etmesi STT'ye göre daha kolaydır.

Eksileri:

- Kullanıcı hâlâ metin yazar.
- Asistanla doğal konuşma deneyimi tam başlamaz.
- TTS engine seçimi platform ve dependency açısından ayrıca değerlendirme ister.

### Seçenek B: STT First

STT-first yaklaşımında kullanıcı mikrofona konuşur, Lina konuşmayı metne çevirir.

Artıları:

- Gerçek sesli giriş deneyimi başlar.
- GUI'deki Mic butonunun ana anlamı karşılanır.
- Desktop assistant vizyonuna güçlü bir adım olur.

Eksileri:

- Mikrofon izni gerekir.
- Ses verisi daha hassastır.
- Engine seçimi, latency, cihaz erişimi ve hata yönetimi daha zordur.
- Test stratejisi daha dikkatli tasarlanmalıdır.

### Seçenek C: Push-to-Talk STT + Optional No-Op TTS Interface

Bu yaklaşımda ilk sürüm için Mic butonu explicit user action olarak kullanılır. Kullanıcı Mic butonuna basınca tek seferlik dinleme/transcription akışı planlanır. TTS tarafında ise gerçek konuşma motoru eklenmeden, gelecekteki mimariye yer açan no-op veya disabled interface tasarlanabilir.

Artıları:

- Always-on listening riskini baştan engeller.
- GUI Mic butonuyla doğrudan uyumludur.
- STT akışı güvenli sınırla başlar.
- TTS geleceği için mimari alan açılır ama gereksiz implementation yapılmaz.

Eksileri:

- STT engine seçimi yine gereklidir.
- İlk sürümde TTS kullanıcıya aktif görünmeyebilir.
- Dependency kararı ayrı sprint ister.

## Önerilen v0.6.0-alpha Kapsamı

Önerilen ilk implementation scope:

**Push-to-talk STT skeleton + optional no-op TTS interface.**

Gerekçe:

- Lina'nın GUI'sinde Mic butonu zaten vardır.
- Kullanıcı eylemine bağlı speech başlangıcı güvenlik ilkeleriyle uyumludur.
- Always-on listening baştan kapsam dışı bırakılır.
- İlk sürümde transcription sonucunu otomatik göndermek yerine input alanına yazmak daha güvenlidir.
- Kullanıcı metni görür, düzeltir ve kendi onayıyla gönderir.
- TTS için interface alanı bırakılır, ancak gerçek TTS dependency'si aceleyle eklenmez.

Bu karar kesin implementation seçimi değildir. Gerçek engine seçimi ve dependency kararı bir sonraki sprintte kullanıcı onayıyla yapılmalıdır.

## Local-First Yaklaşım

Speech capability mümkün olduğunca local-first çalışmalıdır.

Local-first ilkesi burada üç anlam taşır:

- Ses verisi varsayılan olarak cihaz dışına çıkmaz.
- Transcription ve synthesis mümkünse yerel engine ile yapılır.
- Cloud servis kullanılacaksa bu varsayılan değil, açıkça seçilmiş ve dokümante edilmiş bir mod olur.

Bu yaklaşım, Lina'nın kişisel asistan kimliğiyle uyumludur. Kullanıcının sesi, yazılı prompt'lardan daha hassas veri kabul edilmelidir.

## Dependency Politikası

`v0.6.0-alpha` skeleton aşamasında yeni dependency eklenmemiştir. `v0.6.1-alpha` için açık onayla yalnız `faster-whisper` ve `sounddevice` runtime dependency olarak eklenmiştir. TTS, cloud speech, Torch/CUDA veya alternatif STT paketleri bu kararın parçası değildir.

Gelecek sprintte speech engine seçimi yapılırken her dependency şu sorularla değerlendirilmelidir:

- Runtime dependency mi, development dependency mi?
- Yerel çalışabiliyor mu?
- Windows üzerinde güvenilir mi?
- Test ortamında fake provider ile izole edilebiliyor mu?
- Kullanıcıdan mikrofon izni isteme davranışı açık mı?
- Cloud bağlantısı var mı?
- Lisansı proje hedefiyle uyumlu mu?
- Paket boyutu ve kurulum karmaşıklığı kabul edilebilir mi?

## Olası STT Seçenekleri

Bu doküman güncel paket seçimi yapmaz. Aşağıdaki liste yalnızca değerlendirme alanını açar.

### Windows Built-In Speech

Artıları:

- Windows ile doğal entegrasyon potansiyeli vardır.
- Ek model dosyası gerektirmeyebilir.

Eksileri:

- Python entegrasyonu karmaşık olabilir.
- Test ve CI izolasyonu zor olabilir.
- Yerel dil kalitesi değişken olabilir.

### Offline / Local STT Engine

Örnek değerlendirme adayları:

- Whisper.cpp
- faster-whisper
- Vosk

Artıları:

- Local-first hedefiyle uyumludur.
- Cloud bağımlılığını azaltır.
- Bazı engine'ler offline çalışabilir.

Eksileri:

- Model dosyası gerekebilir.
- CPU/GPU performansı önemli hale gelir.
- Paket boyutu ve kurulum karmaşıklığı artabilir.
- Güncel seçim için ayrıca araştırma gerekir.

## Olası TTS Seçenekleri

Bu doküman TTS paketi seçmez; yalnızca değerlendirme alanı açar.

Olası seçenekler:

- Windows SAPI
- pyttsx3
- edge-tts
- Yerel TTS modelleri

Değerlendirme notları:

- Windows SAPI local kullanım açısından değerlendirilebilir.
- pyttsx3 basit olabilir ancak kalite ve platform davranışı test edilmelidir.
- edge-tts kalite açısından iyi olabilir, fakat cloud bağımlılığı ve privacy çizgisi ayrıca değerlendirilmelidir.
- Yerel TTS modelleri uzun vadede daha uyumlu olabilir, ancak ilk sürüm için ağır olabilir.

## Taslak Servis Mimarisi

Önerilen modül:

```text
src/lina/speech/
  models.py
  speech_service.py
  stt_provider.py
  tts_provider.py
```

Bu sınırlar `v0.6.0-alpha` ve `v0.6.1-alpha` implementationlarında somutlaştırılmıştır. Provider, recorder, model ve servis sorumlulukları speech paketi içinde ayrı tutulur.

### SpeechService

Planlanan sorumluluk:

- Speech availability bilgisini sağlamak.
- Kullanıcı eylemiyle dinleme başlatmak.
- Dinlemeyi durdurmak.
- Tek seferlik transcription akışını yönetmek.
- TTS provider varsa metin okutmak.
- Speech state bilgisini GUI'ye anlaşılır şekilde sunmak.

Taslak public davranış:

- `is_available()`
- `start_listening()`
- `stop_listening()`
- `transcribe_once()`
- `speak(text)`
- `stop_speaking()`

### STTProvider

Planlanan sorumluluk:

- Ses girdisini metne dönüştürmek.
- Engine-specific detayları SpeechService dışına almak.

Taslak davranış:

- `transcribe_once() -> SpeechTranscriptionResult`

### TTSProvider

Planlanan sorumluluk:

- Metni sesli okumak.
- Engine-specific TTS detaylarını SpeechService dışına almak.

Taslak davranış:

- `speak(text) -> SpeechSynthesisResult`

## Speech State Modeli

Planlanan state'ler:

- `IDLE`: Speech sistemi pasif.
- `LISTENING`: Kullanıcı eylemiyle mikrofon dinleniyor.
- `TRANSCRIBING`: Ses metne dönüştürülüyor.
- `SPEAKING`: Lina metni sesli okuyor.
- `ERROR`: Speech akışında hata oluştu.
- `UNAVAILABLE`: Speech engine hazır değil.

Bu state'ler GUI status bar ve testler için önemlidir. Kullanıcı, speech sisteminin ne yaptığını görsel olarak anlayabilmelidir.

## GUI Mic Button Planı

`v0.6.1-alpha` ile Mic butonu local push-to-talk akışına bağlanmıştır.

Speech implementation geldiğinde önerilen davranış:

1. Kullanıcı Mic butonuna basar.
2. GUI status bar `Dinliyorum...` durumuna geçer.
3. Kullanıcı ikinci kez Mic butonuna basabilir; sessizlik veya maksimum süre sınırı da kaydı bitirebilir.
4. SpeechService kaydı yerel modele iletir.
5. Transcription tamamlanınca metin input alanına veya mevcut taslağın sonuna yazılır.
6. Kullanıcı metni kontrol eder.
7. Kullanıcı Enter veya Gönder ile mesajı gönderir.

İlk sürümde otomatik gönderme önerilmez. Kullanıcının konuşmasının yanlış algılanması mümkündür; bu nedenle transcription sonucunu input alanına yazmak daha güvenli bir UX sağlar.

Hata durumunda Lina kısa ve açık bir mesaj göstermelidir:

- `Mikrofon motoru hazır değil İlhan.`
- `Ses metne dönüştürülemedi. Tekrar deneyebilirsin.`
- `Speech özelliği bu sistemde henüz kullanılabilir değil.`

## Privacy Rules

- Ses verisi varsayılan olarak kaydedilmez.
- Transcription tamamlandıktan sonra geçici audio buffer tutulmaz.
- Speech geçmişi memory sistemine otomatik yazılmaz.
- Kullanıcının açık memory komutu olmadan konuşmadan kalıcı kişisel bilgi çıkarılmaz.
- Cloud speech servisi varsayılan olarak kullanılmaz.
- Debug log içinde ham audio veya hassas transcription saklanmaz.

## Error ve Fallback Davranışı

Speech engine hazır değilse Lina bunu açıkça söylemelidir.

Önerilen fallback davranışları:

- Mic butonu çalışır, ancak placeholder veya unavailable mesajı gösterir.
- GUI donmaz.
- Input alanı kullanılabilir kalır.
- Status bar hata sonrası tekrar `Hazır` durumuna döner.
- Test ortamında fake speech service ile aynı davranış doğrulanır.

## Test Stratejisi

Speech implementation testleri gerçek mikrofon gerektirmemelidir.

Önerilen test kapsamı:

- SpeechService state transition testleri.
- STTProvider fake transcription testleri.
- TTSProvider fake speak testleri.
- Engine unavailable fallback testleri.
- GUI Mic button status update testleri.
- Transcription sonucunun input alanına yazılması testi.
- Hata durumunda GUI'nin resetlenmesi testi.
- No audio persistence davranışının test edilebilir sınırları.
- Always-on listening başlatılmadığını doğrulayan regression testleri.

## Release Planı

### Planning Sprint

Bu doküman oluşturulur. Güvenlik ilkeleri, scope ve dependency değerlendirme alanı netleşir.

### Implementation Sprint 1

Önerilen kapsam:

- Speech models.
- SpeechService skeleton.
- STTProvider protocol.
- TTSProvider protocol veya no-op TTS provider.
- GUI Mic button'ın fake SpeechService ile entegrasyonu.
- Gerçek microphone engine olmadan test coverage.

### Implementation Sprint 2

Kullanıcı onayıyla `faster-whisper` ve `sounddevice` seçildi. Türkçe multilingual `base` model, CPU ve int8 varsayılanlarıyla local push-to-talk implementation tamamlandı.

Bu sprintte şu kararlar gerekir:

- TTS mi, STT mi önce uygulanacak?
- Speech local-only zorunlu mu?
- Yeni dependency eklenmesine izin var mı?
- Transcription input'a mı yazılacak, otomatik mi gönderilecek?

### Release Candidate

- Full test.
- Manuel GUI smoke test.
- Mic button UX doğrulaması.
- Engine unavailable fallback doğrulaması.
- Privacy ve logging kontrolü.

## Karara Bağlanan Sorular

1. İlk gerçek engine STT olarak seçildi; TTS sonraki değerlendirmeye bırakıldı.
2. İlk sürüm local-first çalışır ve cloud speech kullanmaz.
3. Yalnız `faster-whisper` ve `sounddevice` dependency'lerine izin verildi.
4. Transcription input alanına yazılır ve otomatik gönderilmez.

## Açık Sorular

5. TTS cevapları varsayılan olarak açık mı olmalı, kullanıcı toggle'ı mı gerektirmeli?
6. Speech state GUI dışında ileride event bus ile yayınlanmalı mı?
7. Wake word hangi milestone'a kadar kesin kapsam dışı kalmalı?

## Sonuç

Speech Capability v1, Lina'nın masaüstü asistan kimliğini güçlendirecek önemli bir adımdır. Ancak bu capability, mikrofon ve ses verisi nedeniyle yüksek güvenlik hassasiyeti taşır.

Bu nedenle önerilen yön, `v0.6.0-alpha` için güvenli ve küçük başlamaktır:

`v0.6.0-alpha` ile push-to-talk skeleton, `v0.6.1-alpha` ile local `faster-whisper` STT ve `sounddevice` recorder tamamlanmıştır. TTS hâlâ NoOp sözleşme olarak kalır.

Gelecekteki TTS, wake word veya farklı speech engine kararları ayrı kullanıcı onayı ve teknik değerlendirme sprinti gerektirir.
