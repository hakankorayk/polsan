import { type FormEvent, useEffect, useRef, useState } from "react";

import { api, problemCode } from "./api/client";
import { FormField } from "./FormField";
import { MESSAGES } from "./messages";

export type LoginNotice = "sessionExpired" | "loggedOut";

type Props = {
  notice?: LoginNotice;
  onSuccess: (mustChangePassword: boolean) => void;
};

type FieldErrors = { username?: string; password?: string };

export function LoginForm({ notice, onSuccess }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string>();
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [attempt, setAttempt] = useState(0);
  const alertRef = useRef<HTMLParagraphElement>(null);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // Focus moves to the first error after each submission (spec 0002, AC-22).
  useEffect(() => {
    if (attempt === 0) return;
    if (fieldErrors.username) usernameRef.current?.focus();
    else if (fieldErrors.password) passwordRef.current?.focus();
    else if (formError) alertRef.current?.focus();
  }, [attempt, fieldErrors, formError]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const missing: FieldErrors = {
      username: username.trim() ? undefined : MESSAGES.required,
      password: password ? undefined : MESSAGES.required,
    };
    setFormError(undefined);
    setFieldErrors(missing);
    if (missing.username || missing.password) {
      setAttempt((n) => n + 1);
      return;
    }
    setSubmitting(true);
    try {
      const { data, error } = await api.POST("/api/auth/login/", {
        body: { username, password },
      });
      if (data) {
        onSuccess(data.must_change_password);
        return;
      }
      const code = problemCode(error);
      setFormError(code === "login_locked" ? MESSAGES.locked : MESSAGES.invalidCredentials);
    } catch {
      setFormError(MESSAGES.unreachable);
    } finally {
      setSubmitting(false);
      setAttempt((n) => n + 1);
    }
  }

  return (
    <form className="form" onSubmit={submit} noValidate aria-label="Giriş">
      {notice && (
        <p role="status" className="form-notice">
          {MESSAGES[notice]}
        </p>
      )}
      {formError && (
        <p ref={alertRef} role="alert" tabIndex={-1} className="form-alert">
          {formError}
        </p>
      )}
      <FormField
        id="username"
        label="Kullanıcı adı"
        autoComplete="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        error={fieldErrors.username}
        inputRef={usernameRef}
      />
      <FormField
        id="password"
        label="Parola"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
        inputRef={passwordRef}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
      </button>
    </form>
  );
}
