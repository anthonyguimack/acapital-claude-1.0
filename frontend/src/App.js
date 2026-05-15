import React, { useRef, useEffect, useState, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import { MemberProvider, useMember } from './lib/memberAuth';
import { authAPI, publicAPI } from './lib/api';
import { Toaster } from 'sonner';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import LoginModal from './components/LoginModal';
import HomePage from './pages/HomePage';
import NewsPage from './pages/NewsPage';
import NewsDetailPage from './pages/NewsDetailPage';
import ReadingListPage from './pages/ReadingListPage';
import GalleryPage from './pages/GalleryPage';
import MapDetailPage from './pages/MapDetailPage';
import CheckoutSuccess from './pages/CheckoutSuccess';
import FeaturedProjectsPage from './pages/FeaturedProjectsPage';
import ConferencesPage, { RecommendedSitesPage } from './pages/MapTypePage';
import DynamicPage from './pages/DynamicPage';
import ServiceDetailPage from './pages/ServiceDetailPage';
import LayoutSubGallery from './components/layouts/LayoutSubGallery';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/Dashboard';
import HeroManager from './pages/admin/HeroManager';
import HeroSlideForm from './pages/admin/HeroSlideForm';
import HeroAbAnalytics from './pages/admin/HeroAbAnalytics';
import AboutManager from './pages/admin/AboutManager';
import ServicesManager from './pages/admin/ServicesManager';
import BlogManager from './pages/admin/BlogManager';
import BooksManager from './pages/admin/BooksManager';
import MapsManager from './pages/admin/MapsManager';
import GalleryManager from './pages/admin/GalleryManager';
import GalleryAlbumsManager from './pages/admin/GalleryAlbumsManager';
import PortfolioManager from './pages/admin/PortfolioManager';
import TestimonialsManager from './pages/admin/TestimonialsManager';
import ContactsManager from './pages/admin/ContactsManager';
import PurchasesManager from './pages/admin/PurchasesManager';
import SettingsManager from './pages/admin/SettingsManager';
import EmailManagement from './pages/admin/EmailManagement';
import PagesManager from './pages/admin/PagesManager';
import UsersManager from './pages/admin/UsersManager';
import AnalyticsDashboard from './pages/admin/AnalyticsDashboard';
import SeoManager from './pages/admin/SeoManager';
import SectionOrderManager from './pages/admin/SectionOrderManager';
import MembersManager from './pages/admin/MembersManager';
import MemberLevelsManager from './pages/admin/MemberLevelsManager';
import MemberTypesManager from './pages/admin/MemberTypesManager';
import MembershipSettingsManager from './pages/admin/MembershipSettingsManager';
import BackupManager from './pages/admin/BackupManager';
import ContactSettingsManager from './pages/admin/ContactSettingsManager';
import LandingContentManager from './pages/admin/LandingContentManager';
import LandingSubscribersManager from './pages/admin/LandingSubscribersManager';
import LandingContactsManager from './pages/admin/LandingContactsManager';
import LandingHeroManager from './pages/admin/LandingHeroManager';
import LandingHeroSlideForm from './pages/admin/LandingHeroSlideForm';
import AdminLoginPage from './pages/admin/AdminLoginPage';
// Membership / My Account
import MemberLogin from './pages/myaccount/MemberLogin';
import MemberRegister from './pages/myaccount/MemberRegister';
import MemberForgotPassword from './pages/myaccount/MemberForgotPassword';
import MemberResetPassword from './pages/myaccount/MemberResetPassword';
import MyAccountLayout from './pages/myaccount/MyAccountLayout';
import MembershipProfile from './pages/myaccount/MembershipProfile';
import MentorshipProfile from './pages/myaccount/MentorshipProfile';
import MySponsor from './pages/myaccount/MySponsor';
import InviteCode from './pages/myaccount/InviteCode';
import MyCommunity from './pages/myaccount/MyCommunity';
import MyEbank from './pages/myaccount/MyEbank';
import PortfolioList from './pages/myaccount/PortfolioList';
import PortfolioDetail from './pages/myaccount/PortfolioDetail';
import PortfolioForm from './pages/myaccount/PortfolioForm';
import GlobalCalendar from './pages/myaccount/GlobalCalendar';
import MentorshipCalendar from './pages/myaccount/MentorshipCalendar';
import MentorCalendarView from './pages/myaccount/MentorCalendarView';
import MyBookings from './pages/myaccount/MyBookings';
import CalendarSync from './pages/myaccount/CalendarSync';
import MentorshipCheckoutSuccess from './pages/myaccount/MentorshipCheckoutSuccess';
import MentorEarnings from './pages/myaccount/MentorEarnings';
import BundlesBrowse from './pages/myaccount/BundlesBrowse';
import BundleDetail from './pages/myaccount/BundleDetail';
import BundleCheckoutSuccess from './pages/myaccount/BundleCheckoutSuccess';
import AdminBundlesManager from './pages/admin/AdminBundlesManager';
import AdminPayoutsManager from './pages/admin/AdminPayoutsManager';
import AdminCouponsManager from './pages/admin/AdminCouponsManager';
import AurexSectionsManager from './pages/admin/AurexSectionsManager';
import EventDetail from './pages/myaccount/EventDetail';

import LandingPage from './pages/LandingPage';
import MembershipEnrollment from './pages/MembershipEnrollment';
import EnrollmentFieldsManager from './pages/admin/EnrollmentFieldsManager';
import GeoManager from './pages/admin/GeoManager';
import DocumentationManager from './pages/admin/DocumentationManager';
import QuickLinksManager from './pages/admin/QuickLinksManager';
import MyAccountNavManager from './pages/admin/MyAccountNavManager';
import GlobalEventsManager from './pages/admin/GlobalEventsManager';
import MentorshipScheduleManager from './pages/admin/MentorshipScheduleManager';
import MentorSlotTemplatesManager from './pages/admin/MentorSlotTemplatesManager';
import BlockedDatesManager from './pages/admin/BlockedDatesManager';
import RolesManager from './pages/admin/RolesManager';
import CmsWelcome from './pages/admin/CmsWelcome';
import { CmsSectionGuard } from './pages/admin/Forbidden';

import { injectThemeColors } from './lib/themeColors';
import { LanguageProvider } from './lib/i18n';
import { t as i18nT } from './lib/i18n';
import BackToTop from './components/BackToTop';

// Global settings context for colors and theme
export const SettingsContext = createContext({});
export const useSettings = () => useContext(SettingsContext);

export const ThemeContext = createContext('default');
export const useTheme = () => useContext(ThemeContext);

function SettingsProvider({ children }) {
  const [settings, setSettings] = useState({ _loaded: false });
  useEffect(() => {
    publicAPI.getSettings()
      .then(r => setSettings({ ...(r.data || {}), _loaded: true }))
      .catch(() => setSettings({ _loaded: true }));
  }, []);

  // Apply CSS variables from theme_colors (new) and colors (legacy)
  useEffect(() => {
    const themeColors = settings.theme_colors || {};
    // Migrate legacy colors.* into website group if theme_colors.website is empty
    if (!themeColors.website && settings.colors) {
      themeColors.website = settings.colors;
    }
    injectThemeColors(themeColors, { my_account_color_scheme: settings.my_account_color_scheme });
  }, [settings.theme_colors, settings.colors, settings.my_account_color_scheme]);

  // Dynamic favicon
  useEffect(() => {
    const faviconUrl = settings.favicon;
    if (!faviconUrl) return;
    const src = faviconUrl.startsWith('/api') ? `${process.env.REACT_APP_BACKEND_URL}${faviconUrl}` : faviconUrl;
    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
    }
    link.href = src;
  }, [settings.favicon]);

  // Dynamic page title from tagline — pick the admin's default language
  // (multi-language tab update is not critical here; fresh load always gets
  // the right one).
  useEffect(() => {
    const lang = localStorage.getItem('aurex_locale') || settings.default_language || 'en';
    const tagline = i18nT(settings.tagline, lang);
    const brand = i18nT(settings.brand_name, lang);
    if (tagline) {
      document.title = tagline;
    } else if (brand) {
      document.title = brand;
    }
  }, [settings.tagline, settings.brand_name, settings.default_language]);

  const activeTheme = settings.active_theme || 'default';

  return (
    <SettingsContext.Provider value={settings}>
      <ThemeContext.Provider value={activeTheme}>
        <LanguageProvider settings={settings}>
          {children}
        </LanguageProvider>
      </ThemeContext.Provider>
    </SettingsContext.Provider>
  );
}

function AuthCallback() {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();
  const { setUserData } = useAuth();
  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;
    const hash = window.location.hash;
    const sessionId = new URLSearchParams(hash.substring(1)).get('session_id');
    if (!sessionId) { navigate('/'); return; }
    (async () => {
      try {
        const res = await authAPI.exchangeSession(sessionId);
        setUserData(res.data);
        navigate('/', { replace: true });
      } catch { navigate('/', { replace: true }); }
    })();
  }, [navigate, setUserData]);
  return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-[var(--color-accent,#0D9488)] border-t-transparent rounded-full"></div></div>;
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-[var(--color-accent,#0D9488)] border-t-transparent rounded-full"></div></div>;
  // Admins pass immediately. Operators need at least one CMS permission.
  if (!user) return <Navigate to="/admin/login" replace />;
  const hasAnyCmsAccess = user.role === 'admin' || ((user.effective_permissions || []).length > 0);
  if (!hasAnyCmsAccess) return <Navigate to="/admin/login" replace />;
  return children;
}

/* Single source of truth for every /admin sub-route.
 *   `section` maps the route to a CMS Section Registry key; CmsSectionGuard
 *   renders a 403 panel (inside AdminLayout) for operators without the perm.
 *   `adminOnly` locks a route to accounts with `role: "admin"` regardless of
 *   their granted CMS permissions (currently only Roles & Permissions and the
 *   legacy Users manager). */
/* Admin index route picker.
 *   Admin and operators with the `dashboard` permission see the full dashboard;
 *   operators without it land on the CMS Welcome page (greeting + admin-managed
 *   rich-text from Settings → General → CMS Welcome). This guarantees every
 *   logged-in CMS user lands on a meaningful screen, not on a 403. */
function AdminIndexRouter() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const perms = user?.effective_permissions || [];
  const canSeeDashboard = isAdmin || perms.includes('dashboard');
  return canSeeDashboard ? <AdminDashboard /> : <CmsWelcome />;
}

const ADMIN_ROUTES = [
  { index: true, el: <AdminIndexRouter /> },
  { path: 'hero',                            section: 'hero',                             el: <HeroManager /> },
  { path: 'hero/add',                        section: 'hero',                             el: <HeroSlideForm /> },
  { path: 'hero/edit/:id',                   section: 'hero',                             el: <HeroSlideForm /> },
  { path: 'hero-ab',                         section: 'hero_ab',                          el: <HeroAbAnalytics /> },
  { path: 'about',                           section: 'about',                            el: <AboutManager /> },
  { path: 'services',                        section: 'services',                         el: <ServicesManager /> },
  { path: 'blog',                            section: 'blog',                             el: <BlogManager /> },
  { path: 'books',                           section: 'books',                            el: <BooksManager /> },
  { path: 'maps',                            section: 'maps',                             el: <MapsManager /> },
  { path: 'gallery',                         section: 'gallery',                          el: <GalleryManager /> },
  { path: 'gallery-albums',                  section: 'gallery_albums',                   el: <GalleryAlbumsManager /> },
  { path: 'portfolio',                       section: 'portfolio',                        el: <PortfolioManager /> },
  { path: 'testimonials',                    section: 'testimonials',                     el: <TestimonialsManager /> },
  { path: 'contacts',                        section: 'contacts',                         el: <ContactsManager /> },
  { path: 'contact-settings',                section: 'contact_settings',                 el: <ContactSettingsManager /> },
  { path: 'purchases',                       section: 'purchases',                        el: <PurchasesManager /> },
  { path: 'settings',                        section: 'settings',                         el: <SettingsManager /> },
  { path: 'email-management',                section: 'email_management',                 el: <EmailManagement /> },
  { path: 'pages',                           section: 'pages',                            el: <PagesManager /> },
  { path: 'users',                           adminOnly: true,                             el: <UsersManager /> },
  { path: 'members',                         section: 'members',                          el: <MembersManager /> },
  { path: 'member-levels',                   section: 'member_levels',                    el: <MemberLevelsManager /> },
  { path: 'member-types',                    section: 'member_types',                     el: <MemberTypesManager /> },
  { path: 'membership-settings',             section: 'membership_settings',              el: <MembershipSettingsManager /> },
  { path: 'analytics',                       section: 'analytics',                        el: <AnalyticsDashboard /> },
  { path: 'seo',                             section: 'seo',                              el: <SeoManager /> },
  { path: 'backup',                          section: 'backup',                           el: <BackupManager /> },
  { path: 'section-order',                   section: 'section_order',                    el: <SectionOrderManager /> },
  { path: 'aurex-sections',                  section: 'aurex_sections',                   el: <AurexSectionsManager /> },
  { path: 'landing-content',                 section: 'landing_content',                  el: <LandingContentManager /> },
  { path: 'landing-hero',                    section: 'landing_hero',                     el: <LandingHeroManager /> },
  { path: 'landing-hero/add',                section: 'landing_hero',                     el: <LandingHeroSlideForm /> },
  { path: 'landing-hero/edit/:id',           section: 'landing_hero',                     el: <LandingHeroSlideForm /> },
  { path: 'landing-subscribers',             section: 'landing_subscribers',              el: <LandingSubscribersManager /> },
  { path: 'landing-contacts',                section: 'landing_contacts',                 el: <LandingContactsManager /> },
  { path: 'enrollment-fields',               section: 'enrollment_fields',                el: <EnrollmentFieldsManager /> },
  { path: 'documentation',                   section: 'documentation',                    el: <DocumentationManager /> },
  { path: 'quick-links',                     section: 'quick_links',                      el: <QuickLinksManager /> },
  { path: 'myaccount-nav',                   section: 'myaccount_nav',                    el: <MyAccountNavManager /> },
  { path: 'calendar/global',                 section: 'calendar_global',                  el: <GlobalEventsManager /> },
  { path: 'calendar/mentorship',             section: 'calendar_mentorship',              el: <MentorshipScheduleManager /> },
  { path: 'calendar/mentor-slot-templates',  section: 'calendar_mentor_slot_templates',   el: <MentorSlotTemplatesManager /> },
  { path: 'calendar/blocked-dates',          section: 'calendar_blocked_dates',           el: <BlockedDatesManager /> },
  { path: 'calendar/bundles',                section: 'calendar_bundles',                 el: <AdminBundlesManager /> },
  { path: 'calendar/coupons',                section: 'calendar_coupons',                 el: <AdminCouponsManager /> },
  { path: 'payouts',                         section: 'payouts',                          el: <AdminPayoutsManager /> },
  { path: 'geo',                             section: 'geo',                              el: <GeoManager /> },
  { path: 'roles',                           adminOnly: true,                             el: <RolesManager /> },
];

function renderAdminRoutes() {
  return ADMIN_ROUTES.map(r => {
    const el = r.adminOnly
      ? <AdminOnlyRoute>{r.el}</AdminOnlyRoute>
      : (r.section ? <CmsSectionGuard section={r.section}>{r.el}</CmsSectionGuard> : r.el);
    return r.index
      ? <Route key="index" index element={el} />
      : <Route key={r.path} path={r.path} element={el} />;
  });
}

function AdminOnlyRoute({ children }) {
  const { user } = useAuth();
  if (user?.role !== 'admin') return <CmsSectionGuard section="__admin_only__">{children}</CmsSectionGuard>;
  return children;
}

function PageProtectedRoute({ children }) {
  const { user, loading: authLoading } = useAuth();
  const { member, loading: memberLoading } = useMember();
  const location = useLocation();
  const [pageData, setPageData] = useState(null);
  const [checking, setChecking] = useState(true);
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    publicAPI.getNavPages().then(r => {
      const pages = r.data || [];
      const path = location.pathname;
      const found = pages.find(p => p.url === path || `/page/${p.id}` === path);
      setPageData(found || null);
      setChecking(false);
    }).catch(() => setChecking(false));
  }, [location.pathname]);

  if (checking || authLoading || memberLoading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-[var(--color-accent,#0D9488)] border-t-transparent rounded-full"></div></div>;

  // If page requires login
  if (pageData?.login_required) {
    // Admin bypasses all restrictions
    if (user?.role === 'admin') return children;

    // If member is logged in, check their type's allowed_pages
    if (member) {
      const allowedPages = member._member_type?.allowed_pages || [];
      const pageId = pageData.id;
      if (allowedPages.length > 0 && !allowedPages.includes(pageId)) {
        return (
          <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <div className="text-center max-w-md mx-auto px-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }}>
                <span className="text-white text-2xl" style={{ fontFamily: 'Playfair Display, serif' }}>L</span>
              </div>
              <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-heading, #1a2332)', fontFamily: 'Playfair Display, serif' }}>Access Restricted</h2>
              <p className="text-slate-500 text-sm mb-6">Your membership type does not include access to this page.</p>
            </div>
          </div>
        );
      }
      return children;
    }

    // Not logged in at all — show login prompt
    if (!user && !member) {
      return (
        <>
          <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <div className="text-center max-w-md mx-auto px-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }}>
                <span className="text-white text-2xl" style={{ fontFamily: 'Playfair Display, serif' }}>L</span>
              </div>
              <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-heading, #1a2332)', fontFamily: 'Playfair Display, serif' }}>Login Required</h2>
              <p className="text-slate-500 text-sm mb-6">You need to be logged in to access this page.</p>
              <button onClick={() => setShowLogin(true)} className="px-6 py-2.5 rounded-sm text-sm font-medium" style={{ backgroundColor: 'var(--color-button-bg, #1a2332)', color: 'var(--color-button-text, #fff)' }} data-testid="page-login-btn">
                Login to Continue
              </button>
            </div>
          </div>
          <LoginModal open={showLogin} onClose={() => setShowLogin(false)} />
        </>
      );
    }
  }

  return children;
}

function MemberRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#0d0f14]"><div className="animate-spin w-8 h-8 border-2 border-[#c9a84c] border-t-transparent rounded-full" /></div>;
  if (!user) return <Navigate to="/my-account/login" replace />;
  // My Account access gate — admins always pass; everyone else must hold
  // role_member.  If an admin revokes role_member from this user, the very
  // next render bounces them back to the login screen.
  const allowedAccess = user.role === 'admin' || (user.cms_roles || []).includes('role_member');
  if (!allowedAccess) return <Navigate to="/my-account/login" replace />;
  return children;
}

// Maps system page URLs to their hero page identifiers
const SYSTEM_PAGE_MAP = {
  '/news': 'news',
  '/gallery': 'gallery',
  '/reading-list': 'reading-list',
};

function SystemPageHero() {
  const location = useLocation();
  const [heroSlides, setHeroSlides] = useState([]);
  const pageId = SYSTEM_PAGE_MAP[location.pathname];

  useEffect(() => {
    if (!pageId) { setHeroSlides([]); return; }
    publicAPI.getHeroSlides(pageId).then(r => setHeroSlides(r.data || [])).catch(() => setHeroSlides([]));
  }, [pageId]);

  if (heroSlides.length === 0) return null;

  // Lazy-load HeroSection to avoid circular import issues
  const HeroSection = require('./components/HeroSection').default;
  return <HeroSection slides={heroSlides} />;
}

function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const id = hash.substring(1);
      const tryScroll = (attempts) => {
        const el = document.getElementById(id);
        if (el) { el.scrollIntoView({ behavior: 'smooth' }); }
        else if (attempts > 0) { setTimeout(() => tryScroll(attempts - 1), 200); }
      };
      setTimeout(() => tryScroll(5), 100);
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname, hash]);
  return null;
}

function useLandingActive(settings) {
  const [active, setActive] = useState(false);
  useEffect(() => {
    if (!settings.landing_page_enabled) { setActive(false); return; }
    const check = () => {
      if (!settings.landing_page_launch_date) { setActive(true); return; }
      const launch = new Date(settings.landing_page_launch_date).getTime();
      setActive(Date.now() < launch);
    };
    check();
    const id = setInterval(check, 1000);
    return () => clearInterval(id);
  }, [settings.landing_page_enabled, settings.landing_page_launch_date]);
  return active;
}

function AppRouter() {
  const location = useLocation();
  const settings = useSettings();
  const landingActive = useLandingActive(settings);

  // Show nothing until settings are loaded (prevents flash of main site before landing page)
  if (!settings._loaded) {
    return <div className="min-h-screen" style={{ backgroundColor: '#0a0a12' }} />;
  }

  if (location.hash?.includes('session_id=')) return <AuthCallback />;

  const isMemberArea = location.pathname.startsWith('/my-account');
  const isAdmin = location.pathname.startsWith('/admin');

  if (isMemberArea) {
    return (
      <Routes>
        <Route path="/my-account/login" element={<MemberLogin />} />
        <Route path="/my-account/register" element={<MemberRegister />} />
        <Route path="/my-account/forgot-password" element={<MemberForgotPassword />} />
        <Route path="/my-account/reset-password" element={<MemberResetPassword />} />
        <Route path="/my-account" element={<MemberRoute><MyAccountLayout /></MemberRoute>}>
          <Route index element={<Navigate to="/my-account/membership-profile" replace />} />
          <Route path="membership-profile" element={<MembershipProfile />} />
          <Route path="mentorship-profile" element={<MentorshipProfile />} />
          <Route path="my-sponsor" element={<MySponsor />} />
          <Route path="invite-code" element={<InviteCode />} />
          <Route path="ebank" element={<MyEbank />} />
          <Route path="my-community" element={<MyCommunity />} />
          <Route path="portfolios" element={<PortfolioList />} />
          <Route path="portfolios/new" element={<PortfolioForm />} />
          <Route path="portfolios/:id" element={<PortfolioDetail />} />
          <Route path="portfolios/:id/edit" element={<PortfolioForm />} />
          <Route path="global-calendar" element={<GlobalCalendar />} />
          <Route path="event/:eventId" element={<EventDetail />} />
          <Route path="mentorship-calendar" element={<MentorshipCalendar />} />
          <Route path="mentor-calendar" element={<MentorCalendarView />} />
          <Route path="my-bookings" element={<MyBookings />} />
          <Route path="calendar-sync" element={<CalendarSync />} />
          <Route path="mentorship/checkout-success" element={<MentorshipCheckoutSuccess />} />
          <Route path="earnings" element={<MentorEarnings />} />
          <Route path="bundles" element={<BundlesBrowse />} />
          <Route path="bundles/checkout-success" element={<BundleCheckoutSuccess />} />
          <Route path="bundles/:id" element={<BundleDetail />} />
        </Route>
      </Routes>
    );
  }

  // Landing page takes over all non-admin, non-my-account routes
  if (landingActive && !isAdmin) {
    return (
      <Routes>
        <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
          {renderAdminRoutes()}
        </Route>
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/membership-enrollment" element={<MembershipEnrollment />} />
        <Route path="*" element={<LandingPage />} />
      </Routes>
    );
  }

  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/membership-enrollment" element={<MembershipEnrollment />} />
        <Route path="*" element={
          <>
            <Navbar />
            <SystemPageHero />
            <Routes>
              <Route path="/" element={<HomePage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/news/:slug" element={<NewsDetailPage />} />
        <Route path="/reading-list" element={<ReadingListPage />} />
        <Route path="/gallery" element={<GalleryPage />} />
        <Route path="/map/:slug" element={<MapDetailPage />} />
        <Route path="/service/:serviceId" element={<ServiceDetailPage />} />
        <Route path="/featured-projects" element={<FeaturedProjectsPage />} />
        <Route path="/conferences" element={<ConferencesPage />} />
        <Route path="/recommended_sites" element={<RecommendedSitesPage />} />
        <Route path="/album/:albumId" element={<LayoutSubGallery />} />
        <Route path="/terms" element={<PageProtectedRoute><DynamicPage /></PageProtectedRoute>} />
        <Route path="/privacy" element={<PageProtectedRoute><DynamicPage /></PageProtectedRoute>} />
        <Route path="/checkout/success" element={<CheckoutSuccess />} />
        <Route path="/page/:pageId" element={<PageProtectedRoute><DynamicPage /></PageProtectedRoute>} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
          {renderAdminRoutes()}
        </Route>
        <Route path="/membership-enrollment" element={<MembershipEnrollment />} />
        {/* Catch-all: custom page URLs like /kls */}
        <Route path="*" element={<PageProtectedRoute><DynamicPage /></PageProtectedRoute>} />
      </Routes>
      <Footer />
      <BackToTop />
    </>
    } />
      </Routes>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SettingsProvider>
          <MemberProvider>
            <AppRouter />
            <Toaster position="top-right" richColors />
          </MemberProvider>
        </SettingsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
