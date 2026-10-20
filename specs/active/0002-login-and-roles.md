# Spec 0002 — Giriş ve roller

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0002-plan.md`

## Intent
Polsan çalışanları uygulamaya kendi hesaplarıyla güvenli biçimde girebilmeli. Uygulama her
kullanıcının kim olduğunu ve hangi rollere sahip olduğunu (Çalışan, Yönetici, İK) bilmeli. İzin
talebi, onay ve bakiye gibi bütün sonraki özelliklerin yetki kuralları buna dayanacak.

Başarı:
- İK bir çalışanı kaydeder, ona hesap açar ve geçici parola verir.
- Çalışan ilk girişte parolasını değiştirir; ardından adını, rollerini ve yöneticiyse doğrudan
  bağlı çalışanlarını görür.
- Giriş yapmamış biri hiçbir veriye erişemez.

Bilinçli olarak yapılmayanlar: izin talebi, bakiye ve hak ediş, uygulama içi İK ekranları,
e-postayla parola sıfırlama, AD/Entra ID entegrasyonu.

Netleştirme kararları (2026-10-20):
- Hesap ve çalışan kayıtlarını İK, yalnızca İK'ya açık yönetim panelinden oluşturur.
- Giriş kimliği kullanıcı adıdır.
- İK geçici parola verir; ilk girişte parola değişimi zorunludur; e-postayla sıfırlama yoktur.
- Aynı kullanıcı adına 5 hatalı denemede 15 dakika kilit; 30 dakika işlem yapılmazsa oturum
  kapanır; "beni hatırla" yoktur.
- Yönetici rolü organizasyon ağacından türetilir; İK rolü açıkça atanır.
- Girişten sonra ad, roller ve (yöneticiyse) doğrudan bağlı çalışanlar görünür.
- Doğum tarihi bakiye spec'ine kalır (KVKK veri minimizasyonu).

## Requirements
1. **Çalışan kaydı:** İK, yönetim panelinden çalışan oluşturur ve düzenler. Alanlar: ad, soyad,
   işe giriş tarihi, yönetici (başka bir çalışan, isteğe bağlı), aktif/pasif.
2. **Organizasyon ağacı:** Bir çalışan kendi yöneticisi olamaz; yönetici zincirinde döngü
   oluşamaz (A → B → A). Geçersiz atama kaydedilmez ve İK'ya anlaşılır bir hata gösterilir.
3. **Hesap:** Her çalışanın en fazla bir hesabı vardır; her hesap tam olarak bir çalışana
   bağlıdır. İK hesabı oluştururken geçici parola belirler.
   Kullanıcı adı kuralları:
   - Benzersizdir ve büyük/küçük harf duyarsızdır (`HKacar` ile `hkacar` aynıdır).
   - Yalnızca İngilizce harf, rakam ve `.` `_` `-` içerir; Türkçe karakter içermez (İ/ı
     karışıklığını önler).
4. **Roller:**
   - Her aktif çalışan **Çalışan** rolündedir.
   - En az bir **aktif** doğrudan bağlı çalışanı olan kişi **Yönetici** rolündedir.
   - **İK** rolü, İK tarafından hesaba açıkça verilen bir yetkidir.
   - Bir kişi aynı anda birden çok role sahip olabilir.
5. **Yönetim paneli:** Yalnızca İK rolündeki kullanıcılar girebilir.
   - İlk İK hesabı sunucu üzerinde çalıştırılan bir komutla oluşturulur.
   - Son aktif İK hesabının İK yetkisi kaldırılamaz, hesap ya da çalışan kaydı pasif yapılamaz.
6. **Giriş:** Kullanıcı adı ve parola ile yapılır. Hatalı kullanıcı adı, hatalı parola ve pasif
   hesap aynı genel mesajı alır; hangi bilginin yanlış olduğu ve hesabın var olup olmadığı belli
   edilmez.
7. **Kilit:** Aynı kullanıcı adıyla son 15 dakika içinde 5 hatalı denemeden sonra o kullanıcı adı
   15 dakika kilitlenir. Başarılı bir giriş hatalı deneme sayacını sıfırlar.
   Kilit, var olmayan kullanıcı adları için de aynı şekilde işler (varlık sızmaz). Kilitliyken
   doğru parola da reddedilir.
8. **Zorunlu parola değişimi:** Geçici parolayla giren kullanıcı, yeni parola belirleyene kadar
   başka hiçbir sayfaya veya veriye erişemez. Yeni parola `docs/security.md` kurallarına uyar (en
   az 12 karakter, parola doğrulayıcıları) ve geçici parolayla aynı olamaz. İK bir hesabın
   parolasını yeniden geçiciye çekebilir; bu durumda kural yeniden işler.
9. **Oturum:** 30 dakika işlem yapılmazsa oturum kapanır; sonraki işlemde kullanıcı giriş
   ekranına yönlenir ve süresinin dolduğu söylenir. Kullanıcı istediği zaman çıkış yapabilir.
   Hesabı veya çalışan kaydı pasif yapılan kullanıcının açık oturumu bir sonraki isteğinde sona
   erer.
10. **Ana sayfa:** Giriş yapan kullanıcı adını, soyadını ve rollerini görür. Yöneticiyse
    **yalnızca kendi doğrudan bağlı aktif** çalışanlarının listesini (ad, soyad) görür. Liste
    soyad, sonra ad olarak Türkçe alfabetik sıralıdır.
11. **Erişim:** Giriş yapmamış kullanıcı uygulamanın hiçbir sayfasına ve verisine erişemez;
    giriş ekranına yönlenir. Sunucu durum sorgusu (spec 0001) herkese açık kalır.
12. **Korunan davranış (spec 0001):** Giriş ekranı ürün adını tek birincil başlık olarak ve sunucu
    bağlantı durumunu (kontrol ediliyor / Bağlı / ulaşılamıyor) göstermeye devam eder.

## User experience
- **Flow:**
  1. Kullanıcı uygulamayı açar → giriş ekranı (ürün adı, sunucu durumu, kullanıcı adı ve parola
     alanları, "Giriş yap" düğmesi).
  2. Doğru bilgiler + geçici parola → "Parolanızı değiştirin" ekranı → yeni parola iki kez →
     ana sayfa.
  3. Doğru bilgiler + kalıcı parola → ana sayfa: "Hoş geldiniz, Ad Soyad", roller, (yöneticiyse)
     "Ekibim" listesi, "Çıkış yap".
  4. "Çıkış yap" → giriş ekranı, "Çıkış yapıldı." mesajı.
- **States:**
  - Giriş ekranı:
    - Boş form.
    - Gönderiliyor: düğme devre dışı, "Giriş yapılıyor…".
    - Hata: "Kullanıcı adı veya parola hatalı."
    - Kilitli: "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin."
    - Oturum süresi doldu: "Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın."
    - Çıkış yapıldı: "Çıkış yapıldı."
    - Sunucuya ulaşılamıyor: spec 0001'deki durum mesajı; giriş denemesi yapılırsa
      "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin."
  - Parola değiştirme ekranı:
    - Boş form, gönderiliyor.
    - Doğrulama hataları alan bazında (çok kısa, çok yaygın, yalnız rakam, geçici parolayla aynı,
      iki alan eşleşmiyor).
    - Başarı → ana sayfa.
  - Ana sayfa:
    - Yükleniyor.
    - Başarı.
    - Hata: "Bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin."
    - Yönetici değil: "Ekibim" bölümü hiç gösterilmez.
    - Boş durum yoktur: Yönetici rolü aktif bağlı çalışan olmasından türer.
  - Yetkisiz: giriş yapmamış kullanıcı → giriş ekranı; İK olmayan kullanıcı yönetim paneline
    giremez.
- **Design reference:** none — the flow above is the design.
- **Accessibility:**
  - Her alanın görünür bir etiketi vardır.
  - Hata mesajları ilgili alana bağlıdır ve ekran okuyucuya duyurulur.
  - Gönderimden sonra odak ilk hataya taşınır.
  - Tüm akış yalnız klavyeyle tamamlanabilir.
  - Her ekran durumunda WCAG 2.1 AA.

## Constraints & out of scope
- Spec 0001'in bütün kabul kriterleri geçerli kalır; giriş ekranı onun başlangıç sayfasının yerini
  alır.
- `docs/security.md`: Argon2, en az 12 karakter, oturum çerezi + CSRF, varsayılan reddet, nesne
  düzeyinde yetki yalnızca sunucuda, başkasının kaydı → 404, loglarda kişisel veri yerine UUID.
- Yönetim paneli ve uygulama aynı origin'den sunulur.
- **Out of scope:**
  - Uygulama içi İK ekranları (çalışan ekleme/düzenleme).
  - E-postayla parola sıfırlama; AD/Entra ID; çok adımlı doğrulama (MFA).
  - Kalıcı parolası olan kullanıcının parolasını kendisinin değiştirmesi (unutulan parola İK
    üzerinden geçiciye çekilir).
  - Doğum tarihi, izin, bakiye, hak ediş.
  - Giriş olaylarının audit kaydı (yalnız sunucu logu).
  - Toplu çalışan içe aktarma.

## Acceptance criteria
- [ ] AC-1 — İK yönetim panelinden ad, soyad, işe giriş tarihi, yönetici ve aktif/pasif bilgisiyle çalışan oluşturabilir ve düzenleyebilir.
- [ ] AC-2 — Bir çalışanı kendi yöneticisi yapmak veya yönetici zincirinde döngü oluşturmak (A → B → A, A → B → C → A) kaydedilmez ve İK'ya hata gösterilir.
- [ ] AC-3 — İK bir çalışana kullanıcı adı ve geçici parolayla hesap açabilir; aynı kullanıcı adıyla ikinci hesap ve aynı çalışana ikinci hesap kaydedilmez.
- [ ] AC-4 — Rol türetme: aktif her çalışan Çalışan; en az bir aktif doğrudan bağlısı olan Yönetici; bağlılarının hepsi pasif olan Yönetici değil; İK yetkisi verilen İK. Roller birlikte bulunabilir.
- [ ] AC-5 — İK rolü olmayan giriş yapmış bir kullanıcı ve giriş yapmamış bir kullanıcı yönetim paneline erişemez.
- [ ] AC-6 — Doğru kullanıcı adı ve kalıcı parolayla giriş başarılı olur ve kullanıcı ana sayfaya ulaşır.
- [ ] AC-7 — Hatalı parola, var olmayan kullanıcı adı ve pasif hesap aynı yanıtı ve aynı "Kullanıcı adı veya parola hatalı." mesajını alır.
- [ ] AC-8 — Aynı kullanıcı adıyla 5. hatalı denemeden sonra o kullanıcı adı 15 dakika kilitlenir: kilitliyken doğru parola da reddedilir ve "Çok fazla hatalı deneme…" mesajı gösterilir; 15 dakika dolunca doğru parolayla giriş yapılabilir; 4 hatalı deneme kilitlemez.
- [ ] AC-9 — Var olmayan bir kullanıcı adı da 5 hatalı denemeden sonra aynı kilit mesajını alır.
- [ ] AC-10 — Geçici parolayla giren kullanıcı yeni parola belirleyene kadar parola değiştirme dışındaki her sayfa ve API ucunda reddedilir veya parola değiştirme ekranına yönlenir.
- [ ] AC-11 — Yeni parola 12 karakterden kısa, çok yaygın, yalnız rakam, geçici parolayla aynı veya iki alan eşleşmiyorsa kaydedilmez ve alan bazında hata gösterilir; geçerli parolayla değişim sonrası kullanıcı ana sayfaya ulaşır ve sonraki girişte yeni parola çalışır.
- [ ] AC-12 — İK bir hesabın parolasını yeniden geçiciye çektiğinde kullanıcı sonraki girişte yine parola değiştirmeye zorlanır.
- [ ] AC-13 — 30 dakika işlem yapılmayan oturum kapanır; sonraki istek reddedilir ve kullanıcı "Oturumunuzun süresi doldu…" mesajıyla giriş ekranına yönlenir. 30 dakikadan kısa aralıklarla işlem yapan kullanıcının oturumu açık kalır.
- [ ] AC-14 — "Çıkış yap" oturumu sonlandırır; çıkış sonrası korunan bir sayfa veya API ucu reddedilir ve giriş ekranında "Çıkış yapıldı." gösterilir.
- [ ] AC-15 — Ana sayfa giriş yapan kullanıcının adını, soyadını ve rollerini gösterir.
- [ ] AC-16 — Yönetici ana sayfada yalnızca kendi doğrudan bağlı **aktif** çalışanlarını görür (dolaylı bağlılar ve pasifler görünmez), liste soyad, sonra ad olarak Türkçe alfabetik sıralıdır (ör. Çelik, Demir, Şahin, Yılmaz); yönetici olmayan kullanıcıda "Ekibim" bölümü yoktur.
- [ ] AC-17 — Bir kullanıcı API üzerinden başka bir çalışanın bilgisini veya başka bir yöneticinin ekibini isteyemez; böyle bir istek 404 alır.
- [ ] AC-18 — Giriş yapmamış kullanıcı ana sayfaya veya herhangi bir korunan API ucuna eriştiğinde reddedilir ve giriş ekranına yönlenir; sunucu durum sorgusu herkese açık kalır.
- [ ] AC-19 — Giriş ve parola değiştirme istekleri CSRF koruması olmadan reddedilir; oturum çerezi `HttpOnly` ve `SameSite=Lax`'tır (üretim ayarlarında `Secure`).
- [ ] AC-20 — Parolalar Argon2 ile saklanır; hiçbir yanıt veya log satırı parola, geçici parola ya da oturum anahtarı içermez.
- [ ] AC-21 — Giriş ekranı ürün adını tek birincil başlık olarak ve sunucu bağlantı durumunu spec 0001'deki üç durumla göstermeye devam eder (spec 0001 AC-1…AC-4, AC-19, AC-20 geçerli).
- [ ] AC-22 — Giriş, parola değiştirme ve ana sayfa ekranlarının listelenen her durumunda otomatik erişilebilirlik taraması WCAG 2.1 AA ihlali bulmaz; her alanın görünür etiketi vardır, hata mesajları alana bağlıdır ve gönderimden sonra odak ilk hataya taşınır.
- [ ] AC-23 — Giriş → zorunlu parola değişimi → ana sayfa → çıkış akışı yalnız klavyeyle tamamlanabilir.
- [ ] AC-24 — Sunucu üzerinde çalıştırılan komut, çalışan kaydıyla birlikte ilk İK hesabını oluşturur; oluşan hesap ilk girişte parola değiştirmeye zorlanır.
- [ ] AC-25 — Son aktif İK hesabının İK yetkisini kaldırmak, hesabını veya çalışan kaydını pasif yapmak kaydedilmez ve hata gösterilir; ikinci bir aktif İK varken bu işlemler yapılabilir.
- [ ] AC-26 — Kullanıcı adı büyük/küçük harf duyarsızdır: `HKacar` ile girişte `hkacar` hesabı kullanılır, `HKacar` adıyla ikinci hesap kaydedilmez; Türkçe karakter, boşluk veya `. _ -` dışı işaret içeren kullanıcı adı kaydedilmez.
- [ ] AC-27 — Kilit sayacı yalnızca son 15 dakikadaki hatalı denemeleri sayar (15 dakikadan eski denemeler sayılmaz) ve başarılı bir giriş sayacı sıfırlar (4 hata + başarılı giriş + 4 hata kilitlemez).
- [ ] AC-28 — Hesabı veya çalışan kaydı pasif yapılan kullanıcının açık oturumu bir sonraki isteğinde reddedilir ve kullanıcı giriş ekranına yönlenir.

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale
- [ ] Docs / ADRs updated if behavior or architecture changed
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise | |
| Regressions introduced | |
| Bugs escaped to production | |
