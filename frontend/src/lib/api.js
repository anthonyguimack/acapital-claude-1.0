import axios from 'axios';
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const api = axios.create({ baseURL: API, withCredentials: true });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const publicAPI = {
  getSettings: () => api.get('/public/settings'),
  getHero: () => api.get('/public/hero'),
  getHeroSlides: (page = '') => api.get(`/public/hero-slides${page ? `?page=${page}` : ''}`),
  getAbout: () => api.get('/public/about'),
  getServices: () => api.get('/public/services'),
  getBlog: (page = 1, limit = 9, category = '') => api.get(`/public/blog?page=${page}&limit=${limit}&category=${category}`),
  getBlogDetail: (slug) => api.get(`/public/blog/${slug}`),
  getBooks: () => api.get('/public/books'),
  getMaps: () => api.get('/public/maps'),
  getMapDetail: (slug) => api.get(`/public/maps/${slug}`),
  getMapLocations: (mapType = '') => api.get(`/public/map-locations?map_type=${mapType}`),
  getGallery: (category = '') => api.get(`/public/gallery?category=${category}`),
  getGalleryCategories: () => api.get('/public/gallery-categories'),
  getPortfolio: () => api.get('/public/portfolio'),
  getTestimonials: () => api.get('/public/testimonials'),
  getSections: () => api.get('/public/sections'),
  getPage: (type) => api.get(`/public/page/${type}`),
  getNavPages: () => api.get('/public/nav-pages'),
  getSitePages: () => api.get('/public/site-pages'),
  getSeo: (path) => api.get(`/public/seo/${path}`),
  getGalleryAlbums: () => api.get('/public/gallery-albums'),
  getAlbumPhotos: (albumId) => api.get(`/public/gallery-albums/${albumId}/photos`),
  getServiceDetail: (id) => api.get(`/public/services/${id}`),
  getMyAccountLinks: () => api.get('/public/myaccount-links'),
  getMyAccountNav: () => api.get('/public/myaccount-nav'),
  getBlockedDates: () => api.get('/public/blocked-dates'),
  getCaptchaConfig: () => api.get('/public/captcha-config'),
};

export const searchAPI = {
  search: (q) => api.get(`/search?q=${encodeURIComponent(q)}`),
};

export const blogExternalAPI = {
  getLatest: () => api.get('/blog/latest'),
};

export const authAPI = {
  login: (email, password, loginType = 'any') => api.post('/auth/login', { email, password, login_type: loginType }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  exchangeSession: (sessionId) => api.post('/auth/session', { session_id: sessionId }),
  forgotPassword: (email, captchaToken) => api.post('/auth/forgot-password', { email, captcha_token: captchaToken }),
  resetPassword: (token, password) => api.post('/auth/reset-password', { token, password }),
  verifyResetToken: (token) => api.get(`/auth/reset-password/verify?token=${encodeURIComponent(token)}`),
  changePassword: (currentPassword, newPassword) => api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
};

export const contactAPI = { submit: (data) => api.post('/contact', data) };

export const landingAPI = {
  getContent: () => api.get('/public/landing-content'),
  getHeroSlides: () => api.get('/public/landing-hero'),
  subscribe: (data) => api.post('/public/landing-subscribe', data),
  submitContact: (data) => api.post('/public/landing-contact', data),
};

export const checkoutAPI = {
  create: (serviceId, originUrl) => api.post('/checkout', { service_id: serviceId, origin_url: originUrl }),
  status: (sessionId) => api.get(`/checkout/status/${sessionId}`),
};

export const adminAPI = {
  dashboard: () => api.get('/admin/dashboard'),
  // Roles & Permissions
  getCmsSections: () => api.get('/admin/cms-sections'),
  getCmsRoles: () => api.get('/admin/cms-roles'),
  createCmsRole: (data) => api.post('/admin/cms-roles', data),
  updateCmsRole: (id, data) => api.put(`/admin/cms-roles/${id}`, data),
  deleteCmsRole: (id) => api.delete(`/admin/cms-roles/${id}`),
  assignMemberCmsRoles: (memberId, roleIds) => api.put(`/admin/members/${memberId}/cms-roles`, { cms_roles: roleIds }),
  getHero: () => api.get('/admin/hero'),
  updateHero: (data) => api.put('/admin/hero', data),
  // Hero Slides CRUD
  getHeroSlides: () => api.get('/admin/hero-slides'),
  getHeroSlide: (id) => api.get(`/admin/hero-slides/${id}`),
  createHeroSlide: (data) => api.post('/admin/hero-slides', data),
  updateHeroSlide: (id, data) => api.put(`/admin/hero-slides/${id}`, data),
  deleteHeroSlide: (id) => api.delete(`/admin/hero-slides/${id}`),
  getAbout: () => api.get('/admin/about'),
  updateAbout: (data) => api.put('/admin/about', data),
  getServices: () => api.get('/admin/services'),
  createService: (data) => api.post('/admin/services', data),
  updateService: (id, data) => api.put(`/admin/services/${id}`, data),
  deleteService: (id) => api.delete(`/admin/services/${id}`),
  getBlog: () => api.get('/admin/blog'),
  createBlog: (data) => api.post('/admin/blog', data),
  updateBlog: (id, data) => api.put(`/admin/blog/${id}`, data),
  deleteBlog: (id) => api.delete(`/admin/blog/${id}`),
  // Blog Categories
  getBlogCategories: () => api.get('/admin/blog-categories'),
  createBlogCategory: (data) => api.post('/admin/blog-categories', data),
  updateBlogCategory: (id, data) => api.put(`/admin/blog-categories/${id}`, data),
  deleteBlogCategory: (id) => api.delete(`/admin/blog-categories/${id}`),
  getBooks: () => api.get('/admin/books'),
  createBook: (data) => api.post('/admin/books', data),
  updateBook: (id, data) => api.put(`/admin/books/${id}`, data),
  deleteBook: (id) => api.delete(`/admin/books/${id}`),
  getMaps: () => api.get('/admin/maps'),
  createMap: (data) => api.post('/admin/maps', data),
  updateMap: (id, data) => api.put(`/admin/maps/${id}`, data),
  deleteMap: (id) => api.delete(`/admin/maps/${id}`),
  getMapLocations: () => api.get('/admin/map-locations'),
  createMapLocation: (data) => api.post('/admin/map-locations', data),
  updateMapLocation: (id, data) => api.put(`/admin/map-locations/${id}`, data),
  deleteMapLocation: (id) => api.delete(`/admin/map-locations/${id}`),
  getGallery: () => api.get('/admin/gallery'),
  createGallery: (data) => api.post('/admin/gallery', data),
  updateGallery: (id, data) => api.put(`/admin/gallery/${id}`, data),
  deleteGallery: (id) => api.delete(`/admin/gallery/${id}`),
  reorderGallery: (items) => api.put('/admin/gallery/reorder/batch', { items }),
  // Gallery Categories
  getGalleryCategories: () => api.get('/admin/gallery-categories'),
  createGalleryCategory: (data) => api.post('/admin/gallery-categories', data),
  updateGalleryCategory: (id, data) => api.put(`/admin/gallery-categories/${id}`, data),
  deleteGalleryCategory: (id) => api.delete(`/admin/gallery-categories/${id}`),
  getPortfolio: () => api.get('/admin/portfolio'),
  createPortfolio: (data) => api.post('/admin/portfolio', data),
  updatePortfolio: (id, data) => api.put(`/admin/portfolio/${id}`, data),
  deletePortfolio: (id) => api.delete(`/admin/portfolio/${id}`),
  getTestimonials: () => api.get('/admin/testimonials'),
  createTestimonial: (data) => api.post('/admin/testimonials', data),
  updateTestimonial: (id, data) => api.put(`/admin/testimonials/${id}`, data),
  deleteTestimonial: (id) => api.delete(`/admin/testimonials/${id}`),
  getContacts: () => api.get('/admin/contacts'),
  updateContact: (id, data) => api.put(`/admin/contacts/${id}`, data),
  deleteContact: (id) => api.delete(`/admin/contacts/${id}`),
  getPurchases: () => api.get('/admin/purchases'),
  getSettings: () => api.get('/admin/settings'),
  updateSettings: (data) => api.put('/admin/settings', data),
  getPage: (type) => api.get(`/admin/pages/${type}`),
  updatePage: (type, data) => api.put(`/admin/pages/${type}`, data),
  // Nav Pages
  getNavPages: () => api.get('/admin/nav-pages'),
  createNavPage: (data) => api.post('/admin/nav-pages', data),
  updateNavPage: (id, data) => api.put(`/admin/nav-pages/${id}`, data),
  deleteNavPage: (id) => api.delete(`/admin/nav-pages/${id}`),
  // Gallery Albums
  getGalleryAlbums: () => api.get('/admin/gallery-albums'),
  createGalleryAlbum: (data) => api.post('/admin/gallery-albums', data),
  updateGalleryAlbum: (id, data) => api.put(`/admin/gallery-albums/${id}`, data),
  deleteGalleryAlbum: (id) => api.delete(`/admin/gallery-albums/${id}`),
  // Album Photos
  getAlbumPhotos: (albumId) => api.get(`/admin/album-photos/${albumId}`),
  createAlbumPhoto: (data) => api.post('/admin/album-photos', data),
  updateAlbumPhoto: (id, data) => api.put(`/admin/album-photos/${id}`, data),
  deleteAlbumPhoto: (id) => api.delete(`/admin/album-photos/${id}`),
  // Users
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  // SMTP
  testSmtpConnection: (data) => api.post('/admin/smtp/test-connection', data),
  testSmtpEmail: (data) => api.post('/admin/smtp/test-email', data),
  // Email Management — templates + branding wrapper
  listEmailTemplates: () => api.get('/admin/email-templates'),
  getEmailTemplate: (key) => api.get(`/admin/email-templates/${key}`),
  updateEmailTemplate: (key, data) => api.put(`/admin/email-templates/${key}`, data),
  resetEmailTemplate: (key) => api.post(`/admin/email-templates/${key}/reset`),
  previewEmailTemplate: (key, draft) => api.post(`/admin/email-templates/${key}/preview`, draft || {}),
  testSendEmailTemplate: (key, data) => api.post(`/admin/email-templates/${key}/test-send`, data),
  getEmailBranding: () => api.get('/admin/email-branding'),
  updateEmailBranding: (data) => api.put('/admin/email-branding', data),
  // Captcha
  getCaptchaSettings: () => api.get('/admin/captcha-settings'),
  updateCaptchaSettings: (data) => api.put('/admin/captcha-settings', data),
  // Upload
  uploadImage: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  uploadFile: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/upload-file', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  // Bulk Operations
  bulkDelete: (collection, ids) => api.post('/admin/bulk-delete', { collection, ids }),
  bulkUpdate: (collection, ids, update) => api.post('/admin/bulk-update', { collection, ids, update }),
  // Section Order
  getSectionOrder: (theme) => api.get('/admin/section-order', { params: theme ? { theme } : {} }),
  updateSectionOrder: (order, theme) => api.put('/admin/section-order', theme ? { order, theme } : { order }),
  getSectionConfig: (theme = 'aurex') => api.get('/admin/section-config', { params: { theme } }),
  updateSectionConfig: (configs, theme = 'aurex') => api.put('/admin/section-config', { configs, theme }),
  // SEO
  getSeo: () => api.get('/admin/seo'),
  updateSeo: (pagePath, data) => api.put(`/admin/seo/${pagePath}`, data),
  // Analytics
  getAnalytics: () => api.get('/admin/analytics'),
  // CSV Export
  exportContacts: () => api.get('/admin/contacts/export', { responseType: 'blob' }),
  // Members
  getMembers: () => api.get('/admin/members'),
  createMember: (data) => api.post('/admin/members', data),
  getMember: (id) => api.get(`/admin/members/${id}`),
  updateMember: (id, data) => api.put(`/admin/members/${id}`, data),
  deleteMember: (id) => api.delete(`/admin/members/${id}`),
  assignMentor: (id, data) => api.put(`/admin/members/${id}/mentor`, data),
  getMentors: () => api.get('/admin/mentors'),
  getMemberEbank: (id) => api.get(`/admin/members/${id}/ebank`),
  generateMemberQR: (id, data) => api.post(`/admin/members/${id}/generate-qr`, data),
  // Member Levels
  getLevels: () => api.get('/admin/member-levels'),
  createLevel: (data) => api.post('/admin/member-levels', data),
  updateLevel: (id, data) => api.put(`/admin/member-levels/${id}`, data),
  deleteLevel: (id) => api.delete(`/admin/member-levels/${id}`),
  // Member Types
  getMemberTypes: () => api.get('/admin/member-types'),
  createMemberType: (data) => api.post('/admin/member-types', data),
  updateMemberType: (id, data) => api.put(`/admin/member-types/${id}`, data),
  deleteMemberType: (id) => api.delete(`/admin/member-types/${id}`),
  // Membership Settings
  getMembershipSettings: () => api.get('/admin/membership-settings'),
  updateMembershipSettings: (data) => api.put('/admin/membership-settings', data),
  // Backup & Restore
  exportContent: (collections) => api.get(`/admin/export-content${collections ? `?collections=${collections}` : ''}`),
  importContent: (data) => api.post('/admin/import-content', data),
  // Backup Snapshots
  getBackupSettings: () => api.get('/admin/backup-settings'),
  updateBackupSettings: (data) => api.put('/admin/backup-settings', data),
  listBackups: () => api.get('/admin/backups'),
  getBackup: (id) => api.get(`/admin/backups/${id}`),
  createBackupNow: (label) => api.post('/admin/backups/create-now', { label: label || 'manual' }),
  deleteBackup: (id) => api.delete(`/admin/backups/${id}`),
  // Contact Settings
  getContactSettings: () => api.get('/admin/contact-settings'),
  updateContactSettings: (data) => api.put('/admin/contact-settings', data),
  // System Pages
  seedSystemPages: () => api.post('/admin/seed-system-pages'),
  // Landing Page
  getLandingContent: () => api.get('/admin/landing-content'),
  updateLandingContent: (data) => api.put('/admin/landing-content', data),
  getLandingHeroSlides: () => api.get('/admin/landing-hero'),
  createLandingHeroSlide: (data) => api.post('/admin/landing-hero', data),
  getLandingHeroSlide: (id) => api.get(`/admin/landing-hero/${id}`),
  updateLandingHeroSlide: (id, data) => api.put(`/admin/landing-hero/${id}`, data),
  deleteLandingHeroSlide: (id) => api.delete(`/admin/landing-hero/${id}`),
  getLandingSubscribers: () => api.get('/admin/landing-subscribers'),
  deleteLandingSubscriber: (id) => api.delete(`/admin/landing-subscribers/${id}`),
  getLandingContacts: () => api.get('/admin/landing-contacts'),
  deleteLandingContact: (id) => api.delete(`/admin/landing-contacts/${id}`),
  // My Account Quick Links
  getMyAccountLinks: () => api.get('/admin/myaccount-links'),
  createMyAccountLink: (data) => api.post('/admin/myaccount-links', data),
  updateMyAccountLink: (id, data) => api.put(`/admin/myaccount-links/${id}`, data),
  deleteMyAccountLink: (id) => api.delete(`/admin/myaccount-links/${id}`),
  reorderMyAccountLinks: (ordered_ids) => api.put('/admin/myaccount-links-reorder', { ordered_ids }),
  // My Account Navigation (ordering + visibility of built-in sidebar items)
  getMyAccountNav: () => api.get('/admin/myaccount-nav'),
  updateMyAccountNav: (id, data) => api.put(`/admin/myaccount-nav/${id}`, data),
  reorderMyAccountNav: (ordered_ids) => api.put('/admin/myaccount-nav-reorder', { ordered_ids }),
  // Per-member enrollment Q&A (info modal)
  getMemberEnrollment: (memberId) => api.get(`/admin/members/${memberId}/enrollment`),
  // Stripe configuration status (Settings → Stripe tab)
  getStripeStatus: () => api.get('/admin/stripe-status'),
  testStripeConnection: (apiKey) => api.post('/admin/stripe-test', apiKey ? { api_key: apiKey } : {}),
  // Calendar
  getCalendarEvents: () => api.get('/admin/calendar/events'),
  createCalendarEvent: (data) => api.post('/admin/calendar/events', data),
  getCalendarEvent: (id) => api.get(`/admin/calendar/events/${id}`),
  updateCalendarEvent: (id, data) => api.put(`/admin/calendar/events/${id}`, data),
  deleteCalendarEvent: (id) => api.delete(`/admin/calendar/events/${id}`),
  getEventRegistrations: (id) => api.get(`/admin/calendar/events/${id}/registrations`),
  getEventRegistrationsCSV: (id) => api.get(`/admin/calendar/events/${id}/registrations/csv`, { responseType: 'blob' }),
  cloneCalendarEvent: (id) => api.post(`/admin/calendar/events/${id}/clone`),
  // Mentorship Schedule
  getMentorshipSlots: () => api.get('/admin/mentorship/slots'),
  createMentorshipSlot: (data) => api.post('/admin/mentorship/slots', data),
  updateMentorshipSlot: (id, data) => api.put(`/admin/mentorship/slots/${id}`, data),
  deleteMentorshipSlot: (id) => api.delete(`/admin/mentorship/slots/${id}`),
  getSlotBookings: (id) => api.get(`/admin/mentorship/slots/${id}/bookings`),
  getMentors: () => api.get('/admin/mentors'),
  // Mentor Slot Templates
  getMentorSlotTemplates: () => api.get('/admin/mentor-slot-templates'),
  createMentorSlotTemplate: (data) => api.post('/admin/mentor-slot-templates', data),
  updateMentorSlotTemplate: (id, data) => api.put(`/admin/mentor-slot-templates/${id}`, data),
  deleteMentorSlotTemplate: (id) => api.delete(`/admin/mentor-slot-templates/${id}`),
  // Blocked Dates
  getBlockedDates: () => api.get('/admin/blocked-dates'),
  createBlockedDate: (data) => api.post('/admin/blocked-dates', data),
  updateBlockedDate: (id, data) => api.put(`/admin/blocked-dates/${id}`, data),
  deleteBlockedDate: (id) => api.delete(`/admin/blocked-dates/${id}`),
  // Admin global bundles
  getAdminBundles: () => api.get('/admin/bundles'),
  createAdminBundle: (d) => api.post('/admin/bundles', d),
  updateAdminBundle: (id, d) => api.put(`/admin/bundles/${id}`, d),
  deleteAdminBundle: (id) => api.delete(`/admin/bundles/${id}`),
  // Payouts
  getPayouts: () => api.get('/admin/payouts'),
  createPayout: (d) => api.post('/admin/payouts', d),
  deletePayout: (id) => api.delete(`/admin/payouts/${id}`),
  // Coupons
  getCoupons: () => api.get('/admin/coupons'),
  getCouponAnalytics: () => api.get('/admin/coupons/analytics'),
  createCoupon: (d) => api.post('/admin/coupons', d),
  updateCoupon: (id, d) => api.put(`/admin/coupons/${id}`, d),
  deleteCoupon: (id) => api.delete(`/admin/coupons/${id}`),
  // Aurex Sections (generic CRUD for all 7 new one-page sections)
  getAurexConfig: (section) => api.get(`/admin/aurex/${section}/config`),
  saveAurexConfig: (section, data) => api.put(`/admin/aurex/${section}/config`, data),
  getAurexItems: (section) => api.get(`/admin/aurex/${section}/items`),
  createAurexItem: (section, data) => api.post(`/admin/aurex/${section}/items`, data),
  updateAurexItem: (section, id, data) => api.put(`/admin/aurex/${section}/items/${id}`, data),
  deleteAurexItem: (section, id) => api.delete(`/admin/aurex/${section}/items/${id}`),
  reorderAurexItems: (section, order) => api.put(`/admin/aurex/${section}/reorder`, { order }),
};

// Member API (unified - uses same auth_token)
export const memberAPI = {
  login: (data) => api.post('/auth/login', { email: data.username || data.email, password: data.password }),
  me: () => api.get('/auth/me'),
  // Invite codes
  generateCodes: (count) => api.post('/member/invite-codes/generate', { count }),
  listCodes: () => api.get('/member/invite-codes'),
  sendInvite: (codeId, data) => api.post(`/member/invite-codes/${codeId}/send`, data),
  // Public
  validateCode: (code) => api.get(`/member/validate-code/${code}`),
  register: (data) => api.post('/member/register', data),
  // My Account
  getSponsor: () => api.get('/member/my-sponsor'),
  getMentor: () => api.get('/member/my-mentor'),
  getAvailableMentors: () => api.get('/member/available-mentors'),
  getEbank: () => api.get('/member/ebank'),
  updateEbank: (data) => api.put('/member/ebank', data),
  getEbankActivities: () => api.get('/member/ebank/activities'),
  generateQR: (data) => api.post('/member/generate-qr', data),
  validateSponsor: (num) => api.get(`/member/validate-sponsor/${num}`),
  getCommunity: () => api.get('/member/my-community'),
  updateBiography: (data) => api.put('/member/biography', data),
  updateProfile: (data) => api.put('/member/profile', data),
  // Portfolios
  getPortfolios: () => api.get('/member/portfolios'),
  createPortfolio: (data) => api.post('/member/portfolios', data),
  getPortfolio: (id) => api.get(`/member/portfolios/${id}`),
  updatePortfolio: (id, data) => api.put(`/member/portfolios/${id}`, data),
  deletePortfolio: (id) => api.delete(`/member/portfolios/${id}`),
  // Sectors / Industries / Companies
  getSectors: () => api.get('/member/sectors'),
  getIndustries: (sectorId) => api.get(`/member/industries${sectorId ? `?sector_id=${sectorId}` : ''}`),
  getCompanies: (industryId) => api.get(`/member/companies${industryId ? `?industry_id=${industryId}` : ''}`),
  getMembersList: () => api.get('/member/members-list'),
  getMyLevel: () => api.get('/member/my-level'),
  changePassword: (data) => api.put('/member/change-password', data),
  getMembershipSettings: () => api.get('/public/membership-settings'),
  getProfileActivities: () => api.get('/member/profile-activities'),
  uploadImage: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/member/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  uploadFile: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/member/upload-file', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  // Calendar
  getCalendarEvents: () => api.get('/member/calendar/events'),
  getCalendarEvent: (id) => api.get(`/member/calendar/events/${id}`),
  registerEvent: (id) => api.post(`/member/calendar/events/${id}/register`),
  cancelEventRegistration: (id) => api.post(`/member/calendar/events/${id}/cancel`),
  uploadEventFile: (id, data) => api.post(`/member/calendar/events/${id}/upload`, data),
  // Notifications
  getNotifications: () => api.get('/member/notifications'),
  getUnreadCount: () => api.get('/member/notifications/unread-count'),
  markNotificationRead: (id) => api.put(`/member/notifications/${id}/read`),
  markAllNotificationsRead: () => api.put('/member/notifications/read-all'),
  // Mentorship Calendar
  getMentorSlots: () => api.get('/member/mentorship/slots'),
  createMentorSlot: (data) => api.post('/member/mentorship/slots', data),
  updateMentorSlot: (id, data) => api.put(`/member/mentorship/slots/${id}`, data),
  deleteMentorSlot: (id) => api.delete(`/member/mentorship/slots/${id}`),
  getMentorCalendar: () => api.get('/member/mentor-calendar'),
  bookMentorSlot: (id, data) => api.post(`/member/mentorship/book/${id}`, data || {}),
  cancelMentorBooking: (id) => api.post(`/member/mentorship/cancel/${id}`),
  getMyBookings: () => api.get('/member/my-bookings'),
  // Mentor earnings
  getMentorEarnings: () => api.get('/member/mentor/earnings'),
  // Session Bundles
  getBundles: () => api.get('/member/bundles'),
  getBundle: (id) => api.get(`/member/bundles/${id}`),
  checkoutBundle: (id, data) => api.post(`/member/bundles/checkout/${id}`, data),

  // Coupons
  validateCoupon: (data) => api.post('/member/coupons/validate', data),
  getBundleCheckoutStatus: (sid) => api.get(`/member/bundles/checkout/status/${sid}`),
  getMyCredits: () => api.get('/member/credits'),
  // Mentor personal bundles
  getMyMentorBundles: () => api.get('/member/mentor/bundles'),
  createMentorBundle: (d) => api.post('/member/mentor/bundles', d),
  updateMentorBundle: (id, d) => api.put(`/member/mentor/bundles/${id}`, d),
  deleteMentorBundle: (id) => api.delete(`/member/mentor/bundles/${id}`),
  // Mentor payouts (personal history)
  getMyPayouts: () => api.get('/member/mentor/payouts'),
  // Mentor Slot Templates (public list, gated by setting server-side)
  getMentorSlotTemplates: () => api.get('/member/mentor-slot-templates'),
  // iCal subscription feed
  getIcalInfo: () => api.get('/member/ical/info'),
  regenerateIcal: () => api.post('/member/ical/regenerate'),
};

// Geo API (public)
export const geoAPI = {
  getCountries: () => api.get('/geo/countries'),
  getStates: (countryId) => api.get(`/geo/states${countryId ? `?country_id=${countryId}` : ''}`),
  getCities: (stateId) => api.get(`/geo/cities${stateId ? `?state_id=${stateId}` : ''}`),
  // Admin
  adminCreateCountry: (data) => api.post('/admin/geo/countries', data),
  adminUpdateCountry: (id, data) => api.put(`/admin/geo/countries/${id}`, data),
  adminDeleteCountry: (id) => api.delete(`/admin/geo/countries/${id}`),
  adminCreateState: (data) => api.post('/admin/geo/states', data),
  adminUpdateState: (id, data) => api.put(`/admin/geo/states/${id}`, data),
  adminDeleteState: (id) => api.delete(`/admin/geo/states/${id}`),
  adminCreateCity: (data) => api.post('/admin/geo/cities', data),
  adminUpdateCity: (id, data) => api.put(`/admin/geo/cities/${id}`, data),
  adminDeleteCity: (id) => api.delete(`/admin/geo/cities/${id}`),
};

export const enrollmentAPI = {
  getFields: () => api.get('/public/enrollment-fields'),
  validateCode: (code) => api.post('/public/enrollment/validate-code', { code }),
  checkEmail: (email) => api.post('/public/enrollment/check-email', { email }),
  submit: (form_data) => api.post('/public/enrollment/submit', { form_data }),
  // Admin
  adminGetFields: () => api.get('/admin/enrollment-fields'),
  adminGetField: (id) => api.get(`/admin/enrollment-fields/${id}`),
  adminCreateField: (data) => api.post('/admin/enrollment-fields', data),
  adminUpdateField: (id, data) => api.put(`/admin/enrollment-fields/${id}`, data),
  adminDeleteField: (id) => api.delete(`/admin/enrollment-fields/${id}`),
  adminToggleVisibility: (id, visible) => api.put(`/admin/enrollment-fields/${id}/visibility`, { visible }),
  adminReorderFields: (ordered_ids) => api.put('/admin/enrollment-fields/reorder', { ordered_ids }),
  adminGetApplications: () => api.get('/admin/enrollment-applications'),
  getStep4Content: () => api.get('/public/enrollment-content/step4'),
  adminGetStep4Content: () => api.get('/admin/enrollment-content/step4'),
  adminUpdateStep4Content: (data) => api.put('/admin/enrollment-content/step4', data),
};

export default api;
