import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { publicAPI, contactAPI, checkoutAPI, blogExternalAPI } from '../lib/api';
import CaptchaWidget from '../components/CaptchaWidget';
import { useSettings, useTheme } from '../App';
import { useAuth } from '../lib/auth';
import { getTileUrl, getTileAttribution } from '../lib/mapConfig';
import { useT } from '../lib/i18n';
import { toast } from 'sonner';
import {
  ArrowRight, Phone, Briefcase, TrendingUp, BarChart3, Monitor, Star,
  MapPin, BookOpen, Send, ChevronRight, Quote, Shield, Clock, ExternalLink, Loader2,
  ChevronLeft, ArrowUpRight
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const iconMap = { 'briefcase': Briefcase, 'trending-up': TrendingUp, 'bar-chart-3': BarChart3, 'monitor': Monitor };
const API = process.env.REACT_APP_BACKEND_URL;
const cleanHtml = (html) => {
  if (html == null) return '';
  const str = typeof html === 'string' ? html : String(html);
  return str
    .replace(/&nbsp;/gi, ' ')
    .replace(/&nbsp\b/gi, ' ')
    .replace(/\u00A0/g, ' ');
};

import HeroSection from '../components/HeroSection';
import {
  AurexAudience, AurexProcess, AurexPricing, AurexTeam, AurexEvents, AurexPartners, AurexClients, AurexVideo, useAurexSections,
  AurexAboutMono, AurexServicesMono, AurexNewsMono, AurexBlogMono, AurexReadingMono,
  AurexMapMono, AurexPortfolioMono, AurexGalleryMono, AurexTestimonialsMono, AurexContactMono,
} from '../components/AurexSections';
import { AUREX_FONTS, isAurexFamily, PERSONALBRAND_DEFAULTS } from '../lib/themeColors';

/* ==================== ABOUT ==================== */
function AboutSection({ data, theme }) {
  const tt = useT();
  if (!data?.title) return null;
  // Apply translation + rich HTML render consistently across all three themes.
  const label = tt(data.label);
  const title = tt(data.title);
  const descriptionHtml = cleanHtml(tt(data.description));
  const signatureName = tt(data.signature_name);
  const signatureTitle = tt(data.signature_title);
  if (theme === 'modern') return (
    <section className="py-24 bg-white" id="about" data-testid="about-section">
      <div className="max-w-7xl mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-16 items-center">
          {data.image && <div className="lg:col-span-2"><img src={data.image?.startsWith('/api') ? `${API}${data.image}` : data.image} alt="" className="w-full rounded-2xl shadow-2xl" /></div>}
          <div className={data.image ? 'lg:col-span-3' : 'lg:col-span-5'}>
            <div className="w-12 h-0.5 mb-6" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
            {label && <p className="text-xs uppercase tracking-[0.3em] font-semibold mb-2" style={{ color: 'var(--color-accent, #0D9488)' }}>{label}</p>}
            <h2 className="text-4xl md:text-5xl font-bold leading-tight mb-6" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="about-title">{title}</h2>
            {descriptionHtml && <div className="text-lg leading-relaxed rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: descriptionHtml }} />}
            {data.phone && <div className="mt-8 flex items-center gap-3"><div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}><Phone className="w-5 h-5 text-white" /></div><div><p className="text-xs text-slate-400">Call us anytime</p><p className="font-semibold" style={{ color: 'var(--color-heading, #1a2332)' }}>{data.phone}</p></div></div>}
          </div>
        </div>
      </div>
    </section>
  );
  if (theme === 'classic') return (
    <section className="py-20 bg-[#faf9f6]" id="about" data-testid="about-section">
      <div className="max-w-6xl mx-auto px-6">
        <div className="border-2 p-10 md:p-16" style={{ borderColor: 'var(--color-primary, #1a2332)' }}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              {label && <p className="text-xs uppercase tracking-[0.3em] font-semibold mb-3" style={{ color: 'var(--color-accent, #0D9488)' }}>{label}</p>}
              <h2 className="text-3xl md:text-4xl font-bold leading-tight mb-6" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="about-title">{title}</h2>
              <div className="w-16 h-0.5 mb-6" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
              {descriptionHtml && <div className="leading-relaxed rich-text-content" style={{ color: 'var(--color-body-text, #475569)', fontFamily: "'Playfair Display', serif" }} dangerouslySetInnerHTML={{ __html: descriptionHtml }} />}
              {signatureName && <p className="mt-6 text-lg italic" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }}>- {signatureName}{signatureTitle ? `, ${signatureTitle}` : ''}</p>}
            </div>
            {data.image && <img src={data.image?.startsWith('/api') ? `${API}${data.image}` : data.image} alt="" className="w-full border-2" style={{ borderColor: 'var(--color-primary, #1a2332)' }} />}
          </div>
        </div>
      </div>
    </section>
  );
  // Default
  return (
    <section className="py-20 md:py-28 bg-white" id="about" data-testid="about-section">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            {label && <p className="text-xs uppercase tracking-[0.3em] font-semibold mb-3" style={{ color: 'var(--color-accent, #0D9488)' }}>{label}</p>}
            <h2 className="text-3xl md:text-4xl font-bold leading-tight" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="about-title">{title}</h2>
            {descriptionHtml && <div className="mt-6 leading-relaxed rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: descriptionHtml }} />}
            <div className="flex items-center gap-6 mt-8">
              {data.phone && <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}><Phone className="w-4 h-4 text-white" /></div><div><p className="text-xs text-slate-400">Call us anytime</p><p className="text-sm font-semibold" style={{ color: 'var(--color-heading, #1a2332)' }}>{data.phone}</p></div></div>}
              {signatureName && <div className="border-l border-slate-200 pl-6"><p className="text-lg italic" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }}>{signatureName}</p>{signatureTitle && <p className="text-xs text-slate-400">{signatureTitle}</p>}</div>}
            </div>
          </div>
          {data.image && <img src={data.image?.startsWith('/api') ? `${API}${data.image}` : data.image} alt="" className="rounded-lg shadow-lg" />}
        </div>
      </div>
    </section>
  );
}

/* ==================== SERVICES ==================== */
function ServicesSection({ services, theme }) {
  const tt = useT();
  if (!services?.length) return null;
  const handleCheckout = async (s) => {
    if (!s.stripe_price_id) { toast.info('No pricing configured'); return; }
    try { const r = await checkoutAPI.create({ price_id: s.stripe_price_id, service_name: s.title, amount: s.price }); if (r.data.url) window.location.href = r.data.url; } catch { toast.error('Checkout error'); }
  };

  const ServiceLink = ({ s }) => {
    const linkCls = "inline-flex items-center gap-1 text-sm font-medium hover:gap-2 transition-all";
    if (s.external_url) {
      return <a href={s.external_url} target={s.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className={linkCls} style={{ color: 'var(--color-accent, #0D9488)' }} data-testid={`service-link-${s.id}`}>Read More <ArrowRight className="w-3.5 h-3.5" /></a>;
    }
    return <Link to={`/service/${s.id}`} className={linkCls} style={{ color: 'var(--color-accent, #0D9488)' }} data-testid={`service-link-${s.id}`}>Read More <ArrowRight className="w-3.5 h-3.5" /></Link>;
  };

  if (theme === 'modern') return (
    <section className="py-24 bg-slate-50" id="services" data-testid="services-section">
      <div className="max-w-7xl mx-auto px-6 md:px-10">
        <div className="text-center mb-16">
          <div className="w-12 h-0.5 mx-auto mb-6" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
          <h2 className="text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="services-title">Our Services</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map(s => {
            const Icon = iconMap[s.icon] || Briefcase;
            return (
              <div key={s.id} className="bg-white rounded-2xl p-8 hover:shadow-xl transition-all duration-300 group border border-slate-100">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-6 transition-colors group-hover:scale-110" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}><Icon className="w-6 h-6 text-white" /></div>
                <h3 className="text-xl font-bold mb-3" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(s.title)}</h3>
                <div className="text-sm leading-relaxed mb-3 rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: cleanHtml(tt(s.short_description) || tt(s.description)) }} />
                <div className="mb-4"><ServiceLink s={s} /></div>
                {s.price > 0 && <div className="flex items-center justify-between pt-4 border-t border-slate-100"><span className="text-2xl font-bold" style={{ color: 'var(--color-accent, #0D9488)' }}>${s.price}</span><button onClick={() => handleCheckout(s)} className="px-4 py-2 rounded-full text-sm font-medium text-white transition-colors" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}>Get Started</button></div>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );

  if (theme === 'classic') return (
    <section className="py-20 bg-[#faf9f6]" id="services" data-testid="services-section">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="services-title">Our Services</h2>
          <div className="w-20 h-0.5 mx-auto mt-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map(s => {
            const Icon = iconMap[s.icon] || Briefcase;
            return (
              <div key={s.id} className="border-2 p-8 hover:shadow-md transition-all" style={{ borderColor: 'var(--color-primary, #1a2332)', backgroundColor: '#faf9f6' }}>
                <Icon className="w-8 h-8 mb-4" style={{ color: 'var(--color-accent, #0D9488)' }} />
                <h3 className="text-lg font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }}>{tt(s.title)}</h3>
                <div className="w-10 h-0.5 mb-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
                <div className="text-sm leading-relaxed mb-3 rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: cleanHtml(tt(s.short_description) || tt(s.description)) }} />
                <div className="mb-4"><ServiceLink s={s} /></div>
                {s.price > 0 && <div className="flex items-center justify-between"><span className="text-lg font-bold" style={{ color: 'var(--color-heading, #1a2332)' }}>${s.price}</span><button onClick={() => handleCheckout(s)} className="px-4 py-2 text-sm font-medium text-white" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }}>Purchase</button></div>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );

  // Default
  return (
    <section className="py-20 bg-slate-50" id="services" data-testid="services-section">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="text-center mb-14"><p className="text-xs uppercase tracking-[0.3em] font-semibold mb-2" style={{ color: 'var(--color-accent, #0D9488)' }}>What We Offer</p><h2 className="text-3xl md:text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="services-title">Our Services</h2></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map(s => {
            const Icon = iconMap[s.icon] || Briefcase;
            return (
              <div key={s.id} className="bg-white rounded-lg p-8 shadow-sm hover:shadow-md transition-all border border-slate-100 group">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-5" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}><Icon className="w-5 h-5 text-white" /></div>
                <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(s.title)}</h3>
                <div className="text-sm leading-relaxed mb-3 rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: cleanHtml(tt(s.short_description) || tt(s.description)) }} />
                <div className="mb-4"><ServiceLink s={s} /></div>
                {s.price > 0 && <div className="flex items-center justify-between border-t border-slate-100 pt-4"><span className="text-xl font-bold" style={{ color: 'var(--color-accent, #0D9488)' }}>${s.price}</span><button onClick={() => handleCheckout(s)} className="text-sm font-medium px-4 py-2 rounded-sm text-white" style={{ backgroundColor: 'var(--color-button-bg, #1a2332)' }}>Purchase</button></div>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ==================== NEWS ==================== */
function NewsSection({ posts, theme }) {
  const tt = useT();
  if (!posts?.length) return null;
  const bgClass = theme === 'classic' ? 'bg-[#faf9f6]' : 'bg-white';
  const cardStyle = theme === 'modern' ? 'rounded-2xl overflow-hidden shadow-sm hover:shadow-xl' : theme === 'classic' ? 'border-2 overflow-hidden hover:shadow-md' : 'rounded-lg overflow-hidden shadow-sm hover:shadow-md border border-slate-100';
  const borderColor = theme === 'classic' ? 'var(--color-primary, #1a2332)' : undefined;
  return (
    <section className={`py-20 ${bgClass}`} id="news" data-testid="news-section">
      <div className={`${theme === 'classic' ? 'max-w-6xl' : 'max-w-7xl'} mx-auto px-6 ${theme === 'modern' ? 'md:px-10' : 'md:px-12'}`}>
        <div className={`flex items-center justify-between mb-12`}>
          <div>
            {theme === 'modern' && <div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
            <h2 className={`text-3xl ${theme === 'modern' ? 'md:text-4xl' : ''} font-bold`} style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="news-title">Latest News</h2>
            {theme === 'classic' && <div className="w-16 h-0.5 mt-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
          </div>
          <Link to="/news" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }} data-testid="news-view-all"><span>View All</span> <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {posts.slice(0, 3).map(p => (
            <Link to={`/news/${p.slug || p.id}`} key={p.id} className={`bg-white group transition-all ${cardStyle}`} style={borderColor ? { borderColor } : {}}>
              {p.image && <div className="h-48 overflow-hidden"><img src={p.image?.startsWith('/api') ? `${API}${p.image}` : p.image} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" /></div>}
              <div className="p-6">
                <div className="flex items-center gap-2 mb-3"><Clock className="w-3 h-3 text-slate-400" /><span className="text-xs text-slate-400">{new Date(p.created_at).toLocaleDateString()}</span></div>
                <h3 className="font-bold mb-2 group-hover:opacity-70 transition-colors" style={{ color: 'var(--color-heading, #1a2332)', fontFamily: theme === 'classic' ? "'Playfair Display', serif" : undefined }}>{tt(p.title)}</h3>
                <p className="text-sm line-clamp-2" style={{ color: 'var(--color-body-text, #475569)' }}>{(cleanHtml(tt(p.excerpt)) || cleanHtml(tt(p.content)).replace(/<[^>]*>/g, '')).slice(0, 120)}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==================== EXTERNAL BLOG ==================== */
function ExternalBlogSection({ theme }) {
  const settings = useSettings();
  const [posts, setPosts] = useState([]);
  useEffect(() => {
    if (settings.blog_api_url) blogExternalAPI.getLatest().then(r => setPosts(r.data?.posts || [])).catch(() => {});
  }, [settings.blog_api_url]);
  if (!posts.length) return null;
  const bgClass = theme === 'classic' ? 'bg-white' : 'bg-slate-50';
  const cardStyle = theme === 'modern' ? 'rounded-2xl overflow-hidden shadow-sm hover:shadow-xl' : theme === 'classic' ? 'border-2 overflow-hidden hover:shadow-md' : 'rounded-lg overflow-hidden shadow-sm hover:shadow-md border border-slate-100';
  return (
    <section className={`py-20 ${bgClass}`} id="blog" data-testid="blog-section">
      <div className={`${theme === 'classic' ? 'max-w-6xl' : 'max-w-7xl'} mx-auto px-6 ${theme === 'modern' ? 'md:px-10' : 'md:px-12'}`}>
        <div className="flex items-center justify-between mb-12">
          <div>
            {theme === 'modern' && <div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
            <h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="blog-title">Blog</h2>
            {theme === 'classic' && <div className="w-16 h-0.5 mt-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {posts.slice(0, 3).map((p, i) => (
            <a key={i} href={p.url || p.link} target="_blank" rel="noreferrer" className={`bg-white group transition-all ${cardStyle}`} style={theme === 'classic' ? { borderColor: 'var(--color-primary, #1a2332)' } : {}}>
              {p.image && <div className="h-48 overflow-hidden"><img src={p.image} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" /></div>}
              <div className="p-6">
                <h3 className="font-bold mb-2 group-hover:opacity-70 transition-colors flex items-center gap-1" style={{ color: 'var(--color-heading, #1a2332)' }}>{p.title} <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-40" /></h3>
                <p className="text-sm line-clamp-2" style={{ color: 'var(--color-body-text, #475569)' }}>{p.summary || p.excerpt}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==================== READING LIST ==================== */
function ReadingListSection({ books, theme }) {
  const tt = useT();
  if (!books?.length) return null;
  const bgClass = theme === 'classic' ? 'bg-[#faf9f6]' : 'bg-white';
  return (
    <section className={`py-20 ${bgClass}`} id="reading-list" data-testid="reading-section">
      <div className={`${theme === 'classic' ? 'max-w-6xl' : 'max-w-7xl'} mx-auto px-6 ${theme === 'modern' ? 'md:px-10' : 'md:px-12'}`}>
        <div className="flex items-center justify-between mb-12">
          <div>
            {theme === 'modern' && <div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
            <h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="reading-title">Reading List</h2>
            {theme === 'classic' && <div className="w-16 h-0.5 mt-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
          </div>
          <Link to="/reading-list" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }}>View All <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className={`grid gap-6 ${theme === 'modern' ? 'grid-cols-2 md:grid-cols-4 lg:grid-cols-5' : theme === 'classic' ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5'}`}>
          {books.slice(0, theme === 'modern' ? 5 : theme === 'classic' ? 4 : 5).map(b => {
            const coverImg = b.image || b.cover_image;
            const imgSrc = coverImg ? (coverImg.startsWith('/api') ? `${process.env.REACT_APP_BACKEND_URL}${coverImg}` : coverImg) : null;
            return (
            <Link to="/reading-list" key={b.id} className={`group transition-all ${theme === 'modern' ? 'rounded-xl overflow-hidden shadow-sm hover:shadow-lg bg-white' : theme === 'classic' ? 'border-2 overflow-hidden hover:shadow-md bg-white' : 'rounded-lg overflow-hidden shadow-sm hover:shadow-md bg-white'}`} style={theme === 'classic' ? { borderColor: 'var(--color-primary, #1a2332)' } : {}}>
              {imgSrc ? (
                <div className={`${theme === 'modern' ? 'h-56' : 'h-48'} overflow-hidden`}>
                  <img src={imgSrc} alt={b.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                </div>
              ) : (
                <div className={`${theme === 'modern' ? 'h-56' : 'h-48'} flex items-center justify-center`} style={{ backgroundColor: 'var(--color-primary, #1a2332)' }}>
                  <BookOpen className="w-8 h-8 text-white/50" />
                </div>
              )}
              <div className="p-3"><p className="text-sm font-medium truncate" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(b.title)}</p><p className="text-xs text-slate-400 truncate">{tt(b.author)}</p></div>
            </Link>
          );})}
        </div>
      </div>
    </section>
  );
}

/* ==================== MAP ==================== */
function MapSection({ maps, locations, theme, title, mapsLang }) {
  const tt = useT();
  const allLocations = [...(maps || []).filter(m => m.lat && m.lng), ...(locations || []).filter(l => l.lat && l.lng)];
  if (!allLocations.length) return null;
  const center = [allLocations[0].lat, allLocations[0].lng];
  const sectionTitle = tt(title) || 'Our Locations';
  const lang = mapsLang || 'local';
  return (
    <section className={`py-20 ${theme === 'classic' ? 'bg-white' : 'bg-slate-50'}`} id="locations" data-testid="map-section">
      <div className={`${theme === 'classic' ? 'max-w-6xl' : 'max-w-7xl'} mx-auto px-6`}>
        <div className="text-center mb-10">
          {theme === 'modern' && <div className="w-12 h-0.5 mx-auto mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
          <h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="map-title">{sectionTitle}</h2>
          {theme === 'classic' && <div className="w-16 h-0.5 mx-auto mt-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
        </div>
        <div className={`${theme === 'modern' ? 'rounded-2xl' : theme === 'classic' ? 'border-2' : 'rounded-lg'} overflow-hidden shadow-lg h-[400px]`} style={theme === 'classic' ? { borderColor: 'var(--color-primary, #1a2332)' } : {}}>
          <MapContainer center={center} zoom={5} style={{ height: '100%', width: '100%' }}>
            <TileLayer url={getTileUrl(lang)} attribution={getTileAttribution(lang)} />
            <MarkerClusterGroup>
              {allLocations.map((loc, i) => (<Marker key={i} position={[loc.lat, loc.lng]}><Popup><strong>{tt(loc.title) || tt(loc.name)}</strong>{loc.description && <p>{tt(loc.description)}</p>}{loc.link && <a href={loc.link} target={loc.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className="text-blue-500 underline">Visit</a>}</Popup></Marker>))}
            </MarkerClusterGroup>
          </MapContainer>
        </div>
      </div>
    </section>
  );
}

/* ==================== PORTFOLIO ==================== */
function PortfolioSection({ items, theme }) {
  const tt = useT();
  if (!items?.length) return null;
  if (theme === 'modern') return (
    <section className="py-24 bg-white" id="portfolio" data-testid="portfolio-section">
      <div className="max-w-7xl mx-auto px-6 md:px-10">
        <div className="flex items-center justify-between mb-16">
          <div><div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} /><h2 className="text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="portfolio-title">Featured Projects</h2></div>
          <Link to="/featured-projects" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }} data-testid="portfolio-view-all">View All <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {items.slice(0, 4).map(p => (
            <div key={p.id} className="group relative rounded-2xl overflow-hidden shadow-lg">
              {p.image && <img src={p.image?.startsWith('/api') ? `${API}${p.image}` : p.image} alt="" className="w-full h-72 object-cover group-hover:scale-105 transition-transform duration-500" />}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-8">
                <div className="flex-1"><h3 className="text-xl font-bold text-white mb-1">{tt(p.title)}</h3><p className="text-white/70 text-sm">{tt(p.category)}</p></div>
                {p.link && <a href={p.link} target={p.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-white hover:bg-white/30 flex-shrink-0"><ArrowUpRight className="w-4 h-4" /></a>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
  if (theme === 'classic') return (
    <section className="py-20 bg-[#faf9f6]" id="portfolio" data-testid="portfolio-section">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex items-center justify-between mb-14">
          <div><h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="portfolio-title">Featured Projects</h2><div className="w-20 h-0.5 mt-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} /></div>
          <Link to="/featured-projects" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }} data-testid="portfolio-view-all">View All <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {items.slice(0, 4).map(p => (
            <div key={p.id} className="border-2 group overflow-hidden" style={{ borderColor: 'var(--color-primary, #1a2332)' }}>
              {p.image && <div className="h-52 overflow-hidden"><img src={p.image?.startsWith('/api') ? `${API}${p.image}` : p.image} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" /></div>}
              <div className="p-6 bg-[#faf9f6]">
                <h3 className="font-bold mb-1" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }}>{tt(p.title)}</h3>
                <p className="text-xs" style={{ color: 'var(--color-accent, #0D9488)' }}>{tt(p.category)}</p>
                <p className="text-sm mt-2 line-clamp-2" style={{ color: 'var(--color-body-text, #475569)' }}>{tt(p.description)}</p>
                {p.link && <a href={p.link} target={p.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium mt-2 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }}>View Project <ArrowUpRight className="w-3 h-3" /></a>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
  // Default
  return (
    <section className="py-20 bg-white" id="portfolio" data-testid="portfolio-section">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="flex items-center justify-between mb-14">
          <div><p className="text-xs uppercase tracking-[0.3em] font-semibold mb-2" style={{ color: 'var(--color-accent, #0D9488)' }}>Our Work</p><h2 className="text-3xl md:text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="portfolio-title">Featured Projects</h2></div>
          <Link to="/featured-projects" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }} data-testid="portfolio-view-all">View All <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.slice(0, 6).map(p => (
            <div key={p.id} className="bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all border border-slate-100 group">
              {p.image && <div className="h-48 overflow-hidden"><img src={p.image?.startsWith('/api') ? `${API}${p.image}` : p.image} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" /></div>}
              <div className="p-5">
                <h3 className="font-bold mb-1" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(p.title)}</h3>
                <p className="text-xs" style={{ color: 'var(--color-accent, #0D9488)' }}>{tt(p.category)}</p>
                <p className="text-sm mt-2 line-clamp-2" style={{ color: 'var(--color-body-text, #475569)' }}>{tt(p.description)}</p>
                {p.link && <a href={p.link} target={p.open_in_new_tab ? '_blank' : '_self'} rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium mt-2 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }}>View Project <ArrowUpRight className="w-3 h-3" /></a>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==================== GALLERY ==================== */
function GallerySection({ items, theme }) {
  if (!items?.length) return null;
  const gridCls = theme === 'modern' ? 'grid-cols-2 md:grid-cols-3 gap-4' : theme === 'classic' ? 'grid-cols-2 md:grid-cols-4 gap-3' : 'grid-cols-2 md:grid-cols-3 gap-4';
  const imgCls = theme === 'modern' ? 'rounded-xl' : theme === 'classic' ? 'border-2' : 'rounded-lg';
  return (
    <section className={`py-20 ${theme === 'classic' ? 'bg-white' : 'bg-slate-50'}`} id="gallery" data-testid="gallery-section">
      <div className={`${theme === 'classic' ? 'max-w-6xl' : 'max-w-7xl'} mx-auto px-6`}>
        <div className="flex items-center justify-between mb-12">
          <div>
            {theme === 'modern' && <div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
            <h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="gallery-title">Gallery</h2>
            {theme === 'classic' && <div className="w-16 h-0.5 mt-3" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />}
          </div>
          <Link to="/gallery" className="text-sm font-medium flex items-center gap-1 hover:opacity-70" style={{ color: 'var(--color-accent, #0D9488)' }}>View All <ArrowRight className="w-4 h-4" /></Link>
        </div>
        <div className={`grid ${gridCls}`}>
          {items.slice(0, theme === 'classic' ? 8 : 6).map(img => (
            <div key={img.id} className={`group overflow-hidden ${imgCls} shadow-sm hover:shadow-lg transition-all`} style={theme === 'classic' ? { borderColor: 'var(--color-primary, #1a2332)' } : {}}>
              <img src={img.image?.startsWith('/api') ? `${API}${img.image}` : img.image} alt={img.title} className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-500" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==================== TESTIMONIALS ==================== */
function TestimonialsSection({ items, theme }) {
  const tt = useT();
  const [carouselIdx, setCarouselIdx] = useState(0);
  const perPage = 3;
  const totalPages = Math.ceil((items?.length || 0) / perPage);
  if (!items?.length) return null;

  if (theme === 'modern') {
    const visible = items.slice(carouselIdx * perPage, carouselIdx * perPage + perPage);
    return (
      <section className="py-24 bg-white" id="testimonials" data-testid="testimonials-section">
        <div className="max-w-7xl mx-auto px-6 md:px-10">
          <div className="flex items-center justify-between mb-16">
            <div><div className="w-12 h-0.5 mb-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} /><h2 className="text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="testimonials-title">What People Say</h2></div>
            {totalPages > 1 && (
              <div className="flex gap-2" data-testid="testimonials-carousel-arrows">
                <button onClick={() => setCarouselIdx(p => Math.max(0, p - 1))} disabled={carouselIdx === 0} className="w-10 h-10 rounded-full border-2 flex items-center justify-center disabled:opacity-30 transition-colors hover:bg-slate-50" style={{ borderColor: 'var(--color-primary, #1a2332)' }}><ChevronLeft className="w-4 h-4" style={{ color: 'var(--color-heading, #1a2332)' }} /></button>
                <button onClick={() => setCarouselIdx(p => Math.min(totalPages - 1, p + 1))} disabled={carouselIdx >= totalPages - 1} className="w-10 h-10 rounded-full border-2 flex items-center justify-center disabled:opacity-30 transition-colors hover:bg-slate-50" style={{ borderColor: 'var(--color-primary, #1a2332)' }}><ChevronRight className="w-4 h-4" style={{ color: 'var(--color-heading, #1a2332)' }} /></button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {visible.map(t => (
              <div key={t.id} className="bg-slate-50 rounded-2xl p-8 relative">
                <Quote className="w-8 h-8 mb-4 opacity-20" style={{ color: 'var(--color-accent, #0D9488)' }} />
                <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--color-body-text, #475569)' }}>"{tt(t.content)}"</p>
                <div className="flex items-center gap-3">
                  {(t.avatar || t.image) && <img src={(t.avatar || t.image)?.startsWith('/api') ? `${API}${t.avatar || t.image}` : (t.avatar || t.image)} alt="" className="w-12 h-12 rounded-full object-cover" />}
                  <div><p className="font-bold text-sm" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(t.name)}</p><p className="text-xs" style={{ color: 'var(--color-accent, #0D9488)' }}>{tt(t.role) || tt(t.title) || tt(t.company)}</p></div>
                </div>
                <div className="flex gap-0.5 mt-4">{[1,2,3,4,5].map(s => <Star key={s} className="w-3.5 h-3.5" style={{ color: s <= (t.rating || 5) ? '#f59e0b' : '#e2e8f0', fill: s <= (t.rating || 5) ? '#f59e0b' : 'none' }} />)}</div>
              </div>
            ))}
          </div>
          {totalPages > 1 && <div className="flex justify-center gap-2 mt-8">{Array.from({ length: totalPages }).map((_, i) => <button key={i} onClick={() => setCarouselIdx(i)} className="w-2.5 h-2.5 rounded-full transition-colors" style={{ backgroundColor: i === carouselIdx ? 'var(--color-accent, #0D9488)' : '#e2e8f0' }} />)}</div>}
        </div>
      </section>
    );
  }

  if (theme === 'classic') return (
    <section className="py-20 bg-[#faf9f6]" id="testimonials" data-testid="testimonials-section">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-14"><h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="testimonials-title">Testimonials</h2><div className="w-20 h-0.5 mx-auto mt-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} /></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {items.slice(0, 4).map(t => (
            <div key={t.id} className="border-2 p-6 relative" style={{ borderColor: 'var(--color-primary, #1a2332)', backgroundColor: '#faf9f6' }}>
              <div className="absolute -top-4 left-6 w-8 h-8 flex items-center justify-center" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }}><Quote className="w-4 h-4 text-white" /></div>
              <p className="text-sm leading-relaxed mt-4 mb-6" style={{ color: 'var(--color-body-text, #475569)', fontFamily: "'Playfair Display', serif", fontStyle: 'italic' }}>"{tt(t.content)}"</p>
              <div className="border-t pt-4" style={{ borderColor: 'var(--color-primary, #1a2332)' }}>
                <p className="font-bold text-sm" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }}>{tt(t.name)}</p>
                <p className="text-xs" style={{ color: 'var(--color-accent, #0D9488)' }}>{tt(t.role) || tt(t.title) || tt(t.company)}</p>
                <div className="flex gap-0.5 mt-2">{[1,2,3,4,5].map(s => <Star key={s} className="w-3 h-3" style={{ color: s <= (t.rating || 5) ? '#f59e0b' : '#d1d5db', fill: s <= (t.rating || 5) ? '#f59e0b' : 'none' }} />)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );

  // Default
  return (
    <section className="py-20 bg-slate-50" id="testimonials" data-testid="testimonials-section">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="text-center mb-14"><p className="text-xs uppercase tracking-[0.3em] font-semibold mb-2" style={{ color: 'var(--color-accent, #0D9488)' }}>Testimonials</p><h2 className="text-3xl md:text-4xl font-bold" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="testimonials-title">What Our Clients Say</h2></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {items.slice(0, 3).map(t => (
            <div key={t.id} className="bg-white rounded-lg p-8 shadow-sm border border-slate-100">
              <Quote className="w-6 h-6 mb-4 opacity-30" style={{ color: 'var(--color-accent, #0D9488)' }} />
              <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--color-body-text, #475569)' }}>"{tt(t.content)}"</p>
              <div className="flex items-center gap-3">
                {(t.avatar || t.image) && <img src={(t.avatar || t.image)?.startsWith('/api') ? `${API}${t.avatar || t.image}` : (t.avatar || t.image)} alt="" className="w-10 h-10 rounded-full object-cover" />}
                <div><p className="font-bold text-sm" style={{ color: 'var(--color-heading, #1a2332)' }}>{tt(t.name)}</p><p className="text-xs text-slate-400">{tt(t.role) || tt(t.title) || tt(t.company)}</p></div>
              </div>
              <div className="flex gap-0.5 mt-4">{[1,2,3,4,5].map(s => <Star key={s} className="w-3.5 h-3.5" style={{ color: s <= (t.rating || 5) ? '#f59e0b' : '#e2e8f0', fill: s <= (t.rating || 5) ? '#f59e0b' : 'none' }} />)}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==================== CONTACT ==================== */
function ContactSection({ theme, contactSettings }) {
  const tt = useT();
  const cs = contactSettings || {};
  const csTitle = tt(cs.title) || 'Contact';
  const csSubtitle = tt(cs.subtitle) || "Let's Work Together";
  const csDescription = cleanHtml(tt(cs.description) || 'Have a project in mind? Let\'s discuss how we can help');
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [captchaToken, setCaptchaToken] = useState('');
  const [sending, setSending] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    try { await contactAPI.submit({ ...form, captcha_token: captchaToken }); toast.success('Message sent!'); setForm({ name: '', email: '', message: '' }); setCaptchaToken(''); }
    catch (err) { toast.error(err?.response?.data?.detail || 'Failed to send'); }
    finally { setSending(false); }
  };

  if (theme === 'modern') return (
    <section className="py-24 bg-slate-50" id="contact" data-testid="contact-section">
      <div className="max-w-3xl mx-auto px-6 md:px-10 text-center">
        <div className="w-12 h-0.5 mx-auto mb-6" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} />
        <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif', color: 'var(--color-heading, #1a2332)' }} data-testid="contact-title">{csSubtitle}</h2>
        <div className="mb-10 rich-text-content" style={{ color: 'var(--color-body-text, #475569)' }} dangerouslySetInnerHTML={{ __html: csDescription }} />
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-2 gap-4"><input value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} required placeholder="Your Name" className="px-5 py-3.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-[#0D9488]" /><input type="email" value={form.email} onChange={e => setForm(p => ({...p, email: e.target.value}))} required placeholder="Your Email" className="px-5 py-3.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-[#0D9488]" /></div>
          <textarea value={form.message} onChange={e => setForm(p => ({...p, message: e.target.value}))} required placeholder="Your Message" rows={5} className="w-full px-5 py-3.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-[#0D9488]" />
          <div className="flex justify-center"><CaptchaWidget onChange={setCaptchaToken} testId="contact-captcha-modern" /></div>
          <button type="submit" disabled={sending} className="px-8 py-3.5 rounded-full text-white font-medium text-sm flex items-center gap-2 mx-auto disabled:opacity-50" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} data-testid="contact-submit">{sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Send Message</button>
        </form>
      </div>
    </section>
  );

  if (theme === 'classic') return (
    <section className="py-20 bg-white" id="contact" data-testid="contact-section">
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-10"><h2 className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--color-heading, #1a2332)' }} data-testid="contact-title">{csSubtitle}</h2><div className="w-20 h-0.5 mx-auto mt-4" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} /></div>
        <form onSubmit={handleSubmit} className="border-2 p-10" style={{ borderColor: 'var(--color-primary, #1a2332)' }}>
          <div className="grid grid-cols-2 gap-4 mb-4"><input value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} required placeholder="Full Name" className="px-4 py-3 bg-[#faf9f6] border text-sm focus:outline-none" style={{ borderColor: 'var(--color-primary, #1a2332)' }} /><input type="email" value={form.email} onChange={e => setForm(p => ({...p, email: e.target.value}))} required placeholder="Email Address" className="px-4 py-3 bg-[#faf9f6] border text-sm focus:outline-none" style={{ borderColor: 'var(--color-primary, #1a2332)' }} /></div>
          <textarea value={form.message} onChange={e => setForm(p => ({...p, message: e.target.value}))} required placeholder="Your message..." rows={5} className="w-full px-4 py-3 bg-[#faf9f6] border text-sm focus:outline-none mb-4" style={{ borderColor: 'var(--color-primary, #1a2332)' }} />
          <div className="flex justify-center mb-4"><CaptchaWidget onChange={setCaptchaToken} testId="contact-captcha-classic" /></div>
          <button type="submit" disabled={sending} className="px-8 py-3 text-white font-medium text-sm flex items-center gap-2 mx-auto disabled:opacity-50" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }} data-testid="contact-submit">{sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Send Message</button>
        </form>
      </div>
    </section>
  );

  // Default
  return (
    <section className="py-20 relative overflow-hidden" style={{ backgroundColor: 'var(--color-primary, #1a2332)' }} id="contact" data-testid="contact-section">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div><p className="text-xs uppercase tracking-[0.3em] font-semibold mb-3" style={{ color: 'var(--color-accent, #0D9488)' }}>{csTitle}</p><h2 className="text-3xl md:text-4xl font-bold text-white leading-tight" style={{ fontFamily: 'Playfair Display, serif' }} data-testid="contact-title">{csSubtitle}</h2><div className="text-white/60 mt-4 leading-relaxed rich-text-content" dangerouslySetInnerHTML={{ __html: csDescription }} /></div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} required placeholder="Your Name" className="w-full px-5 py-3 bg-white/10 border border-white/20 rounded-sm text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-white/40" />
            <input type="email" value={form.email} onChange={e => setForm(p => ({...p, email: e.target.value}))} required placeholder="Your Email" className="w-full px-5 py-3 bg-white/10 border border-white/20 rounded-sm text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-white/40" />
            <textarea value={form.message} onChange={e => setForm(p => ({...p, message: e.target.value}))} required placeholder="Your Message" rows={4} className="w-full px-5 py-3 bg-white/10 border border-white/20 rounded-sm text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-white/40" />
            <CaptchaWidget onChange={setCaptchaToken} testId="contact-captcha-default" />
            <button type="submit" disabled={sending} className="w-full py-3 text-white font-medium rounded-sm text-sm flex items-center justify-center gap-2 disabled:opacity-50" style={{ backgroundColor: 'var(--color-accent, #0D9488)' }} data-testid="contact-submit">{sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Send Message</button>
          </form>
        </div>
      </div>
    </section>
  );
}

/* ==================== HOME PAGE ==================== */
export default function HomePage() {
  const settings = useSettings();
  const theme = useTheme();
  const { user } = useAuth();
  const [about, setAbout] = useState(null);
  const [services, setServices] = useState([]);
  const [posts, setPosts] = useState([]);
  const [books, setBooks] = useState([]);
  const [maps, setMaps] = useState([]);
  const [locations, setLocations] = useState([]);
  const [locConferences, setLocConferences] = useState([]);
  const [locRecommended, setLocRecommended] = useState([]);
  const [portfolio, setPortfolio] = useState([]);
  const [gallery, setGallery] = useState([]);
  const [testimonials, setTestimonials] = useState([]);
  const [heroSlides, setHeroSlides] = useState([]);

  useEffect(() => {
    publicAPI.getAbout().then(r => setAbout(r.data)).catch(() => {});
    publicAPI.getServices().then(r => setServices(r.data)).catch(() => {});
    publicAPI.getBlog().then(r => setPosts(r.data?.posts || r.data || [])).catch(() => {});
    publicAPI.getBooks().then(r => setBooks(r.data)).catch(() => {});
    publicAPI.getMaps().then(r => setMaps(r.data)).catch(() => {});
    publicAPI.getMapLocations('global_business').then(r => setLocations(r.data)).catch(() => {});
    publicAPI.getMapLocations('conferences').then(r => setLocConferences(r.data)).catch(() => {});
    publicAPI.getMapLocations('recommended_sites').then(r => setLocRecommended(r.data)).catch(() => {});
    publicAPI.getPortfolio().then(r => setPortfolio(r.data)).catch(() => {});
    publicAPI.getGallery().then(r => setGallery(r.data)).catch(() => {});
    publicAPI.getTestimonials().then(r => setTestimonials(r.data)).catch(() => {});
    publicAPI.getHeroSlides().then(r => setHeroSlides(r.data)).catch(() => {});
  }, []);

  const sections = settings.sections || {};
  const activeTheme = settings.active_theme || 'default';
  // Aurex-family themes (Aurex One-page + Personal Brand Pro) all share the
  // same one-page section architecture, just with different default colours
  // and typography.  Treating them as a single render pipeline keeps the
  // section components DRY.
  const isAurex = isAurexFamily(activeTheme);
  const isPersonalBrand = activeTheme === 'personalbrand';

  // Apply Personal Brand Pro warm defaults to :root so the existing Aurex
  // mono components inherit terracotta accents / cream backgrounds without
  // any per-component code changes.  Operator overrides from
  // Settings → Colors → Website continue to win because they're written to
  // :root *after* this effect runs.
  useEffect(() => {
    if (!isPersonalBrand) return;
    const root = document.documentElement;
    const previous = {};
    Object.entries(PERSONALBRAND_DEFAULTS).forEach(([k, v]) => {
      previous[k] = root.style.getPropertyValue(k);
      // Only set if the operator hasn't already overridden it via Settings.
      if (!previous[k]) root.style.setProperty(k, v);
    });
    return () => {
      Object.keys(previous).forEach((k) => {
        if (!previous[k]) root.style.removeProperty(k);
      });
    };
  }, [isPersonalBrand]);
  const aurexData = useAurexSections();
  // Each Aurex-family theme keeps its own section_configs scope so the
  // operator can have separate per-section bg/font choices for each layout.
  const aurexConfigs = (settings.section_configs && settings.section_configs[activeTheme]) || (settings.section_configs && settings.section_configs.aurex) || {};
  const aurexDefaultOrder = ['hero', 'about', 'aurex_audience', 'services', 'aurex_process', 'aurex_video', 'aurex_pricing', 'aurex_team', 'testimonials', 'reading_list', 'aurex_events', 'news', 'blog', 'aurex_partners', 'aurex_clients', 'map', 'contact'];
  const legacyDefault = ['hero', 'about', 'services', 'news', 'blog', 'reading_list', 'locations', 'map_global', 'map_conferences', 'map_recommended', 'portfolio', 'gallery', 'testimonials', 'contact'];
  const perThemeOrder = settings.section_orders && settings.section_orders[activeTheme];
  let sectionOrder = perThemeOrder || settings.section_order || (isAurex ? aurexDefaultOrder : legacyDefault);
  // If Aurex theme is active, append any known Aurex keys that the stored order
  // is missing (can happen after we add new Aurex sections like `aurex_video`
  // without asking the admin to re-save).
  if (isAurex && perThemeOrder) {
    const knownAurexKeys = aurexDefaultOrder.filter(k => k.startsWith('aurex_'));
    const missing = knownAurexKeys.filter(k => !sectionOrder.includes(k));
    if (missing.length) sectionOrder = [...sectionOrder, ...missing];
  }
  const homeSlides = heroSlides.filter(s => !s.assigned_pages || s.assigned_pages.length === 0 || s.assigned_pages.includes('home'));

  const mapsLang = settings.maps_language || 'local';

  // Renders an Aurex section with per-section bg + font pulled from CMS.
  const aurexSection = (key, Comp) => {
    const cfg = aurexConfigs[key] || {};
    const data = aurexData[key] || { config: {}, items: [] };
    const font = cfg.font_family ? (AUREX_FONTS.find(f => f.key === cfg.font_family)?.css) : undefined;
    return <Comp key={key} config={data.config || {}} items={data.items || []} bg={cfg.bg_color} font={font} />;
  };

  // Pulls per-section bg + font for a legacy section rendered in its Aurex mono variant,
  // plus the CMS-editable header/CTA overrides stored under the matching `aurex_<key>_cfg` entry.
  const aurexMono = (key) => {
    const cfg = aurexConfigs[key] || {};
    const font = cfg.font_family ? (AUREX_FONTS.find(f => f.key === cfg.font_family)?.css) : undefined;
    const overrideKey = {
      services: 'aurex_services_cfg',
      testimonials: 'aurex_testimonials_cfg',
      news: 'aurex_news_cfg',
      blog: 'aurex_blog_cfg',
      map: 'aurex_locations_cfg',
      locations: 'aurex_locations_cfg',
      map_global: 'aurex_locations_cfg',
      map_conferences: 'aurex_locations_cfg',
      map_recommended: 'aurex_locations_cfg',
    }[key];
    const override = overrideKey ? (aurexData[overrideKey]?.config || {}) : {};
    return { bg: cfg.bg_color, font, cmsConfig: override };
  };

  const sectionMap = {
    hero: homeSlides.length > 0 ? <HeroSection key="hero" slides={homeSlides} data={homeSlides[0]} /> : null,
    about: isAurex ? <AurexAboutMono key="about" data={about} {...aurexMono('about')} /> : <AboutSection key="about" data={about} theme={theme} />,
    services: isAurex ? <AurexServicesMono key="services" services={services} {...aurexMono('services')} /> : <ServicesSection key="services" services={services} theme={theme} />,
    news: isAurex ? <AurexNewsMono key="news" posts={posts} {...aurexMono('news')} /> : <NewsSection key="news" posts={posts} theme={theme} />,
    blog: isAurex ? <AurexBlogMono key="blog" {...aurexMono('blog')} /> : <ExternalBlogSection key="blog" theme={theme} />,
    reading_list: isAurex ? <AurexReadingMono key="reading" books={books} {...aurexMono('reading_list')} /> : <ReadingListSection key="reading" books={books} theme={theme} />,
    map: isAurex ? <AurexMapMono key="map" maps={maps} locations={locations} mapsLang={mapsLang} {...aurexMono('map')} /> : <MapSection key="map" maps={maps} locations={locations} theme={theme} mapsLang={mapsLang} />,
    locations: isAurex ? <AurexMapMono key="locations" maps={maps} locations={locations} mapsLang={mapsLang} {...aurexMono('locations')} /> : <MapSection key="locations" maps={maps} locations={locations} theme={theme} mapsLang={mapsLang} />,
    map_global: isAurex ? <AurexMapMono key="map_global" maps={maps} locations={locations} title="Global Business Presence" mapsLang={mapsLang} {...aurexMono('map_global')} /> : <MapSection key="map_global" maps={maps} locations={locations} theme={theme} title="Global Business Presence" mapsLang={mapsLang} />,
    map_conferences: isAurex ? <AurexMapMono key="map_conferences" maps={maps} locations={locConferences} title="Conferences" mapsLang={mapsLang} {...aurexMono('map_conferences')} /> : <MapSection key="map_conferences" maps={maps} locations={locConferences} theme={theme} title="Conferences" mapsLang={mapsLang} />,
    map_recommended: isAurex ? <AurexMapMono key="map_recommended" maps={maps} locations={locRecommended} title="Recommended Sites" mapsLang={mapsLang} {...aurexMono('map_recommended')} /> : <MapSection key="map_recommended" maps={maps} locations={locRecommended} theme={theme} title="Recommended Sites" mapsLang={mapsLang} />,
    portfolio: isAurex ? <AurexPortfolioMono key="portfolio" items={portfolio} {...aurexMono('portfolio')} /> : <PortfolioSection key="portfolio" items={portfolio} theme={theme} />,
    gallery: isAurex ? <AurexGalleryMono key="gallery" items={gallery} {...aurexMono('gallery')} /> : <GallerySection key="gallery" items={gallery} theme={theme} />,
    testimonials: isAurex ? <AurexTestimonialsMono key="testimonials" items={testimonials} {...aurexMono('testimonials')} /> : <TestimonialsSection key="testimonials" items={testimonials} theme={theme} />,
    contact: isAurex ? <AurexContactMono key="contact" contactSettings={settings.contact_settings} {...aurexMono('contact')} /> : <ContactSection key="contact" theme={theme} contactSettings={settings.contact_settings} />,
    // Aurex Theme 2.0 sections — only meaningful when active_theme = 'aurex'
    aurex_audience: aurexSection('aurex_audience', AurexAudience),
    aurex_process: aurexSection('aurex_process', AurexProcess),
    aurex_pricing: aurexSection('aurex_pricing', AurexPricing),
    aurex_team: aurexSection('aurex_team', AurexTeam),
    aurex_events: aurexSection('aurex_events', AurexEvents),
    aurex_partners: aurexSection('aurex_partners', AurexPartners),
    aurex_clients: aurexSection('aurex_clients', AurexClients),
    aurex_video: aurexSection('aurex_video', AurexVideo),
  };

  return (
    <main data-testid="home-page">
      {sectionOrder.map(key => {
        const sec = sections[key];
        // Eye OFF → hidden from everyone.
        if (sec?.enabled === false) return null;
        // Padlock ON → only logged-in members see it. Anonymous visitors
        // get nothing (we don't render a "login prompt" stub here because
        // the admin explicitly chose to hide the section rather than gate
        // it interactively). The auth user object uses different id keys
        // depending on how it was populated (`id` from /auth/me, `member_id`
        // from member login, `username`/`email` fallback) — any of those
        // indicate a logged-in session.
        if (sec?.login_required === true && !(user && (user.id || user.member_id || user.username || user.email))) return null;
        return sectionMap[key] || null;
      })}
    </main>
  );
}
