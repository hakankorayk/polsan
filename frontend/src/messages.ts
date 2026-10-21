/** User-facing texts, verbatim from the specs' "User experience" (0002, 0003). */
export const MESSAGES = {
  invalidCredentials: "Kullanıcı adı veya parola hatalı.",
  locked: "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin.",
  sessionExpired: "Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın.",
  loggedOut: "Çıkış yapıldı.",
  unreachable: "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
  profileFailed: "Bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  loading: "Yükleniyor…",
  required: "Bu alan zorunludur.",
  // Spec 0003 "User experience": the "İzin bakiyem" section.
  balanceLoading: "Bakiye yükleniyor…",
  balanceFailed: "Bakiye bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  balanceEmpty: "Henüz bakiye hareketiniz yok.",
} as const;

export const LEDGER_KIND_LABELS: Record<string, string> = {
  ACCRUAL: "Hak ediş",
  ADJUSTMENT: "Düzeltme",
};

export const ROLE_LABELS: Record<string, string> = {
  employee: "Çalışan",
  manager: "Yönetici",
  hr: "İK",
};
