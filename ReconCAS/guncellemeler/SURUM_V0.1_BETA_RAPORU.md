# 🚀 ReconCAS // Sürüm Güncelleme & Hata Çözüm Raporu (V0.1.1 BETA)
**Vision-Based Computer Algebra System & Kinetic Sandbox**

Bu doküman, ReconCAS V0.1 BETA sürümünde gerçek dünya testleri (*Simple Algebra Practice Worksheet.pdf*) neticesinde tespit edilen **28 adet hatanın (BUG-001 - BUG-021 ve BUG-PDF-001 - BUG-PDF-007)** teknik kök nedenlerini, uygulanan algoritmik çözümleri ve 27 maddelik otomatik test takımının doğrulama sonuçlarını içermektedir.

---

## 📊 1. Test Takımı ve Doğrulama Sonuçları

Önceki sürümde bulunan 9 birim test, Doküman Motoru ve yeni doğrulama katmanlarının eklenmesiyle **27 kapsamlı teste (%200 artış)** çıkarılmıştır.

### 🧪 Test Koşum Özeti
```text
PS C:\Users\Hp\Desktop\ReconCAS> python -m unittest discover -s tests
...........................
----------------------------------------------------------------------
Ran 27 tests in 30.561s

OK
```

### 📋 Modül Bazlı Test Dökümü

| Test Dosyası | Test Sayısı | Durum | Kapsanan Senaryolar ve Doğrulamalar |
| :--- | :---: | :---: | :--- |
| [`tests/test_auth.py`](file:///c:/Users/Hp/Desktop/ReconCAS/tests/test_auth.py) | 2 | **BAŞARILI** | Geçici test veritabanı izolasyonu, Bcrypt `gensalt()` ile parola/ipucu şifreleme, kimlik doğrulama döngüleri, gizli ipucuyla parola sıfırlama protokolü. |
| [`tests/test_math.py`](file:///c:/Users/Hp/Desktop/ReconCAS/tests/test_math.py) | 10 | **BAŞARILI** | Aritmetik işlem doğruluğu, `exp(0)` regresyonu, zararlı kod enjeksiyonu engelleme (`__import__`, `eval`), Unicode matematik sembolleri (`π`, `∞`, `√`, `∫`, `×`, `÷`), canonical lowercase `SAFE_WORDS` (`Abs`/`abs`, `Matrix`/`matrix`), sözdizimi duyarlı kök/integral, mutlak değer `\|x\|`, birinci sınıf sembolik operation dispatcher (`diff`, `integrate`, `solve`), `validate_expression` durum ve hata raporlaması. |
| [`tests/test_ocr.py`](file:///c:/Users/Hp/Desktop/ReconCAS/tests/test_ocr.py) | 5 | **BAŞARILI** | Çok kriterli Multi-PSM seçimi, context-aware OCR fonksiyon koruması (`log`, `cos`), false-positive doğal dil elemesi (`crore/ serine iar`, `hello/world`, `=8`, `ly-`), token confusion düzeltmesi (`ly+5=2 -> y+5=2`, `lx-4=3 -> x-4=3`), çoklu denklem satır bölümleme (`x+0=1 ly-3=9`). |
| [`tests/test_document.py`](file:///c:/Users/Hp/Desktop/ReconCAS/tests/test_document.py) | 10 | **BAŞARILI** | Sentetik PNG/JPG görüntü analizi, tek/çok sayfalı PDF taraması, 35 sayfalık belgede `MAX_PDF_PAGES = 30` kısıtı ve UI uyarı tespiti, geçersiz dosya uzantısı (`.docx`), eksik dosya yönetimi, `progress_cb` ilerleme bildirimi, 0-byte boş doküman, OCRError hata simülasyonu. |

---

## 🛠️ 2. Çözülen Hataların Teknik Analizi & Kök Nedenleri

### 🔴 P0 — Kritik Seviye Hatalar (Core & Pipeline)

#### [BUG-001] Unicode Matematik Karakterlerinin Lexical Validation'da Reddedilmesi
- **Kök Neden**: `MathEngine` içinde girdi işleme sıralaması `_lexical_validation(raw)` -> `format_input(raw)` şeklindeydi. `ALLOWED_TOKENS` regex'i Unicode karakterleri (`π`, `∞`, `√`, `∫`, `×`, `÷`) tanımadığı için kullanıcı veya OCR girdisi daha normalize edilmeden `UnsafeExpressionException` fırlatıyordu.
- **Teknik Çözüm**: Pipeline sıralaması `format_input` -> `_lexical_validation` -> `parse_expr` olarak yeniden düzenlendi. Savunma derinliği (defense-in-depth) ilkesi gereği Unicode matematik karakterleri doğrudan `ALLOWED_TOKENS` regex kümesine de dahil edildi.
- **Sonuç**: `π*x`, `∞`, `√x`, `∫x dx`, `2×3`, `10÷2` ifadeleri doğrudan kabul edilip işlenmektedir.

#### [BUG-002] SAFE_WORDS Beyaz Listesinin Case-Insensitive Olmaması
- **Kök Neden**: `_lexical_validation` metni `clean_text.lower()` yapıyordu. Ancak `SAFE_WORDS` listesinde `Abs`, `Matrix`, `Eq`, `Function` gibi sınıflar büyük harfle tanımlıydı. `clean_text` içinde `matrix` arandığında listede bulunamıyor ve ifade engelleniyordu.
- **Teknik Çözüm**: `SAFE_WORDS` listesi canonical lowercase bir `set` yapısına dönüştürüldü (`abs`, `matrix`, `eq`, vb.). `format_input` aşamasında ise SymPy'nin büyük harfle beklediği sınıflar (`Matrix`, `Abs`, `Eq`, `Function`) regex ile canonical büyük harf formuna getirildi.
- **Sonuç**: `Abs(x)` ve `abs(x)`, `Matrix(...)` ve `matrix(...)` semantik olarak eşitlenerek sorunsuz parse edilir hale geldi.

#### [BUG-003] √ ve ∫ Normalizasyonunun Parantezi Açık Bırakması
- **Kök Neden**: `format_input` içindeki kör metin değişimi `text.replace('√', 'sqrt(')` ve `replace('∫', 'integrate(')` yapıyordu. Girdi `√x` olduğunda çıktı `sqrt(x` kalıyor, kapanış parantezi eklenmediği için SymPy parser sözdizimi hatası veriyordu.
- **Teknik Çözüm**: Kör değişim yerine sözdizimi duyarlı (syntax-aware) regex normalizasyonu kuruldu:
  - `√\(([^)]+)\)` ve `√\{([^}]+)\}` -> `sqrt(\1)`
  - `√([a-zA-Z0-9_]+)` -> `sqrt(\1)` (örn: `√x` -> `sqrt(x)`, `√16` -> `sqrt(16)`)
  - `∫\s*(.+?)\s*d([a-zA-Z])` -> `integrate(\1, \2)` (örn: `∫x dx` -> `integrate(x, x)`)
  - `∫\s*([a-zA-Z0-9_+*/^-]+)` -> `integrate(\1, x)` (örn: `∫x` -> `integrate(x, x)`)
- **Sonuç**: Kök ve integraller matematiksel sınırları korunarak hatasız SymPy fonksiyon çağrılarına çevrilmektedir.

#### [BUG-004] Multi-PSM OCR Seçim Algoritmasının Yanlış Sonuç Seçmesi
- **Kök Neden**: Eski sistem `--psm 6`, `--psm 11` ve `--psm 4` modlarını çalıştırıyor ve sadece metindeki matematik karakter sayısına (`len(re.findall(r'[\d+\-*/=^().]', text))`) bakıyordu. `1234 //// === +++` gibi OCR çöpü, sırf sembol sayısı fazla olduğu için gerçek bir denklemin (`x + 4 = 6`) önüne geçebiliyordu.
- **Teknik Çözüm**: Çok kriterli skorlama mimarisi geliştirildi:
  $$\text{Skor} = 0.30 \cdot C_{\text{ocr}} + 0.30 \cdot S_{\text{parse}} + 0.20 \cdot S_{\text{struct}} + 0.15 \cdot S_{\text{math}} - 0.25 \cdot P_{\text{garbage}}$$
  - $C_{\text{ocr}}$: Tesseract `image_to_data` üzerinden toplanan kelime güven ortalaması
  - $S_{\text{parse}}$: Aday ifadelerin `MathEngine.validate_expression()` başarı oranı
  - $S_{\text{struct}}$: Dengeli parantez `()` `[]` ve operatör ardışıklığı kontrolü (örn. `++++` veya `====` olmaması)
  - $S_{\text{math}}$: Karakter yoğunluğu
  - $P_{\text{garbage}}$: Doğal dil kelime dizisi cezası
- **Sonuç**: En çok karaktere sahip olan değil, matematiksel olarak en geçerli ve güvenilir olan PSM adayı seçilmektedir.

#### [BUG-005 & BUG-PDF-005] Doğal Dil Metinlerinin Matematik Sanılması
- **Kök Neden**: `Simple Algebra Practice Worksheet.pdf` taranırken `crore/ serine iar` ifadesi yakalanmıştı. Eski `is_actual_math()` fonksiyonu metinde `/` operatörünü görünce bunu bir bölme işlemi zannederek kabul ediyordu.
- **Teknik Çözüm**: `is_actual_math()` yeniden tasarlandı:
  1. İçinde 3 harften uzun en az 2 kelime bulunan, bu kelimeleri `SAFE_WORDS` içinde yer almayan ve rakam barındırmayan ifadeler (örn. `crore/ serine iar`, `hello / world`) kesin olarak elendi.
  2. Başlangıçta veya sonda sarkan geçersiz operatörler (`=8`, `ly-`, `+5=`) reddedildi.
  3. İfadenin `MathEngine.validate_expression()` veya token düzeltici tarafından onaylanması şart koşuldu.
- **Sonuç**: PDF sayfalarındaki başlık, paragraf ve doğal dil gürültüleri tamamen elendi.

#### [BUG-006 & BUG-PDF-001..006] l / I / x / y Token Confusion Hataları
- **Kök Neden**: Yazı tipi veya tarama kalitesi nedeniyle Tesseract `y` ve `x` değişkenlerinin başına `l` veya `I` eklemekteydi (`ly+5=2`, `lx-4=3`, `Ix-4=3`, `ly-3=9`, `ly*3=15`). Basit global replace (`l -> 1`) yapılırsa `log`, `limit`, `ln` gibi fonksiyonlar bozuluyordu.
- **Teknik Çözüm**: `OCREngine.correct_ocr_confusion()` fonksiyonu yazıldı:
  - Değişken başındaki `l` veya `I` için aday hipotezler üretildi (`y+5=2`, `1*y+5=2`).
  - Operatör sonrası gelen karışıklıklar (`= ly` -> `= y`) temizlendi.
  - Sayı sonuna yapışan tarama gürültüleri (`x+02H -> x+0=2`) normalize edildi.
  - Adaylar `validate_expression` filtresine sokularak doğrulamayı geçen en anlamlı cebirsel ifade seçildi.
- **Sonuç**: `ly+5=2 -> y+5=2`, `lx-4=3 -> x-4=3`, `Ix-4=3 -> x-4=3`, `ly-3=9 -> y-3=9` dönüşümleri %100 doğrulukla gerçekleşti.

#### [BUG-007] OCR Çıktılarının SymPy ile Doğrulanmadan Sunulması
- **Kök Neden**: Doküman motoru OCR -> regex filtre -> liste akışını işletiyordu; aradaki parse doğrulama katmanı eksikti.
- **Teknik Çözüm**: `MathEngine.validate_expression(text)` fonksiyonu geliştirildi. Her aday ifade `(is_valid, normalized_text, parsed_obj, error_msg)` dörtlüsü ile doğrulanmakta, sadece geçerli veya düzeltilmiş ifadeler sonuç listesine aktarılmaktadır.

---

### 🟣 PDF Testinden Çıkan Özel Hatalar (BUG-PDF-001 - BUG-PDF-007)

#### [BUG-PDF-007] Çok Sütunlu Sayfalarda Denklem Bölümleme (Segmentation)
- **Kök Neden**: Çalışma kağıdında iki sütun halinde yan yana duran denklemler (`x+0=1` ve `ly-3=9` ya da `x= 11` ve `ly= 12`) tüm sayfa tarandığında tek bir OCR satırında birleşiyordu (`x+0=1 ly-3=9`). Sistem tek bir satırda birden fazla eşitlik olmasını yönetemiyordu.
- **Teknik Çözüm**: `_segment_line_into_equations()` fonksiyonu eklendi:
  - Satırda birden fazla `=` işareti tespit edildiğinde, boşluklar ve değişken sınırları analiz edilerek satır bağımsız alt ifadelere (`['x+0=1', 'ly-3=9']`) bölümlendi.
  - Ardından her alt ifade bağımsız olarak `correct_ocr_confusion` ve `validate_expression` hattına sokuldu.
- **Sonuç**: `x+0=1 ly-3=9` satırından `x+0=1` ve `y-3=9` olarak iki bağımsız, geçerli denklem başarıyla kurtarıldı.

---

### 🟠 P1 — Mimari ve Doküman İyileştirmeleri

#### [BUG-008 & BUG-009] PDF Çözünürlük Kaybı & Satır Bölge Tespiti (Line Slicing)
- **Kök Neden**: Eski `ocr_engine.py` içinde `h > 600` ise tüm sayfa `scale = 400 / h` ile 400px yüksekliğe küçültülüyordu. 2200x1700 piksel boyutundaki bir A4 sayfası 5.5 kat küçültülüyor, metinler 2-3 piksele düşerek Tesseract tarafından okunamaz hale geliyordu.
- **Teknik Çözüm**:
  1. Yıkıcı küçültme kodu tamamen kaldırıldı.
  2. `segment_into_line_regions()` fonksiyonu geliştirildi: Sayfa görseli üzerinde yatay morfolojik kernel (`cv2.MORPH_RECT, (40, 5)`) ile satır bölgeleri ve konturları çıkarıldı.
  3. Her satır bölgesi bağımsız yüksek çözünürlükte kırpılıp (crop) ideal 96px ölçeğinde OCR'a iletildi.
- **Sonuç**: Üs işaretleri ($x^2$), alt simgeler ve ince operatörler netliğini korudu; OCR okuma başarısı katlanarak arttı.

#### [BUG-010 & BUG-011] Güven Skoru ve Zengin Veri Modeli
- **Kök Neden**: OCR çıktıları sadece düz metin dizisi (`list[str]`) olarak dönüyordu; güven puanı (`confidence`) ve ham metin (`raw_text`) kayboluyordu.
- **Teknik Çözüm**: `extract_from_array` ve `extract_equations` fonksiyonlarına `return_details=True` modu eklendi. Çıktı modeli:
  ```json
  {
      "index": 1,
      "source": "Sayfa 1",
      "raw_text": "ly+5=2",
      "normalized_text": "1y+5=2",
      "equation": "y+5=2",
      "confidence": 88.5,
      "is_valid": true
  }
  ```
- **Sonuç**: Hangi ifadenin hangi aşamada nasıl dönüştüğü ve Tesseract güven oranı şeffaf şekilde izlenebilir hale geldi.

#### [BUG-012] DocumentEngine İçin Kapsamlı Test Takımı Eksikliği
- **Teknik Çözüm**: [`tests/test_document.py`](file:///c:/Users/Hp/Desktop/ReconCAS/tests/test_document.py) oluşturuldu. 10 adet izole birim test yazılarak doküman analiz motorunun tüm uç senaryoları kapsandı.

#### [BUG-013] PDF 30 Sayfa Sınırının Kullanıcıya Açıklanması
- **Teknik Çözüm**: `DocumentWindow` arayüzüne belirgin bir sarı uyarı paneli eklendi (`lbl_page_warning`). Belge 30 sayfadan büyükse:
  `⚠ PDF {N} sayfa içeriyor. İlk 30 sayfa analiz edildi.`
  ifadesi liste başında ve arayüzde gösterilmektedir.

---

### 🟡 P2 — Arayüz, Dokümantasyon & Tedarik Zinciri

#### [BUG-014] Desteklenen Dosya Formatlarının Eşitlenmesi
- **Teknik Çözüm**: Dosya seçici filtreleri güncellendi:
  `("Desteklenen Tüm Dosyalar", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.pdf")`.

#### [BUG-015] Birinci Sınıf Sembolik İşlem Dağıtıcısı (Operation Dispatcher)
- **Teknik Çözüm**: `MathEngine.dispatch_operation(text)` metodu eklendi. `diff`, `integrate`, `limit`, `series`, `factor`, `simplify`, `solve` ve `Matrix` fonksiyonları doğrudan sembolik işlem olarak değerlendirilmektedir.

#### [BUG-016] Mutlak Değer `|x|` Desteği
- **Teknik Çözüm**: `format_input()` içine `re.sub(r'\|([^|]+)\|', r'Abs(\1)', text)` eklendi. `|-5| -> 5`, `|x+1| -> Abs(x+1)` desteği sağlandı.

#### [BUG-017] `app_windows.py` Dosyasının Modülerleştirilmesi
- **Teknik Çözüm**: 889 satırlık monolitik dosya mantıksal modüllere ayrıldı:
  - `gui/theme.py`: Siberpunk renk ve font tanımları
  - `gui/widgets.py`: `AnimatedToggle` bileşeni
  - `gui/auth_window.py`: Kimlik doğrulama penceresi
  - `gui/terminal_window.py`: Ana komuta merkezi
  - `gui/lab_window.py`: CAS Laboratuvarı
  - `gui/sandbox_window.py`: Kinetik 3D Uzay Simülatörü
  - `gui/document_window.py`: Doküman Analiz Penceresi
  - `gui/app_windows.py`: Geriye dönük %100 uyumlu Facade (re-export)

#### [BUG-018 & BUG-019] README Dokümantasyonunun Güncellenmesi
- **Teknik Çözüm**: `README.md` 4 katmanlı mimari, 96px adaptif hedef, 30 sayfa mevcut limiti ve 80+ sayfa gelecek yol haritası ile güncellendi.

#### [BUG-020] SLSA Level 3 Release Workflow'u
- **Teknik Çözüm**: [`.github/workflows/slsa_release.yml`](file:///c:/Users/Hp/Desktop/ReconCAS/.github/workflows/slsa_release.yml) oluşturuldu. Gerçek ReconCAS dağıtım arşivini (`reconcas-release.zip`) paketleyen, SHA256 özetini çıkaran ve SLSA Level 3 provenance üreten resmi GitHub Actions iş akışı kuruldu.

#### [BUG-021] Güvenlik Beyanının Gerçekçi Hale Getirilmesi
- **Teknik Çözüm**: "Enterprise-grade" ifadesi yerine yerel SQLite üzerinde `bcrypt.gensalt()` ile tuzlanmış parola hash'leme ve zero-trust lexical whitelist güvenliği ifadeleri kullanıldı.

---

## 🏛️ 3. Mimari Dönüşüm Karşılaştırması

```
[ ESKİ MİMARİ — V0.1 BETA ]
Dosya (PDF / Görsel)
   ↓ (Tüm sayfa 400px'e küçültülür — ÇÖZÜNÜRLÜK KAYBI)
Tekli / İlkel OCR
   ↓ (Sadece matematik karakter sayısı sayılır)
Basit Karakter Skoru (Çöp metinler öne geçer)
   ↓
Doğrulanmamış Adaylar (crore/ serine iar, ly+5=2)
   ↓
Liste / Arayüz (Hatalı ve bozuk formüller)

-----------------------------------------------------------

[ YENİ MİMARİ — V0.1.1 BETA ]
Dosya (PDF / Görsel)
   ↓ (200 DPI tam çözünürlük korunur)
Sayfa Satır Bölge Tespiti (segment_into_line_regions)
   ↓ (Her satır bağımsız ~96px crop olarak işlenir)
Çok Kriterli Multi-PSM Motoru (Confidence + Parse + Struct - Garbage)
   ↓
Çoklu Denklem Bölümleme (x+0=1 ly-3=9 -> ['x+0=1', 'ly-3=9'])
   ↓
Token Confusion Düzeltme (ly+5=2 -> y+5=2, lx-4=3 -> x-4=3)
   ↓
Syntax-Aware Normalizasyon (√x -> sqrt(x), ∫x dx -> integrate(x, x), |x| -> Abs(x))
   ↓
Zero-Trust Lexical Whitelist (Case-Insensitive SAFE_WORDS)
   ↓
SymPy Doğrulama Katmanı (validate_expression)
   ↓
Zengin Veri Modeli ({raw, normalized, equation, conf, is_valid})
   ↓
CAS Lab / 3D Sandbox / Document Window
```

---

## 🏁 4. Sonuç ve Sürüm Durumu

ReconCAS V0.1.1 BETA sürümü itibarıyla:
- **Tüm 28 hata maddesi eksiksiz çözülmüştür.**
- **27/27 otomatik test başarıyla geçmektedir.**
- PDF ve görsel tarama doğruluğu dramatik şekilde artırılmış, matematik dışı gürültüler elenmiş ve OCR karakter karışıklıkları otomatik düzeltilmiştir.
- Kod tabanı modülerleştirilerek sürdürülebilir ve temiz bir mimariye kavuşturulmuştur.

