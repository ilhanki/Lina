# Katkı ve Geliştirme Standartları

Bu doküman Lina projesinde izlenecek kalıcı geliştirme standartlarını tanımlar.

## Dil Standardı

Türkçe yazılacak alanlar:

- README dosyaları.
- `docs` altındaki tüm dokümanlar.
- Mimari açıklamalar.
- Geliştirme notları.
- Yol haritası.
- Kullanıcıya yapılan açıklamalar.

İngilizce yazılacak alanlar:

- Python kodları.
- Dosya ve klasör isimleri.
- Class, function, variable ve enum isimleri.
- Interface, protocol ve API isimleri.
- Type hint'ler.
- Exception sınıfları.
- Commit mesajları.

Kod bloklarında, dosya yollarında ve API örneklerinde İngilizce isimlendirme korunur.

## Python Sürümü

Hedef Python sürümü:

```text
Python 3.11+
```

Yeni özellikler bu sürüm hedefiyle uyumlu yazılmalıdır.

## Type Hint Standardı

- Yeni Python kodlarında type hint kullanılmalıdır.
- Public function ve method imzaları açık tiplerle yazılmalıdır.
- Dönüş tipi belirtilmelidir.
- Belirsiz `Any` kullanımı gerekçesiz tercih edilmemelidir.

Örnek:

```python
def build_prompt(user_message: str, context: list[str]) -> str:
    ...
```

## Docstring Standardı

- Public class ve public function için gerektiğinde docstring yazılır.
- Docstring dili İngilizcedir, çünkü kod tabanı İngilizcedir.
- Bariz fonksiyonlara gereksiz docstring eklenmez.
- Karmaşık kararlar kısa ve açıklayıcı yorumlarla desteklenir.

Örnek:

```python
def load_settings(path: Path) -> AppSettings:
    """Load application settings from a TOML file."""
```

## Logging Standardı

- `print` debugging için kalıcı olarak kullanılmaz.
- Uygulama kodunda Python `logging` altyapısı kullanılır.
- Log mesajları İngilizce yazılır.
- Kullanıcıya gösterilecek metinler ayrı ele alınır.
- Hata logları context içermelidir ancak hassas veri sızdırmamalıdır.

## Exception Yönetimi

- Geniş `except Exception` bloklarından kaçınılır.
- Yakalanan hata ya anlamlı şekilde ele alınır ya da üst katmana taşınır.
- Özel hata sınıfları İngilizce isimlendirilir.
- Kullanıcı onayı gerektiren işlemler exception ile değil permission policy ile yönetilmelidir.

Örnek exception adı:

```python
class ConfigurationError(Exception):
    ...
```

## İsimlendirme Standardı

- Packages ve modules: `snake_case`
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions ve methods: `snake_case`
- Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Protocol/interface benzeri yapılar: `PascalCase`
- Tests: `test_<module_name>.py`

## Mimari Standartlar

- Business logic UI katmanına yazılmaz.
- Dış sistemler doğrudan servislerin içine gömülmez; adapter ile izole edilir.
- Capability'ler birbirine doğrudan sıkı bağımlı hale getirilmez.
- `Brain` katmanı orchestration sorumluluğu taşır, her şeyi bilen monolitik sınıfa dönüşmez.
- Event bus yalnızca modüller arası bildirim ve yan etkiler için kullanılır.
- Kritik use-case akışları okunabilir servis çağrıları olarak kalır.
- `ApplicationContext` küçük tutulur ve yalnızca `settings`, `paths` ve `logger` taşır.
- `ApplicationContext` içine LLM, Memory, Vision, Speech, Automation veya benzeri servisler eklenmez.
- `ApplicationContext` bir Service Locator'a dönüştürülmez.

## YAGNI Prensibi

Projede YAGNI prensibi uygulanır: İhtiyaç henüz gerçek davranıştan doğmadıysa soyutlama eklenmez.

Şunlardan kaçınılır:

- Kullanılmayan base class'lar.
- Erken oluşturulmuş factory yapıları.
- Henüz ihtiyaç duyulmayan manager sınıfları.
- Gerçek kullanım senaryosu olmayan registry yapıları.
- Sadece gelecekte gerekebilir düşüncesiyle eklenen klasör veya modüller.

Her milestone yalnızca kendi ihtiyacını çözmelidir. Yeni ihtiyaç ortaya çıktığında kontrollü refactor yapılır.

## Bağımlılık Politikası

Mümkün olduğunca Python standart kütüphanesi tercih edilir.

Yeni üçüncü parti paket eklenmeden önce şu sorular cevaplanmalıdır:

- Bu paket hangi problemi çözüyor?
- Standart kütüphane ile makul şekilde çözülebilir mi?
- Paket aktif bakım alıyor mu?
- Lisansı proje kullanımıyla uyumlu mu?
- Güvenlik veya performans riski var mı?
- Test edilebilirliği nasıl etkiliyor?

Runtime bağımlılıkları `requirements.txt` içinde tutulur.

Geliştirme araçları `requirements-dev.txt` içinde tutulur. Örnek geliştirme araçları:

- `pytest`
- `ruff`
- `mypy`

Yeni bağımlılık eklendiğinde doğru dosya güncellenmelidir. Test, lint ve type checking araçları runtime bağımlılığı olarak eklenmez.

## Test Standardı

- Testler `tests` altında kaynak yapıyı takip eder.
- Yeni davranış mümkün olduğunca unit test ile desteklenir.
- Dış sistemlere bağlı testler integration test olarak ayrılmalıdır.
- Testler deterministik olmalıdır.

## Commit Standardı

Commit mesajları İngilizce yazılır ve Conventional Commits formatı kullanılır.

Her commit tek bir sorumluluğa sahip olmalıdır. Büyük ve ilgisiz değişiklikler aynı commit içinde birleştirilmez.

Örnekler:

```text
docs: define project standards
chore: add development dependencies
feat: add configuration loader
fix: handle missing config file
test: cover event bus subscriptions
```

Milestone 1 için örnek küçük commit sırası:

```text
docs: mark milestone 0 complete
chore: add development dependencies
feat: add core exception types
feat: add application paths
feat: add settings loader
feat: add logging setup
feat: add application context
feat: add application lifecycle
```
