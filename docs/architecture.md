# Architecture

> Bootstrap'ta karar verilen mimari (2026-10-19). Ajanlar planlamadan önce bu dosyayı okur.

## System overview
Polsan Leave Manager, Polsan çalışanlarının yıllık izin talebi oluşturduğu, yöneticilerin
onayladığı/reddettiği ve izin bakiyelerinin yasal kurallara göre takip edildiği **iç web
uygulamasıdır**. Şirket içi sunucuda (on-prem) çalışır; arayüz Türkçedir.
Stil: **modüler monolit** — tek deploy, tek PostgreSQL veritabanı; modüller yalnızca public
arayüzleri üzerinden konuşur ve sınırlar araçla (import-linter) zorlanır.
Backend: Django + Django REST Framework (Web API, OpenAPI şeması drf-spectacular ile).
Frontend: React + TypeScript + Vite SPA, aynı origin'den sunulur.
Gerekçe: [ADR 0001](decisions/0001-modular-monolith-django-react.md).

Repo düzeni (monorepo):
- `backend/` — Django projesi; her modül bir Django app (`backend/<modül>/`).
  `backend/config/` composition root'tur: settings, URL'ler, herkese açık durum ucu
  (`config/health.py`), hata biçimi (`config/exceptions.py`) ve yalnız İK'ya açık yönetim
  paneli (`config/admin.py`). Modülleri bir araya getirir; iki modülü birden gerektiren kurallar
  (ör. "son aktif İK pasif yapılamaz") yalnızca modüllerin `api.py`'si çağrılarak burada
  birleştirilir.
- `backend/tests/` — modüllere ait olmayan testler (mimari, ayarlar) ve ortak test fabrikaları
  (`tests/factories.py`); kural 1'e tabi değildir.
- `frontend/` — React SPA; backend'e yalnızca OpenAPI'den üretilen tipli istemciyle erişir.
- `frontend/e2e/` — Playwright uçtan uca testleri (`docs/testing.md`).
- `docker-compose.yml` — yalnızca yerel geliştirme veritabanı (testler kullanmaz).

Her backend modülünün iç düzeni:
- `api.py` — modülün **tek public arayüzü** (diğer modüller yalnızca bunu import eder).
- `domain/` — saf Python iş kuralları (Django import etmez).
- `models.py`, `services.py`, `views.py`, `serializers.py` — modül içi; dışarıya kapalı.

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `employees` (Personel) | Çalışan kaydı, işe giriş tarihi, doğum tarihi, yönetici hiyerarşisi | Çalışan, organizasyon ağacı |
| `workcalendar` (Takvim) | Çalışma günleri ayarı, resmi tatil takvimi, iş günü hesabı | Tatil takvimi, çalışma haftası ayarı |
| `balances` (Bakiye) | Hak ediş (kıdem/yaşa göre), devir, İK düzeltmeleri, bakiye sorgusu | Bakiye defteri (append-only hareketler) |
| `leaves` (İzinler) | İzin talebi yaşam döngüsü: oluştur, onayla, reddet, iptal | İzin talepleri, izin türleri |
| `identity` (Kimlik) | Giriş/çıkış, oturum, rol çözümleme (Çalışan / Yönetici / İK) | Kullanıcı hesabı, kullanıcı–rol eşlemesi |
| `audit` (altyapı) | Onay/ret/iptal/düzeltme olaylarının değiştirilemez kaydı | Audit kayıtları |

`workcalendar` adı, Python standart kütüphanesindeki `calendar` ile çakışmamak için seçildi.

## Communication rules
- Modüller arası çağrılar **senkron, süreç içi** fonksiyon çağrılarıdır ve yalnızca hedef modülün
  `api.py`'si üzerinden yapılır.
- İzin verilen bağımlılık yönü (döngü yasak):
  `leaves → balances, workcalendar, employees` · `balances → workcalendar, employees` ·
  `identity → employees` · `workcalendar`, `employees` → hiçbir modül.
  Her modül `audit`'i çağırabilir; `audit` hiçbir modülü çağırmaz.
- Bir iş akışı birden çok modülü değiştiriyorsa (örn. onay → bakiyeden düşüm) akışın sahibi modül
  (`leaves`) tek bir veritabanı transaction'ı içinde açık çağrılarla yürütür.
- Message broker / kuyruk / arka plan işçisi v1'de yoktur.
- Frontend ↔ backend: yalnızca REST/JSON API (`/api/...`), OpenAPI şemasından üretilen istemciyle.

## Forbidden dependencies (make them testable)
Her madde bir import-linter sözleşmesi, ESLint kuralı veya mimari test olarak `scripts/check`
içinde çalışır: 1, 4, 5 → `backend/tests/architecture/` (pytest); 2, 3 → import-linter
(`backend/pyproject.toml`); 6 → ESLint + `scripts/api-contract`.
1. Bir modül, başka bir modülün `api.py` dışındaki hiçbir alt modülünü (`models`, `services`,
   `domain`, `views`…) import etmez.
2. Yukarıdaki bağımlılık yönü dışındaki modül→modül importları yasaktır; döngüler yasaktır.
3. `*/domain/` paketleri `django`, `rest_framework` ve diğer modülleri import etmez.
4. Modüller arası `ForeignKey` yalnızca `employees.Employee`'ye verilebilir; diğer tüm modüller
   arası referanslar düz kimlik (UUID) ile tutulur (mimari test).
5. İş mantığında Django signals kullanılmaz (`post_save` vb. receiver yasak); altyapı istisnası
   gerekirse ADR ile açılır.
6. Frontend iş kuralı hesaplamaz (iş günü sayısı, bakiye, hak ediş) — sunucunun döndürdüğünü
   gösterir. Frontend `fetch`/`axios`'u doğrudan çağırmaz; yalnızca üretilmiş API istemcisini
   kullanır (ESLint `no-restricted-imports` / `no-restricted-globals`).

## Deliberately out of scope
v1 için bilinçli kapsam dışı:
- Yıllık izin dışındaki izin türlerinin işletilmesi (model türleri destekler, yalnızca Yıllık aktif).
- Saatlik izin; çalışan bazlı çalışma takvimi / vardiya planlama.
- Bordro, ERP, AD/Entra ID entegrasyonu (kimlik doğrulama arka ucu değiştirilebilir kurulur).
- Mobil uygulama; çoklu şirket / çoklu kiracı.
- Avans (negatif bakiye) izin; çok aşamalı onay.
- Sağlık raporu vb. özel nitelikli kişisel veri.
