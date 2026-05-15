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
  // Aurex-specific
  aurex_audience: 'Aurex is for you (Target Audience)',
  aurex_process: 'Our Process',
  aurex_pricing: 'Pricing',
  aurex_team: 'Our Team',
  aurex_events: 'Events (from AUX Calendar)',
  aurex_partners: 'Partners',
  aurex_clients: 'Our Clients',
  aurex_video: 'Video',
};

function SortableItem({ id, label, enabled, loginRequired, config, onToggle, onToggleLogin, onConfigChange, showAurexControls }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  const bgHex = config?.bg_color || (showAurexControls ? '#FFFFFF' : null);
  const textScheme = bgHex ? aurexContrastFor(bgHex) : 'dark';

  return (
    <div ref={setNodeRef} style={style} className="flex flex-col gap-3 bg-white border border-slate-100 rounded-sm p-4 mb-2" data-testid={`section-item-${id}`}>
      <div className="flex items-center gap-3">
        <button {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500">
          <GripVertical className="w-5 h-5" />
        </button>
        {/* Preview chip showing bg + font */}
        {showAurexControls && (
          <div className="w-12 h-12 rounded border border-slate-200 flex items-center justify-center shrink-0" style={{ backgroundColor: bgHex, color: textScheme === 'light' ? '#fff' : '#111827', fontFamily: AUREX_FONTS.find(f => f.key === config?.font_family)?.css || "'Inter', sans-serif" }} data-testid={`section-preview-${id}`}>
            <span className="text-sm font-bold">Aa</span>
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[#1a2332] truncate">{label}</p>
          <p className="text-xs text-slate-400 font-mono">{id}</p>
        </div>
        {/* Login Required (padlock). Independent from the Eye toggle:
            - Eye OFF          → hidden from everyone (hard hide).
            - Padlock ON       → shown only to logged-in members.
            - Padlock OFF      → shown to public (no login needed). */}
        <button
          type="button"
          onClick={() => onToggleLogin(id)}
          title={loginRequired ? 'Login required — click to make public' : 'Public — click to restrict to logged-in members'}
          className={`p-1.5 rounded transition-colors ${loginRequired ? 'text-amber-600 hover:text-amber-700 bg-amber-50' : 'text-slate-300 hover:text-slate-500'}`}
          data-testid={`section-login-${id}`}
        >
          {loginRequired ? <Lock className="w-4 h-4" /> : <LockOpen className="w-4 h-4" />}
        </button>
        <div className="flex items-center gap-2">
          {enabled ? <Eye className="w-4 h-4 text-[#0D9488]" /> : <EyeOff className="w-4 h-4 text-slate-300" />}
          <Switch checked={enabled} onCheckedChange={() => onToggle(id)} data-testid={`section-toggle-${id}`} />
        </div>
      </div>
      {/* Aurex-only per-section color + font controls */}
      {showAurexControls && (
        <div className="flex items-start gap-4 pl-8 pt-1 flex-wrap">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-1"><Palette className="w-3 h-3" /> Background</p>
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
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-1"><Type className="w-3 h-3" /> Font</p>
            <select
              value={config?.font_family || ''}
              onChange={(e) => onConfigChange(id, { ...config, font_family: e.target.value })}
              className="text-xs border border-slate-200 rounded px-2 py-1 max-w-[220px] w-full bg-white"
              data-testid={`font-${id}`}
            >
              <option value="">Theme default ({textScheme === 'dark' ? 'Sora' : 'Inter'})</option>
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

export default function SectionOrderManager() {
  const [order, setOrder] = useState([]);
  const [sections, setSections] = useState({});
  const [configs, setConfigs] = useState({});
  const [loading, setLoading] = useState(false);
  const [activeTheme, setActiveTheme] = useState(null);
  const [theme, setTheme] = useState(null); // theme being edited — initialised to the site's active theme on mount
  const [bootstrapped, setBootstrapped] = useState(false);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  // Bootstrap — read the site's active theme once and open the manager with that scope preselected.
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
      const [orderRes, settingsRes, configRes] = await Promise.all([
        adminAPI.getSectionOrder(theme === 'default' ? null : theme),
        adminAPI.getSettings(),
        isAurexLike ? adminAPI.getSectionConfig(theme) : Promise.resolve({ data: {} }),
      ]);
      let nextOrder = orderRes.data || [];
      // Ensure any newly added Aurex-family section types automatically appear in
      // the builder even if the admin saved the order before we added them.
      if (isAurexLike) {
        const known = ['hero', 'about', 'aurex_audience', 'services', 'aurex_process', 'aurex_video', 'aurex_pricing', 'aurex_team', 'testimonials', 'reading_list', 'aurex_events', 'news', 'blog', 'aurex_partners', 'aurex_clients', 'map', 'contact'];
        const missing = known.filter(k => !nextOrder.includes(k));
        if (missing.length) nextOrder = [...nextOrder, ...missing];
      }
      setOrder(nextOrder);
      setSections(settingsRes.data?.sections || {});
      setConfigs(configRes.data || {});
    } catch (e) { console.error(e); }
  }, [theme]);

  useEffect(() => { if (bootstrapped) loadAll(); }, [loadAll, bootstrapped]);

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      setOrder(prev => arrayMove(prev, prev.indexOf(active.id), prev.indexOf(over.id)));
    }
  };
  const handleToggle = (key) => {
    setSections(prev => ({ ...prev, [key]: { ...prev[key], enabled: !(prev[key]?.enabled !== false) } }));
  };
  const handleToggleLogin = (key) => {
    setSections(prev => ({ ...prev, [key]: { ...prev[key], login_required: !(prev[key]?.login_required === true) } }));
  };
  const handleConfigChange = (id, cfg) => {
    setConfigs(prev => ({ ...prev, [id]: cfg }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const isAurexLike = theme === 'aurex' || theme === 'personalbrand';
      await adminAPI.updateSectionOrder(order, theme === 'default' ? null : theme);
      await adminAPI.updateSettings({ sections });
      if (isAurexLike) {
        await adminAPI.updateSectionConfig(configs, theme);
      }
      toast.success(`Saved ${theme === 'default' ? '(legacy order)' : `for ${theme} theme`}`);
    } catch (err) { toast.error(err.response?.data?.detail || 'Error saving'); }
    finally { setLoading(false); }
  };

  const showAurexControls = theme === 'aurex' || theme === 'personalbrand';

  return (
    <div data-testid="section-order-manager">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2332] flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            Page Builder
            {showAurexControls && <Sparkles className="w-5 h-5 text-amber-500" />}
          </h1>
          <p className="text-sm text-slate-500 mt-1">Drag to reorder, toggle visibility. {showAurexControls ? 'Aurex scope lets you pick a custom background colour and font per section.' : 'Select Aurex to unlock per-section background & font pickers.'}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Active theme on website: <strong className="uppercase">{activeTheme || '…'}</strong>{activeTheme && activeTheme !== theme && <span className="ml-2 text-amber-600">· You are editing the <strong className="uppercase">{theme}</strong> scope (changes will not affect the live theme).</span>}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Editing:</label>
            <select value={theme || ''} onChange={(e) => setTheme(e.target.value)} className="text-sm border border-slate-200 rounded px-3 py-1.5 bg-white" data-testid="theme-scope-select">
              <option value="default">Default / Modern / Classic (legacy order)</option>
              {THEMES.filter(t => t.id === 'aurex' || t.id === 'personalbrand').map(t => <option key={t.id} value={t.id}>{t.name} — full config</option>)}
            </select>
          </div>
          <button onClick={handleSave} disabled={loading} className="bg-[#0D9488] text-white px-4 py-2 rounded-sm text-sm font-medium flex items-center gap-2 disabled:opacity-50" data-testid="section-save-btn">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
          </button>
        </div>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={order} strategy={verticalListSortingStrategy}>
          {order.map(key => (
            <SortableItem
              key={key}
              id={key}
              label={sectionLabels[key] || key}
              enabled={sections[key]?.enabled !== false}
              loginRequired={sections[key]?.login_required === true}
              config={configs[key]}
              onToggle={handleToggle}
              onToggleLogin={handleToggleLogin}
              onConfigChange={handleConfigChange}
              showAurexControls={showAurexControls}
            />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
}
