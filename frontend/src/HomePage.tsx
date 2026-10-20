import { ROLE_LABELS } from "./messages";

export type Profile = {
  first_name: string;
  last_name: string;
  roles: string[];
  team: { first_name: string; last_name: string }[] | null;
};

type Props = {
  profile: Profile;
  loggingOut: boolean;
  onLogout: () => void;
};

/** Spec 0002, AC-15 and AC-16: own name and roles; managers also see their direct team. */
export function HomePage({ profile, loggingOut, onLogout }: Props) {
  const roles = profile.roles.map((role) => ROLE_LABELS[role] ?? role).join(", ");
  return (
    <main className="page">
      <h1>
        Hoş geldiniz, {profile.first_name} {profile.last_name}
      </h1>
      <p>Rolleriniz: {roles}</p>
      {profile.team !== null && (
        <section aria-labelledby="team-heading">
          <h2 id="team-heading">Ekibim</h2>
          <ul>
            {profile.team.map((member, index) => (
              // Two reports may share a name; the server's order is stable (review L8).
              <li key={`${index}-${member.last_name}-${member.first_name}`}>
                {member.first_name} {member.last_name}
              </li>
            ))}
          </ul>
        </section>
      )}
      <button type="button" onClick={onLogout} disabled={loggingOut}>
        {loggingOut ? "Çıkış yapılıyor…" : "Çıkış yap"}
      </button>
    </main>
  );
}
