# ADR 0004 — Hak edişler okuma anında, idempotent olarak deftere yazılır

- Status: Accepted
- Date: 2026-10-21

## Context
Spec 0003, kıdem yıldönümündeki yıllık izin hakkının "yıldönümü günü, kimsenin bir işlem
yapmasına gerek kalmadan" bakiyede görünmesini istiyor. Öte yandan:
- v1'de arka plan işçisi, kuyruk ya da zamanlanmış görev yok (`docs/architecture.md`).
- Bakiye her zaman defter hareketlerinin toplamı olmalı; başka bir bakiye alanı tutulmaz
  (`docs/domain.md` invariant).

Kurulum on-prem; cron gibi işletim tarafı bir bağımlılık eklemek, ANEW'in kapsamı dışında kalan
ve doğrulanamayan bir adım olur (ANEW-0005).

## Decision
Bir çalışanın bakiyesi her okunmadan önce (çalışan ekranı, İK paneli, ileride izin talebi),
o güne kadar oluşması gereken ama defterde olmayan hak ediş hareketleri yazılır.

Bu yazım **idempotenttir**:
- `(çalışan, kıdem yılı)` hak ediş hareketleri için veritabanında benzersizdir.
- Ekleme çakışmada sessizce atlanır; eşzamanlı okumalar ikinci hareket üretemez.

Sistem okuma anında çalışanın geçmişteki aktiflik durumunu bilemez. Bu yüzden İK paneli çalışan
kaydını değiştirmeden önce eski verilerle materialize eder. Değişiklik pasiften aktife dönüş veya
tarih değişikliği ise çalışana bir **hak ediş sınırı** (`AccrualFloor`) yazar; o tarihten önceki
yıldönümleri artık oluşmaz.

## Consequences
- **Kazanç:**
  - Yeni altyapı yok.
  - Defter gerçek hareketleri taşır: kim, hangi gün, ne kadar hak etti sorgulanabilir. İzin
    talebi ve onay akışları da aynı defteri okur.
  - Kurallar saf domain fonksiyonlarında ve sahte saatle test edilir.
- **Maliyet:**
  - GET istekleri yazma yapabilir. Bunun sonuçları:
    - Okuma ucunun bir transaction'ı ve veritabanı yazma yetkisi olmalı.
    - Salt okunur bir replika kullanılamaz.
  - Kimse bakiyeyi okumazsa hareket de yazılmaz. Hareketin `effective_date`'i yine yıldönümüdür;
    yazılma anı `created_at`'te görünür.
  - Pasiflik ve tarih değişikliklerinin doğru işlenmesi, değişikliklerin yönetim panelinden
    geçmesine bağlıdır. Panel dışı bir değiştirme yolu (toplu içe aktarma, kabuk) aynı çağrıları
    yapmak zorundadır.

## Alternatives considered
- **Cron ile günlük `manage.py` komutu:** Kurulumda işletim bağımlılığı ekler. Çalışmadığı gün
  sessizce hak ediş kaçırılır. Uygulamanın kendisi doğrulayamaz.
- **Defter yazmadan sanal hesap:** Bakiye = hareketler + "hesaplanmış hak edişler". Bu durumda
  defter tek doğruluk kaynağı olmaktan çıkar (invariant ihlali). Ayrıca tarih değişikliğinde
  geçmiş hak edişler sessizce yeniden hesaplanır (spec 0003, AC-15 ihlali).
- **Arka plan işçisi (Celery vb.):** v1 mimarisinde bilinçli olarak yok; yalnız bunun için
  broker eklemek orantısız.

## Revisit triggers
- Bir arka plan işçisi başka bir nedenle mimariye girerse.
- Okuma ucu yazma kilitleri yüzünden ölçülebilir gecikme gösterirse.
- Çalışan verisini panel dışından değiştiren bir yol (ör. AD/Entra ID senkronu) gelirse.
