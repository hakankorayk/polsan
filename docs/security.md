# Security

> Ajanların her plan ve review'da uyduğu temel kurallar.

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- Django `SECRET_KEY`, veritabanı parolası ve benzerleri yalnızca ortam değişkeninden okunur;
  kodda varsayılan değer yoktur (yalnızca test ayarlarında sabit bir test anahtarı olabilir).
- Üretimde `DEBUG = False`; `ALLOWED_HOSTS` açıkça listelenir.

## Input & output
- Tüm girdi sunucuda, DRF serializer'larında doğrulanır; frontend doğrulaması yalnızca kullanıcı
  kolaylığıdır, güvenlik sınırı değildir.
- ORM dışında ham SQL yalnızca parametreli sorguyla ve gerekçesi review'da belirtilerek yazılır.
- React çıktıyı varsayılan olarak escape eder; `dangerouslySetInnerHTML` yasaktır (ESLint
  `react/no-danger`).
- Hata yanıtları `docs/conventions.md` "Error handling"e uyar: stack trace, SQL, iç kimlik veya
  başka kullanıcının verisi asla sızmaz.
- **KVKK:** izin verisi kişisel veridir. v1'de sağlık bilgisi/rapor gibi özel nitelikli kişisel veri
  saklanmaz. Loglara kişisel veri (ad, e-posta, izin gerekçesi) değil, yalnızca UUID yazılır.
- Güvenlik başlıkları: `SECURE_*` ayarları, `X-Frame-Options: DENY`, katı Content-Security-Policy.

## AuthN / AuthZ
- **Kimlik doğrulama:** yerel Django hesapları ([ADR 0002](decisions/0002-local-django-accounts.md)).
  - Parola hash: **Argon2**; en az **12 karakter**; Django parola doğrulayıcıları açık.
  - Başarısız giriş denemeleri sınırlandırılır (hesap/IP kilitleme); uygulama aracı ilk kimlik
    spec'inde plan onayıyla seçilir.
  - İşten ayrılan çalışanın hesabını İK **pasifleştirir** (`is_active = False`); hesap silinmez,
    audit izi korunur.
  - `identity` modülü kimlik doğrulama arka ucunu değiştirilebilir tutar (ileride AD/Entra ID).
- **Oturum:** SPA aynı origin'den sunulur; Django session cookie (`HttpOnly`, `Secure`,
  `SameSite=Lax`) + **CSRF** token. JWT ve localStorage'da token yoktur.
- **Yetkilendirme — varsayılan reddet:** DRF `DEFAULT_PERMISSION_CLASSES` = kimliği doğrulanmış +
  açık izin; her uç kendi rol/nesne kontrolünü bildirir. Yetkisiz uç bir mimari testle yakalanır.
- **Nesne düzeyinde yetki (yalnızca sunucuda):**
  - Çalışan → yalnızca kendi talepleri, bakiyesi ve geçmişi.
  - Yönetici → kendisi + **doğrudan** bağlı çalışanlarının talepleri; yalnızca onları onaylar/reddeder.
  - İK → tüm kayıtları görür; bakiye düzeltme ve tatil takvimi yalnızca İK.
  - Kimse kendi talebini onaylayamaz (BR-8).
  - Erişim yetkisi olmayan kayıt için yanıt **404** (varlığı sızdırılmaz).
- Frontend'de gizlenen buton güvenlik kontrolü sayılmaz.

## Dependencies
- Yeni bir paket (Python veya npm) **planda gerekçesiyle önerilir, insan onaylar**: lisans
  (MIT/BSD/Apache-2.0 tercih; GPL/AGPL onaysız eklenmez), bakım durumu (son 12 ayda sürüm) ve
  bilinen CVE kontrolü.
- Lock dosyaları (`uv.lock`, `package-lock.json`) her zaman commit'lenir; `scripts/check` bunlarla
  (`--frozen`, `npm ci`) çalışır.
- `pip-audit` ve `npm audit --audit-level=high` CI'da **ayrı bir job** olarak çalışır; ağ bağımlı
  olduğu için `scripts/check`'e girmez. Eşikler: **Python — bilinen her açık** kırmızıdır
  (`pip-audit`'in önem filtresi yoktur); **npm — high ve üstü** kırmızıdır. Kırmızı audit bir
  bug raporu açar (ya da açığı kapatan yükseltme o anki işe plan onayıyla eklenir).

## Audit
- Onay, ret, iptal ve İK bakiye düzeltmeleri `audit` modülüne yazılır: kim (UUID), ne zaman (UTC),
  ne yaptı, hangi kayıt, gerekçe. Audit kayıtları değiştirilmez ve silinmez.

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.
