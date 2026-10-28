const navItems = [{ label: "Overview", active: true }];

export default function HomePage() {
  return (
    <div className="workspace">
      <aside className="sidebar" aria-label="Workspace navigation">
        <div className="brand"><span className="brand-mark" aria-hidden="true">O</span> OPSYRO</div>
        <p className="nav-label">Workspace</p>
        <nav className="nav-list" aria-label="Main">
          {navItems.map((item) => (
            <a className="nav-item" href="#overview" aria-current={item.active ? "page" : undefined} key={item.label}>
              <span className="nav-mark" aria-hidden="true" />{item.label}
            </a>
          ))}
        </nav>
        <p className="sidebar-note">Audience curiosity, made visible.<br />Creator workspace foundation</p>
      </aside>

      <main className="main" id="overview">
        <header className="topline">
          <div><p className="eyebrow">Creator workspace</p><h1>Overview</h1></div>
          <span className="top-note">Foundation · Phase 1</span>
        </header>
        <section className="intro" aria-labelledby="intro-title">
          <p className="eyebrow">Audience understanding</p>
          <h2 id="intro-title">See what your audience wants to understand.</h2>
          <p>OPSYRO will bring moments of curiosity and audience questions together, so creators can see what matters and respond with intent.</p>
        </section>
        <section aria-labelledby="signals-title">
          <div className="section-heading"><h2 id="signals-title">Audience signals</h2><span>Not connected</span></div>
          <div className="empty-state">
            <div className="empty-copy">
              <h3>Your signal workspace is ready to take shape.</h3>
              <p>There are no sessions or audience signals yet. Session creation and signal collection will arrive in later implementation phases. No activity is simulated here.</p>
            </div>
            <aside className="setup-note" aria-label="Current integration status">
              <strong>Integration status</strong>
              <p>This workspace is a local foundation. Twitch authorization and live session data are not configured.</p>
            </aside>
          </div>
        </section>
        <footer className="footerline">OPSYRO · Audience intelligence for interactive media</footer>
      </main>
    </div>
  );
}
