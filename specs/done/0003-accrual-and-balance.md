# Spec 0003 — Hak ediş ve izin bakiyesi

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0003-plan.md`

## Intent
İK ve çalışanlar, yıllık izin bakiyesinin İş Kanunu'na göre otomatik ve şeffaf biçimde
tutulmasını istiyor; bugün bu bilgi uygulamada hiç yok ve izin talebi özelliği buna dayanacak.

Başarı:
- Kıdem yıldönümünde yıllık izin hakkı, kimse elle girmeden bakiyeye eklenir (BR-1, BR-2, BR-3).
- Çalışan kendi bakiyesini ve onu oluşturan hareketleri ana sayfada görür.
- İK gerekçeli düzeltme yapar; düzeltmeler değiştirilemez ve audit kaydına düşer (BR-12).
- Kıdemli çalışanların mevcut bakiyesi, İK'nın girdiği açılış düzeltmesiyle sisteme taşınır.

Bilinçli olarak yapılmayanlar: izin talebi, onay, kullanım ve iade hareketleri, kullanılabilir
bakiye, resmi tatil takvimi, yöneticinin ekibinin bakiyesini görmesi.

Netleştirme kararları (2026-10-21):
- Açılış: İK her kıdemli çalışana gerekçeli bir **açılış düzeltmesi** girer. Otomatik hak ediş
  yalnızca İK'nın belirlediği **otomatik hak ediş başlangıç tarihi** ve sonrasındaki
  yıldönümleri için çalışır; geçmiş yıllar geriye dönük hesaplanmaz.
- Hak ediş, yıldönümü günü itibarıyla kimsenin bir işlem yapmasına gerek kalmadan bakiyede görünür.
- Doğum tarihi çalışan kaydında zorunludur; yalnız İK görür.
- Çalışan yalnız kendi bakiyesini uygulamada görür; İK tüm bakiyeleri ve düzeltmeleri yönetim
  panelinden yönetir. Yöneticinin ekip bakiyesi onay spec'ine kalır.

## Requirements
1. **Doğum tarihi:** İK, çalışan oluştururken ve düzenlerken doğum tarihini girmek zorundadır.
   Doğum tarihi bugünden sonra olamaz ve işe giriş tarihinden önce olmalıdır; aksi hâlde kayıt
   yapılmaz ve İK'ya alan bazında hata gösterilir. Doğum tarihini uygulamada yalnız İK görür
   (yönetim paneli); çalışana ve yöneticiye gösterilmez.
2. **Kıdem:** Kıdem, Polsan'daki işe giriş tarihinden itibaren tamamlanan tam hizmet yılıdır
   (BR-15). n'inci kıdem yıldönümü, işe giriş tarihinin n yıl sonrasıdır. 29 Şubat'ta işe
   girenlerin artık olmayan yıllardaki yıldönümü 28 Şubat'tır. Aynı kural yaş için de geçerlidir:
   29 Şubat doğumlu çalışan, artık olmayan yıllarda yeni yaşını 28 Şubat'ta doldurur (BR-2; review
   L1, 2026-10-21).
3. **Hak ediş miktarı:** n'inci yıldönümünde eklenen gün:
   - n = 1–5 → 14; n = 6–14 → 20; n ≥ 15 → 26 (BR-1).
   - Çalışan o yıldönümü günü tamamlanmış yaşına göre 18 veya daha küçük ya da 50 veya daha büyükse
     ve yukarıdaki değer 20'den küçükse → 20 (BR-2).
   - İşe girişten 1 tam yıl dolmadan hak ediş yoktur (BR-3).
4. **Otomatik hak ediş:** Yıldönümü günü (Türkiye saatiyle) başladığı andan itibaren o yılın hakkı
   bakiyede tek bir **hak ediş** hareketi olarak yer alır; kimsenin bir işlem yapması gerekmez.
   Aynı yıldönümü için ikinci bir hak ediş hareketi hiçbir koşulda oluşmaz.
   Hak ediş yalnızca şu yıldönümleri için yapılır:
   - otomatik hak ediş başlangıç tarihi veya sonrasına düşen;
   - yıldönümü günü çalışan kaydı **aktif** olan.

   - çalışan kaydının sisteme **eklendiği gün veya sonrasına** düşen. Kayıttan önceki dönemi İK
     açılış düzeltmesiyle girer (review M3, 2026-10-21).

   Pasif olduğu dönemde kaçırılan yıldönümü, çalışan yeniden aktif yapılınca sonradan eklenmez;
   gerekirse İK düzeltmeyle yansıtır. Bu kural ve Gereksinim 6, yalnız otomatik hak ediş başlangıç
   tarihi girildikten sonra yapılan değişikliklere uygulanır. Kurulum sırasında, başlangıç tarihi
   girilmeden önce yapılan yeniden aktif yapma ve tarih düzeltmeleri bir sınır oluşturmaz; geçmiş
   bir başlangıç tarihi bütün çalışanlara aynı biçimde uygulanır (review M3, 2026-10-21).
5. **Otomatik hak ediş başlangıç tarihi:**
   - İK bu tarihi yönetim panelinden bir kez girer. Girilene kadar hiçbir otomatik hak ediş yapılmaz.
   - Tarih geçmiş bir gün olabilir (review M3, 2026-10-21).
   - Tarih değişikliği ile aynı anda yapılan bakiye okumaları, değişiklikten önceki ya da sonraki
     tarihi tutarlı biçimde kullanır. Okuma eski tarihle hak ediş yazdıysa değişiklik reddedilir
     (review M1, 2026-10-21).
   - İlk otomatik hak ediş hareketi oluştuktan sonra tarih değiştirilemez.
6. **Kayıt değişikliği:** İK işe giriş veya doğum tarihini değiştirirse mevcut hak ediş hareketleri
   değişmez. Sonraki yıldönümleri yeni tarihlere göre hesaplanır. Geçmişin düzeltilmesi İK
   düzeltmesiyle yapılır. Defterde hak edişi zaten bulunan bir kıdem yılı, tarih değişse de
   yeniden oluşmaz. Örneğin işe giriş tarihi ileri kaydırılırsa, hak edişi alınmış yıllar atlanır
   (review M2, 2026-10-21).
7. **Düzeltme:** İK yönetim panelinden bir çalışana düzeltme hareketi ekler (BR-12):
   - **Miktar:** sıfırdan farklıdır, 0,5'in katıdır (BR-5), artı veya eksi olabilir ve mutlak
     değeri en fazla 100 gündür.
   - **Gerekçe:** zorunludur ve yalnız boşluktan oluşamaz.

   Geçersiz giriş kaydedilmez ve alan bazında hata gösterilir. Düzeltme bakiyeyi sıfırın altına
   indirebilir; bu yalnız İK'ya açık bir yetkidir.
   Açılış bakiyesi, gerekçesi açılışı belirten sıradan bir düzeltmedir.
8. **Değişmezlik:** Hak ediş ve düzeltme hareketleri hiçbir kullanıcı tarafından (İK dahil,
   yönetim paneli dahil) değiştirilemez ve silinemez. Hatalı hareket ters yönde yeni bir
   düzeltmeyle giderilir.
9. **Audit:** Her düzeltme audit kaydına yazılır: kim, ne zaman, hangi çalışan, miktar, gerekçe.
   Audit kaydı değiştirilemez ve silinemez.
10. **Bakiye:** Bir çalışanın bakiyesi, hareketlerinin toplamıdır. Kullanılmayan gün yıl sonunda
    yanmaz, olduğu gibi devreder (BR-11); yıl sonunda hiçbir hareket oluşmaz.
11. **Çalışanın görünümü:** Giriş yapan kullanıcı ana sayfada **yalnız kendi** bilgilerini görür:
    - **Bakiye:** güncel bakiye.
    - **Sonraki hak ediş:** gerçekten oluşacak ilk hak edişin tarihi ve gün sayısı; defterde
      hak edişi bulunan kıdem yılları atlanır (review M2). Bir sonraki yıldönümü otomatik hak ediş
      başlangıç tarihinden önceyse veya başlangıç tarihi girilmemişse bu satır gösterilmez.
    - **Hareket geçmişi:** her harekette tarih, tür (Hak ediş / Düzeltme), miktar (işaretli) ve
      düzeltmelerde gerekçe. Hareketler yeniden eskiye sıralıdır.

    Gün miktarları Türkçe biçimde gösterilir: "12,5 gün", "+14 gün", "−2 gün".
12. **İK'nın görünümü:** İK yönetim panelinde her çalışanın bakiyesini ve hareket geçmişini görür.
    Hareketleri çalışana göre süzebilir.
13. **Erişim:** Bir kullanıcı başka bir çalışanın bakiyesine veya hareketlerine uygulama
    üzerinden erişemez; denemesi "bulunamadı" olarak sonuçlanır. Giriş yapmamış kullanıcı
    hiçbir bakiye verisine erişemez.
14. **Korunan davranış (spec 0001, 0002):** Giriş, roller, ana sayfanın mevcut içeriği ("Hoş
    geldiniz", roller, "Ekibim", "Çıkış yap") ve bütün kabul kriterleri değişmeden geçerlidir.

## User experience
- **Flow:**
  1. **Kurulum (İK, yönetim paneli):**
     1. Her çalışanın doğum tarihini girer.
     2. Kıdemli çalışanlara açılış düzeltmesi girer.
     3. Otomatik hak ediş başlangıç tarihini girer.
  2. **Çalışan:** Girişten sonra ana sayfada "İzin bakiyem" bölümünü görür: bakiye, sonraki hak
     ediş ve "Hareketler" listesi.
  3. **Düzeltme (İK, yönetim paneli):** İK bir çalışana düzeltme ekler; çalışan ana sayfayı
     yenilediğinde yeni bakiyeyi ve hareketi görür.
- **States:**
  - **"İzin bakiyem" bölümü:**
    - **Yükleniyor:** "Bakiye yükleniyor…"
    - **Başarı:** bakiye, sonraki hak ediş (varsa), hareket listesi.
    - **Boş:** hiç hareket yok → bakiye "0 gün" ve "Henüz bakiye hareketiniz yok."
    - **Hata:** "Bakiye bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin." Ana sayfanın geri
      kalanı (spec 0002) etkilenmeden görünür.
  - **Yönetim paneli:** doğum tarihi ve düzeltme formlarında alan bazında doğrulama hataları.
    Hareketlerde düzenleme ve silme seçeneği yoktur.
  - **Yetkisiz:** giriş yapmamış kullanıcı → giriş ekranı (spec 0002). İK olmayan kullanıcı
    yönetim paneline giremez.
- **Design reference:** none — the flow above is the design.
- **Accessibility:**
  - "İzin bakiyem" bir başlıkla (h2) etiketlenmiş bölümdür.
  - Hareketler, sütun başlıkları olan bir tablodur.
  - Yükleniyor ve hata durumları ekran okuyucuya duyurulur.
  - Eksi işareti ekran okuyucuda "eksi" olarak okunur.
  - Bölüm yalnız klavyeyle gezilebilir.
  - Her durumda WCAG 2.1 AA.

## Constraints & out of scope
- `docs/security.md` ve KVKK:
  - Doğum tarihi kişisel veridir, uygulamada yalnız İK'ya görünür.
  - Loglarda kişisel veri yerine UUID kullanılır.
  - Nesne düzeyinde yetki yalnız sunucuda; başkasının kaydı → 404.
- Bakiye ayrı bir alanda saklanmaz, her zaman hareketlerden hesaplanır (`docs/domain.md`
  invariant).
- v1'de arka plan işçisi veya kuyruk yoktur (`docs/architecture.md`). Gereksinim 4'ün
  "kimsenin işlem yapmasına gerek kalmadan" davranışı bu sınır içinde sağlanmalıdır.
- BR-1 kademeleri İK teyidi bekliyor (`docs/domain.md`). Teyit farklı çıkarsa bu bir spec
  değişikliğidir (R-08).
- **Out of scope:**
  - İzin talebi, onay ve ret; kullanım ve iade hareketleri; kullanılabilir bakiye (BR-4…BR-10).
  - Resmi tatil takvimi ve iş günü hesabı.
  - Yöneticinin ekibinin bakiyesini görmesi; uygulama içi (panel dışı) İK ekranları.
  - Geçmiş yılların geriye dönük otomatik hak edişi; toplu açılış bakiyesi içe aktarma.
  - Önceki işverenlerdeki hizmet süresi (BR-15; gerekirse düzeltmeyle).
  - Bakiye bildirimleri (e-posta vb.), raporlar ve dışa aktarma.

## Acceptance criteria
- [x] AC-1 — İK, doğum tarihi olmadan çalışan oluşturamaz veya kaydedemez; alan bazında hata gösterilir.
- [x] AC-2 — Bugünden sonraki veya işe giriş tarihine eşit ya da ondan sonraki doğum tarihi kaydedilmez ve alan bazında hata gösterilir.
- [x] AC-3 — Doğum tarihi, uygulamanın hiçbir yanıtında ve ekranında (ana sayfa dahil) çalışana veya yöneticiye görünmez.
- [x] AC-4 — İşe girişten 1 tam yıl dolmamış çalışanın hak ediş hareketi yoktur; 1. yıldönümü günü 14 günlük hak ediş görünür, bir gün öncesinde görünmez.
- [x] AC-5 — Kademe sınırları: 5. yıldönümünde 14, 6. yıldönümünde 20, 14. yıldönümünde 20, 15. yıldönümünde 26 gün eklenir.
- [x] AC-6 — Yaş tabanı: yıldönümü günü 18 yaşında veya daha küçük ya da 50 yaşında veya daha büyük olan çalışana 1.–5. yıllarda 20 gün eklenir. 19 ve 49 yaşındakine 14 gün eklenir. 15. yıl ve sonrasında 26 gün değişmez.
- [x] AC-7 — Yaş, yıldönümü günündeki tamamlanmış yaştır: 50. doğum günü yıldönümünden bir gün sonra olan çalışana BR-1 değeri (ör. 14) eklenir. 50. doğum günü yıldönümü günü olana 20 eklenir.
- [x] AC-8 — 29 Şubat'ta işe giren çalışanın artık olmayan yıldaki yıldönümü hak edişi 28 Şubat'ta görünür.
- [x] AC-9 — Otomatik hak ediş başlangıç tarihi girilmemişse hiçbir otomatik hak ediş hareketi oluşmaz.
- [x] AC-10 — Başlangıç tarihinden önceye düşen yıldönümleri için hak ediş oluşmaz. Başlangıç tarihine veya sonrasına düşen yıldönümü için oluşur.
- [x] AC-11 — İlk otomatik hak ediş oluştuktan sonra başlangıç tarihi değiştirilemez ve İK'ya hata gösterilir. Öncesinde değiştirilebilir.
- [x] AC-12 — Aynı yıldönümü için hak ediş hareketi tam bir kez oluşur: bakiye tekrar tekrar ve eşzamanlı sorgulansa da ikinci hareket oluşmaz.
- [x] AC-13 — Birden çok yıldönümü (sorgulanmadan geçen yıllar) başlangıç tarihinden sonra birikmişse her biri kendi kademesi ve o günkü yaşıyla ayrı birer hareket olarak görünür.
- [x] AC-14 — Yıldönümü günü pasif olan çalışana o yıldönümü için hak ediş oluşmaz. Yeniden aktif yapıldığında da sonradan eklenmez.
- [x] AC-15 — İK işe giriş veya doğum tarihini değiştirdiğinde mevcut hak ediş hareketleri değişmez. Sonraki yıldönümü yeni tarihlerle hesaplanır.
- [x] AC-16 — İK; artı, eksi ve 0,5 katı miktarla, gerekçeli düzeltme ekleyebilir. Bakiye ve hareket geçmişi buna göre değişir.
- [x] AC-17 — Miktarı 0, 0,5'in katı olmayan (ör. 1,3), mutlak değeri 100'den büyük veya gerekçesi boş ya da yalnız boşluk olan düzeltme kaydedilmez. Alan bazında hata gösterilir.
- [x] AC-18 — Bakiyeyi sıfırın altına indiren İK düzeltmesi kaydedilir ve bakiye eksi görünür.
- [x] AC-19 — Hak ediş ve düzeltme hareketleri yönetim panelinde dahil kimse tarafından değiştirilemez veya silinemez.
- [x] AC-20 — Her düzeltme için audit kaydı oluşur: kim, ne zaman, çalışan, miktar, gerekçe. Audit kaydı değiştirilemez ve silinemez.
- [x] AC-21 — Yıl sonunu geçen bakiye aynen devreder: 31 Aralık ve 1 Ocak'taki bakiye aynıdır, arada hiçbir hareket oluşmaz.
- [x] AC-22 — Ana sayfada "İzin bakiyem" bölümü giriş yapanın güncel bakiyesini, sonraki hak ediş tarihini ve gün sayısını gösterir.
- [x] AC-23 — Sonraki yıldönümü başlangıç tarihinden önceyse veya başlangıç tarihi girilmemişse "Sonraki hak ediş" satırı gösterilmez.
- [x] AC-24 — Hareket geçmişi yeniden eskiye sıralıdır. Her satırda tarih, tür (Hak ediş / Düzeltme), işaretli miktar ve düzeltmelerde gerekçe vardır.
- [x] AC-25 — Gün miktarları Türkçe biçimdedir ("12,5 gün", "+14 gün", "−2 gün").
- [x] AC-26 — Hiç hareketi olmayan çalışan "0 gün" ve "Henüz bakiye hareketiniz yok." görür.
- [x] AC-27 — Bakiye yüklenirken "Bakiye yükleniyor…" görünür.
- [x] AC-28 — Bakiye yüklenemezse "Bakiye bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin." görünür; ana sayfanın geri kalanı görünmeye devam eder.
- [x] AC-29 — Bir kullanıcı başka bir çalışanın bakiyesini veya hareketlerini istediğinde "bulunamadı" (404) alır. Giriş yapmamış kullanıcı hiçbir bakiye verisine erişemez.
- [x] AC-30 — İK yönetim panelinde her çalışanın bakiyesini ve hareketlerini görür, hareketleri çalışana göre süzebilir. İK olmayan kullanıcı panele giremez.
- [x] AC-31 — "İzin bakiyem" bölümü yükleniyor, boş, başarı ve hata durumlarında axe denetiminden ihlalsiz geçer ve yalnız klavyeyle gezilebilir.
- [x] AC-32 — Spec 0001 ve 0002'nin bütün kabul kriterleri geçerli kalır (regresyon yok).
- [x] AC-33 — 29 Şubat doğumlu çalışan, artık olmayan yılda 28 Şubat'a denk gelen yıldönümünde yeni yaşını doldurmuş sayılır (ör. 1976-02-29 doğumluya 2026-02-28'de 50 yaşında 20 gün eklenir).
- [x] AC-34 — İK'nın sisteme eklediği çalışan için, kaydın eklendiği günden önceki yıldönümlerine otomatik hak ediş oluşmaz; eklendiği gün veya sonrasındaki yıldönümleri için oluşur.
- [x] AC-35 — Başlangıç tarihi girilmeden önce yapılan yeniden aktif yapma veya tarih düzeltmesi sınır oluşturmaz; sonradan girilen geçmiş başlangıç tarihi o çalışanlara da diğerleriyle aynı uygulanır. Başlangıç tarihi geçmiş bir gün olarak kaydedilebilir.
- [x] AC-36 — İşe giriş tarihi ileri kaydırılan çalışanın "Sonraki hak ediş" satırı, defterde hak edişi olan kıdem yıllarını atlayıp gerçekten oluşacak ilk hak edişi gösterir; o tarihte o hak ediş oluşur.
- [x] AC-37 — Başlangıç tarihi değişikliği, eski tarihle hak ediş yazan eşzamanlı bir bakiye okumasıyla çakışırsa değişiklik reddedilir ve İK'ya form hatası gösterilir (500 değil); ayar ile defter tutarlı kalır.

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale
- [x] Docs / ADRs updated if behavior or architecture changed
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 1 (review 1. tur sonrası R-08: Req 2, 4, 5, 6, 11; AC-33…AC-37) |
| Fix rounds | 2 (review 1. tur: M1–M3, L1–L3, L5; 2. tur: N1, N2) |
| Review findings: real / noise | 10 / 9 — review 9 / 3 (M1–M3, L1–L3, L5, N1, N2 / L4, P1, P2), verify 1 / 6 (1 / 2–7) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 |
