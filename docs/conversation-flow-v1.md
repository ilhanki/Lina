# Lina Conversation Flow Spesifikasyonu v1

Bu belge Lina'nın konuşma yaşam döngüsü için resmi mimari spesifikasyondur.

Bu belge bir implementasyon dokümanı değildir. Bir programlama rehberi değildir. Amaç, Lina ile kurulan her etkileşimin kullanıcı isteğinin geldiği andan konuşmanın tamamlandığı ana kadar kavramsal olarak nasıl ilerlemesi gerektiğini tanımlamaktır.

Conversation Flow, Lina'nın tutarlı, güvenli, test edilebilir ve uzun vadede genişletilebilir kalması için temel bir referanstır. Gelecekte farklı arayüzler, model sağlayıcıları, araçlar, sesli etkileşimler, görsel bağlam veya çoklu ajan yapıları eklense bile her etkileşim ortak bir yaşam döngüsü anlayışına sahip olmalıdır.

---

## 1. Giriş

Conversation Flow, kullanıcıdan gelen isteğin Lina tarafından nasıl ele alınacağını belirleyen kavramsal yaşam döngüsüdür.

Bu akışın amacı, her isteğin rastgele veya bağlama göre dağınık şekilde işlenmesini engellemektir. Lina büyüdükçe farklı request türleri ortaya çıkacaktır: basit sohbet, soru cevaplama, kod açıklama, dosya işlemleri, tarayıcı kullanımı, ekran analizi, otomasyon, hafıza güncelleme veya çok adımlı görevler. Bu türlerin her biri farklı alt yollar izleyebilir, fakat hepsi aynı temel disipline sahip olmalıdır.

Her request'in öngörülebilir bir lifecycle izlemesi önemlidir. Çünkü kullanıcı güveni yalnızca doğru cevaplarla kurulmaz; sistemin nasıl düşündüğünün ve ne zaman harekete geçtiğinin anlaşılabilir olmasıyla kurulur.

Tutarlılık optimizasyondan daha önemlidir.

Bazı durumlarda kısa yoldan cevap üretmek mümkün olabilir. Fakat konuşma akışı her yerde farklı davranırsa sistem zamanla tahmin edilemez hale gelir. Lina için erken aşamadaki hedef en hızlı cevap değil, doğru ve güvenilir davranış kalıbıdır.

Optimizasyon daha sonra yapılabilir. Tutarsızlık ise mimarinin içine yerleşirse temizlenmesi zorlaşır.

Bu nedenle Conversation Flow şu ilkeye dayanır:

> Her etkileşim önce anlaşılır, sonra güvenli biçimde değerlendirilir, sonra gerekli bağlamla işlenir ve sonunda kullanıcıya açık bir sonuçla tamamlanır.

---

## 2. Tasarım Hedefleri

### Öngörülebilirlik

Lina'nın aynı tür isteklere benzer şekilde yaklaşması gerekir.

Öngörülebilirlik, hem kullanıcı deneyimi hem de geliştirici güveni için önemlidir. Kullanıcı kritik bir işlem istediğinde Lina'nın rastgele davranmayacağını bilmelidir. Geliştirici de bir isteğin hangi aşamalardan geçeceğini anlayabilmelidir.

Öngörülebilir bir conversation lifecycle, hata ayıklamayı ve gelecekte yeni capability eklemeyi kolaylaştırır.

### Deterministik Davranış

Her request LLM gerektirmez.

Basit ve açık istekler mümkün olduğunda deterministic yollarla çözülmelidir. Bu yaklaşım gecikmeyi azaltır, maliyeti düşürür ve yanlış tahmin riskini azaltır.

Deterministik davranış, Lina'nın daha az akıllı olması anlamına gelmez. Tam tersine, doğru yerde basit davranabilmek olgun bir sistem işaretidir.

### Modülerlik

Conversation Flow, Lina'nın farklı bileşenlerini birbirine sıkı bağlamamalıdır.

Brain, memory, tools, capabilities, model providers ve arayüzler kendi sorumluluklarını korumalıdır. Conversation Flow bu bileşenlerin nasıl sıraya gireceğini ve nasıl birlikte çalışacağını tarif eder; onların iç davranışlarını uygulamaz.

Modülerlik, gelecekte yeni request türlerinin mevcut sistemi kırmadan eklenebilmesini sağlar.

### Hata Ayıklanabilirlik

Bir conversation neden belirli bir yoldan ilerlediği anlaşılabilir olmalıdır.

Lina neden context topladı? Neden memory kullandı? Neden tool çağırdı? Neden kullanıcıdan onay istedi? Neden LLM çağırmadı? Bu sorulara cevap verilemiyorsa conversation lifecycle fazla belirsizdir.

Hata ayıklanabilirlik yalnızca geliştirici konforu değildir. Kullanıcı güveni için de gereklidir.

### Genişletilebilirlik

Conversation Flow bugünkü özelliklerle sınırlı kalmamalıdır.

Gelecekte streaming cevaplar, sesli konuşmalar, background tasks, task continuation, interruptions, scheduling ve multi-agent collaboration gibi daha gelişmiş davranışlar eklenebilir. Bu özellikler mevcut lifecycle'ı çöpe atmamalı; onu genişletmelidir.

Bu nedenle akış kavramsal ve uzun ömürlü tasarlanmalıdır.

### Provider Bağımsızlığı

Conversation Flow hiçbir model sağlayıcısına bağımlı olmamalıdır.

Bir request'in nasıl işlendiği belirli bir LLM sağlayıcısının özelliklerine göre şekillenmemelidir. Model seçimi lifecycle içinde bir karardır, lifecycle'ın kendisi değildir.

Bu ayrım Lina'nın uzun vadeli bağımsızlığı için önemlidir.

### Güvenlik

Conversation Flow, güvenliği sonradan eklenen bir kontrol olarak değil, lifecycle'ın doğal parçası olarak ele almalıdır.

Bir request işlem, dosya değişikliği, otomasyon veya dış sistem erişimi gerektiriyorsa güvenlik ve izin değerlendirmesi erken aşamada yapılmalıdır. Tehlikeli işlemler yalnızca yanıt üretiminin sonunda fark edilmemelidir.

Güvenlik, konuşmanın akışını yavaşlatabilir. Bu kabul edilebilir. Kullanıcı güveni hızdan daha değerlidir.

---

## 3. Üst Seviye Conversation Lifecycle

Lina'nın temel conversation lifecycle'ı kavramsal olarak şu akışla temsil edilir:

```text
User Request
↓
Input Normalization
↓
Intent Analysis
↓
Safety Check
↓
Context Collection
↓
Memory Retrieval
↓
Planning
↓
Model Decision
↓
Tool Decision
↓
Execution
↓
Response Generation
↓
Memory Update
↓
Audit / Logging
↓
Conversation Finished
```

Her request bu aşamaların tamamını aktif şekilde kullanmak zorunda değildir. Basit bir selamlaşma memory retrieval, planning, tool decision veya execution gerektirmeyebilir. Fakat bu aşamalar conversation'ın zihinsel modelini oluşturur.

### User Request

Conversation kullanıcının isteğiyle başlar.

Bu istek yazılı, sesli, arayüz üzerinden, dosya bağlamından, kısayoldan veya gelecekte farklı bir giriş kanalından gelebilir. Giriş kanalı değişebilir; fakat request lifecycle'a ham kullanıcı niyeti olarak girer.

Bu aşamada Lina henüz karar vermemiştir. Kullanıcıdan gelen ifade önce anlaşılmalıdır.

### Input Normalization

Input normalization, isteğin işlenebilir hale getirilmesidir.

Bu aşamanın amacı kullanıcının niyetini değiştirmek değil, girişi tutarlı biçimde temsil etmektir. Sesli girişten gelen metin, GUI'den gelen komut, seçili dosya bağlamı veya doğrudan yazılmış mesaj ortak conversation akışına uygun hale getirilir.

Normalization, anlam üretme aşaması değildir. Anlam üretme Intent Analysis aşamasına aittir.

### Intent Analysis

Intent Analysis, kullanıcının ne istediğini anlamaya çalışır.

Bu aşama conversation'ın yönünü belirler. Kullanıcı sohbet mi ediyor? Bilgi mi istiyor? Bir aracı mı çalıştırmak istiyor? Kod açıklaması mı istiyor? Bilgisayarda işlem mi istiyor? Belirsiz bir istekte mi bulunuyor?

Doğru intent analizi olmadan sonraki adımlar rastgeleleşir.

### Safety Check

Safety Check, request'in potansiyel riskini erken değerlendirir.

Bu aşamada sistem şu soruları sorar:

- Bu istek kullanıcı verisine etki eder mi?
- Bilgisayarda değişiklik yapar mı?
- Dış sistemlere veri gönderir mi?
- Başka kişilerin güvenliği veya mahremiyetiyle ilişkili mi?
- Kullanıcı onayı gerektirir mi?

Safety Check, execution öncesi son dakika kontrolü değildir. Conversation'ın erken aşamasında risk farkındalığı oluşturur.

### Context Collection

Context Collection, isteği doğru anlamak veya işlemek için gerekli bağlamı toplar.

Burada amaç mümkün olan her şeyi toplamak değildir. Gereksiz context, hem maliyet hem de gizlilik riski yaratır. Lina yalnızca isteğin gerektirdiği bağlamı toplamaya çalışmalıdır.

### Memory Retrieval

Memory Retrieval yalnızca gerekli olduğunda devreye girer.

Kullanıcının geçmiş tercihleri, devam eden projeleri veya daha önce açıkça hatırlatılmış bilgiler request'i daha iyi anlamaya yardımcı olabilir. Fakat her konuşmada memory açmak doğru değildir.

Memory kasıtlı kullanılmalıdır.

### Planning

Planning, bir isteğin nasıl ele alınacağını kavramsal olarak düzenler.

Basit request'lerde plan tek bir adım olabilir veya açıkça plan oluşturmak gerekmeyebilir. Çok adımlı görevlerde ise planning, execution öncesi riskleri ve sıralamayı görünür hale getirir.

Planlama execution değildir.

### Model Decision

Model Decision, bir LLM veya başka bir model gerekip gerekmediğine karar verir.

Her request model gerektirmez. Bazı request'ler deterministic olarak cevaplanabilir. Bazıları küçük veya yerel bir modelle çözülebilir. Bazıları daha güçlü reasoning gerektirebilir.

Model seçimi conversation lifecycle'ın içinde bir karar noktasıdır.

### Tool Decision

Tool Decision, request'i tamamlamak için araç veya capability kullanımı gerekip gerekmediğini belirler.

Tool kullanımı eylem doğurabilir. Bu nedenle tool kararı intent, context ve safety check sonuçlarıyla uyumlu olmalıdır.

### Execution

Execution, seçilen planın ilgili capability veya tool'lar aracılığıyla gerçekleştirilmesidir.

Conversation Flow execution'ın iç detaylarını tanımlamaz. Bu aşama yalnızca execution'ın lifecycle içindeki yerini tanımlar.

### Response Generation

Response Generation, kullanıcıya verilecek yanıtın oluşturulduğu aşamadır.

Yanıt; tool sonuçları, model çıktısı, memory, context, açıklama, özet, uyarı veya netleştirme sorusu içerebilir. Amaç, kullanıcının niyetine uygun ve anlaşılır bir sonuç üretmektir.

### Memory Update

Memory Update, conversation sonunda bir bilginin kalıcı veya geçici hafızaya alınmasının gerekip gerekmediğini değerlendirir.

Her konuşma hafızaya yazılmamalıdır. Hafıza bilinçli ve kullanıcı yararına kullanılmalıdır.

### Audit / Logging

Audit ve logging, conversation'ın önemli olaylarını izlenebilir hale getirir.

Bu, özellikle tool kullanımı, izin akışları, hata durumları ve bilgisayarda değişiklik yapan işlemler için önemlidir.

### Conversation Finished

Conversation Finished, etkileşimin tamamlandığı noktadır.

Bu aşamada kullanıcıya yanıt verilmiş, gerekli işlem tamamlanmış veya konuşma güvenli şekilde durdurulmuş olmalıdır. Eğer görev devam edecekse bunun kullanıcıya açık şekilde belirtilmesi gerekir.

---

## 4. Request Türleri

Lina farklı request türlerini destekleyebilir. Bu türler farklı alt yollar izleyebilir, fakat genel lifecycle ortak kalmalıdır.

### Gündelik Sohbet

Kullanıcı yalnızca sohbet etmek isteyebilir.

Bu tür isteklerde tool, memory veya planning çoğu zaman gerekmez. Ancak Lina'nın tonu, bağlamı ve kullanıcı tercihleri yine dikkate alınabilir.

### Soru Cevaplama

Kullanıcı bir bilgi sorabilir.

Bu istekler basit, güncel veya bağlam gerektiren olabilir. "Saat kaç?" deterministic olarak cevaplanabilirken, "Bu kavramı bana örnekle açıkla" model reasoning gerektirebilir. "Bugün hava nasıl?" güncel veri ihtiyacı doğurabilir.

### Kodlama

Kodlama request'leri açıklama, analiz, hata ayıklama, refactor önerisi veya dosya değişikliği isteği içerebilir.

Bu tür isteklerde doğru context çok önemlidir. Yanlış dosya, eksik proje bağlamı veya hatalı varsayım kötü sonuç doğurabilir.

### Araştırma

Araştırma request'leri bilgi toplama, karşılaştırma, özetleme veya kaynak değerlendirme gerektirebilir.

Bu tür isteklerde güncellik ve kaynak güvenilirliği önemlidir. Modelin kendi bilgisi yeterli olmayabilir.

### Tool Execution

Kullanıcı belirli bir aracın çalışmasını isteyebilir.

Tool execution request'lerinde intent çoğu zaman açıktır, fakat izin, risk ve sonuç bildirimi yine değerlendirilmelidir.

### Automation

Automation request'leri bilgisayar üzerinde işlem yapmayı içerir.

Bu alan yüksek dikkat gerektirir. Lina ne yapacağını, neden yapacağını ve kullanıcının onayının gerekip gerekmediğini açık şekilde değerlendirmelidir.

### Vision

Vision request'leri ekran veya görüntü bağlamı gerektirebilir.

Bu tür isteklerde context collection hassastır. Ekranda kişisel veya hassas bilgiler olabilir. Lina yalnızca gerekli görsel bağlamı kullanmalıdır.

### Camera

Camera request'leri fiziksel dünya veya kullanıcı çevresiyle ilgili bağlam gerektirebilir.

Kamera erişimi doğal olarak mahremiyet açısından hassastır. Kullanıcı onayı ve açık amaç olmadan kullanılmamalıdır.

### Browser

Browser request'leri web sayfası okuma, gezinme veya etkileşim gerektirebilir.

Bu tür isteklerde güncel veri, oturum bilgileri, form doldurma ve kullanıcı adına işlem yapma gibi riskler dikkatle ele alınmalıdır.

### Memory

Memory request'leri kullanıcının bir şeyi hatırlatmasını, unutmasını veya geçmiş bağlamı kullanmasını içerebilir.

Memory işlemleri bilinçli ve şeffaf olmalıdır. Lina kullanıcının neyi kalıcı hale getirmek istediğini varsaymamalıdır.

### File Management

Dosya yönetimi request'leri okuma, listeleme, taşıma, düzenleme veya silme gibi işlemleri kapsayabilir.

Dosya değiştiren veya silen işlemler izin ve geri alınabilirlik açısından dikkatli ele alınmalıdır.

### Planning

Kullanıcı bir plan, yol haritası veya görev sıralaması isteyebilir.

Bu tür request'lerde execution gerekmeyebilir. Lina'nın görevi kullanıcının düşünmesini kolaylaştıran açık ve uygulanabilir bir plan üretmek olabilir.

### Multi-Step Task

Çok adımlı görevler birden fazla capability, tool veya model kararı gerektirebilir.

Bu tür request'lerde lifecycle'ın tamamı daha görünür hale gelir. Intent, context, planning, tool decision, execution ve response generation birbirinden ayrılmalıdır.

---

## 5. Intent Analysis

Her request önce anlaşılmalıdır.

Intent Analysis'in temel felsefesi, execution'dan önce anlamayı zorunlu kılmaktır. Kullanıcının söylediği şey ile gerçekten istediği şey her zaman aynı açıklıkta olmayabilir.

Örneğin "Şunu halleder misin?" gibi bir ifade tek başına yetersizdir. Lina bağlamı bilmiyorsa önce açıklama istemelidir. Buna karşılık "Bu klasördeki dosyaları listele" daha açık bir eylem isteğidir.

Intent Analysis şu nedenlerle gereklidir:

- Yanlış tool kullanımını engeller.
- Gereksiz LLM çağrılarını azaltır.
- Riskli işlemleri erken fark eder.
- Context ihtiyacını belirler.
- Kullanıcıdan netleştirme gerekip gerekmediğini ortaya çıkarır.

Anlamak, yalnızca metni sınıflandırmak değildir. Anlamak; niyet, risk, bağlam ihtiyacı ve olası sonraki adımları birlikte değerlendirmektir.

Lina'nın conversation flow'u şu ilkeyi korumalıdır:

> Anlamadan uygulama.

---

## 6. Context Collection

Context, Lina'nın bir request'i doğru yorumlaması için gerekli çevresel bilgidir.

Olası context kaynakları:

- Conversation history.
- Kullanıcı tercihleri.
- Project context.
- Current workspace.
- Open applications.
- Screen information.
- Current task.
- Memory.
- Seçili metin veya dosya.
- Son tool sonuçları.
- Zaman ve yerel durum.

Context collection'ın amacı mümkün olan en fazla bilgiyi toplamak değildir. Doğru miktarda ve doğru türde bilgi toplamak gerekir.

Gereksiz context toplamak üç sorun yaratır:

- Kullanıcı mahremiyetini gereksiz yere genişletir.
- Model veya tool kararlarını gürültülü hale getirir.
- Sistemin maliyetini ve karmaşıklığını artırır.

Context toplama şu sorularla yönlendirilmelidir:

- Bu bilgi request'i cevaplamak için gerçekten gerekli mi?
- Kullanıcı bu bilginin kullanılmasını bekler mi?
- Bilgi güncel ve güvenilir mi?
- Daha az context ile doğru cevap verilebilir mi?
- Eksik context varsa kullanıcıdan sormak daha doğru mu?

Örneğin kullanıcı "Bu kodu açıkla" dediğinde seçili kod parçası yüksek önceliklidir. Tüm proje geçmişini toplamak gerekmeyebilir. Kullanıcı "Bu projede neden testler kırılıyor?" dediğinde ise daha geniş project context gerekebilir.

---

## 7. Safety and Permission

Lina'nın güvenlik felsefesi, kullanıcı kontrolünü korumaktır.

Bir request yalnızca teknik olarak yapılabilir olduğu için otomatik yapılmamalıdır. Lina, özellikle kullanıcının bilgisayarı, dosyaları, hesapları, mesajları veya dış sistemlerle ilişkili işlemlerde dikkatli davranmalıdır.

### Safe Actions

Safe actions genellikle bilgi verme, açıklama yapma, özetleme veya düşük riskli okuma işlemleridir.

Bu işlemler çoğu zaman açık confirmation gerektirmez. Yine de kullanıcı mahremiyeti ve context sınırları korunmalıdır.

### Confirmation Required

Bazı işlemler kullanıcı onayı gerektirir.

Örnek kategoriler:

- Dosya değiştirme.
- Dosya taşıma.
- Uygulama üzerinde işlem yapma.
- Tarayıcıda kullanıcı adına adım atma.
- Mesaj veya e-posta taslağı gönderme.
- Kalıcı ayar değiştirme.

Bu tür işlemlerde Lina ne yapacağını açıkça belirtmeli ve kullanıcının onayını almalıdır.

### High-Risk Actions

High-risk actions geri alınması zor, güvenlik etkisi olan veya başka kişileri etkileyebilecek işlemlerdir.

Bu tür işlemler otomatik çalışmamalıdır. Hatta bazı durumlarda Lina işlemi reddetmeli, alternatif güvenli yol önermeli veya kullanıcıyı profesyonel/manuel kontrole yönlendirmelidir.

Güvenlik ilkesi:

> Tehlikeli işlemler kolaylaştırılabilir, fakat izinsiz otomatikleştirilemez.

---

## 8. Planning

Planning, Lina'nın ne yapılması gerektiğini kavramsal olarak belirlediği aşamadır.

Basit request'lerde planning görünür olmayabilir. Örneğin "Saat kaç?" sorusunda planlama gereksizdir. Ancak "Bu projeyi incele, sorunları bul ve düzeltme planı çıkar" gibi bir istek çok adımlıdır.

Planning şu amaçlara hizmet eder:

- Görev adımlarını görünür kılar.
- Gerekli context ve tool'ları belirler.
- Riskli noktaları ayırır.
- Kullanıcı onayı gereken adımları tanımlar.
- Execution öncesi daha güvenli karar verilmesini sağlar.

Planning execution'dan ayrı olmalıdır.

Bu ayrım önemlidir çünkü bir görevi planlamak, o görevi yapmakla aynı riskleri taşımaz. Lina önce planı anlayabilir, kullanıcıya sunabilir ve ancak onaydan sonra execution aşamasına geçebilir.

Multi-step request'lerde plan kullanıcıya açık hale getirilebilir. Bu, özellikle bilgisayar üzerinde işlem yapılacaksa güveni artırır.

---

## 9. Model Decision

Her request model gerektirmez.

Conversation Flow içinde Model Decision aşaması, LLM veya başka bir model kullanımının gerekli olup olmadığını değerlendirir.

### Model Gerekmeyen Durumlar

Bazı request'ler deterministic olarak çözülebilir:

- Saat bilgisi.
- Basit hesaplama.
- Açık ve düşük riskli sistem bilgisi.
- Doğrudan tool sonucu yeterli olan istekler.

Bu durumlarda LLM çağırmak gereksiz belirsizlik ekleyebilir.

### Küçük veya Yerel Modelin Yeterli Olduğu Durumlar

Bazı request'ler hafif yorumlama veya kısa doğal dil üretimi gerektirebilir.

Bu tür durumlarda küçük veya yerel model yeterli olabilir. Özellikle kişisel veya yerel verilerle çalışırken yerel model tercih etmek gizlilik açısından daha uygun olabilir.

### Daha Güçlü Reasoning Gerektiren Durumlar

Karmaşık analiz, çok adımlı planlama, kod mimarisi değerlendirmesi, uzun bağlam sentezi veya belirsiz problem çözme daha güçlü reasoning gerektirebilir.

Bu durumda model seçimi kullanıcı tercihi, gizlilik, maliyet, hız ve görev niteliği dikkate alınarak yapılmalıdır.

### Provider Bağımsızlığı

Conversation Flow belirli bir provider'a bağlı olmamalıdır.

Model kararı; sağlayıcı detayı değil, conversation lifecycle içindeki bir yönlendirme kararıdır. Lina gelecekte farklı sağlayıcılarla çalışabilmelidir.

---

## 10. Tool Decision

Tool Decision, request'in tamamlanması için araç veya capability gerekip gerekmediğini belirler.

Brain veya conversation layer şu soruları değerlendirmelidir:

- Kullanıcı bir eylem mi istiyor?
- Gerçek veri veya sistem durumu gerekiyor mu?
- LLM'in tahmin etmemesi gereken bir bilgi mi gerekli?
- Tool kullanımı güvenli mi?
- Kullanıcı onayı gerekiyor mu?
- Tool başarısız olursa conversation nasıl devam edecek?

Tool'lar reasoning'in yerine geçmez; gerçek dünyayla veya sistemle etkileşimi temsil eder.

### Permission Checks

Tool kararı permission check'ten bağımsız düşünülmemelidir.

Bir tool dosya okuyorsa, yazıyorsa, tarayıcıda işlem yapıyorsa veya bilgisayarı kontrol ediyorsa izin seviyesi değerlendirilmelidir.

### Tool Failure Fallback

Tool başarısız olduğunda Lina bunu gizlememelidir.

Doğru davranış şunlardan biri olabilir:

- Hata nedenini kullanıcıya açıklamak.
- Alternatif yol önermek.
- Kullanıcıdan ek bilgi istemek.
- Görevin güvenli kısmını tamamlamak.
- İşlemi durdurmak.

Tool failure, conversation'ın başarısız olduğu anlamına gelmek zorunda değildir. İyi bir conversation flow, başarısızlığı anlaşılır hale getirir.

---

## 11. Execution

Execution, planlanan veya seçilen işlemlerin ilgili capability veya tool tarafından gerçekleştirilmesidir.

Execution'ın felsefesi şudur:

> Uygulama kontrollü, izlenebilir ve gerektiğinde durdurulabilir olmalıdır.

### Sequential Execution

İlk ve varsayılan yaklaşım sequential execution olmalıdır.

Sıralı execution daha anlaşılırdır. Özellikle erken mimaride, bir adım tamamlanmadan diğerine geçmemek hata ayıklamayı kolaylaştırır.

### Future Parallel Execution

Gelecekte bazı işlemler paralel yürütülebilir.

Örneğin bağımsız context kaynaklarını toplamak veya birden fazla araştırma kanalını aynı anda çalıştırmak mümkün olabilir. Ancak paralellik lifecycle'ın temel güvenlik ve izlenebilirlik ilkelerini bozmamalıdır.

Paralel execution yalnızca gerçekten değer kattığında eklenmelidir.

### Recoverable Failures

Bazı execution hataları geri kazanılabilir.

Örneğin bir tool beklenen dosyayı bulamazsa kullanıcıdan doğru yol istenebilir. Bir model cevap üretemezse alternatif model veya daha küçük bir cevap stratejisi denenebilir. Bir izin reddedilirse görev güvenli şekilde durdurulabilir.

Recoverable failure tasarımı, kullanıcı deneyimini korur.

### Transparent Execution

Execution sırasında kullanıcı ne olduğunu anlayabilmelidir.

Bu her küçük adımın gösterilmesi anlamına gelmez. Ancak önemli, riskli veya uzun süren işlemlerde kullanıcıya yeterli görünürlük sağlanmalıdır.

---

## 12. Response Generation

Response Generation, conversation'ın kullanıcıya dönen yüzüdür.

Final yanıt yalnızca LLM çıktısı değildir. Yanıt birçok kaynaktan oluşabilir:

- Tool results.
- Reasoning.
- Memory.
- Clarifications.
- Suggestions.
- Summaries.
- Error explanations.
- Permission status.

Yanıt kullanıcının intent'ine ve context'ine uygun olmalıdır.

Örneğin kullanıcı kısa bir bilgi istediyse uzun bir analiz gereksizdir. Kullanıcı mimari değerlendirme istediyse tek cümlelik cevap yetersizdir. Kullanıcı bir işlem yaptırdıysa ne yapıldığı ve sonucun ne olduğu açık olmalıdır.

İyi bir yanıt:

- Doğrudan ve anlaşılırdır.
- Kullanıcı niyetine uygundur.
- Gerekirse sınırlarını belirtir.
- Tool veya model hatalarını saklamaz.
- Gereksiz teknik ayrıntıyla boğmaz.
- Riskli işlemlerde açık davranır.

Response generation, conversation'ın yalnızca kapanışı değil, güven ilişkisinin de bir parçasıdır.

---

## 13. Memory Update

Memory Update bilinçli bir aşama olmalıdır.

Lina her konuşmadan otomatik olarak hafıza üretmemelidir. Hafıza, kullanıcının yararına olduğunda ve bağlamı doğru anlaşıldığında kullanılmalıdır.

### Ne Zaman Hafızaya Alınmalı?

Lina şu tür bilgileri hafızaya almayı değerlendirebilir:

- Kullanıcının açıkça hatırlatmak istediği bilgiler.
- Uzun vadeli tercihleri.
- Devam eden projeler için önemli bağlam.
- Tekrar eden çalışma alışkanlıkları.
- Gelecekte yardım kalitesini artıracak sınırlı bilgiler.

### Ne Zaman Hafızaya Alınmamalı?

Lina şu tür bilgileri otomatik kaydetmemelidir:

- Geçici duygusal ifadeler.
- Hassas kişisel bilgiler.
- Bağlamından koparıldığında yanlış anlaşılabilecek cümleler.
- Kullanıcının açıkça kalıcı olmasını istemediği bilgiler.
- Sadece bir defalık görev için gerekli detaylar.

Memory intentional olmalıdır; otomatik ve kontrolsüz olmamalıdır.

Kullanıcı Lina'nın neyi hatırladığını görebilmeli, değiştirebilmeli ve silebilmelidir. Bu ilke memory sisteminin implementation detayından bağımsızdır.

---

## 14. Logging and Audit

Logging ve audit, Lina'nın güvenilirliği için önemlidir.

Önemli conversation olayları izlenebilir olmalıdır:

- Intent kararları.
- Permission gerektiren işlemler.
- Tool çağrıları.
- Execution sonuçları.
- Hata durumları.
- Kullanıcı onayları veya reddetmeleri.
- Memory update kararları.

Logging kullanıcıyı gözetlemek için değil, sistem davranışını açıklanabilir ve denetlenebilir kılmak için vardır.

Audit özellikle gelecekte önemli olacaktır. Lina bilgisayarda daha fazla işlem yapabildikçe kullanıcı "ne oldu?" sorusuna geçmişten cevap alabilmelidir.

Şeffaflık burada temel ilkedir. Kullanıcı adına yapılan önemli işlemler görünmez olmamalıdır.

---

## 15. Failure Handling

Lina hata durumlarında sakin, açık ve güvenli davranmalıdır.

Hatalar conversation lifecycle'ın dışında düşünülmemelidir. Her aşama hata üretebilir ve bu hatalar kullanıcı deneyimini bozmadan ele alınmalıdır.

### Model Failure

Model başarısız olursa Lina bunu gizlememelidir.

Olası davranışlar:

- Kullanıcıya modelden yanıt alınamadığını söylemek.
- Alternatif model veya daha basit yanıt stratejisi önermek.
- Daha az context ile tekrar denemek.
- Görevi güvenli şekilde durdurmak.

### Tool Failure

Tool başarısız olursa Lina tool sonucunu uydurmamalıdır.

Kullanıcıya neyin başarısız olduğu ve mümkünse nasıl devam edilebileceği açıklanmalıdır.

### Permission Denied

Kullanıcı izin vermezse bu karar saygıyla kabul edilmelidir.

Lina kullanıcıyı ikna etmeye çalışmamalı veya izinsiz alternatif yol aramamalıdır. Gerekirse izin gerektirmeyen güvenli bir seçenek sunabilir.

### Missing Information

Gerekli bilgi eksikse Lina tahminle ilerlememelidir.

Doğru davranış kullanıcıdan netleştirme istemektir. Eksik bilgiyle yapılan işlem özellikle automation, file management ve coding alanlarında risklidir.

### Unexpected Errors

Beklenmeyen hata durumunda Lina panikleyen veya belirsiz davranan bir sistem gibi görünmemelidir.

Kullanıcıya kısa, açık ve dürüst bir açıklama yapılmalı; mümkünse güvenli sonraki adım önerilmelidir.

Hata yönetiminde temel ilke:

> Hata saklanmaz; anlaşılır hale getirilir.

---

## 16. Gelecekteki Evrim

Conversation Flow bugün küçük ve anlaşılır başlamalıdır. Ancak gelecekte doğal olarak genişleyebilmelidir.

Olası evrim alanları:

- Streaming responses.
- Background tasks.
- Task continuation.
- Interruptions.
- Voice conversations.
- Multi-agent collaboration.
- Scheduling.
- Long-running workflows.
- Proactive assistance.

### Streaming Responses

Gelecekte Lina cevapları parça parça üretebilir. Bu, lifecycle'ı değiştirmemelidir. Response generation aşaması streaming hale gelebilir, fakat intent, safety ve context ilkeleri korunmalıdır.

### Background Tasks

Bazı görevler konuşma bittikten sonra devam edebilir.

Bu durumda conversation finished kavramı yeniden düşünülmelidir: kullanıcıya göre konuşma bitmiş olabilir, fakat görev arka planda devam ediyor olabilir. Böyle durumlarda durum bilgisi, durdurma imkânı ve audit daha önemli hale gelir.

### Task Continuation

Kullanıcı bir göreve daha sonra devam etmek isteyebilir.

Conversation Flow gelecekte task state ve continuation kavramlarını destekleyebilir. Ancak bu, memory ve audit ilkeleriyle uyumlu olmalıdır.

### Interruptions

Kullanıcı devam eden bir görevi durdurabilir, değiştirebilir veya önceliklendirebilir.

Interruptions, özellikle voice ve automation alanlarında önemli olacaktır. Lina'nın akışı kesintilere dayanıklı olmalıdır.

### Voice Conversations

Sesli etkileşimler conversation lifecycle'ı değiştirmez; yalnızca input ve output biçimlerini değiştirir.

Sesli konuşmada belirsizlik, yanlış transkripsiyon ve daha hızlı geri bildirim ihtiyacı dikkate alınmalıdır.

### Multi-Agent Collaboration

Gelecekte farklı ajanlar görevleri paylaşabilir.

Bu durumda Conversation Flow, ajanlar arası koordinasyonu kapsayacak şekilde genişleyebilir. Ancak temel ilke değişmez: kullanıcı isteği anlaşılır, güvenlik değerlendirilir, context toplanır, plan yapılır ve sonuç kullanıcıya açıklanır.

### Scheduling

Zamanlanmış görevler conversation lifecycle'ın sınırlarını genişletir.

Bir görev gelecekte çalışacaksa kullanıcı neyin ne zaman yapılacağını açıkça bilmelidir. Zamanlanmış görevler özellikle izin, audit ve iptal edilebilirlik gerektirir.

Gelecek yetenekler lifecycle'ı değiştirmemeli; lifecycle'ı genişletmelidir.

---

## 17. Conversation İlkeleri

Bu ilkeler Lina'nın tüm future ConversationService tasarımlarında korunmalıdır.

1. Önce anla, sonra hareket et.
2. Kullanıcı niyeti execution'dan önce netleşmelidir.
3. Basit istekler basit çözümlerle ele alınmalıdır.
4. Her request LLM gerektirmez.
5. Context gerektiği kadar toplanmalıdır.
6. Gereksiz bilgi toplama gizlilik riskidir.
7. Safety check conversation'ın erken parçasıdır.
8. Riskli işlemler otomatik çalışmamalıdır.
9. Planning execution'dan ayrıdır.
10. Tool kullanımı niyet, risk ve izinle birlikte değerlendirilmelidir.
11. Tool sonuçları uydurulmamalıdır.
12. Kullanıcı izin vermezse kararına saygı duyulmalıdır.
13. Memory intentional olmalıdır.
14. Her konuşma hafızaya yazılmamalıdır.
15. Hatalar saklanmamalı, açıklanmalıdır.
16. Yanıt kullanıcının intent ve context'ine uygun olmalıdır.
17. Provider bağımsızlığı korunmalıdır.
18. Lifecycle genişleyebilir ama temel disiplinini kaybetmemelidir.
19. Şeffaflık güvenin parçasıdır.
20. Güvenlik kolaylık için feda edilmemelidir.

---

## 18. Kapanış

Conversation Flow, Lina'nın kullanıcıyla kurduğu her etkileşimin omurgasıdır.

Bu akışın değeri, yalnızca bugün düzgün cevap üretmesinde değil, Lina büyüdükçe sistemin güvenli, anlaşılır ve sürdürülebilir kalmasını sağlamasındadır.

Lina'nın conversation lifecycle'ı, kullanıcının güvenini korumalı, gereksiz karmaşıklıktan kaçınmalı ve her request'i doğru seviyede dikkatle ele almalıdır.

Bu belgenin temel ilkesi şudur:

> Lina her konuşmada önce anlamaya, sonra güvenli karar vermeye, sonra kullanıcıya açık ve faydalı bir sonuç üretmeye çalışır.
