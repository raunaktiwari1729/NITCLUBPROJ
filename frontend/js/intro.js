/**
 * intro.js — Welcome splash screen for NIT KKR Compass
 * Only shows on the HOME page, only on first visit (sessionStorage).
 * After ~3.2s it animates out and reveals the page.
 */
(function () {
  // Only run on index / home page
  const isHome = location.pathname === '/' ||
                 location.pathname.endsWith('index.html') ||
                 location.pathname === '';

  if (!isHome) return;

  // Uncomment below to show only once per session:
  if (sessionStorage.getItem('intro_seen')) return;
  sessionStorage.setItem('intro_seen', '1');

  /* ── Inject styles ───────────────────────────────────────────── */
  const style = document.createElement('style');
  style.textContent = `
    #nitkkr-intro {
      position: fixed; inset: 0; z-index: 99999;
      background: #0D0A1E;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      overflow: hidden;
      font-family: 'Syne', 'Outfit', sans-serif;
    }

    /* Animated background gradient orbs */
    #nitkkr-intro .orb {
      position: absolute; border-radius: 50%;
      filter: blur(80px); opacity: 0; pointer-events: none;
      animation: orbIn 1s ease forwards;
    }
    #nitkkr-intro .orb-1 {
      width: 500px; height: 500px;
      background: radial-gradient(circle, rgba(91,35,255,0.35), transparent 70%);
      top: -100px; left: -100px;
      animation-delay: 0.1s;
    }
    #nitkkr-intro .orb-2 {
      width: 400px; height: 400px;
      background: radial-gradient(circle, rgba(0,139,255,0.28), transparent 70%);
      bottom: -80px; right: -80px;
      animation-delay: 0.3s;
    }
    #nitkkr-intro .orb-3 {
      width: 300px; height: 300px;
      background: radial-gradient(circle, rgba(228,255,48,0.12), transparent 70%);
      top: 30%; left: 60%;
      animation-delay: 0.5s;
    }
    @keyframes orbIn { to { opacity: 1; } }

    /* Grid dot pattern overlay */
    #nitkkr-intro::before {
      content: '';
      position: absolute; inset: 0;
      background-image: radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px);
      background-size: 32px 32px;
      pointer-events: none;
    }

    /* Content wrapper */
    #nitkkr-intro .intro-content {
      position: relative; z-index: 1;
      text-align: center;
      display: flex; flex-direction: column;
      align-items: center; gap: 0;
    }

    /* Logo icon */
    #nitkkr-intro .intro-logo {
      width: 72px; height: 72px; border-radius: 20px;
      background: linear-gradient(135deg, #5B23FF, #008BFF);
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem;
      box-shadow: 0 0 40px rgba(91,35,255,0.6), 0 0 80px rgba(0,139,255,0.3);
      margin-bottom: 2rem;
      opacity: 0; transform: scale(0.5);
      animation: logoIn 0.6s 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards;
    }
    @keyframes logoIn {
      to { opacity: 1; transform: scale(1); }
    }

    /* "Welcome to" line */
    #nitkkr-intro .intro-welcome {
      font-size: 0.85rem; font-weight: 600;
      letter-spacing: 0.22em; text-transform: uppercase;
      color: rgba(255,255,255,0.45);
      margin-bottom: 0.6rem;
      opacity: 0; transform: translateY(10px);
      animation: lineUp 0.5s 0.7s cubic-bezier(0.16,1,0.3,1) forwards;
    }

    /* Main title — "NIT KKR" */
    #nitkkr-intro .intro-title {
      font-size: clamp(3rem, 10vw, 6rem);
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.04em;
      color: #fff;
      margin-bottom: 0.2rem;
      opacity: 0; transform: translateY(20px);
      animation: lineUp 0.6s 0.85s cubic-bezier(0.16,1,0.3,1) forwards;
    }

    /* "Compass" — gradient accent */
    #nitkkr-intro .intro-subtitle {
      font-size: clamp(2rem, 7vw, 4.2rem);
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.04em;
      background: linear-gradient(135deg, #A78BFF 0%, #60C8FF 55%, #B4FFA8 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 1.8rem;
      opacity: 0; transform: translateY(20px);
      animation: lineUp 0.6s 1s cubic-bezier(0.16,1,0.3,1) forwards;
    }

    /* Tagline */
    #nitkkr-intro .intro-tagline {
      font-size: 0.92rem; font-weight: 400;
      color: rgba(255,255,255,0.5);
      letter-spacing: 0.02em;
      opacity: 0; transform: translateY(10px);
      animation: lineUp 0.5s 1.2s cubic-bezier(0.16,1,0.3,1) forwards;
      margin-bottom: 2.8rem;
    }

    /* Progress bar */
    #nitkkr-intro .intro-bar-wrap {
      width: 180px; height: 2px;
      background: rgba(255,255,255,0.1);
      border-radius: 2px; overflow: hidden;
      opacity: 0;
      animation: lineUp 0.4s 1.3s ease forwards;
    }
    #nitkkr-intro .intro-bar-fill {
      height: 100%; width: 0%; border-radius: 2px;
      background: linear-gradient(90deg, #5B23FF, #008BFF, #E4FF30);
      animation: barFill 1.8s 1.4s cubic-bezier(0.4,0,0.2,1) forwards;
    }
    @keyframes barFill { to { width: 100%; } }

    @keyframes lineUp {
      to { opacity: 1; transform: translateY(0); }
    }

    /* EXIT animation */
    #nitkkr-intro.exit {
      animation: introExit 0.8s cubic-bezier(0.7,0,0.3,1) forwards;
    }
    @keyframes introExit {
      0%   { opacity: 1; transform: scale(1) translateY(0); }
      30%  { opacity: 1; transform: scale(1.04) translateY(0); }
      100% { opacity: 0; transform: scale(1.08) translateY(-30px); }
    }
  `;
  document.head.appendChild(style);

  /* ── Build the DOM ───────────────────────────────────────────── */
  function mountIntro() {
    const intro = document.createElement('div');
    intro.id = 'nitkkr-intro';
    intro.innerHTML = `
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="intro-content">
        <div class="intro-logo">🧭</div>
        <div class="intro-welcome">Welcome to</div>
        <div class="intro-title">NIT KKR</div>
        <div class="intro-subtitle">Compass</div>
        <div class="intro-tagline">Find your tribe. Navigate your first year.</div>
        <div class="intro-bar-wrap">
          <div class="intro-bar-fill"></div>
        </div>
      </div>`;
    document.body.prepend(intro);

    /* Hide scroll until intro exits */
    document.documentElement.style.overflow = 'hidden';

    /* Dismiss after 3.2s */
    setTimeout(() => {
      intro.classList.add('exit');
      document.documentElement.style.overflow = '';
      setTimeout(() => intro.remove(), 800);
    }, 3200);
  }

  /* Wait for <body> to exist */
  if (document.body) {
    mountIntro();
  } else {
    document.addEventListener('DOMContentLoaded', mountIntro);
  }
})();
