# Dosya ekleri

## Desteklenen türler

Composer'daki Dosya düğmesi görsellerin yanında `.txt`, `.md`, `.py`, `.json`, `.csv`, `.pdf`, `.docx` ve `.xlsx` kabul eder. Görseller Vision hattına; belgeler text Brain hattına gider. Vision kapalıyken belge ekleme kullanılabilir, görsel ekleme açık bir unavailable mesajı verir.

## Güvenli çıkarım

- Seçim her seferinde kullanıcı tarafından native file picker ile yapılır.
- Dosya salt-okunur açılır; yazma, taşıma, silme ve yeniden adlandırma yoktur.
- Varsayılan byte sınırı 10 MiB, model bağlamı sınırı 24.000 karakterdir.
- UTF-8 text/JSON/CSV doğrudan bounded okunur. Geçersiz JSON reddedilir.
- DOCX ve XLSX yalnız standart ZIP/XML üyelerinden çıkarılır; uncompressed member boyutu ayrıca sınırlanır.
- PDF şifreliyse reddedilir. Metin içermeyen taranmış PDF için OCR fallback yoktur.
- Credential, secret, auth ve private-key benzeri dosya adları reddedilir.

## Yaşam döngüsü ve gizlilik

Belge adı, türü, çıkarılan metin ve truncation bilgisi yalnız aktif attachment nesnesinde tutulur. Başarılı conversation sonucunda attachment tüketilir; hata veya kullanıcı iptalinde tekrar denenebilmesi için composer'da kalır. Conversation veritabanına ham belge içeriği ya da dosya yolu yazılmaz. Model prompt'unda içerik “kullanıcının açıkça eklediği salt-okunur belge” olarak ayrılır ve sistem talimatı sayılmaz.

Önizleme en fazla ilk 4.000 karakteri gösterir. Bu UI sınırı model context sınırından ayrıdır.
