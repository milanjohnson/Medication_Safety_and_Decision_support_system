import { NavLink, Route, Routes, useParams } from "react-router-dom";
import { ComingSoon } from "../features/aakaash/pages/ComingSoon";
import { MODULE_COMPONENTS, modulePath, SCREENS } from "../features/aakaash/registry";
import { StatusProvider, useStatus } from "../features/aakaash/StatusContext";

function ModuleRoute() {
  const { id = "" } = useParams();
  const Custom = MODULE_COMPONENTS[id];
  return Custom ? <Custom /> : <ComingSoon id={id} />;
}

function Sidebar() {
  const q = useStatus();
  const link = ({ isActive }: { isActive: boolean }) => (isActive ? "nav-link active" : "nav-link");
  return (
    <nav className="sidebar" aria-label="Main">
      <ul>
        {SCREENS.map((s) => (
          <li key={s.id}>
            <NavLink to={s.path} end={s.path === "/"} className={link}>{s.label}</NavLink>
          </li>
        ))}
      </ul>
      <h2 className="nav-heading">Coming soon</h2>
      {q.state === "loading" && !q.data && <p className="small muted nav-note">Loading…</p>}
      {q.state === "error" && (
        <p className="small nav-note">
          Module list unavailable (API not reachable). <button type="button" className="link-btn" onClick={q.reload}>Retry</button>
        </p>
      )}
      <ul>
        {q.data?.modules.map((m) => (
          <li key={m.id}>
            <NavLink to={modulePath(m.id)} className={link}>
              {m.label}
              <span className="soon-tag">soon</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function App() {
  return (
    <StatusProvider>
      <div className="banner" role="note">
        <span aria-hidden="true">⚕</span> Research prototype. Decision support only. Not medical advice.
      </div>
      <div className="shell">
        <header className="brand">
          <strong>Medication Safety Support</strong>
          <span className="muted small">Subareas A and B</span>
        </header>
        <Sidebar />
        <main className="content" id="main">
          <Routes>
            {SCREENS.map((s) => (
              <Route key={s.id} path={s.path} element={<s.Component />} />
            ))}
            <Route path="/modules/:id" element={<ModuleRoute />} />
            <Route path="*" element={<><h1>Page not found</h1><p>Use the menu to go to a screen.</p></>} />
          </Routes>
        </main>
      </div>
    </StatusProvider>
  );
}
