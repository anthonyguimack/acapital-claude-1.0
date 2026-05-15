import React from 'react';
import { FileText, Map, BookOpen, Wrench, ExternalLink, ClipboardCheck, Server } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const docs = [
  {
    title: 'Use Case & Flow Diagram',
    description: 'Complete system flow diagram showing all actors, registration paths, and module interactions.',
    icon: Map,
    url: `${API}/api/docs/flow-diagram`,
    color: '#2563eb',
  },
  {
    title: 'Technical Documentation',
    description: 'System architecture, database structure, API endpoints, authentication, CSS variables, and security.',
    icon: Wrench,
    url: `${API}/api/docs/technical`,
    color: '#0D9488',
  },
  {
    title: 'Operator Manual (CMS)',
    description: 'Step-by-step guide for managing the platform from the admin panel. No technical knowledge required.',
    icon: BookOpen,
    url: `${API}/api/docs/operator-manual`,
    color: '#d97706',
  },
  {
    title: 'User Guide (My Account)',
    description: 'Member manual for navigating My Account: profile, community, invite codes, QR, portfolios.',
    icon: FileText,
    url: `${API}/api/docs/user-guide`,
    color: '#059669',
  },
  {
    title: 'Testing Manual',
    description: 'Test accounts (login, password, role, type, level, mentor, sponsor) plus suggested test scenarios. Auto-generated from live database.',
    icon: ClipboardCheck,
    url: `${API}/api/docs/testing-manual`,
    color: '#9333ea',
  },
  {
    title: 'AWS Installation Guide',
    description: 'Step-by-step guide to deploy this CMS on a fresh AWS Ubuntu server — server prep, dependencies, MongoDB import, Nginx, SSL, Stripe, troubleshooting.',
    icon: Server,
    url: `${API}/api/docs/aws-install`,
    color: '#f59e0b',
  },
];

export default function DocumentationManager() {
  return (
    <div data-testid="documentation-manager">
      <h1 className="text-xl font-bold mb-2" style={{ color: 'var(--ad-heading, #1a2332)', fontFamily: 'Playfair Display, serif' }}>Documentation</h1>
      <p className="text-sm mb-6" style={{ color: 'var(--ad-text-secondary, #6b7280)' }}>
        View and download platform documentation. Click "Open" to view in a new tab, then use "Save as PDF" to download.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {docs.map(doc => (
          <div key={doc.title} className="bg-white rounded border p-5 hover:shadow-md transition-shadow" style={{ borderColor: 'var(--ad-card-border, #e2e8f0)' }}>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${doc.color}15` }}>
                <doc.icon className="w-5 h-5" style={{ color: doc.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm mb-1" style={{ color: 'var(--ad-heading, #1a2332)' }}>{doc.title}</h3>
                <p className="text-xs mb-3" style={{ color: 'var(--ad-text-secondary, #6b7280)' }}>{doc.description}</p>
                <a href={doc.url} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium text-white transition-opacity hover:opacity-90"
                  style={{ backgroundColor: doc.color }}
                  data-testid={`doc-link-${doc.title.toLowerCase().replace(/[^a-z]/g, '-')}`}>
                  <ExternalLink className="w-3 h-3" /> Open Document
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 rounded border" style={{ backgroundColor: 'var(--ad-table-header-bg, #f8fafc)', borderColor: 'var(--ad-card-border, #e2e8f0)' }}>
        <p className="text-xs" style={{ color: 'var(--ad-text-secondary, #6b7280)' }}>
          <strong>How to save as PDF:</strong> Open any document, then click the "Save as PDF" button in the top toolbar. This uses your browser's print dialog — select "Save as PDF" as the destination.
        </p>
      </div>
    </div>
  );
}
