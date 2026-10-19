# ADR 0002 — Kimlik doğrulama: yerel Django hesapları, oturum çerezi + CSRF

- Status: Accepted
- Date: 2026-10-19

## Context
Uygulamaya Çalışan, Yönetici ve İK rolleriyle giriş yapılacak. Şirketin kurumsal kimlik altyapısı
(on-prem AD veya Microsoft Entra ID) ile entegrasyon v1 kapsamında değil. SPA, Django ile aynı
origin'den sunulacak.

## Decision
v1'de **yerel Django hesapları** kullanıyoruz (Argon2, en az 12 karakter, başarısız girişte
kilitleme, ayrılan çalışan için pasifleştirme). Oturum **Django session cookie** (`HttpOnly`,
`Secure`, `SameSite=Lax`) + **CSRF** ile yönetilir. `identity` modülü kimlik doğrulama arka ucunu
değiştirilebilir tutar.

## Consequences
- Kazanç: dış sisteme bağımlılık yok, hızlı başlangıç; cookie tabanlı oturum token'ı JavaScript'e
  açmaz (XSS ile çalınamaz) ve JWT iptal/yenileme karmaşıklığı yoktur.
- Maliyet: çalışanlar ayrı bir parola yönetir; hesap açma/kapama İK'nın manuel işidir — işten
  ayrılan birinin hesabı unutulursa erişim sürer. Parola sıfırlama akışı uygulamada yazılmalıdır.

## Alternatives considered
- **On-prem AD (LDAP):** tek parola ve otomatik erişim kapatma; v1 için entegrasyon kapsam dışı tutuldu.
- **Entra ID (OIDC SSO):** MFA ve tek tıkla giriş; internet bağımlılığı ve M365 kullanımı teyit edilmedi.
- **JWT:** farklı origin'e izin verir ama token saklama/iptal riski taşır; aynı origin olduğu için gereksiz.

## Revisit triggers
- Kullanıcı sayısı İK'nın hesapları elle yönetemeyeceği düzeye çıkarsa.
- Bir denetim/KVKK değerlendirmesi merkezi kimlik veya MFA isterse.
- Şirket M365/Entra ID kullanımını teyit ederse.
