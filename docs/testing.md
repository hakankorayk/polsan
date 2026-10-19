# Testing

> Bootstrap'ta dolduruldu (2026-10-19). ANEW çekirdek kuralları (İngilizce bölümler) aynen geçerlidir.

## The contract
- Every acceptance criterion maps to at least one test (criterion ↔ test map lives in the plan).
- Tests assert **behavior**, not implementation details or mere status codes.
- The whole suite runs inside `scripts/check` — one command, everywhere.

## Frameworks & layout

| Katman | Araç | Yer | Profil |
|---|---|---|---|
| Domain unit (saf Python, DB yok) | pytest | `backend/<modül>/tests/unit/`; modüle ait olmayanlar `backend/tests/unit/` | fast |
| API / entegrasyon (gerçek PostgreSQL) | pytest + pytest-django + Testcontainers | `backend/<modül>/tests/integration/`; modüle ait olmayanlar `backend/tests/integration/` | full |
| Mimari (yalnız `api` erişimi, FK kuralı, signals yasağı, uç izin bildirimi) | pytest + grimp | `backend/tests/architecture/` | fast |
| API sözleşmesi (backend şeması = commit'li frontend istemcisi) | `scripts/api-contract` | — | fast |
| Modül sınırları | import-linter | `backend/pyproject.toml` `[tool.importlinter]` | fast |
| Frontend bileşen/unit | Vitest + React Testing Library (jsdom) | `frontend/src/**/*.test.tsx` | fast |
| Uçtan uca (e2e) | **Playwright** | `frontend/e2e/*.spec.ts` | full |

**Profil ayrımı selector ile yapılır (Two speeds, kural 4):**
- pytest: `backend/conftest.py`, `tests/integration/` altındaki her testi otomatik olarak
  `integration` marker'ı ile işaretler. Hızlı adım `-m "not integration"`, tam adım
  `-m integration` çalıştırır — yeni bir test her zaman tam olarak birinde koşar.
- Vitest yalnızca `src/**/*.test.{ts,tsx}` toplar ve `e2e/`'yi hariç tutar; Playwright yalnızca
  `e2e/` (`testDir`) toplar. Glob ile ayrım, dosya listesiyle değil.

**PostgreSQL (Testcontainers):** veritabanı isteyen ilk test geldiğinde (`backend/conftest.py`,
`django_db_modify_db_settings`) oturum başına tek bir `postgres:17-alpine` container'ı başlatılır —
DB'siz hızlı profil hiç container başlatmaz; oturum sonunda (başarısızlık dahil) fixture
finalizer'ında durdurulup silinir. Ryuk reaper kapalıdır
(`TESTCONTAINERS_RYUK_DISABLED=true`) çünkü run sonrasında yaşamaya devam eder; temizlik fixture'ın
sorumluluğundadır. Docker çalışmıyorsa entegrasyon adımı **kırmızı** olur (sessizce atlanmaz).

### Playwright (e2e)
- Konum: `frontend/e2e/`, yapılandırma `frontend/playwright.config.ts`; paket `@playwright/test`
  (`frontend/package.json` devDependency), tarayıcı **Chromium**, `npx playwright install chromium`
  ile kurulur (CI'da `--with-deps`).
- Çalıştırma: `npm run e2e` (= `node e2e/run.mjs`; çıplak `playwright test` veritabanı olmadan
  koşar, kullanılmaz) — **headless**, tek worker, `retries: 0` (flaky test R-03 ile düzeltilir,
  retry ile gizlenmez), `forbidOnly: true`.
- E2E her zaman `frontend/e2e/run.mjs` üzerinden çalışır (`check.conf` `e2e` adımı):
  **veritabanının sahibi `run.mjs`'tir** — geçici bir Testcontainers PostgreSQL 17 başlatır,
  `playwright test --workers=1`'ı bağlantı bilgisiyle çalıştırır ve container'ı `finally`
  içinde durdurur (başarısızlık ve Ctrl+C dahil). `globalSetup` kullanılmaz: Playwright
  `webServer`'ı `globalSetup`'tan **önce** başlatır, backend veritabanını bulamazdı (plan 0001).
- **Uygulama yaşam döngüsünün tek sahibi Playwright `webServer`'dır** (Resource hygiene, kural 4):
  - Backend: `backend/scripts/e2e_server.py` — migrate + `runserver` autoreloader **kapalı**,
    tek süreç, `127.0.0.1:8001`, üretim ayarları (`DEBUG=false`, e2e'ye özel test anahtarı).
    Autoreloader ikinci bir süreç doğurur ve durdurmada geride kalabilir.
  - Frontend: `vite build` çıktısı `vite preview --strictPort` ile `127.0.0.1:4173`'te sunulur
    (dev server değil); `/api` backend'e proxy'lenir — sayfa ve API aynı origin.
  - Komutlar `npm run`/`npx` sarmalayıcısı olmadan doğrudan verilir — Windows'ta sarmalayıcının
    alt süreçleri Playwright durdurduğunda yetim kalabilir.
  - `reuseExistingServer: false` — e2e her zaman kendi başlattığı uygulamaya karşı koşar; açık
    kalmış bir geliştirme sunucusuna bağlanmaz.
- Artefaktlar (`playwright-report/`, `test-results/`) gitignore'dadır; yalnızca hata durumunda
  trace/screenshot üretilir (`trace: 'retain-on-failure'`). Kanıt olarak repoya konmaz (Evidence policy).
- Seçiciler erişilebilirlik odaklıdır: `getByRole`, `getByLabel` (Türkçe etiketlerle); CSS/XPath
  seçici yalnızca gerekçeyle.
- Erişilebilirlik: her ekran durumunda `@axe-core/playwright` ile WCAG 2.1 AA taraması
  (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`); ihlal testi kırmızı yapar.

## What must be tested
- **Her iş kuralı (BR-n)** en az bir testle; test adı BR numarasını içerir (`docs/domain.md`).
- **İş Kanunu sınırları** ayrı ayrı: kıdem 1/5/6/14/15/16. yıl, yaş 18/19 ve 49/50 eşikleri
  (BR-1, BR-2); hak ediş yıldönümü günü/öncesi (BR-3).
- **İş günü hesabı:** hafta sonu, resmi tatil, arife yarım günü, yıl geçişi, yarım gün başlangıç/bitiş (BR-4, BR-5).
- **Her durum geçişi** ve yasak geçişler (`docs/domain.md` invariants).
- **Yetki:** her uç için en az bir "yetkisiz rol reddedilir" testi; başkasının kaydı → 404;
  kendi talebini onaylama reddedilir (BR-8).
- **Her yasak bağımlılık** bir import-linter sözleşmesi veya mimari testle (`docs/architecture.md`).
- **E2E (Playwright):** kritik akış — çalışan talep oluşturur → yönetici onaylar → çalışan güncel
  bakiyeyi görür; ve ret akışı. Her yeni kullanıcı akışı spec'inin "User experience" durumları
  (boş, yükleniyor, hata, başarı, yetkisiz) bileşen testleri veya e2e ile kapsanır.
- Kod kapsama yüzdesi eşiği **yoktur**; kanıt kabul kriteri ↔ test eşlemesidir.

## Protected-tests rule
Weakening asserts, deleting, or skipping tests to reach green is forbidden. A red test triggers
`prompts/recovery/red-test.md` (R-02) — first decide what is wrong: code, test, or spec.

## Characterization tests
Before refactoring untested code (`workflows/refactor.md`) and for brownfield change requests
(`workflows/change-request.md`, Preserved behavior), pin the current behavior first — warts
included. They are written from observation, not from what the code "should" do.

## Evidence for UI criteria
A screenshot is evidence for a UI criterion; for change requests, before/after screenshots that
also show the preserved behavior. Screenshots go into the PR, not the repo (Evidence policy).
A screenshot proves a criterion only against the spec's "User experience": every state it lists
(empty, loading, error, success, no permission), compared with the linked design if there is one.

## Evidence policy
1. **Evidence is referenced, not stored.** Each acceptance criterion's evidence is a pointer: the
   test's name and the command that reproduces it (`./scripts/check`). The criterion ↔ evidence
   table in the spec/plan is the only evidence artifact that lives in the repo.
2. **Reproducible evidence is never filed.** No saved check output, console dumps, coverage reports
   or log copies in the repo — git history and CI runs already archive every execution.
3. **Non-reproducible evidence** (a screenshot of a manual UI check, a one-off measurement, an
   external-system confirmation) goes into the pull request (description or attachment); the
   evidence table links to it. It is the exception, not the rule.
4. **Never clone or copy the repository inside its own working tree.** Clean-clone verification
   runs in a temporary directory outside the repo; only the one-line result (command + green/red)
   is recorded in the evidence table. The clone is always deleted, never kept.
5. **There is no `evidence/` (or `.evidence/`) directory in this workspace.** An agent that feels
   the need to create one is about to violate rule 1. `scripts/doctor` warns on both violations.

## Resource hygiene
1. **A check run leaves nothing running.** No survivors of any kind: build/compile daemons,
   package-manager services, test hosts and parallel workers, watch modes, browsers, the application
   under test, containers or emulators started for the run. Agents run check an order of magnitude
   more often than humans; per-run residue compounds into machine starvation.
2. **The residue test** (the rule's definition, not advice): run `./scripts/check` twice back to
   back; after each run, process count and memory return to the baseline measured before the first.
   `./scripts/residue` runs it (`--fast` for the fast profile) and names every survivor with its
   command line; it lists anything started meanwhile too, so run it on an otherwise idle machine.
   Rerun it whenever `scripts/check.conf` changes.
3. Warm-process caches trade memory for speed for humans who build rarely; with an agent, trade the
   seconds back for a flat memory profile.
4. Interactive modes (watchers, dev servers, REPLs) never belong in check. e2e runs single-worker
   and headless by default; one component owns the app-under-test lifecycle — started for the run,
   stopped at the end, including on failure and timeout.

## Two speeds, one contract
1. `./scripts/check` is still the one way to ask "is this good?"; `--fast` is a speed of the
   contract, not a second contract.
2. **Fast green is a working state; only full green is evidence.** Per step, per finding, per
   iteration → `--fast`. Segment exits, PROVE steps, recovery-ramp exits, the verify table and CI
   → `CHECK GREEN (full, …)`. `scripts/doctor` warns when a shipped spec, or in CI the pull
   request description, shows `CHECK GREEN (fast, …)` and no `(full, …)`.
3. Fast: compile and the quick tests (unit, lint). Full only: e2e, long integration suites, and
   any single step over ~a minute — the minute is a per-step threshold, not a total for the fast
   profile; fast has no fixed total. Bootstrap decides per stack and tags the steps `[fast]` in
   check.conf. When fast grows too long to iterate with, take steps out in this order: lint
   first, then formatting, then unit tests; compilation stays longest.
4. **Split a test step by a selector, never by a list.** The fast step selects with a filter
   (a category, trait, tag or namespace) and the full-only step runs the same filter inverted,
   so "fast ∪ the rest = every test" holds by construction: a test added later still runs in
   one of them. Splitting by naming projects or files leaves a silent hole — a new one that is
   not added to check.conf runs in neither profile while check stays green.
5. Durations come from check itself (`<== <step> (n s)` per step, the total in the green line).
   Decide a split, or report a profile's duration, on the median of at least 3 runs — single
   runs vary too much to decide on.

## Determinism
Flaky tests are fixed, not retried or skipped — see R-03. Evidence of a fix: 5 consecutive green runs.
