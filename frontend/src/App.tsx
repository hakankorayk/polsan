import { StartPage } from "./StartPage";
import { useServerStatus } from "./useServerStatus";

export function App() {
  return <StartPage status={useServerStatus()} />;
}
