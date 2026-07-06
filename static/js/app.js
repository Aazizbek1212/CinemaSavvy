// ─── Alpine global state ────────────────────────────
document.addEventListener('alpine:init', () => {

  Alpine.data('appState', () => ({
    mobileMenu: false,
    scrolled: false,
    init() {
      document.documentElement.classList.add('dark');
      document.body.style.backgroundColor = '#0A0A0A';
      window.addEventListener('scroll', () => {
        this.scrolled = window.scrollY > 20;
      }, { passive: true });
    }
  }));

  Alpine.data('navbar', () => ({
    scrolled: false,
    init() {
      window.addEventListener('scroll', () => {
        this.scrolled = window.scrollY > 20;
      }, { passive: true });
    }
  }));

  Alpine.data('searchBar', () => ({
    query: '',
    results: [],
    open: false,
    async search() {
      if (this.query.length < 2) { this.results = []; return; }
      try {
        const res = await fetch(`/api/movies/?search=${encodeURIComponent(this.query)}&page_size=6`);
        const data = await res.json();
        this.results = data.results || [];
        this.open = true;
      } catch { this.results = []; }
    }
  }));

  Alpine.data('toastManager', () => ({
    toasts: [],
    addToast({ message, type = 'info', duration = 4000 }) {
      const id = Date.now();
      this.toasts.push({ id, message, type, visible: true });
      setTimeout(() => this.removeToast(id), duration);
    },
    removeToast(id) {
      const t = this.toasts.find(t => t.id === id);
      if (t) t.visible = false;
      setTimeout(() => { this.toasts = this.toasts.filter(t => t.id !== id); }, 300);
    }
  }));

  Alpine.data('reviewForm', () => ({
    rating: 0,
    text: '',
    submitting: false,
    async submitReview(slug) {
      if (!this.rating || this.submitting) return;

      const token = getToken(); // ✅ token tekshirish
      if (!token) {
        toast('Iltimos, tizimga kiring', 'error');
        return;
      }

      this.submitting = true;
      try {
        const res = await fetch(`/api/reviews/movies/${slug}/reviews/create/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'Authorization': `Bearer ${token}`, // ✅ faqat token bor bo'lsa
          },
          body: JSON.stringify({ rating: this.rating, text: this.text }),
        });
        if (res.ok) {
          this.rating = 0; this.text = '';
          htmx.trigger('#reviews-list', 'load');
          toast('Bahoyingiz qabul qilindi!', 'success');
        } else {
          const err = await res.json();
          const msg = err.error?.non_field_errors?.[0] || 'Xato yuz berdi';
          toast(msg, 'error');
        }
      } catch { toast('Tarmoq xatosi', 'error'); }
      finally { this.submitting = false; }
    }
  }));

});

// ─── HTMX ────────────────────────────────────────────
document.addEventListener('htmx:configRequest', e => {
  e.detail.headers['X-CSRFToken'] = getCsrfToken();
  const token = getToken();
  if (token) e.detail.headers['Authorization'] = `Bearer ${token}`; // ✅ faqat bor bo'lsa
});

document.addEventListener('htmx:responseError', () => {
  toast('Server xatosi yuz berdi', 'error');
});

// ─── Utils ───────────────────────────────────────────
function getCsrfToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

function getToken() {
  return localStorage.getItem('access_token') || null; // ✅ null qaytaradi
}

function toast(message, type = 'info') {
  window.dispatchEvent(new CustomEvent('show-toast', { detail: { message, type } }));
}

// ─── Share Movie ─────────────────────────────────────  ✅ YANGI
async function shareMovie() {
  const url = window.location.href;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
    } else {
      const el = document.createElement('textarea');
      el.value = url;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
    }
    toast('Havola nusxalandi! 🔗', 'success');
  } catch {
    toast('Nusxalash muvaffaqiyatsiz', 'error');
  }
}

// ─── Language switcher ───────────────────────────────
function switchLanguage(langCode) {
  document.querySelectorAll('[id^="lang-btn-"]').forEach(btn => {
    btn.classList.remove('active');
  });
  const btn = document.getElementById('lang-btn-' + langCode);
  if (btn) btn.classList.add('active');

  const playerEl = document.querySelector('[x-data^="videoPlayer"]');
  if (playerEl && playerEl._x_dataStack) {
    const player = playerEl._x_dataStack[0];
    if (player) {
      player.selectedLang = langCode;
      player.loadStream();
    }
  }
}