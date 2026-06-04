import React, { useState, useEffect, useCallback } from 'react';
import { adminAPI } from '../../lib/api';
import { toast } from 'sonner';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Save, Loader2, Eye, EyeOff, Palette, Type, Sparkles, Lock, LockOpen } from 'lucide-react';
import { Switch } from '../../components/ui/switch';
import { AUREX_PALETTE, AUREX_FONTS, aurexContrastFor, THEMES } from '../../lib/themeColors';

const sectionLabels = {
  // Existing
  hero: 'Hero Banner', about: 'About Us', services: 'Services',
  news: 'Company News', blog: 'External Blog', reading_list: 'Reading List',
  map: 'Travel Map', portfolio: 'Portfolio', gallery: 'Gallery',
  testimonials: 'Testimonials', contact: 'Contact Form',
  locations: 'Locations Map', map_global: 'Global Map',
  map_conferences: 'Conferences Map', map_recommended: 'Recommended Sites Map',
  // Aurex-specific
  aurex_audience: 'Aurex is for you (Target Audience)',
  aurex_process: 'Our Process',
  aurex_pricing: 'Pricing',
  aurex_team: 'Our Team',
  aurex_events: 'Events (from AUX Calendar)',
  aurex_partners: 'Partners',
  aurex_clients: 'Our Clients',
  aurex_video: 'Video',
  // Config-only section header overrides
  aurex_services_cfg:     'Services — Section Config',
  aurex_testimonials_cfg: 'Testimonials — Section Config',
  aurex_news_cfg:         'Latest News — Section Config',
  aurex_blog_cfg:         'Blog — Section Config',
  aurex_locations_cfg:    'Locations — Section Config',
  aurex_reading_cfg:      'Reading List — Section Config',
  aurex_portfolio_cfg:    'Portfolio — Section Config',
  aurex_gallery_cfg:      'Gallery — Section Config',
  // Personal Brand modernisation
  pb_stats:   'Stats / Numbers',
  pb_marquee: 'Marquee Ticker Strip',
};

function SortableItem({ id, label, enabled, loginRequired, config, onToggle, onToggleLogin, onConfigChange, showAurexControls, isPB }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const dndStyle = { transform: CSS.Transform.toString(transform), transition };
  // Default to white when Aurex controls are shown; null for non-Aurex (no bg override)
  const bgHex = config?.bg_color || (showAurexControls ? '#FFFFFF' : null);
  const textScheme = bgHex ? aurexContrastFor(bgHex) : 'dark';
  const isLight = textScheme === 'light';
  const selectedFont = AUREX_FONTS.find(f => f.key === config?.font_family)?.css;

  return (
    <div
      ref={setNodeRef}
      style={{
        ...dndStyle,
        backgroundColor: bgHex || '#FFFFFF',
        transition: [dndStyle.transition, 'background-color 200ms ease'].filter(Boolean).join(', '),
      }}
      className={`flex flex-col gap-3 border rounded-sm p-4 mb-2 ${isLight ? 'border-white/20' : 'border-slate-100'}`}
      data-testid={`section-item-${id}`}
    >
      <div className="flex items-center gap-3">
        <button {...attributes} {...listeners} className={`cursor-grab active:cursor-grabbing ${isLight ? 'text-white/40 hover:text-white/80' : 'text-slate-300 hover:text-slate-500'}`}>
          <GripVertical className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-medium truncate"
            style={{
              color: isLight ? '#ffffff' : '#1a2332',
              fontFamily: selectedFont || undefined,
            }}
            data-testid={`section-preview-${id}`}
          >
            {label}
          </p>
          <p className={`text-xs font-mono ${isLight ? 'text-white/50' : 'text-slate-400'}`}>{id}</p>
        </div>
        {/* Login Required (padlock). Independent from the Eye toggle:
            - Eye OFF          → hidden from everyone (hard hide).
            - Padlock ON       → shown only to logged-in members.
            - Padlock OFF      → shown to public (no login needed). */}
        <button
          type="button"
          onClick={() => onToggleLogin(id)}
          title={loginRequired ? 'Login required — click to make public' : 'Public — click to restrict to logged-in members'}
          className={`p-1.5 rounded transition-colors ${loginRequired ? 'text-amber-500 hover:text-amber-400 bg-amber-500/10' : isLight ? 'text-white/30 hover:text-white/70' : 'text-slate-300 hover:text-slate-500'}`}
          data-testid={`section-login-${id}`}
        >
          {loginRequired ? <Lock className="w-4 h-4" /> : <LockOpen className="w-4 h-4" />}
        </button>
        <div className="flex items-center gap-2">
          {enabled
            ? <Eye className={`w-4 h-4 ${isLight ? 'text-white/70' : 'text-[#0D9488]'}`} />
            : <EyeOff className={`w-4 h-4 ${isLight ? 'text-white/30' : 'text-slate-300'}`} />
          }
          <Switch checked={enabled} onCheckedChange={() => onToggle(id)} data-testid={`section-toggle-${id}`} />
        </div>
      </div>
      {/* Aurex-only per-section color + font controls */}
      {showAurexControls && (
        <div className="flex items-start gap-4 pl-8 pt-1 flex-wrap">
          <div>
            <p className={`text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1 ${isLight ? 'text-white/50' : 'text-slate-500'}`}><Palette className="w-3 h-3" /> Background</p>
            <div className="flex gap-1.5 items-center">
              {AUREX_PALETTE.map(sw => (
                <button key={sw.key} type="button" onClick={() => onConfigChange(id, { ...config, bg_color: sw.hex })}
                  className={`w-6 h-6 rounded transition-all ${bgHex === sw.hex ? 'ring-2 ring-[#0D9488] ring-offset-1' : 'ring-1 ring-slate-200 hover:ring-slate-400'}`}
                  style={{ backgroundColor: sw.hex }}
                  title={sw.label}
                  data-testid={`swatch-${id}-${sw.key}`}
                />
              ))}
              {/* Custom hex color input — native picker + free-text hex entry */}
              <label className="flex items-center gap-1 ml-1 border border-slate-200 rounded px-1.5 py-0.5 bg-white hover:border-slate-400 transition-colors cursor-pointer" title="Custom color (any hex)">
                <input
                  type="color"
                  value={(bgHex || '#FFFFFF').slice(0, 7)}
                  onChange={(e) => onConfigChange(id, { ...config, bg_color: e.target.value.toUpperCase() })}
                  className="w-5 h-5 rounded cursor-pointer border-0 p-0 bg-transparent"
                  style={{ appearance: 'none' }}
                  data-testid={`color-picker-${id}`}
                />
                <input
                  type="text"
                  value={bgHex || ''}
                  onChange={(e) => {
                    const v = e.target.value;
                    // Accept partial/typing input, only commit if it matches #RRGGBB
                    onConfigChange(id, { ...config, bg_color: v });
                  }}
                  onBlur={(e) => {
                    const v = e.target.value.trim();
                    if (!v) return;
                    const hex = v.startsWith('#') ? v : `#${v}`;
                    if (/^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(hex)) {
                      onConfigChange(id, { ...config, bg_color: hex.toUpperCase() });
                    }
                  }}
                  placeholder="#RRGGBB"
                  className="w-[74px] text-[11px] font-mono border-0 focus:outline-none bg-transparent text-slate-600"
                  data-testid={`hex-input-${id}`}
                />
              </label>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1 ${isLight ? 'text-white/50' : 'text-slate-500'}`}><Type className="w-3 h-3" /> Font</p>
            <select
              value={config?.font_family || ''}
              onChange={(e) => onConfigChange(id, { ...config, font_family: e.target.value })}
              className={`text-xs border rounded px-2 py-1 max-w-[220px] w-full ${isLight ? 'bg-white/10 border-white/20 text-white' : 'bg-white border-slate-200'}`}
              data-testid={`font-${id}`}
            >
              <option value="">Theme default ({isPB ? 'Plus Jakarta Sans' : textScheme === 'dark' ? 'Sora' : 'Inter'})</option>
              {AUREX_FONTS.map(f => (
                <option key={f.key} value={f.key} style={{ fontFamily: f.css }}>{f.label} — {f.note}</option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}

// Personality tabs shown when editing the Personal Brand theme.
// Each tab configures section visibility independently for that mini-site.
const PB_PERSONALITIES = [
  { key: 'business',  label: 'Business',  color: 'text-slate-600  border-slate-400'  },
  { key: 'lifestyle', label: 'Lifestyle', color: 'text-emerald-600 border-emerald-500' },
  { key: 'personal',  label: 'Personal',  color: 'text-violet-600  border-violet-500'  },
];

// All section keys that belong to the Personal Brand / Aurex-family pipeline,
// ordered to match the intended Personal Brand Pro section flow (§2-§11 from
// PersonalBrandSections.js, followed by secondary and Aurex-only sections).
// Any key present in the stored order but missing from this list is appended
// at the end so newly-added sections automatically appear without a re-save.
const PB_KNOWN_SECTIONS = [
  // Core PB sections in presentation order
  'hero', 'about', 'services', 'aurex_audience',
  'portfolio', 'testimonials', 'aurex_team',
  'contact', 'reading_list', 'gallery',
  // Secondary content sections
  'news', 'blog',
  // Aurex-native sections (optional for PB)
  'aurex_process', 'aurex_video', 'aurex_pricing', 'aurex_events',
  'aurex_partners', 'aurex_clients',
  // Map sections
  'map', 'map_global', 'map_conferences', 'map_recommended',
  // Meta / config-only entries
  'pb_marquee', 'pb_stats',
];

// Returns true when the order contains PB-specific section keys that are absent
// from the legacy DEFAULT_SECTION_ORDER.  Used to detect whether a personality
// order was ever explicitly saved vs. the backend returning the generic default.
const isPBLikeOrder = (ord) =>
  (ord || []).some(k => ['map_global', 'map_conferences', 'aurex_audience', 'aurex_process'].includes(k));

// Append any PB_KNOWN_SECTIONS that are missing from `ord`.
const ensurePBSections = (ord) => {
  const missing = PB_KNOWN_SECTIONS.filter(k => !ord.includes(k));
  return [...ord, ...missing];
};

export default function SectionOrderManager() {
  const [order, setOrder] = useState([]);
  const [sections, setSections] = useState({});
  const [configs, setConfigs] = useState({});
  // section_auth_gates: { [personality]: { [sectionKey]: 'public' | 'members' | 'hidden' } }
  // Controls per-personality, per-section visibility on the Personal Brand theme.
  const [authGates, setAuthGates] = useState({});
  // pbOrdersMap stores the section order for each PB personality independently.
  // { business: string[], lifestyle: string[], personal: string[] }
  // Allows the admin to drag-drop sections in each personality tab without
  // affecting the other two.  All three are saved together on "Save".
  const [pbOrdersMap, setPbOrdersMap] = useState({ business: [], lifestyle: [], personal: [] });
  // Which PB personality is currently shown on the public site.
  // null = Global (no per-personality content served); 'business'|'lifestyle'|'personal' = that mini-site.
  const [pbActivePersonality, setPbActivePersonality] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTheme, setActiveTheme] = useState(null);
  const [theme, setTheme] = useState(null);
  const [pbPersonality, setPbPersonality] = useState('business'); // active PB personality tab
  const [bootstrapped, setBootstrapped] = useState(false);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  // Bootstrap — read the site's active theme once.
  useEffect(() => {
    (async () => {
      try {
        const r = await adminAPI.getSettings();
        const at = r.data?.active_theme || 'default';
        setActiveTheme(at);
        setTheme(prev => prev || at);
      } catch { setActiveTheme('default'); setTheme('default'); }
      finally { setBootstrapped(true); }
    })();
  }, []);

  const loadAll = useCallback(async () => {
    if (!theme) return;
    try {
      const isAurexLike = theme === 'aurex' || theme === 'personalbrand';
      const isPBTheme   = theme === 'personalbrand';

      // For Personal Brand, load section orders for all 3 personalities in
      // parallel so the admin can switch tabs without extra network round-trips.
      const [orderRes, settingsRes, configRes, lifestyleOrderRes, personalOrderRes] = await Promise.all([
        adminAPI.getSectionOrder(theme === 'default' ? null : theme),
        adminAPI.getSettings(),
        isAurexLike ? adminAPI.getSectionConfig(theme) : Promise.resolve({ data: {} }),
        isPBTheme ? adminAPI.getSectionOrder('personalbrand_lifestyle') : Promise.resolve({ data: null }),
        isPBTheme ? adminAPI.getSectionOrder('personalbrand_personal')  : Promise.resolve({ data: null }),
      ]);

      setSections(settingsRes.data?.sections || {});
      setConfigs(configRes.data || {});
      setAuthGates(settingsRes.data?.section_auth_gates || {});
      if (isPBTheme) {
        setPbActivePersonality(settingsRes.data?.pb_active_personality || null);
      }

      if (isPBTheme) {
        // Build per-personality orders.  If a personality's order was never
        // explicitly saved (backend returns the generic legacy default), fall
        // back to the Business order so each tab starts with a sane initial
        // order rather than an unrelated legacy list.
        const bizOrder  = ensurePBSections(orderRes.data || []);
        const lifestyleOrder = isPBLikeOrder(lifestyleOrderRes.data)
          ? ensurePBSections(lifestyleOrderRes.data)
          : [...bizOrder];
        const personalOrder = isPBLikeOrder(personalOrderRes.data)
          ? ensurePBSections(personalOrderRes.data)
          : [...bizOrder];

        const newMap = { business: bizOrder, lifestyle: lifestyleOrder, personal: personalOrder };
        setPbOrdersMap(newMap);
        // Show the order for whichever tab is currently active.
        setOrder(newMap[pbPersonality] || bizOrder);
      } else {
        let nextOrder = orderRes.data || [];
        if (isAurexLike) {
          const known = ['hero', 'about', 'aurex_audience', 'services', 'aurex_process', 'aurex_video', 'aurex_pricing', 'aurex_team', 'testimonials', 'reading_list', 'aurex_events', 'news', 'blog', 'aurex_partners', 'aurex_clients', 'map', 'contact'];
          const missing = known.filter(k => !nextOrder.includes(k));
          if (missing.length) nextOrder = [...nextOrder, ...missing];
        }
        setOrder(nextOrder);
      }
    } catch (e) { console.error(e); }
  }, [theme]); // pbPersonality intentionally omitted — we handle tab-switch locally

  useEffect(() => { if (bootstrapped) loadAll(); }, [loadAll, bootstrapped]);

  // ── Derived flags ────────────────────────────────────────────────────────────
  const isPB = theme === 'personalbrand';
  const showAurexControls = theme === 'aurex' || isPB;

  // When editing the Personal Brand theme we work on per-personality auth gates
  // rather than the global sections object.  Each section can be:
  //   'public'  — visible to everyone (default)
  //   'members' — requires login (padlock ON, eye ON)
  //   'hidden'  — never shown for this personality (eye OFF)
  const currentGates = isPB ? (authGates[pbPersonality] || {}) : null;
  const gateFor = (key) => (currentGates ? currentGates[key] || 'public' : null);

  // Resolve enabled / loginRequired for the SortableItem props.
  const getEnabled      = (key) => isPB ? gateFor(key) !== 'hidden'   : sections[key]?.enabled !== false;
  const getLoginRequired = (key) => isPB ? gateFor(key) === 'members'  : sections[key]?.login_required === true;

  // ── Toggle handlers ──────────────────────────────────────────────────────────
  // Global (non-PB) handlers — unchanged behaviour.
  const handleToggle = (key) => {
    setSections(prev => ({ ...prev, [key]: { ...prev[key], enabled: !(prev[key]?.enabled !== false) } }));
  };
  const handleToggleLogin = (key) => {
    setSections(prev => ({ ...prev, [key]: { ...prev[key], login_required: !(prev[key]?.login_required === true) } }));
  };

  // Per-personality PB handlers — operate on authGates[pbPersonality][key].
  const handleTogglePB = (key) => {
    setAuthGates(prev => {
      const gates = prev[pbPersonality] || {};
      const cur = gates[key] || 'public';
      // eye OFF ↔ 'public' or 'members' (restore to 'public' when re-enabling)
      return { ...prev, [pbPersonality]: { ...gates, [key]: cur === 'hidden' ? 'public' : 'hidden' } };
    });
  };
  const handleToggleLoginPB = (key) => {
    setAuthGates(prev => {
      const gates = prev[pbPersonality] || {};
      const cur = gates[key] || 'public';
      return { ...prev, [pbPersonality]: { ...gates, [key]: cur === 'members' ? 'public' : 'members' } };
    });
  };

  const handleConfigChange = (id, cfg) => {
    setConfigs(prev => ({ ...prev, [id]: cfg }));
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      const newOrder = arrayMove(order, order.indexOf(active.id), order.indexOf(over.id));
      setOrder(newOrder);
      // In PB mode keep pbOrdersMap in sync so switching tabs doesn't lose unsaved changes.
      if (isPB) {
        setPbOrdersMap(prev => ({ ...prev, [pbPersonality]: newOrder }));
      }
    }
  };

  // Switching personality tabs updates the displayed section order from the in-memory map.
  const handlePersonalityChange = (key) => {
    setPbPersonality(key);
    if (pbOrdersMap[key]?.length) setOrder(pbOrdersMap[key]);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const isAurexLike = theme === 'aurex' || isPB;
      if (isPB) {
        // Save all 3 personality orders in parallel — each is stored under its own
        // section_orders key: personalbrand, personalbrand_lifestyle, personalbrand_personal.
        await Promise.all([
          adminAPI.updateSectionOrder(pbOrdersMap.business,  'personalbrand'),
          adminAPI.updateSectionOrder(pbOrdersMap.lifestyle, 'personalbrand_lifestyle'),
          adminAPI.updateSectionOrder(pbOrdersMap.personal,  'personalbrand_personal'),
        ]);
      } else {
        await adminAPI.updateSectionOrder(order, theme === 'default' ? null : theme);
      }
      // Always save global sections + auth gates together so neither overwrites the other.
      await adminAPI.updateSettings({
        sections,
        ...(isPB ? { section_auth_gates: authGates, pb_active_personality: pbActivePersonality } : {}),
      });
      if (isAurexLike) await adminAPI.updateSectionConfig(configs, theme);
      toast.success(isPB
        ? 'Saved — all 3 Personal Brand personality orders + visibility gates'
        : `Saved ${theme === 'default' ? '(legacy order)' : `for ${theme} theme`}`);
    } catch (err) { toast.error(err.response?.data?.detail || 'Error saving'); }
    finally { setLoading(false); }
  };

  // Active toggle handlers — route to PB or global depending on current mode.
  const activeToggle      = isPB ? handleTogglePB      : handleToggle;
  const activeToggleLogin = isPB ? handleToggleLoginPB : handleToggleLogin;

  return (
    <div data-testid="section-order-manager">
      {/* ── Header ────────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2332] flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Page Builder
            {showAurexControls && <Sparkles className="w-5 h-5 text-amber-500" />}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {isPB
              ? 'Drag to reorder sections per mini-site. Configure visibility and login gating per personality.'
              : showAurexControls
                ? 'Drag to reorder, toggle visibility. Pick a custom background & font per section.'
                : 'Drag to reorder, toggle visibility.'}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Active theme on website: <strong className="uppercase">{activeTheme || '…'}</strong>
            {activeTheme && activeTheme !== theme && (
              <span className="ml-2 text-amber-600">· Editing <strong className="uppercase">{theme}</strong> scope — changes won't affect the live theme.</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Editing:</label>
            <select value={theme || ''} onChange={(e) => setTheme(e.target.value)} className="text-sm border border-slate-200 rounded px-3 py-1.5 bg-white" data-testid="theme-scope-select">
              <option value="default">Default / Modern / Classic (legacy order)</option>
              {THEMES.filter(t => t.id === 'aurex' || t.id === 'personalbrand').map(t => (
                <option key={t.id} value={t.id}>{t.name} — full config</option>
              ))}
            </select>
          </div>
          <button onClick={handleSave} disabled={loading} className="bg-[#0D9488] text-white px-4 py-2 rounded-sm text-sm font-medium flex items-center gap-2 disabled:opacity-50" data-testid="section-save-btn">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
          </button>
        </div>
      </div>

      {/* ── Personal Brand personality tabs ───────────────────────────────────── */}
      {isPB && (
        <div className="mb-5 border border-slate-200 rounded-sm bg-slate-50 p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Personal Brand mini-sites
          </p>
          <p className="text-xs text-slate-400 mb-3">
            Each tab has its own section order (drag to reorder) and visibility settings (eye / lock). Changes in one personality don't affect the others.
          </p>
          <div className="flex gap-1" role="tablist">
            {PB_PERSONALITIES.map(({ key, label, color }) => {
              const gates = authGates[key] || {};
              const membersCount = Object.values(gates).filter(v => v === 'members').length;
              const hiddenCount  = Object.values(gates).filter(v => v === 'hidden').length;
              // Show a subtle indicator if this personality has a custom order
              // different from the business order (i.e. it was explicitly saved).
              const hasCustomOrder = isPBLikeOrder(pbOrdersMap[key]);
              return (
                <button
                  key={key}
                  role="tab"
                  aria-selected={pbPersonality === key}
                  onClick={() => handlePersonalityChange(key)}
                  className={`flex-1 px-3 py-2 rounded-sm text-sm font-medium transition-colors border-b-2 ${
                    pbPersonality === key
                      ? `bg-white shadow-sm ${color}`
                      : 'text-slate-400 border-transparent hover:text-slate-600 hover:bg-white/60'
                  }`}
                  data-testid={`pb-personality-tab-${key}`}
                >
                  {label}
                  <span className="ml-1.5 text-[10px] text-slate-400">
                    {membersCount > 0 && `🔒${membersCount} `}
                    {hiddenCount  > 0 && `🚫${hiddenCount} `}
                    {hasCustomOrder && key !== 'business' && '✦'}
                  </span>
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-400 mt-2.5 flex flex-wrap gap-x-4 gap-y-1">
            <span className="inline-flex items-center gap-1"><Eye className="w-3 h-3" /> Visible to everyone</span>
            <span className="inline-flex items-center gap-1"><EyeOff className="w-3 h-3" /> Hidden from everyone</span>
            <span className="inline-flex items-center gap-1"><Lock className="w-3 h-3 text-amber-500" /> Members only</span>
            <span className="inline-flex items-center gap-1"><LockOpen className="w-3 h-3" /> Public</span>
            <span className="text-[10px]">✦ custom order saved</span>
          </p>

          {/* Active mini-site selector — determines which personality's section content
              (titles, subtitles, items) is served to visitors on the public website. */}
          <div className="mt-4 pt-4 border-t border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Active mini-site on website
            </p>
            <p className="text-[11px] text-slate-400 mb-2">
              Choose which mini-site's section content visitors see. Global = shared content used by all themes.
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                { key: null,        label: 'Global (default)', cls: 'border-sky-400 text-sky-700' },
                { key: 'business',  label: 'Business',         cls: 'border-slate-400 text-slate-700' },
                { key: 'lifestyle', label: 'Lifestyle',        cls: 'border-emerald-400 text-emerald-700' },
                { key: 'personal',  label: 'Personal',         cls: 'border-violet-400 text-violet-700' },
              ].map(({ key, label, cls }) => {
                const isActive = pbActivePersonality === key;
                return (
                  <button
                    key={key ?? '__global__'}
                    onClick={() => setPbActivePersonality(key)}
                    className={`px-3 py-1.5 rounded-sm text-xs font-semibold border-2 transition-colors ${
                      isActive ? `bg-white shadow-sm ${cls}` : 'border-transparent text-slate-400 hover:text-slate-600 hover:bg-white/60'
                    }`}
                    data-testid={`pb-active-personality-${key ?? 'global'}`}
                  >
                    {label}
                    {isActive && <span className="ml-1.5 text-[9px] font-bold uppercase tracking-wider text-emerald-600">● LIVE</span>}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Section list ──────────────────────────────────────────────────────── */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={order} strategy={verticalListSortingStrategy}>
          {order.map(key => (
            <SortableItem
              key={key}
              id={key}
              label={sectionLabels[key] || key}
              enabled={getEnabled(key)}
              loginRequired={getLoginRequired(key)}
              config={configs[key]}
              onToggle={activeToggle}
              onToggleLogin={activeToggleLogin}
              onConfigChange={handleConfigChange}
              showAurexControls={showAurexControls}
              isPB={isPB}
            />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
}
