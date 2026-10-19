# Conventions

> Yalnızca gerçek kurallar: her kural ya araçla zorlanır (tercih edilen) ya da review'da kontrol
> edilir. Temenniler buraya girmez.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): Turkish (`tr`)
- Document language (docs/, specs, plans, ADRs, review and verify reports): Turkish (`tr`)
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: English. Domain terimlerinin İngilizce
  karşılıkları `docs/domain.md` sözlüğündedir; sözlükte olmayan bir terim için önce sözlüğe ekleme
  yapılır. Kullanıcıya görünen arayüz metinleri ve API hata mesajları (`detail`) Türkçedir.
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
- Backend: Python **3.12** · Django **5.2 LTS** · Django REST Framework **3.16** ·
  drf-spectacular · PostgreSQL **17** · bağımlılık yönetimi **uv** (`backend/pyproject.toml` +
  `backend/uv.lock`, lock dosyası commit'lenir).
- Frontend: Node **24 LTS** · npm (`frontend/package-lock.json` commit'lenir) · React **19** ·
  TypeScript **5** (`strict: true`) · Vite · ESLint **9** (`eslint-plugin-react` henüz ESLint
  10'u desteklemiyor).
- API istemcisi: backend şeması `drf-spectacular` ile `frontend/src/api/openapi.yaml`'a, oradan
  `openapi-typescript` ile `schema.d.ts`'e üretilir; istek atan tek nokta `openapi-fetch`
  istemcisidir (`src/api/client.ts`). API değiştiğinde `npm run api:generate`; üretilmiş dosyalar
  elle düzenlenmez ve `scripts/api-contract` ile check'te doğrulanır.
- Test: pytest + pytest-django · Testcontainers (PostgreSQL) · Vitest + React Testing Library ·
  Playwright.
- Sürüm yükseltmeleri (major) bir spec veya ADR ile yapılır.

## Naming
- Backend modülleri (Django app): `employees`, `workcalendar`, `balances`, `leaves`, `identity`,
  `audit` — çoğul, küçük harf, İngilizce.
- Python: modül/fonksiyon `snake_case`, sınıf `PascalCase`, sabit `UPPER_SNAKE` (ruff zorlar).
- TypeScript: bileşen `PascalCase.tsx`, hook `useXxx.ts`, diğer dosyalar `camelCase.ts`.
- API: `/api/<kaynak-çoğul>/` (kebab-case), JSON alanları `snake_case`.
- API uçları yalnızca **class-based** DRF view'larıdır (`APIView` / generic view / ViewSet) ve
  `permission_classes`'ı açıkça bildirir; `@api_view` fonksiyon view'ları kullanılmaz (uç izin
  mimari testi onları reddeder — `backend/tests/architecture/checks.py`).
- Testler: Python `test_<davranış>.py` / `test_<davranış>()`; frontend `<Bileşen>.test.tsx`;
  e2e `frontend/e2e/<akış>.spec.ts`. Test adı davranışı söyler, BR numarası varsa içerir
  (`test_br6_request_exceeding_available_balance_is_rejected`).
- Branch ve commit: `docs/git.md`.

## Error handling
- Domain katmanı iş kuralı ihlalinde tipli bir `DomainError` alt sınıfı fırlatır; her hatanın sabit
  bir makine kodu vardır (örn. `insufficient_balance`, `overlapping_request`, `self_approval`).
- API katmanı tek bir exception handler ile bunları **RFC 9457 `application/problem+json`**
  yanıtına çevirir: `type`, `title`, `status`, `code` (makine kodu), `detail` (Türkçe kullanıcı
  mesajı). Doğrulama hataları alan bazında `errors` listesi ile döner.
- Stack trace, SQL, dosya yolu, iç kimlik veya başka kullanıcının verisi **asla** yanıta sızmaz.
  Beklenmeyen hata → 500 + genel mesaj; ayrıntı sunucu loguna (kişisel veri yerine ID ile).
- `except Exception: pass` ve hatayı yutan geniş `except` yasaktır (ruff `BLE`, `S110`).
- Frontend tüm API hatalarını tek bir yoldan gösterir (`detail` metni); makine kodu üzerinden dallanır,
  metin üzerinden asla.

## Data rules
- İzin gün miktarları `Decimal` — `DecimalField(max_digits=5, decimal_places=1)`, 0,5'in katı
  olduğu doğrulanır. `float` gün/bakiye hesabında **yasak**. API'de string olarak taşınır (`"1.5"`).
- İzin tarihleri saat dilimi olmayan takvim tarihi (`date`, ISO `YYYY-MM-DD`).
- Zaman damgaları `USE_TZ = True`, DB'de **UTC**; arayüzde **Europe/Istanbul** ile gösterilir.
- Dışa açılan kimlikler **UUID**; sıralı/tamsayı ID API'de yer almaz.
- Bakiye defteri append-only: güncelleme/silme yok, düzeltme yeni hareketle (`docs/domain.md`).
- Para birimi yoktur (v1 izin ücreti hesaplamaz).

## Enforced by tooling
Hepsi `scripts/check` içinde çalışır (`scripts/check.conf`):
- **ruff** — lint + format (`ruff check`, `ruff format --check`); kurallar `backend/pyproject.toml`.
- **mypy** — `backend/*/domain/` için `strict`, geri kalan için standart.
- **import-linter** — `docs/architecture.md` "Forbidden dependencies" 1–3.
- **Mimari testler (pytest)** — modüller arası FK kuralı (4) ve signals yasağı (5).
- **ESLint + Prettier** — frontend lint/format; `react/no-danger`, ham `fetch`/`axios` yasağı.
- **tsc --noEmit** — TypeScript `strict` tip kontrolü.
