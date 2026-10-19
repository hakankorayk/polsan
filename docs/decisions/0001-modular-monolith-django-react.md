# ADR 0001 — Modüler monolit: Django + DRF backend, React SPA, PostgreSQL

- Status: Accepted
- Date: 2026-10-19

## Context
Polsan Leave Manager, şirket içi sunucuda çalışacak bir iç izin yönetim uygulamasıdır. Kullanıcı
sayısı şirket çalışanlarıyla sınırlıdır; iş kuralları (İş Kanunu hak edişi, iş günü hesabı, onay
akışı) hassastır ve test edilebilir olmalıdır. Ekip küçüktür (lite mod). Geliştirme makinesinde
.NET 10, Node 24, Python 3.12 ve Docker kuruludur.

## Decision
Uygulamayı **modüler monolit** olarak kuruyoruz: Python/Django + Django REST Framework (OpenAPI:
drf-spectacular) backend, React + TypeScript + Vite SPA frontend, PostgreSQL veritabanı, tek
monorepo (`backend/`, `frontend/`). Modül sınırları import-linter ile zorlanır.

## Consequences
- Kazanç: tek deploy ve tek veritabanı — on-prem operasyonu basit; modüller arası işlemler tek
  transaction'da. Django admin ve ORM İK ekranlarını hızlandırır. Saf `domain/` katmanı kuralları
  DB'siz test ettirir. OpenAPI'den üretilen tipli istemci API kırılmalarını derlemede yakalar.
- Maliyet: iki ayrı toolchain (uv + npm) ve iki test zinciri; SPA, sunucu taraflı şablonlara göre
  daha fazla kod. Testcontainers nedeniyle entegrasyon testleri Docker gerektirir. Modül sınırları
  disiplin ister — araçla zorlanmazsa monolit zamanla erir.

## Alternatives considered
- **.NET 10 / ASP.NET Core + Razor Pages + SQL Server** (bootstrap'ta önerilen): Windows/AD
  entegrasyonu daha doğal; ekip tercihi Python ekosistemi yönünde olduğu için seçilmedi.
- **Node.js/TypeScript backend:** tek dil avantajı; Django'nun admin/ORM/olgun yetki modeli tercih edildi.
- **Klasik katmanlı monolit:** modül sınırı olmadığı için büyüdükçe bağımlılıklar karışır.
- **Mikroservis:** bu ölçek için operasyon yükü gerekçesiz.
- **SQL Server / SQLite:** PostgreSQL ücretsiz ve Django ile en iyi desteklenen motor; SQLite çok
  kullanıcılı üretim için zayıf.

## Revisit triggers
- Bir modülün bağımsız ölçeklenmesi veya ayrı ekip tarafından deploy edilmesi gerekirse.
- Kurumsal kimlik (AD/Entra ID) entegrasyonu Django tarafında ciddi engel çıkarırsa.
- Şirket BT politikası PostgreSQL yerine başka bir veritabanını zorunlu kılarsa.
