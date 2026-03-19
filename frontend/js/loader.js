/**
 * loader.js — Top progress bar + ring spinner overlay on every page
 */
(function () {
  // ── 1. Top loading bar ──────────────────────────────────────────
  const bar = document.createElement('div');
  bar.id = 'nprogress-bar';
  document.documentElement.style.setProperty('--bar-ready', '0');
  document.head.insertAdjacentHTML('beforeend', `<style>
    #nprogress-bar{position:fixed;top:0;left:0;height:3px;z-index:99999;background:linear-gradient(90deg,#5B23FF,#008BFF,#E4FF30);background-size:200% 100%;border-radius:0 3px 3px 0;width:0%;box-shadow:0 0 10px rgba(91,35,255,.6),0 0 20px rgba(0,139,255,.3);animation:barShimmer 1.2s linear infinite;transition:width .3s ease,opacity .3s ease}
    #nprogress-bar::after{content:'';position:absolute;right:0;top:-3px;width:60px;height:9px;background:#E4FF30;border-radius:50%;filter:blur(4px);opacity:.7}
    @keyframes barShimmer{0%{background-position:0% 50%}100%{background-position:200% 50%}}
    .page-loading-overlay{position:fixed;inset:0;z-index:9998;background:var(--bg,#F0F4FF);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.5rem;transition:opacity .4s ease,visibility .4s ease}
    .page-loading-overlay.hidden{opacity:0;visibility:hidden;pointer-events:none}
  </style>`);

  // ── 2. Ring spinner overlay ─────────────────────────────────────
  const overlay = document.createElement('div');
  overlay.className = 'page-loading-overlay';
  overlay.id = 'page-loader';
  overlay.innerHTML = `
    <div class="ring-spinner"><div class="ring-spinner-inner"></div></div>
    <div class="loading-dots">
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
    </div>`;

  // Safely inject — body may not exist yet if script is in <head>
  function inject() {
    document.body.prepend(overlay);
    document.body.prepend(bar);
  }
  if (document.body) { inject(); }
  else { document.addEventListener('DOMContentLoaded', inject); }

  // ── 3. Animate bar ─────────────────────────────────────────────
  let w = 0;
  const tick = setInterval(() => {
    w += w < 30 ? 8 : w < 60 ? 3.5 : w < 82 ? 1.2 : w < 92 ? 0.4 : 0;
    bar.style.width = Math.min(w, 92) + '%';
  }, 80);

  function finish() {
    clearInterval(tick);
    bar.style.width = '100%';
    setTimeout(() => {
      bar.style.opacity = '0';
      overlay.classList.add('hidden');
      setTimeout(() => { bar.remove(); }, 400);
    }, 220);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(finish, 180));
  } else {
    setTimeout(finish, 120);
  }
  setTimeout(finish, 4000); // hard fallback

  // ── 4. Post-DOM setup ──────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    // Navbar scroll shadow
    const nav = document.getElementById('navbar');
    if (nav) {
      window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 8);
      }, { passive: true });
    }

    // Scroll reveal
    const ro = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('revealed');
          e.target.classList.remove('will-reveal');
          ro.unobserve(e.target);
        }
      });
    }, { threshold: 0.06 });
    document.querySelectorAll('.reveal.will-reveal').forEach(el => ro.observe(el));
  });

  // Wake up Render backend silently in background
  fetch('https://ccc-backend-bb1s.onrender.com/api/clubs').catch(()=>{});

})();
