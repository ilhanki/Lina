# Lina Brain Mimari Spesifikasyonu v1

Bu belge Lina'nın Brain mimarisi için resmi teknik mimari spesifikasyondur.

Bu belge uygulama kodu, sınıf tasarımı veya dosya yapısı anlatmaz. Amaç, Lina'nın nasıl düşünmesi, nasıl karar vermesi ve iç bileşenleri nasıl koordine etmesi gerektiğini tanımlamaktır.

Brain, Lina'nın merkezindeki düşünme ve orkestrasyon katmanıdır. Ancak bu merkezilik, Brain'in her şeyi yapacağı anlamına gelmez. Brain'in görevi sistemi yönetmek değil, karar akışını düzenlemektir.

---

## 1. Giriş

Brain, kullanıcıdan gelen isteği anlamak, bağlamı toplamak, gerekirse plan yapmak, uygun modeli veya araçları seçmek ve sonunda kullanıcıya anlamlı bir yanıt üretilmesini koordine etmek için vardır.

Brain'in varlık nedeni, Lina'nın yalnızca bir LLM çağrısı yapan basit bir sohbet uygulaması olmamasıdır. Lina zamanla hafıza, araçlar, ses, görüntü, otomasyon, dosya yönetimi, tarayıcı kontrolü, kod yardımı ve çoklu ajan yapıları gibi birçok yetenek kazanacaktır. Bu yeteneklerin doğrudan birbirine bağlanması sistemi kırılgan hale getirir.

Brain bu karmaşanın ortasında karar akışını düzenleyen katmandır.

Fakat Brain bir "God Object" olmamalıdır.

Bir God Object; her şeyi bilen, her şeyi yapan, her bağımlılığı doğrudan yöneten ve zamanla tüm sistemin içine aktığı dev bir yapı anlamına gelir. Lina için bu kabul edilemez. Çünkü böyle bir yapı:

- Test etmeyi zorlaştırır.
- Yeni özellik eklemeyi riskli hale getirir.
- Capability sınırlarını bulanıklaştırır.
- Tool ve model sağlayıcılarını Brain'e bağımlı kılar.
- Uzun vadede mimariyi anlaşılmaz hale getirir.

Brain küçük kalmalıdır. Brain'in görevi uygulamak değil, koordine etmektir.

Kısa ilke:

> Brain düşünür ve koordine eder; yetenekler kendi işini yapar.

---

## 2. Tasarım Hedefleri

### Genişletilebilirlik

Lina yıllar içinde büyüyecek bir projedir. Brain mimarisi yalnızca bugünkü sohbet akışına göre tasarlanırsa ileride memory, vision, automation, browser veya multi-agent gibi alanlar eklendiğinde kırılacaktır.

Bu nedenle Brain, yeni capability'lerin eklenmesine doğal şekilde izin vermelidir. Yeni bir yetenek eklendiğinde Brain'in tüm karar akışı baştan yazılmamalıdır.

Genişletilebilirlik, erken soyutlama yapmak anlamına gelmez. Buradaki amaç, sorumluluk sınırlarını doğru belirleyerek gelecekte kontrollü büyümeye alan açmaktır.

### Test Edilebilirlik

Brain'in kararları test edilebilir olmalıdır.

Bir kullanıcı isteği geldiğinde sistemin neden LLM çağırdığı, neden araç kullandığı, neden açıklama istediği veya neden işlemi reddettiği anlaşılabilmelidir.

Test edilebilirlik yalnızca kod kalitesi için değil, güven için de gereklidir. Kullanıcının bilgisayarında işlem yapabilen bir asistanın karar akışı öngörülebilir olmalıdır.

### Provider Bağımsızlığı

Lina tek bir LLM sağlayıcısına bağımlı olmamalıdır.

Bugün yerel bir model uygun olabilir. Yarın farklı bir yerel runtime, uzak API, multimodal model veya özel görev modeli gerekebilir. Brain, belirli bir sağlayıcının detaylarına gömülmemelidir.

Provider bağımsızlığı, Lina'nın uzun ömürlü olması ve kullanıcının kontrolünü koruması için önemlidir.

### Modülerlik

Brain, capability'lerin iç detaylarını uygulamamalıdır.

Memory kendi hafıza davranışını, Vision kendi görsel bağlamını, Automation kendi güvenli işlem sınırlarını, Files kendi dosya erişimini yönetmelidir. Brain bu alanları koordine eder, fakat onların yerine geçmez.

Modülerlik, hem geliştirme hızını hem de güvenliği artırır.

### Mümkün Olduğunda Deterministik Davranış

Her istek LLM gerektirmez.

Basit, açık ve düşük riskli istekler deterministic yollarla çözülebiliyorsa Brain pahalı veya belirsiz reasoning süreçlerine başvurmamalıdır.

Örneğin "Saat kaç?" gibi bir istek için genel amaçlı LLM çağırmak gereksizdir. Buna karşılık "Bu kodun mimari risklerini açıkla" gibi bir istek daha geniş bağlam ve model reasoning gerektirebilir.

Deterministik davranış; maliyeti, gecikmeyi ve belirsizliği azaltır.

### Güvenlik

Brain'in kararları kullanıcı güvenliğini korumalıdır.

Bir istek dosya değiştirme, uygulama açma, mesaj gönderme, tarayıcıda işlem yapma veya bilgisayarı kontrol etme gibi sonuçlar doğuruyorsa Brain bu işlemin risk seviyesini dikkate almalıdır.

Güvenlik Brain'in tek başına uygulayacağı bir şey değildir. Capability ve tool katmanları kendi güvenlik sınırlarını korumalıdır. Brain'in sorumluluğu, riskli davranışların farkında olmak ve gerekli izin akışlarını koordine etmektir.

### Anlaşılabilirlik

Brain'in akışı geliştiriciler tarafından kolayca takip edilebilir olmalıdır.

Bir request'in intent analizinden yanıt üretimine kadar hangi aşamalardan geçtiği açık olmalıdır. Karmaşık kararlar tamamen görünmez bir LLM çağrısına gömülmemelidir.

Lina büyüdükçe en büyük risklerden biri, "neden böyle yaptı?" sorusuna cevap verememektir. Brain mimarisi bu riski azaltmalıdır.

---

## 3. Brain'in Sorumlulukları

Brain'in sorumluluğu karar ve koordinasyon akışıdır.

Brain şu alanlardan sorumludur:

- Kullanıcı isteğini anlamak.
- İsteğin intent'ini sınıflandırmak.
- İstek için gerekli bağlamı belirlemek.
- Gerekli context kaynaklarını koordine etmek.
- Hafıza ihtiyacı olup olmadığını değerlendirmek.
- Gerekirse plan oluşturmak.
- Model çağrısı gerekip gerekmediğine karar vermek.
- Uygun model sağlayıcı veya model türünü seçmek.
- Tool kullanımına ihtiyaç olup olmadığını belirlemek.
- Capability'ler arasında koordinasyon sağlamak.
- Tool sonuçları, context ve reasoning çıktılarından final yanıtı oluşturmak.
- Belirsizlik varsa kullanıcıdan açıklama istemek.
- Riskli işlemlerde izin ve güvenlik akışlarını tetiklemek.

Brain şu alanlardan sorumlu değildir:

- Tool'ların iç işleyişini uygulamak.
- Dosya sistemini doğrudan yönetmek.
- Windows API veya işletim sistemi çağrılarını sarmalamak.
- GUI davranışlarını kontrol etmek.
- Veritabanı veya kalıcı depolama yönetmek.
- Speech, Vision, Automation, Browser veya Files capability'lerini doğrudan uygulamak.
- Model sağlayıcıların teknik detaylarını bilmek.
- Configuration manager gibi davranmak.
- Her şeyi merkezi bir registry içinde tutmak.

Brain'in sağlıklı kalması için bu negatif sınırlar en az pozitif sorumluluklar kadar önemlidir.

---

## 4. Intent Pipeline

Intent Pipeline, Brain'in en kritik parçalarından biridir.

Her kullanıcı isteği önce anlaşılmalıdır. Bir isteği anlamadan LLM çağırmak hem gereksiz maliyet hem de belirsiz davranış üretir. Lina'nın Brain'i, gelen isteğin ne tür bir niyet taşıdığını belirlemeye çalışmalıdır.

Intent Pipeline'ın temel felsefesi şudur:

> Önce ne istendiğini anla; sonra nasıl çözüleceğine karar ver.

Bu yaklaşım, her isteği doğrudan büyük bir reasoning sürecine sokmaktan daha güvenli ve daha verimlidir.

### Intent Analizinin Amaçları

Intent analizi şu sorulara cevap arar:

- Kullanıcı bilgi mi istiyor?
- Kullanıcı bir işlem mi yaptırmak istiyor?
- Kullanıcı açıklama mı istiyor?
- Kullanıcı bilgisayarda bir aksiyon mu istiyor?
- İstek riskli mi?
- İstek için LLM gerekli mi?
- İstek için tool veya capability gerekli mi?
- İstek belirsiz mi?

Bu soruların cevabı sonraki pipeline aşamalarını belirler.

### Örnek: "VS Code'u aç"

Bu istek açık bir action intent taşır.

Brain'in burada öncelikle anlaması gereken şey, kullanıcının sohbet etmek değil bir uygulama açmak istediğidir. Bu istek genel amaçlı LLM reasoning gerektirmez. Daha uygun yaklaşım, ilgili automation veya application-launch capability'sini koordine etmektir.

Ancak risk ve izin politikası yine değerlendirilmelidir. Uygulama açmak düşük riskli olabilir; fakat ileride "VS Code'u aç ve şu projede değişiklik yap" gibi bir istek daha fazla planlama ve izin gerektirebilir.

### Örnek: "Saat kaç?"

Bu basit ve deterministic bir bilgi isteğidir.

LLM çağırmak gereksizdir. Brain bu isteğin local time bilgisinden cevaplanabileceğini anlamalıdır. Böylece yanıt daha hızlı, daha ucuz ve daha güvenilir olur.

### Örnek: "Bugün hava nasıl?"

Bu istek dış bilgi gerektirebilir.

Brain burada kullanıcının lokasyonu, izinler ve internet erişimi gibi bağlamları değerlendirmelidir. Eğer güncel veri yoksa Lina bunu açıkça belirtmeli veya gerekli bilgiye erişmek için izin/araç akışı başlatmalıdır.

LLM burada tek başına güvenilir kaynak değildir. Hava durumu güncel veri gerektirir.

### Örnek: "Bana bu kodu açıkla"

Bu istek açıklama ve reasoning intent'i taşır.

Brain önce "bu kod" ifadesinin hangi bağlama referans verdiğini anlamalıdır. Kullanıcının seçili dosyası, açık editörü, gönderdiği metin veya mevcut workspace bilgisi gerekebilir.

Bu istek genellikle LLM reasoning gerektirir, fakat önce doğru context toplanmalıdır. Yanlış dosya veya eksik bağlamla yapılan açıklama yanıltıcı olur.

### LLM Ne Zaman Gereklidir?

LLM şu durumlarda anlamlıdır:

- Doğal dilde açıklama gerekiyorsa.
- Belirsiz veya çok adımlı problem çözülüyorsa.
- Kod, metin veya görsel bağlam yorumlanıyorsa.
- Kullanıcının niyeti karmaşıksa.
- Farklı bilgi parçaları sentezlenmeliyse.
- Planlama veya alternatif değerlendirme gerekiyorsa.

### LLM Ne Zaman Gerekli Değildir?

LLM şu durumlarda gereksiz olabilir:

- İstek deterministic sistem bilgisiyle cevaplanabiliyorsa.
- Basit bir tool doğrudan yeterliyse.
- Kullanıcı açık bir komut veriyorsa ve yorumlama gerekmiyorsa.
- Cevap güncel dış veri gerektiriyor ve LLM bu veriye sahip değilse.
- Güvenlik nedeniyle önce izin veya açıklama gerekiyorsa.

Brain'in olgunluğu, her şeyi LLM'e göndermesinde değil, ne zaman LLM'e ihtiyaç olmadığını bilmesinde de ölçülür.

---

## 5. Thinking Pipeline

Brain'in reasoning akışı kavramsal olarak şu aşamalardan oluşur:

```text
User Request
↓
Intent Analysis
↓
Context Collection
↓
Memory Retrieval
↓
Planner
↓
Model Routing
↓
Tool Planning
↓
Execution
↓
Response Generation
```

Bu akış her istekte tüm aşamaların çalışacağı anlamına gelmez. Basit istekler bazı aşamaları atlayabilir. Önemli olan, Brain'in karar akışını bu zihinsel modelle değerlendirmesidir.

### User Request

Kullanıcının doğal dil, ses, GUI, API veya başka bir arayüz üzerinden ilettiği istektir.

Bu aşamada request henüz hamdır. Brain request'i doğrudan uygulamaya başlamamalıdır.

### Intent Analysis

Brain isteğin niyetini anlamaya çalışır.

Bu aşama, isteğin bilgi, açıklama, eylem, planlama, otomasyon, belirsizlik giderme veya sohbet gibi kategorilerden hangisine yakın olduğunu belirler.

Intent doğru anlaşılmadan yapılan sonraki işlemler hatalı olabilir.

### Context Collection

Brain isteği cevaplamak veya yerine getirmek için hangi bağlamlara ihtiyaç olduğunu belirler.

Context; conversation history, mevcut workspace, seçili dosya, ekran bilgisi, aktif uygulama, kullanıcı hedefi veya geçici görev durumu olabilir.

Her context gerekli değildir. Gereksiz context toplamak hem maliyet hem de gizlilik riski yaratır.

### Memory Retrieval

Eğer istek kullanıcının geçmiş tercihleri, devam eden projeleri veya daha önceki konuşmalarıyla ilişkiliyse hafıza devreye girebilir.

Memory retrieval, kullanıcının tüm geçmişini açmak anlamına gelmez. Brain yalnızca ilgili ve gerekli hafıza parçalarını istemelidir.

### Planner

Eğer istek birden fazla adım gerektiriyorsa Brain kavramsal bir plan oluşturmalıdır.

Plan, yapılacak işlemlerin sırasını ve risk noktalarını görünür hale getirir. Planlama özellikle automation, file operations, browser tasks ve coding tasks için önemlidir.

### Model Routing

Brain bir model çağrısı gerekiyorsa hangi tür modelin veya sağlayıcının uygun olduğunu belirlemelidir.

Bu karar isteğin türüne, gizlilik seviyesine, bağlam büyüklüğüne, multimodal ihtiyaçlara, hız beklentisine ve kullanıcı tercihine göre değişebilir.

### Tool Planning

Brain bir tool kullanılması gerektiğini düşünüyorsa hangi tool'un ne amaçla kullanılacağını belirlemelidir.

Tool planning, execution değildir. Brain tool'un iç işini yapmaz; sadece hangi aracın uygun olduğunu ve hangi izinlerin gerekebileceğini koordine eder.

### Execution

Execution aşaması ilgili capability veya tool tarafından yapılır.

Brain burada işlemin sonucunu takip eder, hata veya izin durumlarını yönetir ve gerekirse kullanıcıdan açıklama ister. Fakat execution detaylarını uygulamaz.

### Response Generation

Son aşamada Brain kullanıcıya dönecek yanıtın oluşturulmasını koordine eder.

Yanıt; tool sonuçları, LLM çıktısı, context, hafıza, özetler veya açıklama isteklerinden oluşabilir.

---

## 6. Planner

Planner, Brain içinde çok adımlı görevleri kavramsal olarak düzenleyen sorumluluktur.

Planlama ile execution ayrılmalıdır. Çünkü bir görevi planlamak ve bir görevi yapmak aynı şey değildir.

Planlama şunları sağlar:

- Görevin adımlara ayrılması.
- Riskli adımların görünür hale gelmesi.
- Kullanıcı onayı gereken noktaların belirlenmesi.
- Gereken capability veya tool'ların anlaşılması.
- Hata durumunda hangi adıma dönüleceğinin anlaşılması.

Örneğin "Bu projeyi incele, eksiklerini bul ve README'yi güncelle" gibi bir istek tek adımlı değildir. Önce proje bağlamı anlaşılmalı, sonra ilgili dosyalar okunmalı, sonra eksikler belirlenmeli, sonra değişiklik önerilmeli veya uygulanmalıdır.

Planner'ın görevi bu akışı kavramsal olarak düzenlemektir. Dosya okumak, kod değiştirmek veya GUI kontrol etmek Planner'ın görevi değildir.

Çok adımlı görevler kavramsal olarak şu bilgileri taşımalıdır:

- Amaç.
- Adımlar.
- Gerekli context.
- Gerekli capability'ler.
- Riskli işlemler.
- Kullanıcı onayı gereken noktalar.
- Tamamlanma kriteri.

Bu belge herhangi bir veri yapısı veya sınıf tasarımı önermez. Önemli olan, planlamanın execution'dan ayrı düşünülmesidir.

---

## 7. Context Manager

Context, Brain'in bir isteği doğru anlayabilmesi için gerekli olan çevresel bilgidir.

Context yalnızca konuşma geçmişi değildir. Lina gibi kişisel bir asistan için context çok katmanlıdır.

Olası context kaynakları:

- Conversation history.
- Kullanıcı hafızası.
- Mevcut uygulama.
- Mevcut workspace.
- Açık dosyalar.
- Seçili metin.
- Ekran bilgisi.
- Son tool sonuçları.
- Devam eden görev durumu.
- Kullanıcı tercihleri.
- Zaman ve yerel çalışma bağlamı.

Context Manager'ın felsefi görevi, her şeyi toplamak değil, doğru şeyi doğru miktarda toplamaktır.

### Context Önceliklendirme

Tüm context kaynakları eşit değildir.

Önceliklendirme şu sorularla yapılmalıdır:

- Bu bilgi mevcut isteği cevaplamak için gerekli mi?
- Bu bilgi güncel mi?
- Bu bilgi güvenilir mi?
- Bu bilgi mahremiyet riski taşıyor mu?
- Bu bilgi yanıt kalitesini gerçekten artırıyor mu?
- Bu bilgi olmadan kullanıcıdan açıklama istemek daha doğru olur mu?

Örneğin kullanıcının açıkça gönderdiği kod parçası, belirsiz bir eski hafıza kaydından daha yüksek öncelikli olabilir. Aktif ekran görüntüsü, saatler önce alınmış bir workspace özetinden daha güncel olabilir.

Context yönetimi, Brain'in hem doğruluğunu hem de gizlilik seviyesini belirleyen önemli bir alandır.

---

## 8. Prompt Builder

Prompt'lar sistemin farklı yerlerine dağınık şekilde yazılmamalıdır.

Dağınık prompt tasarımı şu sorunları üretir:

- Davranış tutarsızlığı.
- Bakım zorluğu.
- Test edilemeyen reasoning akışları.
- Güvenlik ve sistem talimatlarının unutulması.
- Aynı davranışın farklı yerlerde farklı şekilde tanımlanması.

Prompt Builder'ın amacı, Brain'in ihtiyaç duyduğu prompt'ları merkezi ve sürdürülebilir şekilde oluşturmayı sağlamaktır.

Bu merkezi yapı, tek bir dev prompt anlamına gelmez. Aksine, amaca göre düzenlenmiş prompt parçalarının kontrollü şekilde bir araya getirilmesi anlamına gelir.

Prompt construction şu kaynakları dikkate alabilir:

- System-level davranış ilkeleri.
- Kullanıcı isteği.
- Intent sonucu.
- Toplanan context.
- İlgili hafıza.
- Tool veya capability sonuçları.
- Yanıt formatı beklentisi.
- Güvenlik sınırları.

Prompt Builder'ın uzun vadeli değeri, Lina'nın davranışını daha tutarlı ve değiştirilebilir hale getirmesidir.

Prompt'lar zamanla değişebilir. Fakat bu değişim kontrollü olmalıdır. Bir prompt değişikliği Lina'nın kişiliğini, güvenlik davranışını veya reasoning kalitesini etkileyebilir.

---

## 9. Model Router

Lina hiçbir zaman tek bir LLM sağlayıcısına bağımlı olmamalıdır.

Model Router'ın amacı, Brain'in belirli sağlayıcı detaylarına gömülmeden uygun model veya sağlayıcı seçimini koordine etmesini sağlamaktır.

Gelecekte Lina farklı sağlayıcılarla çalışabilir:

- Ollama.
- LM Studio.
- OpenAI.
- Gemini.
- Yerel multimodal modeller.
- Göreve özel küçük modeller.

Bu liste sabit değildir. Önemli olan Brain'in belirli bir sağlayıcıyı varsaymamasıdır.

### Routing Felsefesi

Model seçimi yalnızca "hangi model daha güçlü?" sorusuyla yapılmamalıdır.

Routing kararları şu faktörleri dikkate alabilir:

- Gizlilik seviyesi.
- Yerel çalışma tercihi.
- Görevin karmaşıklığı.
- Context boyutu.
- Multimodal ihtiyaç.
- Hız beklentisi.
- Maliyet.
- Kullanıcı tercihi.
- Modelin güvenilirliği.
- İnternet veya dış servis izni.

Örneğin kişisel dosya içeriğiyle ilgili bir istek varsayılan olarak yerel model gerektirebilir. Genel bilgi veya ağır reasoning gerektiren bir görev için kullanıcı izin verdiyse farklı bir sağlayıcı değerlendirilebilir.

Model Router'ın görevi sağlayıcının nasıl çağrılacağını bilmek değildir. Görevi, hangi sağlayıcı veya model türünün uygun olduğuna karar akışında yardımcı olmaktır.

---

## 10. Tool Planning

Tool'lar reasoning'den ayrılmalıdır.

LLM veya Brain bir şeyin yapılması gerektiğini düşünebilir; fakat o şeyi yapmak ayrı bir sorumluluktur. Bu ayrım güvenlik ve test edilebilirlik için kritiktir.

Brain tool kullanımını şu sorularla değerlendirmelidir:

- Kullanıcının isteği bir eylem gerektiriyor mu?
- Bu eylem deterministic bir tool ile yapılabilir mi?
- Tool kullanımı kullanıcı verisine veya sistem durumuna etki eder mi?
- İzin gerekli mi?
- Tool sonucu final yanıt için yeterli mi?
- Tool çalışmadan önce kullanıcıdan açıklama istenmeli mi?

### Tool Ne Zaman Kullanılmalı?

Tool kullanımı şu durumlarda uygundur:

- Güncel bilgi gerekiyorsa.
- Dosya veya sistem durumu okunacaksa.
- Kullanıcının bilgisayarında işlem yapılacaksa.
- Hesaplama veya veri işleme deterministic olarak yapılabiliyorsa.
- LLM'in tahmin etmemesi gereken gerçek bilgi gerekiyorsa.

### Permission Checks

Brain izin kontrollerini tek başına uygulamamalıdır, fakat izin ihtiyacının farkında olmalıdır.

Riskli tool işlemleri kullanıcının açık onayını gerektirebilir. Örneğin dosya silme, dosya değiştirme, mesaj gönderme, tarayıcıda form doldurma veya işletim sistemi üzerinde kalıcı değişiklik yapma gibi işlemler özel dikkat gerektirir.

Brain'in görevi, böyle durumlarda izin akışının devreye girmesini koordine etmektir.

---

## 11. Capability Coordination

Brain capability'leri koordine eder; capability'leri uygulamaz.

Bu ayrım Lina'nın uzun vadeli mimarisi için temel önemdedir. Capability'ler kendi alanlarının sahibidir. Brain yalnızca hangi capability'nin ne zaman devreye gireceğini belirleyen orkestrasyon katmanıdır.

### Memory

Brain, memory'den ilgili geçmiş bilgileri isteyebilir veya bir konuşma sonucunda hafızaya alınabilecek bilgileri belirleyebilir. Ancak hafızanın nasıl saklanacağı, nasıl aranacağı veya nasıl silineceği Brain'in görevi değildir.

### Speech

Brain, speech capability'den gelen kullanıcı isteğini işleyebilir veya final yanıtın seslendirilmesini koordine edebilir. Ancak ses tanıma, mikrofon yönetimi veya TTS üretimi Brain'in işi değildir.

### Vision

Brain, bir isteği anlamak için ekran veya görsel bağlam gerektiğine karar verebilir. Ancak ekran görüntüsü alma, OCR veya görsel analiz Vision capability'nin sorumluluğudur.

### Automation

Brain, kullanıcının bilgisayarda bir işlem yapmak istediğini anlayabilir ve automation capability'yi koordine edebilir. Ancak pencere kontrolü, klavye/fare işlemleri veya işletim sistemi çağrıları Brain'e ait değildir.

### Browser

Brain, bir web sayfasında işlem yapılması gerektiğini belirleyebilir. Ancak tarayıcı oturumu, sayfa gezinme veya DOM etkileşimi Browser capability'nin sorumluluğudur.

### Files

Brain, bir dosyanın okunması, özetlenmesi veya değiştirilmesi gerektiğini anlayabilir. Ancak dosya erişimi, path güvenliği ve yazma işlemleri Files capability tarafından yönetilmelidir.

### Coding

Brain, kullanıcının kodla ilgili isteğini anlayabilir, açıklama veya planlama yapabilir. Ancak dosya değişiklikleri, test çalıştırma veya proje araçları Coding capability ve ilgili tool'lar tarafından yürütülmelidir.

### Camera

Brain, kamera bağlamına ihtiyaç olup olmadığını değerlendirebilir. Ancak kamera erişimi, görüntü yakalama ve izin sınırları Camera capability'nin sorumluluğudur.

Capability coordination'ın temel ilkesi şudur:

> Brain karar verir ve koordine eder; capability kendi alanında uygular.

---

## 12. Response Generation

Final yanıt yalnızca LLM çıktısının kullanıcıya aktarılması değildir.

Brain yanıt üretimini koordine ederken farklı kaynakları bir araya getirebilir:

- Kullanıcı isteği.
- Intent analizi.
- Toplanan context.
- Memory sonuçları.
- Tool sonuçları.
- LLM reasoning çıktısı.
- Plan durumu.
- Hata veya izin bilgileri.
- Özetler.
- Açıklama soruları.

Yanıtın amacı kullanıcının ihtiyacını karşılamaktır. Bu bazen kısa bir cevap, bazen bir açıklama, bazen bir plan, bazen bir uyarı, bazen de kullanıcıdan netleştirme isteği olabilir.

İyi bir final yanıt:

- Kullanıcının sorusuna doğrudan cevap verir.
- Gerekirse ne yapıldığını açıklar.
- Belirsizlikleri saklamaz.
- Tool sonuçlarını anlaşılır hale getirir.
- Gereksiz reasoning ayrıntısıyla kullanıcıyı boğmaz.
- Riskli durumlarda dikkatli ve açık olur.

Brain final yanıtı oluştururken kullanıcı deneyimini de gözetmelidir. Her teknik detay kullanıcıya gösterilmek zorunda değildir; fakat kullanıcı anlamlı karar verebilmek için gereken bilgiyi almalıdır.

---

## 13. Gelecekteki Evrim

Brain v1 küçük başlamalıdır. Ancak küçük başlamak, geleceği yok saymak anlamına gelmez.

Bugünkü mimari, gelecekte doğal olarak şu alanlara evrilebilmelidir:

- Multi-agent architecture.
- Daha gelişmiş task planning.
- Long-running tasks.
- Background execution.
- Scheduling.
- Periodic context refresh.
- Kullanıcı hedef takibi.
- Daha güçlü memory integration.
- Gelişmiş permission workflows.
- Daha zengin multimodal reasoning.

Bu evrim, Brain'in bugünden karmaşık hale getirilmesiyle sağlanmamalıdır. Aksine, bugünkü sınırların doğru çizilmesi gelecekteki büyümeyi kolaylaştırır.

Multi-agent mimari geldiğinde Brain tamamen ortadan kalkmak zorunda değildir. Brain, ajanların ne zaman devreye gireceğini, görevlerin nasıl bölüneceğini veya final yanıtın nasıl toparlanacağını koordine eden üst düzey akıl yürütme katmanı olarak kalabilir.

Long-running tasks ve background execution gibi alanlar özellikle dikkat ister. Kullanıcı bilgisayarında uzun süre çalışan görevler güven, şeffaflık ve durdurulabilirlik gerektirir. Brain bu tür görevleri başlatan merkezi bir işçi değil, bu görevlerin niyetini ve sınırlarını belirleyen koordinasyon noktası olmalıdır.

---

## 14. Non-Goals

Brain'in ne olmadığı açıkça tanımlanmalıdır.

Brain şunlara dönüşmemelidir:

- God Object.
- Tool implementation layer.
- Windows API wrapper.
- GUI controller.
- Storage system.
- Configuration manager.
- Plugin registry.
- Model provider implementation.
- Filesystem manager.
- Browser automation engine.
- Speech processing engine.
- Vision processing engine.
- Memory database.
- Dependency injection container.

Bu sınırlar, Brain'i küçültmek için değil, Brain'in gerçek değerini korumak için vardır.

Brain'in değeri, her şeyi yapmasında değil; doğru bileşeni doğru zamanda, doğru bağlamla koordine etmesindedir.

---

## 15. Brain İlkeleri

Bu ilkeler Brain ile ilgili her gelecek tasarım ve uygulama kararında referans alınmalıdır.

1. Brain düşünür; tool'lar uygular.
2. Reasoning execution'dan ayrıdır.
3. Her capability kendi sorumluluğunun sahibidir.
4. Brain capability'leri koordine eder, implemente etmez.
5. Basit istekler pahalı reasoning gerektirmemelidir.
6. Her request önce anlaşılmalı, sonra işlenmelidir.
7. LLM çağrısı varsayılan refleks olmamalıdır.
8. Provider bağımsızlığı korunmalıdır.
9. Context gerekli olduğu kadar toplanmalıdır.
10. Hafıza faydalı olduğunda kullanılmalı, gereksiz yere açılmamalıdır.
11. Tool kullanımı niyet, risk ve izin bağlamında değerlendirilmelidir.
12. Riskli işlemler açık izin ve şeffaflık gerektirir.
13. Brain küçük kalmalıdır.
14. God Object tasarımından kaçınılmalıdır.
15. Prompt construction merkezi ve sürdürülebilir olmalıdır.
16. Model routing gizlilik, maliyet, hız ve görev niteliğini dikkate almalıdır.
17. Final yanıt kullanıcı ihtiyacına göre oluşturulmalıdır.
18. Belirsizlik saklanmamalıdır.
19. Mimari, mevcut capability'leri kırmadan evrilebilmelidir.
20. Lina'nın Brain'i kullanıcının kontrolünü artırmalı, azaltmamalıdır.

---

## 16. Kapanış

Brain, Lina'nın düşünme ve koordinasyon merkezidir; fakat Lina'nın tamamı değildir.

Brain'in uzun vadeli başarısı, ne kadar çok sorumluluk aldığıyla değil, sorumlulukları ne kadar doğru ayırdığıyla ölçülecektir.

Sağlıklı bir Brain mimarisi, Lina'nın yıllar boyunca büyümesine izin verirken sistemin anlaşılabilir, test edilebilir, güvenli ve kullanıcı odaklı kalmasını sağlar.

Bu belgenin amacı, Brain ile ilgili gelecekteki tüm uygulamaların aynı temel felsefeden hareket etmesini sağlamaktır:

> Lina önce anlar, sonra düşünür, sonra koordine eder; yalnızca gerektiğinde uygular.
