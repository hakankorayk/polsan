# Domain

> Business, insanlar ve ajanlar arasındaki ortak dil. Bir terim burada yoksa, ajan kendi anlamını
> uydurur. Kodda İngilizce karşılığı kullanılır (`docs/conventions.md`, Naming).

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Çalışan — `Employee` | Polsan'da çalışan, izin talep edebilen kişi | Kullanıcı hesabı (`identity`) ile aynı şey değil; bir çalışanın bir hesabı olur |
| Yönetici — `Manager` | Bir çalışanın doğrudan bağlı olduğu çalışan; o çalışanın onaylayıcısı | Rol, unvan değil: yöneticiliği organizasyon ağacı belirler |
| İK — `HR` | İnsan Kaynakları rolü: bakiye düzeltme, tatil takvimi, tüm kayıtları görme | |
| İzin Türü — `LeaveType` | İznin kategorisi (Yıllık, Ücretsiz, Mazeret…) | v1'de yalnızca **Yıllık izin** aktif |
| İzin Talebi — `LeaveRequest` | Çalışanın tarih aralığı + izin türü ile oluşturduğu kayıt | Durumları: Beklemede `PENDING` → Onaylandı `APPROVED` / Reddedildi `REJECTED` / İptal Edildi `CANCELLED` |
| Yarım gün — `HalfDay` | Bir iş gününün sabah `MORNING` veya öğleden sonra `AFTERNOON` yarısı | 0,5 gün |
| İş Günü — `WorkingDay` | Çalışma haftasına dahil ve resmi tatil olmayan gün | Varsayılan Pzt–Cuma (ayar) |
| Resmi Tatil Takvimi — `HolidayCalendar` | Ulusal bayram ve genel tatillerin yıllık listesi (arife yarım günleri dahil) | İK yönetir |
| Kıdem — `Seniority` | İşe giriş tarihinden itibaren Polsan'da tamamlanan tam hizmet yılı | Önceki işverenlerdeki süre v1'de sayılmaz (BR-15) |
| Hak Ediş — `Accrual` | Kıdem yıldönümünde yıllık iznin tamamının bakiyeye eklenmesi | |
| Bakiye Defteri — `BalanceLedger` | Bakiyeyi değiştiren her hareketin append-only kaydı: hak ediş, kullanım, iade, düzeltme | Bakiye bir sütunda saklanmaz, defterden hesaplanır |
| İzin Bakiyesi — `Balance` | Defterdeki hareketlerin toplamı | |
| Kullanılabilir Bakiye — `AvailableBalance` | Bakiye − beklemedeki taleplerin gün toplamı | Yeni talep bununla karşılaştırılır |
| Devir — `CarryOver` | Kullanılmayan yıllık iznin sonraki yıla aktarılması | Yasal zorunluluk; izin yanmaz |
| Düzeltme — `Adjustment` | İK'nın gerekçeli manuel bakiye hareketi | |
| Onaylayıcı — `Approver` | Talebi onaylama/reddetme yetkisi olan kişi | Yönetici; yöneticisi olmayan için İK |
| Hesap — `Account` (`identity.User`) | Bir çalışanın uygulamaya giriş kaydı; her çalışanın en fazla bir hesabı, her hesabın tam bir çalışanı vardır | Çalışan kaydı değildir; pasif yapılır, silinmez |
| Kullanıcı adı — `username` | Girişte kullanılan, büyük/küçük harf duyarsız, yalnız ASCII harf, rakam ve `. _ -` içeren kimlik | E-posta değildir |
| Geçici parola — `temporary password` | İK'nın verdiği, ilk girişte değiştirilmesi zorunlu parola | `must_change_password` |
| Rol — `Role` | Çalışan (her aktif çalışan), Yönetici (en az bir aktif doğrudan bağlısı olan), İK (açıkça verilen yetki); birlikte bulunabilir | Unvan değildir; Yönetici rolü organizasyon ağacından türer |

## Business rules
Kaynak: 4857 sayılı İş Kanunu md. 53–56 + bootstrap görüşmesi (2026-10-19).

- **BR-1** Yıllık izin hakkı (iş günü) hak ediş anında tamamlanan kıdem yılına göre: 1.–5. yıl
  (5 dahil) → **14**; 6.–14. yıl → **20**; 15. yıl ve sonrası → **26**. Yani 5. yıldönümünde 14,
  6. yıldönümünde 20, 15. yıldönümünde 26 gün eklenir (karar: 2026-10-19; İK teyidi bekleniyor).
- **BR-2** Hak ediş anında 18 yaşında veya daha küçük ya da 50 yaşında veya daha büyük olan
  çalışanın yıllık izni **20 günden az olamaz** (BR-1 ile hesaplanan değer 20'den küçükse 20).
- **BR-3** İlk hak ediş, işe girişten itibaren **1 tam yıl** tamamlanınca olur; sonraki her
  kıdem yıldönümünde o yılın hakkının tamamı bakiyeye **hak ediş** hareketi olarak eklenir.
- **BR-4** Kullanılan gün = talep aralığındaki **iş günleri**. Hafta tatili, ulusal bayram ve genel
  tatil günleri düşülmez. Arife gibi yarım günlük tatile denk gelen tam gün izin **0,5** düşer.
- **BR-5** İzin miktarı 0,5'in katıdır. Yarım gün, sabah veya öğleden sonra olarak seçilir.
- **BR-6** Bir talebin gün sayısı, talep anındaki **kullanılabilir bakiyeyi** (bakiye − beklemedeki
  taleplerin toplamı) aşamaz; beklemedeki talepler bakiyeyi ayırır. Negatif bakiye (avans izin) yoktur.
- **BR-7** Aynı çalışanın tarihleri (yarım gün düzeyinde) çakışan iki **Beklemede** veya
  **Onaylandı** talebi olamaz.
- **BR-8** Talebi çalışanın **doğrudan yöneticisi** onaylar veya reddeder; yöneticisi olmayan
  çalışanın talebini İK onaylar. **Kimse kendi talebini onaylayamaz.** Onay tek aşamalıdır.
- **BR-9** Onaylanan talebin gün sayısı, onay anında defterden **kullanım** hareketi olarak düşer.
- **BR-10** Beklemedeki talebi sahibi iptal edebilir. Onaylanmış talebin iptali onaylayıcının
  onayını gerektirir; iptal edilen günler defterde **iade** hareketi olarak geri eklenir.
- **BR-11** Kullanılmayan yıllık izin yanmaz; yıl sonunda bakiye olduğu gibi **devreder**.
- **BR-12** İK, gerekçe yazmak zorunlu olmak üzere **düzeltme** hareketi ekleyebilir. Mevcut
  defter hareketleri değiştirilmez veya silinmez.
- **BR-13** Reddedilen talep için ret gerekçesi zorunludur.
- **BR-14** Çalışan başlangıç tarihi bugünden önce olan talep oluşturamaz; geçmiş tarihli
  kayıtları yalnızca İK girer.
- **BR-15** Kıdem yalnızca Polsan'daki işe giriş tarihinden hesaplanır; önceki işverenlerdeki süre
  v1'de sayılmaz. Gerekiyorsa İK bunu gerekçeli **düzeltme** hareketiyle (BR-12) yansıtır.

## Key domain invariants
- Bakiye her zaman defter hareketlerinin toplamıdır; başka bir "bakiye" alanı tutulmaz.
- Kullanım ve iade hareketleri bir izin talebine bağlıdır; bir talebin günleri defterde **tam bir
  kez** düşülür ve en fazla bir kez iade edilir.
- Çalışanın kendi talebiyle bakiye hiçbir zaman sıfırın altına inmez (yalnızca İK düzeltmesi
  geçmişi düzeltebilir).
- Durum geçişleri yalnızca: `PENDING → APPROVED | REJECTED | CANCELLED`, `APPROVED → CANCELLED`.
  `REJECTED` ve `CANCELLED` son durumlardır.
- Onay, ret, iptal ve düzeltme olayları audit kaydına yazılır; audit kaydı değiştirilmez ve silinmez.
