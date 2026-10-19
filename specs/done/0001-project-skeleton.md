# Spec 0001 — Proje iskeleti

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0001-plan.md`

## Intent
Geliştirme ekibi, Polsan Leave Manager özelliklerini `docs/` kurallarına uygun ve kanıtlı biçimde
ekleyebilmek için çalışan bir iskelete ihtiyaç duyuyor. Başarı: tek komut (`./scripts/check`)
backend, frontend ve uçtan uca katmanların hepsini doğrular; aynı doğrulama GitHub'da her push ve
PR'da çalışır; tarayıcıda açılan bir başlangıç sayfası frontend ile backend'in (ve veritabanının)
birbirine bağlı olduğunu gösterir; yeni bir geliştirici README'deki talimatla uygulamayı kendi
makinesinde ayağa kaldırabilir. Bilinçli olarak yapılmayan: izin talebi, giriş/kimlik, bakiye gibi
hiçbir iş özelliği ve üretim ortamına kurulum — bunlar sonraki spec'lerdir.

Netleştirme kararları (2026-10-19): başlangıç sayfası + sunucu bağlantı durumu; altı modül boş
public arayüzleriyle şimdi oluşturulur; CI tam check + ayrı bağımlılık güvenlik taraması çalıştırır;
yerel geliştirme veritabanı ve çalıştırma talimatı dahildir.

## Requirements
1. **Başlangıç sayfası:** Uygulama açıldığında Türkçe bir başlangıç sayfası ürün adını ve sunucu
   bağlantı durumunu gösterir.
2. **Bağlantı durumu:** Sayfa açılışta sunucuya durumunu sorar. Sunucu yalnızca kendisi **ve**
   veritabanı erişilebilir olduğunda "sağlıklı" yanıt verir. Durum sorgusu kimlik doğrulama
   gerektirmez ve durum dışında hiçbir bilgi (sürüm, ortam, kişisel veri, hata ayrıntısı) döndürmez.
3. **Varsayılan reddet:** Durum sorgusu dışındaki her sunucu ucu varsayılan olarak kimlik doğrulama
   ister; açık erişim yalnızca bilinçli ve görünür biçimde tanımlanabilir.
4. **Modüller:** `docs/architecture.md`'deki altı modül (`employees`, `workcalendar`, `balances`,
   `leaves`, `identity`, `audit`) iş mantığı olmadan, boş public arayüzleriyle vardır.
5. **Sınırların araçla zorlanması:** `docs/architecture.md` "Forbidden dependencies" maddeleri 1–6
   otomatik kontrollerle zorlanır; bir ihlal `./scripts/check`'i kırmızı yapar.
6. **API sözleşmesi:** Frontend sunucuya yalnızca sunucunun yayımladığı API sözleşmesinden üretilmiş
   istemciyle erişir; sözleşme ile üretilmiş istemci uyumsuz kalırsa `./scripts/check` kırmızı olur.
7. **Doğrulama sözleşmesi:** `./scripts/check` tam profilde `scripts/check.conf`'taki tüm katmanları
   (backend lint, tip, sınır, unit, entegrasyon; frontend lint, tip, unit; e2e) çalıştırır;
   `--fast` yalnızca hızlı adımları. Her test katmanında en az bir gerçek test vardır; hiç test
   toplamayan bir adım kırmızıdır. Check ardında hiçbir süreç bırakmaz (residue testi).
8. **CI:** GitHub Actions her push ve PR'da workspace sağlık kontrolünü ve **tam** check'i çalıştırır;
   ayrı bir job bağımlılıkları bilinen güvenlik açıklarına karşı tarar.
9. **Yerel geliştirme:** README, yeni bir geliştiricinin geliştirme veritabanını başlatıp backend ve
   frontend'i çalıştırarak başlangıç sayfasını görmesi için gereken adımları içerir.
10. **Gizli bilgiler:** Uygulama gizli değerleri (anahtar, veritabanı parolası) yalnızca ortamdan
    okur; repoda örnek bir ortam dosyası bulunur, gerçek değer bulunmaz.

## User experience
- **Flow:** Kullanıcı uygulamanın adresini tarayıcıda açar → başlangıç sayfası yüklenir → sayfa
  sunucu durumunu otomatik sorar → sonuç sayfada gösterilir. Başka etkileşim yoktur.
- **States:**
  - Yükleniyor: "Sunucu bağlantısı kontrol ediliyor…"
  - Başarı: "Sunucu bağlantısı: Bağlı"
  - Hata (sunucu 5 saniye içinde yanıt vermiyor, hata dönüyor veya veritabanına ulaşamıyor):
    "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin." — teknik ayrıntı gösterilmez.
  - Boş: uygulanamaz (gösterilecek liste yok).
  - Yetkisiz: uygulanamaz (sayfa ve durum sorgusu herkese açık; giriş sonraki spec).
- **Design reference:** none — the flow above is the design. Başlık "Polsan Leave Manager".
- **Accessibility:** sayfa dili `tr`; ürün adı tek birincil başlıktır; durum mesajı ekran
  okuyucuya duyurulan bir durum bölgesindedir; metin kontrastı WCAG AA (≥ 4.5:1).

## Constraints & out of scope
- `./scripts/check` hem geliştirme makinesinde (Windows 11, Git Bash) hem CI'da (Ubuntu) yeşildir.
- Başlangıç sayfası ve sunucu API'si **aynı origin**'den sunulur — e2e testinde de
  (`docs/security.md`: oturum çerezi + CSRF buna dayanır).
- Versiyonlar, araçlar ve kalıplar `docs/conventions.md`, `docs/testing.md`, `docs/security.md`'ye
  uyar; yeni bağımlılıklar planda gerekçesiyle listelenir ve plan onayıyla kabul edilir.
- **Out of scope:** giriş/kimlik doğrulama, kullanıcı hesapları, roller; izin, bakiye, takvim
  özellikleri ve bunların veri modelleri; üretim ortamına kurulum (IIS / Windows Service / ters
  proxy); "Tekrar dene" düğmesi veya periyodik durum yenileme; İngilizce arayüz.

## Acceptance criteria
- [x] AC-1 — Başlangıç sayfası açıldığında tek birincil başlık olarak "Polsan Leave Manager" görünür ve sayfanın dili `tr`'dir.
- [x] AC-2 — Sunucu ve veritabanı erişilebilirken sayfa "Sunucu bağlantısı: Bağlı" gösterir.
- [x] AC-3 — Durum sorgusu yanıtlanana kadar sayfa "Sunucu bağlantısı kontrol ediliyor…" gösterir.
- [x] AC-4 — Sunucu 5 saniye içinde yanıt vermediğinde veya hata döndüğünde sayfa "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin." gösterir; sayfada hata kodu, yığın izi veya adres gibi teknik ayrıntı yer almaz.
- [x] AC-5 — Veritabanına ulaşılamadığında sunucu durum sorgusuna "sağlıklı değil" yanıtı verir (başarısız durum kodu) ve yanıt veritabanı adı, adresi veya hata metni içermez.
- [x] AC-6 — Durum sorgusu kimlik doğrulama olmadan yanıtlanır ve yanıt yalnızca durum bilgisini içerir (sürüm, ortam, kişisel veri yok).
- [x] AC-7 — Durum sorgusu dışındaki her sunucu ucu, açıkça erişim izni bildirmiyorsa kimliği doğrulanmamış isteği reddeder; erişim izni bildirmeyen bir uç eklenirse otomatik kontrol kırmızı olur.
- [x] AC-8 — Altı modülün her biri vardır ve yalnızca kendi public arayüzünü dışa açar.
- [x] AC-9 — Bir modülün başka bir modülün public arayüzü dışındaki bir parçasını kullanması, izin verilen yön dışında bir modül bağımlılığı ve `domain` katmanının Django/DRF'e veya başka modüle bağımlılığı `./scripts/check`'i kırmızı yapar (Forbidden dependencies 1–3).
- [x] AC-10 — `employees.Employee` dışındaki bir modüle verilen modüller arası yabancı anahtar ve iş mantığında Django signal alıcısı `./scripts/check`'i kırmızı yapar (Forbidden dependencies 4–5).
- [x] AC-11 — Frontend kodunda ham `fetch`/`axios` kullanımı ve `dangerouslySetInnerHTML` `./scripts/check`'i kırmızı yapar (Forbidden dependencies 6, `docs/security.md`).
- [x] AC-12 — Sunucunun API sözleşmesi değişip frontend'in üretilmiş istemcisi güncellenmezse `./scripts/check` kırmızı olur.
- [x] AC-13 — `./scripts/check` (tam) `check.conf`'taki tüm adımları çalıştırır ve yeşildir; `./scripts/check --fast` yalnızca `[fast]` etiketli adımları çalıştırır ve yeşildir.
- [x] AC-14 — Her test adımı en az bir test çalıştırır (backend unit, backend entegrasyon, frontend unit, e2e); hiç test toplamayan bir adım kırmızıdır.
- [x] AC-15 — *(gerekçeli kabul: plan Amendments ve evidence tablosu)* `./scripts/residue` ve `./scripts/residue --fast` temizdir (RESIDUE CLEAN); her profilin süresi en az 3 çalıştırmanın medyanı olarak raporlanır.
- [x] AC-16 — GitHub Actions'ta bir PR için `doctor --strict`, tam `./scripts/check` ve bağımlılık güvenlik taraması job'ları çalışır; doctor ve check yeşildir.
- [x] AC-17 — Repo dışında geçici bir dizine alınmış temiz bir klonda (Docker, Python, Node kurulu) yalnızca README talimatı izlenerek geliştirme veritabanı başlatılır, backend ve frontend çalıştırılır ve başlangıç sayfası "Sunucu bağlantısı: Bağlı" gösterir; klon sonra silinir, sonuç tek satır olarak kaydedilir.
- [x] AC-18 — Gizli anahtar ortamda tanımlı değilken uygulama üretim ayarlarıyla başlamayı reddeder; repoda `.env.example` vardır ve gerçek gizli değer içermez.
- [x] AC-19 — Durum mesajı ekran okuyucuya duyurulan bir durum bölgesindedir ve başlangıç sayfasının üç durumunda (yükleniyor, başarı, hata) otomatik erişilebilirlik taraması WCAG 2.1 AA ihlali bulmaz (kontrast ≥ 4.5:1 dahil).
- [x] AC-20 — E2E testinde başlangıç sayfası ve durum sorgusu aynı origin'den sunulur (sayfa, sunucuya farklı bir host/port üzerinden erişmez).

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale
- [x] Docs / ADRs updated if behavior or architecture changed
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 0 (açık noktalar G1, G3, G4, G5 onaydan önce katıldı) |
| Fix rounds | 3 (review, verify, CI audit) |
| Review findings: real / noise | 16 / 1 (+1 ertelendi: F-2) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 |
