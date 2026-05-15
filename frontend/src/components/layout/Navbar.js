import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { publicAPI } from '../../lib/api';
import { useSettings, useTheme } from '../../App';
import LanguageSwitcher from '../LanguageSwitcher';
import { useT } from '../../lib/i18n';
import { Menu, X, LogIn, LogOut, Facebook, Twitter, Instagram, Linkedin, Github, Youtube, Search } from 'lucide-react';
import LoginModal from '../LoginModal';
import SearchBar from '../SearchBar';
import { isAurexFamily } from '../../lib/themeColors';

const socialIconMap = { facebook: Facebook, twitter: Twitter, instagram: Instagram, linkedin: Linkedin, github: Github, youtube: Youtube };

export default function Navbar() {
  const theme = useTheme();
  if (theme === 'modern' || isAurexFamily(theme)) return <ModernNavbar />;
  if (theme === 'classic') return <ClassicNavbar />;
  return <DefaultNavbar />;
}

function useNavData() {
  const { user, logout } = useAuth();
  const settings = useSettings();
  const [navPages, setNavPages] = useState([]);
  const [loginOpen, setLoginOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();
  const socialLinks = settings.social_links || [];

  useEffect(() => {
    publicAPI.getNavPages().then(r => setNavPages(r.data || [])).catch(() => {});
  }, []);

  const headerPages = navPages.filter(p => p.show_in_header).sort((a, b) => (a.order || 0) - (b.order || 0));

  const handlePageClick = (page, e) => {
    if (page.login_required && !user) { e.preventDefault(); setLoginOpen(true); return; }
    const url = page.url || '';
    if (url.includes('#')) {
      e.preventDefault();
      const [pathPart, hashPart] = url.split('#');
      const targetPath = pathPart || '/';
      if (location.pathname === targetPath) {
        const el = document.getElementById(hashPart);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      } else {
        window.location.href = url;
      }
    }
  };

  const isExternal = (url) => url?.startsWith('http://') || url?.startsWith('https://');
  const isAdmin = location.pathname.startsWith('/admin');

  // Header visibility flags (Roles & Permissions):
  //   • `hasCmsAccess` controls the "Admin" button — admins always see it,
  //     operators with at least one section permission see it too.  Plain
  //     members never do.
  //   • `hasMyAccount` controls the "My Account" link — admins always see
  //     it, members must hold the `role_member` CMS role.  If an admin
  //     revokes role_member from a user, this link hides instantly.
  const hasCmsAccess = !!user && (user.role === 'admin' || (user.effective_permissions || []).length > 0);
  const hasMyAccount = !!user && (user.role === 'admin' || (user.cms_roles || []).includes('role_member'));

  return { user, logout, settings, socialLinks, headerPages, handlePageClick, isExternal, isAdmin, location, loginOpen, setLoginOpen, searchOpen, setSearchOpen, hasCmsAccess, hasMyAccount };
}

function NavLinks({ headerPages, isExternal, handlePageClick, location, user }) {
  return (
    <>
      {headerPages.map(page => {
        const pageUrl = page.url || `/page/${page.id}`;
        if (isExternal(page.url)) {
          return <a key={page.id} href={page.url} target={page.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className="text-sm font-medium transition-colors hover:opacity-70" style={{ color: 'var(--color-heading-color, #1a2332)' }} data-testid={`nav-${page.title.toLowerCase().replace(/\s/g, '-')}`}>{page.title}</a>;
        }
        return (
          <Link key={page.id} to={pageUrl} onClick={e => handlePageClick(page, e)}
            className="text-sm font-medium transition-colors hover:opacity-70"
            style={{ color: location.pathname === pageUrl ? 'var(--color-accent, #0D9488)' : 'var(--color-heading-color, #1a2332)' }}
            data-testid={`nav-${page.title.toLowerCase().replace(/\s/g, '-')}`}
          >{page.title} {page.login_required && !user && <span className="text-[10px]">*</span>}</Link>
        );
      })}
    </>
  );
}

function DefaultNavbar() {
  const tt = useT();
  const { user, logout, settings, socialLinks, headerPages, handlePageClick, isExternal, isAdmin, location, loginOpen, setLoginOpen, searchOpen, setSearchOpen, hasCmsAccess, hasMyAccount } = useNavData();
  const [mobileOpen, setMobileOpen] = useState(false);
  const API = process.env.REACT_APP_BACKEND_URL;
  const resolveSrc = (v) => v ? (v.startsWith('/api') ? `${API}${v}` : v) : null;
  // Default theme always has solid bg, so use logo_on_2 (or fallback to logo_on_1)
  const logoSrc = resolveSrc(settings.logo_on_2 || settings.logo_on_1 || settings.logo_on);
  const brandName = tt(settings.brand_name) || 'Legacy';
  const settingsLoaded = !!settings.brand_name || !!settings.id;

  if (isAdmin) return null;

  return (
    <>
      <div className="text-white/70 text-xs py-2" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }} data-testid="top-bar">
        <div className="max-w-7xl mx-auto px-6 flex justify-end items-center gap-3">
          {socialLinks.map(link => {
            const IconComp = socialIconMap[link.icon] || Facebook;
            return <a key={link.id} href={link.url} target="_blank" rel="noreferrer" className="hover:text-white transition-colors" data-testid={`social-${link.icon}`} title={link.platform}><IconComp className="w-3.5 h-3.5" /></a>;
          })}
        </div>
      </div>
      <header className="sticky top-0 z-50" style={{ backgroundColor: 'var(--color-navbar-bg, #ffffff)', borderBottom: '1px solid #e2e8f0' }} data-testid="main-navbar">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2" data-testid="brand-logo">
            {logoSrc ? (
              <img src={logoSrc} alt={brandName} className="h-8 w-auto object-contain" data-testid="navbar-logo-img" />
            ) : settingsLoaded ? (
              <>
                <div className="w-8 h-8 rounded-sm flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }}>
                  <span className="text-white font-bold text-sm" style={{ fontFamily: 'Playfair Display, serif' }}>{brandName[0]}</span>
                </div>
                <span className="text-xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading-color, #1a2332)' }}>{brandName}</span>
              </>
            ) : <div className="h-8 w-24" />}
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <NavLinks {...{ headerPages, isExternal, handlePageClick, location, user }} />
          </nav>
          <div className="flex items-center gap-3">
            <button onClick={() => setSearchOpen(!searchOpen)} className="p-2 hover:opacity-70" style={{ color: 'var(--color-heading-color, #1a2332)' }} data-testid="search-toggle"><Search className="w-4 h-4" /></button>
            {user ? (
              <div className="flex items-center gap-2">
                {hasMyAccount && <Link to="/my-account/membership-profile" className="text-xs font-medium px-3 py-1.5 rounded-sm hover:opacity-80" style={{ color: 'var(--color-heading-color, #1a2332)' }} data-testid="nav-my-account">My Account</Link>}
                {hasCmsAccess && <Link to="/admin" className="text-xs font-medium px-3 py-1.5 rounded-sm" style={{ backgroundColor: 'var(--color-accent, #0D9488)', color: '#fff' }} data-testid="nav-admin-btn">Admin</Link>}
                <button onClick={logout} className="text-sm flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-heading-color, #1a2332)' }}><LogOut className="w-4 h-4" /></button>
              </div>
            ) : (
              <button onClick={() => setLoginOpen(true)} className="text-sm font-medium px-4 py-2 rounded-sm flex items-center gap-1.5" style={{ backgroundColor: 'var(--color-button-bg, #1a2332)', color: 'var(--color-button-text, #ffffff)' }} data-testid="login-btn"><LogIn className="w-3.5 h-3.5" /> Login</button>
            )}
            <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2" style={{ color: 'var(--color-heading-color, #1a2332)' }}>
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        {searchOpen && <div className="max-w-7xl mx-auto px-6 pb-3"><SearchBar onClose={() => setSearchOpen(false)} /></div>}
        {mobileOpen && (
          <div className="md:hidden border-t px-6 py-4 space-y-3 bg-white">
            {headerPages.map(page => {
              const href = page.url || `/page/${page.id}`;
              return <Link key={page.id} to={href} onClick={() => setMobileOpen(false)} className="block text-sm font-medium" style={{ color: 'var(--color-heading-color, #1a2332)' }}>{page.title}</Link>;
            })}
            {hasMyAccount && <Link to="/my-account/membership-profile" onClick={() => setMobileOpen(false)} className="block text-sm font-medium" style={{ color: 'var(--color-accent, #0D9488)' }}>My Account</Link>}
          </div>
        )}
      </header>
      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}

function ModernNavbar() {
  const tt = useT();
  const { user, logout, settings, socialLinks, headerPages, handlePageClick, isExternal, isAdmin, location, loginOpen, setLoginOpen, searchOpen, setSearchOpen, hasCmsAccess, hasMyAccount } = useNavData();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [hasHero, setHasHero] = useState(true);
  const API = process.env.REACT_APP_BACKEND_URL;
  const resolveSrc = (v) => v ? (v.startsWith('/api') ? `${API}${v}` : v) : null;
  const logoOn1 = resolveSrc(settings.logo_on_1 || settings.logo_on);
  const logoOn2 = resolveSrc(settings.logo_on_2 || settings.logo_on);
  const brandName = tt(settings.brand_name) || 'Legacy';
  const settingsLoaded = !!settings.brand_name || !!settings.id;

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Detect if page has a hero section
  useEffect(() => {
    const check = () => {
      const hero = document.querySelector('[data-testid="hero-section"]');
      setHasHero(!!hero);
    };
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [location.pathname]);

  if (isAdmin) return null;

  // If no hero, always show solid background
  const showSolid = scrolled || !hasHero;
  const textColor = showSolid ? 'var(--color-heading-color, #1a2332)' : '#ffffff';

  return (
    <>
      <header className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${showSolid ? 'shadow-lg' : ''}`}
        style={{ backgroundColor: showSolid ? 'var(--color-navbar-bg, rgba(255,255,255,0.95))' : 'transparent', backdropFilter: showSolid ? 'blur(20px)' : 'none' }}
        data-testid="main-navbar">
        <div className="max-w-7xl mx-auto px-6 md:px-10 flex items-center justify-between h-20">
          <Link to="/" className="flex items-center gap-3" data-testid="brand-logo">
            {(() => {
              const currentLogo = showSolid ? logoOn2 : logoOn1;
              if (currentLogo) return <img src={currentLogo} alt={brandName} className="h-10 w-auto object-contain" data-testid="navbar-logo-img" />;
              if (!settingsLoaded) return <div className="h-10 w-28" />;
              return (
                <>
                  <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}>
                    <span className="text-white font-bold text-base" style={{ fontFamily: 'Playfair Display, serif' }}>{brandName[0]}</span>
                  </div>
                  <span className="text-xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: textColor }}>{brandName}</span>
                </>
              );
            })()}
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            {headerPages.map(page => {
              const href = isExternal(page.url) ? page.url : (page.url || `/page/${page.id}`);
              const isExt = isExternal(page.url);
              const Comp = isExt ? 'a' : Link;
              const props = isExt ? { href, target: page.open_in_new_tab ? '_blank' : '_self', rel: 'noreferrer' } : { to: href, onClick: e => handlePageClick(page, e) };
              return <Comp key={page.id} {...props} className="text-sm font-medium tracking-wide uppercase transition-colors hover:opacity-70" style={{ color: location.pathname === href ? 'var(--color-accent, #0D9488)' : textColor, letterSpacing: '0.1em' }} data-testid={`nav-${page.title.toLowerCase().replace(/\s/g, '-')}`}>{page.title}</Comp>;
            })}
          </nav>
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-2">
                {hasMyAccount && <Link to="/my-account/membership-profile" className="text-xs font-medium px-3 py-1.5 rounded-full hover:opacity-80" style={{ color: textColor }} data-testid="nav-my-account">My Account</Link>}
                {hasCmsAccess && <Link to="/admin" className="text-xs font-medium px-3 py-1.5 rounded-full" style={{ backgroundColor: 'var(--color-accent, #0D9488)', color: '#fff' }} data-testid="nav-admin-btn">Admin</Link>}
                <button onClick={logout} className="p-2 hover:opacity-70" style={{ color: textColor }}><LogOut className="w-4 h-4" /></button>
              </div>
            ) : (
              <button onClick={() => setLoginOpen(true)} className="text-sm font-medium px-5 py-2.5 rounded-full flex items-center gap-2 transition-colors" style={{ backgroundColor: 'var(--color-accent, #0D9488)', color: '#ffffff' }} data-testid="login-btn"><LogIn className="w-3.5 h-3.5" /> Login</button>
            )}
            <LanguageSwitcher dark={!showSolid} />
            <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2" style={{ color: textColor }}>
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        {mobileOpen && (
          <div className="md:hidden px-6 py-4 space-y-3 bg-white shadow-lg">
            {headerPages.map(page => {
              const href = page.url || `/page/${page.id}`;
              return <Link key={page.id} to={href} onClick={() => setMobileOpen(false)} className="block text-sm font-medium" style={{ color: 'var(--color-heading-color, #1a2332)' }}>{page.title}</Link>;
            })}
            {hasMyAccount && <Link to="/my-account/membership-profile" onClick={() => setMobileOpen(false)} className="block text-sm font-medium" style={{ color: 'var(--color-accent, #0D9488)' }}>My Account</Link>}
          </div>
        )}
      </header>
      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}

function ClassicNavbar() {
  const tt = useT();
  const { user, logout, settings, socialLinks, headerPages, handlePageClick, isExternal, isAdmin, location, loginOpen, setLoginOpen, hasCmsAccess, hasMyAccount } = useNavData();
  const [mobileOpen, setMobileOpen] = useState(false);
  const API = process.env.REACT_APP_BACKEND_URL;
  const resolveSrc = (v) => v ? (v.startsWith('/api') ? `${API}${v}` : v) : null;
  const logoSrc = resolveSrc(settings.logo_on_2 || settings.logo_on_1 || settings.logo_on);
  const brandName = tt(settings.brand_name) || 'Legacy';
  const tagline = tt(settings.tagline) || 'Consulting';
  const settingsLoaded = !!settings.brand_name || !!settings.id;

  if (isAdmin) return null;

  return (
    <>
      {/* Accent top line */}
      <div className="h-1" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
      {/* Top info bar */}
      <div className="py-2 text-xs" style={{ backgroundColor: '#faf9f6', borderBottom: '1px solid #e8e4de' }}>
        <div className="max-w-6xl mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center gap-4">
            {socialLinks.map(link => {
              const IconComp = socialIconMap[link.icon] || Facebook;
              return <a key={link.id} href={link.url} target="_blank" rel="noreferrer" className="hover:opacity-70 transition-colors" style={{ color: 'var(--color-primary, #1a2332)' }}><IconComp className="w-3.5 h-3.5" /></a>;
            })}
          </div>
          <div>
            {user ? (
              <div className="flex items-center gap-3">
                {hasMyAccount && <Link to="/my-account/membership-profile" className="font-medium hover:opacity-70" style={{ color: 'var(--color-primary, #1a2332)' }} data-testid="nav-my-account">My Account</Link>}
                {hasCmsAccess && <Link to="/admin" className="font-medium" style={{ color: 'var(--color-accent, #0D9488)' }} data-testid="nav-admin-btn">Admin Panel</Link>}
                <button onClick={logout} className="flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-primary, #1a2332)' }}><LogOut className="w-3 h-3" /> Logout</button>
              </div>
            ) : (
              <button onClick={() => setLoginOpen(true)} className="font-medium flex items-center gap-1" style={{ color: 'var(--color-primary, #1a2332)' }} data-testid="login-btn"><LogIn className="w-3 h-3" /> Login</button>
            )}
          </div>
        </div>
      </div>
      {/* Main header */}
      <header className="sticky top-0 z-50 shadow-sm" style={{ backgroundColor: '#faf9f6', borderBottom: '2px solid var(--color-primary, #1a2332)' }} data-testid="main-navbar">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3" data-testid="brand-logo">
            {logoSrc ? (
              <img src={logoSrc} alt={brandName} className="h-9 w-auto object-contain" data-testid="navbar-logo-img" />
            ) : settingsLoaded ? (
              <>
                <div className="w-9 h-9 rounded-none flex items-center justify-center border-2" style={{ borderColor: 'var(--color-primary, #1a2332)', backgroundColor: 'var(--color-primary, #1a2332)' }}>
                  <span className="text-white font-bold text-sm" style={{ fontFamily: "'Playfair Display', serif" }}>{brandName[0]}</span>
                </div>
                <div>
                  <span className="text-lg font-bold block leading-tight" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading-color, #1a2332)' }}>{brandName}</span>
                  <span className="text-[9px] uppercase tracking-[0.2em]" style={{ color: 'var(--color-accent, #0D9488)' }}>{tagline}</span>
                </div>
              </>
            ) : <div className="h-9 w-28" />}
          </Link>
          <nav className="hidden md:flex items-center gap-1">
            {headerPages.map(page => {
              const href = isExternal(page.url) ? page.url : (page.url || `/page/${page.id}`);
              const isExt = isExternal(page.url);
              const Comp = isExt ? 'a' : Link;
              const props = isExt ? { href, target: page.open_in_new_tab ? '_blank' : '_self', rel: 'noreferrer' } : { to: href, onClick: e => handlePageClick(page, e) };
              return <Comp key={page.id} {...props} className="text-sm font-medium px-4 py-2 transition-colors" style={{ color: location.pathname === href ? 'var(--color-accent, #0D9488)' : 'var(--color-heading-color, #1a2332)', borderBottom: location.pathname === href ? '2px solid var(--color-accent, #0D9488)' : '2px solid transparent', fontFamily: "'Playfair Display', serif" }} data-testid={`nav-${page.title.toLowerCase().replace(/\s/g, '-')}`}>{page.title}</Comp>;
            })}
          </nav>
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2" style={{ color: 'var(--color-heading-color, #1a2332)' }}>
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
        {mobileOpen && (
          <div className="md:hidden px-6 py-4 space-y-3" style={{ backgroundColor: '#faf9f6', borderTop: '1px solid #e8e4de' }}>
            {headerPages.map(page => {
              const href = page.url || `/page/${page.id}`;
              return <Link key={page.id} to={href} onClick={() => setMobileOpen(false)} className="block text-sm font-medium py-1" style={{ color: 'var(--color-heading-color, #1a2332)', fontFamily: "'Playfair Display', serif" }}>{page.title}</Link>;
            })}
            {hasMyAccount && <Link to="/my-account/membership-profile" onClick={() => setMobileOpen(false)} className="block text-sm font-medium py-1" style={{ color: 'var(--color-accent, #0D9488)', fontFamily: "'Playfair Display', serif" }}>My Account</Link>}
          </div>
        )}
      </header>
      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}
