import "./Forms.css";

import { useCallback, useEffect, useState } from "react";

import { api, problemCode } from "./api/client";
import { HomePage, type Profile } from "./HomePage";
import { LoginForm, type LoginNotice } from "./LoginForm";
import { MESSAGES } from "./messages";
import { PasswordChangeForm } from "./PasswordChangeForm";
import { clearSession, ensureCsrfCookie, hadSession, markSession } from "./session";
import { StartPage } from "./StartPage";
import { useServerStatus } from "./useServerStatus";

type Screen =
  | { kind: "loading" }
  | { kind: "login"; notice?: LoginNotice }
  | { kind: "password" }
  | { kind: "home"; profile: Profile }
  | { kind: "profileError" };

/** Screen state machine: login → (forced password change) → home (spec 0002, "Flow"). */
export function App() {
  const serverStatus = useServerStatus();
  const [screen, setScreen] = useState<Screen>({ kind: "loading" });
  const [loggingOut, setLoggingOut] = useState(false);

  const toLogin = useCallback((notice?: LoginNotice) => {
    clearSession();
    setScreen({ kind: "login", notice });
  }, []);

  const loadProfile = useCallback(
    async (afterLogin: boolean) => {
      try {
        const { data, error } = await api.GET("/api/me/");
        if (data) {
          markSession();
          setScreen({ kind: "home", profile: data });
          return;
        }
        const code = problemCode(error);
        if (code === "password_change_required") {
          markSession();
          setScreen({ kind: "password" });
        } else if (code === "not_authenticated") {
          toLogin(hadSession() ? "sessionExpired" : undefined);
        } else {
          setScreen({ kind: "profileError" });
        }
      } catch {
        // Unreachable server: on first load the start page status says so; after login, say it.
        if (afterLogin) setScreen({ kind: "profileError" });
        else toLogin();
      }
    },
    [toLogin],
  );

  useEffect(() => {
    void ensureCsrfCookie().then(() => loadProfile(false));
  }, [loadProfile]);

  async function logout() {
    setLoggingOut(true);
    try {
      const { response } = await api.POST("/api/auth/logout/");
      toLogin(response.ok ? "loggedOut" : "sessionExpired");
    } catch {
      setScreen({ kind: "profileError" });
    } finally {
      setLoggingOut(false);
    }
  }

  switch (screen.kind) {
    case "loading":
      return (
        <StartPage status={serverStatus}>
          <p className="form-notice">{MESSAGES.loading}</p>
        </StartPage>
      );
    case "login":
      return (
        <StartPage status={serverStatus}>
          <LoginForm
            notice={screen.notice}
            onSuccess={(mustChange) => {
              markSession();
              if (mustChange) {
                setScreen({ kind: "password" });
              } else {
                setScreen({ kind: "loading" }); // no second submit while the profile loads (L8)
                void loadProfile(true);
              }
            }}
          />
        </StartPage>
      );
    case "password":
      return (
        <PasswordChangeForm
          onDone={() => void loadProfile(true)}
          onSessionLost={() => toLogin("sessionExpired")}
        />
      );
    case "home":
      return <HomePage profile={screen.profile} loggingOut={loggingOut} onLogout={logout} />;
    case "profileError":
      return (
        <main className="page">
          <h1>Polsan Leave Manager</h1>
          <p role="alert">{MESSAGES.profileFailed}</p>
        </main>
      );
  }
}
