/** User-facing texts, verbatim from spec 0002 "User experience". */
export const MESSAGES = {
  invalidCredentials: "Kullanıcı adı veya parola hatalı.",
  locked: "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin.",
  sessionExpired: "Oturumunuzun süresi doldu. Lütfen yeniden giriş yapın.",
  loggedOut: "Çıkış yapıldı.",
  unreachable: "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
  profileFailed: "Bilgileriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  loading: "Yükleniyor…",
  required: "Bu alan zorunludur.",
} as const;

export const ROLE_LABELS: Record<string, string> = {
  employee: "Çalışan",
  manager: "Yönetici",
  hr: "İK",
};
