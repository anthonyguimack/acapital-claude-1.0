import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../lib/api';
import { toast } from 'sonner';
import { Plus, Edit2, Trash2, ArrowUp, ArrowDown, Lock, ExternalLink, Home, Newspaper, Image, BookOpen, Loader2 } from 'lucide-react';
import { getLayoutLabel } from '../../components/admin/LayoutPreview';
import PageEditorDialog from '../../components/admin/PageEditorDialog';
import { useDataTable, DataTableToolbar, DataTablePagination, SortableTh } from '../../components/admin/useDataTable';

const emptyPage = { title: '', url: '', show_in_header: false, show_in_footer: false, open_in_new_tab: false, login_required: false, order: 0, summary: '', content: '', page_type: '', layout: '', layout_image: '', zones: {} };

const SYSTEM_ICONS = { home: Home, news: Newspaper, gallery: Image, reading_list: BookOpen };

function StatusBadge({ active, label }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium ${active ? 'bg-[#0D9488]/10 text-[#0D9488]' : 'bg-slate-100 text-slate-400'}`}>
      {label}
    </span>
  );
}

export default function PagesManager() {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const load = () => adminAPI.getNavPages().then(r => setItems((r.data || []).sort((a, b) => (a.order || 0) - (b.order || 0)))).catch(console.error);

  useEffect(() => {
    load();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      if (editing.id) await adminAPI.updateNavPage(editing.id, editing);
      else await adminAPI.createNavPage(editing);
      toast.success('Saved!'); setOpen(false); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleDelete = async (id, isSystem) => {
    const msg = isSystem
      ? 'This is a SYSTEM page. Deleting it will remove it from navigation. It can be re-created by reloading. Continue?'
      : 'Delete this page?';
    if (!window.confirm(msg)) return;
    try { await adminAPI.deleteNavPage(id); toast.success('Deleted'); load(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const moveOrder = async (item, direction) => {
    const newOrder = (item.order || 0) + direction;
    await adminAPI.updateNavPage(item.id, { ...item, order: newOrder });
    load();
  };

  const openEditor = (page) => { setEditing({ ...page }); setOpen(true); };

  const dt = useDataTable(items, {
    searchFields: ['title', 'url'],
    defaultSort: { key: 'order', dir: 'asc' },
    storageKey: 'pages',
  });

  return (
    <div data-testid="pages-manager">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[#1a2332]" style={{ fontFamily: 'Playfair Display, serif' }}>Pages Manager</h1>
        <button onClick={() => openEditor({ ...emptyPage, order: items.length })} className="bg-[#0D9488] text-white px-4 py-2 rounded-sm text-sm font-medium flex items-center gap-2" data-testid="add-page-btn">
          <Plus className="w-4 h-4" /> Add Page
        </button>
      </div>

      <DataTableToolbar dt={dt} testId="pages" placeholder="Search by title or URL…" />

      <div className="bg-white rounded-sm border border-slate-200">
        <table className="w-full text-sm" data-testid="pages-table">
          <thead><tr className="border-b bg-slate-50/80">
            <SortableTh dt={dt} field="order" className="w-16">Order</SortableTh>
            <SortableTh dt={dt} field="title">Page</SortableTh>
            <SortableTh dt={dt} field="url" className="hidden md:table-cell">URL</SortableTh>
            <th className="text-center p-3 font-medium text-slate-500 w-20">Visibility</th>
            <th className="text-center p-3 font-medium text-slate-500 w-20">Access</th>
            <th className="text-right p-3 font-medium text-slate-500 w-24">Actions</th>
          </tr></thead>
          <tbody>
            {dt.visibleItems.map((item, idx) => {
              const isSystem = !!item.system;
              const SysIcon = SYSTEM_ICONS[item.system_key];
              return (
                <tr key={item.id} className="border-b border-slate-50 hover:bg-slate-50/50 group" data-testid={`page-row-${item.id}`}>
                  <td className="p-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => moveOrder(item, -1)} className="text-slate-300 hover:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" disabled={idx === 0}><ArrowUp className="w-3 h-3" /></button>
                      <span className="text-xs text-slate-400 w-5 text-center">{item.order}</span>
                      <button onClick={() => moveOrder(item, 1)} className="text-slate-300 hover:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" disabled={idx === items.length - 1}><ArrowDown className="w-3 h-3" /></button>
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {SysIcon && <SysIcon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />}
                      <div>
                        <div className="font-medium text-[#1a2332]">{item.title}</div>
                        <div className="flex gap-1 mt-0.5">
                          {isSystem && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium">System</span>}
                          {item.layout && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{getLayoutLabel(item.layout)}</span>}
                          {item.zones && Object.values(item.zones).some(z => z?.length > 0) && <span className="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600">Builder</span>}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3 hidden md:table-cell">
                    <span className="text-slate-500 text-xs font-mono bg-slate-50 px-2 py-0.5 rounded">{item.url}</span>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex flex-wrap justify-center gap-1">
                      {item.show_in_header && <StatusBadge active label="Header" />}
                      {item.show_in_footer && <StatusBadge active label="Footer" />}
                      {!item.show_in_header && !item.show_in_footer && <StatusBadge active={false} label="Hidden" />}
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex flex-wrap justify-center gap-1">
                      {item.login_required && <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-sm text-xs font-medium bg-amber-50 text-amber-600"><Lock className="w-3 h-3" />Login</span>}
                      {item.open_in_new_tab && <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-sm text-xs font-medium bg-blue-50 text-blue-500"><ExternalLink className="w-3 h-3" />New Tab</span>}
                      {!item.login_required && !item.open_in_new_tab && <span className="text-xs text-slate-300">Public</span>}
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEditor({ ...item })} className="p-1.5 text-slate-400 hover:text-[#0D9488] transition-colors" data-testid={`edit-page-${item.id}`}><Edit2 className="w-4 h-4" /></button>
                      <button onClick={() => handleDelete(item.id, isSystem)} className={`p-1.5 transition-colors ${isSystem ? 'text-slate-300 hover:text-amber-500' : 'text-slate-400 hover:text-red-500'}`} data-testid={`delete-page-${item.id}`}><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {dt.totalAll === 0 && <div className="p-12 text-center text-slate-400 text-sm">No pages yet. Click "Add Page" to create one.</div>}
        {dt.totalAll > 0 && dt.totalFiltered === 0 && <div className="p-12 text-center text-slate-400 text-sm">No pages match your search</div>}
        <DataTablePagination dt={dt} testId="pages" />
      </div>

      <PageEditorDialog editing={editing} setEditing={setEditing} open={open} setOpen={setOpen} onSave={handleSave} loading={loading} />
    </div>
  );
}
