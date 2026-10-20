import { type FormEvent, useEffect, useRef, useState } from "react";

import { api, problemFieldErrors } from "./api/client";
import { FormField } from "./FormField";
import { MESSAGES } from "./messages";

type Props = {
  onDone: () => void;
  onSessionLost: () => void;
};

type FieldErrors = { new_password?: string; new_password_confirm?: string };

/** Forced change after logging in with a temporary password (spec 0002, AC-10, AC-11). */
export function PasswordChangeForm({ onDone, onSessionLost }: Props) {
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string>();
  const [attempt, setAttempt] = useState(0);
  const newRef = useRef<HTMLInputElement>(null);
  const confirmRef = useRef<HTMLInputElement>(null);
  const alertRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (attempt === 0) return;
    if (errors.new_password) newRef.current?.focus();
    else if (errors.new_password_confirm) confirmRef.current?.focus();
    else if (formError) alertRef.current?.focus();
  }, [attempt, errors, formError]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setFormError(undefined);
    const missing: FieldErrors = {
      new_password: newPassword ? undefined : MESSAGES.required,
      new_password_confirm: confirm ? undefined : MESSAGES.required,
    };
    setErrors(missing);
    if (missing.new_password || missing.new_password_confirm) {
      setAttempt((n) => n + 1);
      return;
    }
    setSubmitting(true);
    try {
      const { response, error } = await api.POST("/api/auth/password/", {
        body: { new_password: newPassword, new_password_confirm: confirm },
      });
      if (response.ok) {
        onDone();
        return;
      }
      if (response.status === 403) {
        onSessionLost();
        return;
      }
      const fields = problemFieldErrors(error);
      setErrors({
        new_password: fields.new_password?.join(" "),
        new_password_confirm: fields.new_password_confirm?.join(" "),
      });
    } catch {
      setFormError(MESSAGES.unreachable);
    } finally {
      setSubmitting(false);
      setAttempt((n) => n + 1);
    }
  }

  return (
    <main className="page">
      <h1>Parolanızı değiştirin</h1>
      <p>Geçici parolanızla giriş yaptınız. Devam etmek için yeni bir parola belirleyin.</p>
      <form className="form" onSubmit={submit} noValidate aria-label="Parola değiştirme">
        {formError && (
          <p ref={alertRef} role="alert" tabIndex={-1} className="form-alert">
            {formError}
          </p>
        )}
        <FormField
          id="new-password"
          label="Yeni parola"
          type="password"
          autoComplete="new-password"
          hint="En az 12 karakter; çok yaygın veya yalnızca rakamdan oluşan parolalar kabul edilmez."
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          error={errors.new_password}
          inputRef={newRef}
        />
        <FormField
          id="new-password-confirm"
          label="Yeni parola (tekrar)"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={errors.new_password_confirm}
          inputRef={confirmRef}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Kaydediliyor…" : "Parolayı değiştir"}
        </button>
      </form>
    </main>
  );
}
