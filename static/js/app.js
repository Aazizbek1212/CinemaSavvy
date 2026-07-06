// ─── Alpine global state ────────────────────────────
document.addEventListener('alpine:init', () => {

  Alpine.data('appState', () => ({
    mobileMenu: false,   // ← navbar uchun
    scrolled: false,     // ← navbar scroll uchun

    init() {
      document.documentElement.classList.add('dark');
      document.body.style.backgroundColor = '#0A0A0A';

      // Scroll listener
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

      // ✅ FIX #1: Token mavjudligini tekshirish
      const token = getToken();
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
            // ✅ FIX #2: Faqat token bor bo'lsa yuborish
            'Authorization': `Bearer ${token}`,
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
  // ✅ FIX #3: Bo'sh token yuborilmasin
  const token = getToken();
  if (token) e.detail.headers['Authorization'] = `Bearer ${token}`;
});

document.addEventListener('htmx:responseError', () => {
  toast('Server xatosi yuz berdi', 'error');
});

// ─── Utils ───────────────────────────────────────────
function getCsrfToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

// ✅ FIX #4: null qaytaradi (bo'sh string emas)
function getToken() {
  return localStorage.getItem('access_token') || null;
}

function toast(message, type = 'info') {
  window.dispatchEvent(new CustomEvent('show-toast', { detail: { message, type } }));
}

// ─── Share Movie ──────────────────────────────────────
// ✅ FIX #5: Bu funksiya butunlay yo'q edi — qo'shildi!
// HTTP da clipboard ishlamaydi, shuning uchun fallback yozildi
async function shareMovie() {
  const url = window.location.href;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      // HTTPS da ishlaydi
      await navigator.clipboard.writeText(url);
    } else {
      // HTTP uchun fallback (eski usul)
      const el = document.createElement('textarea');
      el.value = url;
      el.style.position = 'fixed';
      el.style.opacity = '0';
      document.body.appendChild(el);
      el.focus();
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
  // Barcha til tugmalarini reset
  document.querySelectorAll('[id^="lang-btn-"]').forEach(btn => {
    btn.classList.remove('active');
  });
  // Tanlangan tilni faollashtirish
  const btn = document.getElementById('lang-btn-' + langCode);
  if (btn) btn.classList.add('active');

  // Alpine.js videoPlayer ga xabar berish
  const playerEl = document.querySelector('[x-data^="videoPlayer"]');
  if (playerEl && playerEl._x_dataStack) {
    const player = playerEl._x_dataStack[0];
    if (player) {
      player.selectedLang = langCode;
      player.loadStream();
    }
  }
}