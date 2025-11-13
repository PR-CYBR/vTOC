import Link from 'next/link';
import { useRouter } from 'next/router';
import { PropsWithChildren } from 'react';

export default function Layout({ children }: PropsWithChildren) {
  const { pathname } = useRouter();
  const active = (href: string) => pathname === href ? 'station-nav__link station-nav__link--active' : 'station-nav__link';

  return (
    <div className="station-shell">
      <header className="station-header">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.05rem' }}>
            vTOC Station Command
          </h1>
          <div style={{ fontSize: '.8rem', color: 'var(--muted)' }}>Demo dashboard (static)</div>
        </div>
        <nav className="station-nav">
          <Link href="/stations/toc-s1" className={active('/stations/toc-s1')}>TOC-S1</Link>
          <Link href="/stations/toc-s2" className={active('/stations/toc-s2')}>TOC-S2</Link>
          <Link href="/stations/toc-s3" className={active('/stations/toc-s3')}>TOC-S3</Link>
          <Link href="/stations/toc-s4" className={active('/stations/toc-s4')}>TOC-S4</Link>
        </nav>
      </header>

      <main className="station-content">
        {children}
      </main>

      <aside className="chatkit-console">
        <div className="chatkit-assistant">
          <p style={{ padding: '0.75rem 1rem', margin: 0 }}>
            <strong>Mission Console</strong><br/>
            Placeholder (ChatKit not connected in demo).
          </p>
        </div>
      </aside>
    </div>
  );
}
