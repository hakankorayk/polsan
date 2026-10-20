# ADR 0003 — Özel kullanıcı modeli ve kendi giriş kilidi uygulamamız

- Status: Accepted
- Date: 2026-10-20

## Context
Spec 0002 giriş ve rolleri getiriyor. Gereksinimler:
- Kullanıcı adı büyük/küçük harf duyarsız olmalı ve yalnızca ASCII karakter içermeli.
- Her hesap tam olarak bir çalışana bağlı olmalı.
- İK yetkisi ve "ilk girişte parola değiştir" bayrağı hesapta tutulmalı.
- Aynı kullanıcı adına son 15 dakikada 5 hatalı denemede 15 dakika kilit olmalı. Var olmayan
  kullanıcı adları da aynı işlenmeli ve başarılı giriş sayacı sıfırlamalı.

Django'nun varsayılan `auth.User`'ı bu alanları temiz taşımıyor. Kullanıcı modelini sonradan
değiştirmek ise Django'da çok zahmetli: migration geçmişi ve yabancı anahtarların hepsi etkilenir.
Üretimde henüz veri yok.

## Decision
1. Proje başından **özel kullanıcı modeli** kullanıyoruz: `identity.User`
   (`AUTH_USER_MODEL`). Normalize edilmiş kullanıcı adı, `is_hr`, `must_change_password` ve
   `employee` (OneToOne → `employees.Employee`) alanlarını içerir.
2. Giriş kilidini **kendimiz uyguluyoruz**:
   - Saf bir domain durum makinesi (`identity/domain/throttle.py`, saati dışarıdan alır).
   - Kullanıcı adı başına bir `LoginThrottle` kaydı.
   - `django-axes` gibi bir paket kullanmıyoruz.

## Consequences
- **Kazanç:**
  - Kurallar spec'le birebir aynı ve sahte saatle milisaniyede test ediliyor.
  - Yeni bağımlılık ya da ara katman (middleware) yok.
  - Kullanıcı adı kuralları tek yerde.
  - İleride AD/Entra ID'ye geçişte kimlik doğrulama arka ucu değiştirilebilir; model aynı kalır.
- **Maliyet:**
  - Kilit kodu (~60 satır) ve bakımı bizde. IP bazlı sınırlama veya kilit bildirimleri gibi
    hazır özellikler yok; gerekirse ayrı bir spec ile eklenir.
  - Özel kullanıcı modeli, üçüncü parti paketlerin `get_user_model()` kullanmasını gerektirir;
    bu zaten Django'nun önerdiği kalıp.
  - Var olmayan kullanıcı adları da kilit kaydı açar; bu kayıtlar hiç başarılı girişle
    silinmez. Bu yüzden her hatalı denemede süresi dolmuş kayıtlar (pencere ve kilit dışında
    kalanlar) silinir ve başarılı giriş kayıt açmaz (review M4). Tablo büyüklüğü son
    ~15 dakikadaki farklı kullanıcı adı sayısıyla sınırlıdır.

## Alternatives considered
- **Varsayılan `auth.User` + profil modeli:** Kullanıcı adı normalizasyonu ve büyük/küçük harf
  duyarsız benzersizlik için ek kısıtlar gerekir. Alanlar iki tabloya dağılır. Sonradan özel
  modele geçmek pahalı.
- **`django-axes`:** Olgun bir paket. Ancak varsayılanı IP + kullanıcı adı birleşimine göre
  sayıyor ve kendi middleware'i ile tablolarını getiriyor. Spec'teki "var olmayan kullanıcı adı da
  aynı" ve "başarılı giriş sıfırlar" kurallarını ayarlarla birebir tutturmak, kendi kodumuzdan
  daha fazla yapılandırma ve doğrulama gerektiriyor.

## Revisit triggers
- IP bazlı sınırlama, dağıtık (çok sunuculu) kilit veya kilit bildirimi gerekirse.
- AD/Entra ID entegrasyonu kimlik modelinde değişiklik isterse.
