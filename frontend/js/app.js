// ── Theme ──────────────────────────────────────────────────────────────────
const Theme = {
  get()  { return localStorage.getItem('ccc_theme') || 'light'; },
  set(t) {
    localStorage.setItem('ccc_theme', t);
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.textContent = t === 'light' ? '🌙 Dark' : '☀️ Light';
    });
  },
  toggle(){ this.set(this.get() === 'light' ? 'dark' : 'light'); },
  init() { this.set(this.get()); }
};
Theme.init();

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  let c = document.getElementById('toast-container');
  if (!c) { c = document.createElement('div'); c.id = 'toast-container'; c.className = 'toast-container'; document.body.appendChild(c); }
  const el = document.createElement('div');
  el.className = `toast toast-${type}`; el.textContent = msg; c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = '.18s'; setTimeout(() => el.remove(), 200); }, 3000);
}

// ── Utils ──────────────────────────────────────────────────────────────────
function escHtml(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function timeAgo(iso) {
  if (!iso) return '';
  // Ensure the string is parsed as UTC — append 'Z' if no timezone info present
  const utcIso = /[Zz]$|[+\-]\d{2}:\d{2}$/.test(iso) ? iso : iso + 'Z';
  const d = Date.now() - new Date(utcIso).getTime(), s = Math.floor(d / 1000), m = Math.floor(s / 60), h = Math.floor(m / 60), dd = Math.floor(h / 24);
  if (s < 60) return 'just now'; if (m < 60) return m + 'm ago'; if (h < 24) return h + 'h ago'; if (dd < 30) return dd + 'd ago';
  return new Date(utcIso).toLocaleDateString();
}
function initials(name) { if (!name) return '?'; return name.trim().split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join(''); }
function avatarColor(name) {
  const c = ['#E50914','#1A56DB','#0A7C5C','#7C3AED','#0E7490','#B81D24','#3D3730','#B45309'];
  let h = 0; for (let x of (name || '')) h = ((h << 5) - h) + x.charCodeAt(0);
  return c[Math.abs(h) % c.length];
}
function avatarHtml(name, size = 27) {
  const bg = avatarColor(name || '');
  return `<div class="user-avatar" style="background:${bg};width:${size}px;height:${size}px;font-size:${Math.round(size*.3)}px;color:#fff">${initials(name)}</div>`;
}
function starsHtml(rating) {
  let s = '';
  for (let i = 1; i <= 5; i++) s += `<span style="color:${i <= Math.round(rating) ? 'var(--warning)' : 'var(--ink3)'};font-size:.8rem">★</span>`;
  return s;
}

// ── Domain ─────────────────────────────────────────────────────────────────
const DOMAIN_COLOR = { Technical:'#1A56DB', Cultural:'#7C3AED', Sports:'#E50914', Literary:'#0E7490', Social:'#0A7C5C', Management:'#1A1714' };
const DOMAIN_ICON  = { Technical:'💻', Cultural:'🎭', Sports:'⚽', Literary:'📚', Social:'🌍', Management:'📈' };
function domainColor(d) { return DOMAIN_COLOR[d] || '#E50914'; }

// ── Role / Year badges ─────────────────────────────────────────────────────
function roleBadge(role) {
  const map = { owner:'Owner', club_admin:'Admin', faculty_incharge:'Faculty', senior:'Senior' };
  const cls = { owner:'badge-owner', club_admin:'badge-admin', faculty_incharge:'badge-admin', senior:'badge-senior' };
  if (!map[role]) return '';
  return `<span class="badge ${cls[role]}">${map[role]}</span>`;
}
function yearBadge(year) {
  if (!year) return '';
  const labels = {1:'1st Year',2:'2nd Year',3:'3rd Year',4:'4th Year',5:'5th Year'};
  return `<span class="badge badge-y${Math.min(year,5)}">${labels[year]||'Y'+year}</span>`;
}
function userTagHtml(u, size = 22) {
  if (!u) return '<span class="text-muted">[deleted]</span>';
  const name = u.anonymous ? 'Anonymous' : u.name;
  const av = u.anonymous ? `<div class="user-avatar" style="background:var(--paper4);width:${size}px;height:${size}px;font-size:${Math.round(size*.32)}px">?</div>` : avatarHtml(u.name, size);
  return `<span style="display:inline-flex;align-items:center;gap:.28rem;flex-wrap:wrap">
    ${av}<span style="font-weight:600;font-size:.79rem">${escHtml(name)}</span>
    ${u.anonymous ? '<span class="anon-tag">Anonymous</span>' : roleBadge(u.role)}
    ${!u.anonymous && u.year ? yearBadge(u.year) : ''}
    ${!u.anonymous && u.branch ? `<span class="text-small text-muted">${u.branch}</span>` : ''}
  </span>`;
}

// ── Club card ──────────────────────────────────────────────────────────────
function clubCardHtml(club, compareMode = false) {
  const col  = domainColor(club.domain);
  const icon = club.icon || DOMAIN_ICON[club.domain] || '';
  const img  = club.image_url ? `<img src="${escHtml(club.image_url)}" alt="${escHtml(club.name)}" loading="lazy"/>` : '';
  const ratingHtml = club.avg_rating ? `<span class="club-rating">★ ${club.avg_rating.toFixed(1)}</span>` : '';
  const recruitHtml = club.recruit_status
    ? `<span class="recruit-badge recruit-${club.recruit_status}">${club.recruit_status==='open'?'● Recruiting':club.recruit_status==='closed'?'Closed':'◎ Soon'}</span>` : '';
  return `<div class="club-card">
    ${compareMode ? `<div class="compare-check" id="cc-${club.id}" onclick="toggleCompare('${club.id}','${escHtml(club.name)}',event)">✓</div>` : ''}
    <a href="/club-detail.html?id=${club.id}" style="display:flex;flex-direction:column;flex:1">
      <div class="club-card-banner" style="background:linear-gradient(135deg,${col}16,${col}30)">
        ${img}<span class="club-emoji">${icon}</span>
      </div>
      <div class="club-card-body">
        <div class="club-card-name">${escHtml(club.name)}</div>
        <div class="club-card-tagline">${escHtml(club.tagline)}</div>
        <div class="club-card-footer">
          <span class="domain-badge" style="background:${col}14;color:${col};border:1px solid ${col}28">${club.domain}</span>
          <span class="club-card-meta">${club.members} Members</span>
        </div>
        ${ratingHtml||recruitHtml?`<div style="display:flex;align-items:center;gap:.38rem;margin-top:.38rem;flex-wrap:wrap">${ratingHtml}${recruitHtml}</div>`:''}
      </div>
    </a>
  </div>`;
}

// ── Compare ────────────────────────────────────────────────────────────────
let compareList = [];
function toggleCompare(id, name, event) {
  if (event) event.preventDefault();
  const idx = compareList.findIndex(c => c.id === id);
  if (idx > -1) { compareList.splice(idx, 1); updateCompareUI(); }
  else { if (compareList.length >= 3) { toast('Max 3 clubs', 'error'); return; } compareList.push({id, name}); updateCompareUI(); toast(`Added "${name}"`); }
}
function updateCompareUI() {
  document.querySelectorAll('.compare-check').forEach(el => {
    const id = el.id.replace('cc-', ''); el.classList.toggle('checked', compareList.some(c => c.id === id));
  });
  const bar = document.getElementById('compare-bar'); if (!bar) return;
  if (!compareList.length) { bar.classList.remove('visible'); return; }
  bar.classList.add('visible');
  document.getElementById('compare-chips').innerHTML = compareList.map(c =>
    `<span class="compare-chip">${escHtml(c.name)}<span class="compare-chip-remove" onclick="toggleCompare('${c.id}','')">✕</span></span>`).join('');
  const btn = document.getElementById('compare-btn'); if (btn) btn.disabled = compareList.length < 2;
}
async function openCompareModal() {
  if (compareList.length < 2) { toast('Select at least 2 clubs', 'error'); return; }
  document.getElementById('compare-overlay').classList.add('open');
  const body = document.getElementById('compare-modal-body');
  body.innerHTML = '<div class="loading-center"><span class="spinner"></span></div>';
  try {
    const clubs = await Promise.all(compareList.map(c => api.club(c.id)));
    const rows = [
      {label:'Domain',  fn:c=>`<span style="color:${domainColor(c.domain)};font-weight:700">${c.domain}</span>`},
      {label:'Members', fn:c=>`${c.members} Members`},
      {label:'Founded', fn:c=>`${c.founded}`},
      {label:'Rating',  fn:c=>c.avg_rating?`★ ${c.avg_rating.toFixed(1)} (${c.review_count||0})` : '—'},
      {label:'Tags',    fn:c=>(c.tags||[]).map(t=>`<span class="tag">#${t}</span>`).join(' ')},
      {label:'About',   fn:c=>`<span style="font-size:.77rem;color:var(--ink2)">${(c.description||'').slice(0,85)}…</span>`},
    ];
    body.innerHTML = `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:.81rem">
      <tr>${['',...clubs].map((c,i)=>i===0?`<th style="padding:.55rem .7rem;text-align:left;color:var(--ink3);font-size:.68rem;text-transform:uppercase;letter-spacing:.04em">Club</th>`:
        `<th style="padding:.55rem .7rem;text-align:center;border-left:1px solid var(--border)">
          <div style="font-size:1.35rem"></div>
          <div style="font-family:var(--font-serif);font-weight:700;font-size:.84rem">${escHtml(c.name)}</div>
          <div style="font-size:.69rem;color:var(--ink3)">${escHtml(c.tagline)}</div>
        </th>`).join('')}</tr>
      ${rows.map(row=>`<tr style="border-top:1px solid var(--border)">
        <td style="padding:.52rem .7rem;color:var(--ink3);font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap">${row.label}</td>
        ${clubs.map(c=>`<td style="padding:.52rem .7rem;text-align:center;border-left:1px solid var(--border)">${row.fn(c)}</td>`).join('')}
      </tr>`).join('')}
    </table></div>
    <div style="display:flex;gap:.55rem;margin-top:1rem;flex-wrap:wrap">
      ${clubs.map(c=>`<a href="/club-detail.html?id=${c.id}" class="btn btn-secondary btn-sm">View ${escHtml(c.name)} →</a>`).join('')}
    </div>`;
  } catch(e) { body.innerHTML = `<div class="alert alert-error">${e.message}</div>`; }
}
function closeCompareModal() { document.getElementById('compare-overlay')?.classList.remove('open'); }
function initCompareBar() {
  document.body.insertAdjacentHTML('beforeend', `
    <div class="compare-bar" id="compare-bar">
      <div style="display:flex;align-items:center;gap:.65rem;flex:1;min-width:0">
        <span style="font-size:.77rem;font-weight:700;white-space:nowrap;color:var(--ink2)">Compare</span>
        <div class="compare-chips" id="compare-chips"></div>
      </div>
      <div style="display:flex;gap:.42rem">
        <button class="btn btn-primary btn-sm" id="compare-btn" onclick="openCompareModal()" disabled>Compare</button>
        <button class="btn btn-secondary btn-sm" onclick="compareList=[];updateCompareUI()">Clear</button>
      </div>
    </div>
    <div class="compare-modal-overlay" id="compare-overlay" onclick="if(event.target===this)closeCompareModal()">
      <div class="compare-modal">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.05rem">
          <h2 style="font-family:var(--font-serif);font-size:1.1rem;font-weight:800">Compare Clubs</h2>
          <button class="btn btn-ghost btn-sm" onclick="closeCompareModal()">✕</button>
        </div>
        <div id="compare-modal-body"></div>
      </div>
    </div>`);
}

// ── Navbar ─────────────────────────────────────────────────────────────────
function renderNavbar(activePage = '') {
  const navEl = document.getElementById('navbar'); if (!navEl) return;
  const user  = Auth.getUser();
  const isLight = Theme.get() === 'light';

  function buildNav(unread = 0) {
    const links = [
      { href:'/index.html',    label:'Home',      id:'home' },
      { href:'/clubs.html',    label:'Clubs',     id:'clubs' },
      { href:'/events.html',   label:'Events',    id:'events' },
      { href:'/forum.html',    label:'Forum',     id:'forum' },
      ...(user ? [
        { href:'/messages.html', label:'Messages', id:'messages', badge:unread },
        { href:'/dashboard.html',label:'Dashboard',id:'dashboard' },
      ] : []),
      ...(user?.role==='club_admin'||user?.role==='owner'||user?.role==='faculty_incharge' ? [{href:'/admin.html',label:'Admin',id:'admin'}] : []),
    ];
    navEl.innerHTML = `
      <a href="/index.html" class="navbar-brand">
        <span style="font-family:var(--font-sans);font-weight:800;letter-spacing:-0.02em;font-size:1.35rem;text-transform:uppercase;"><span style="color:var(--red)">NIT</span> CLUB COMPASS</span>
      </a>
      <ul class="navbar-links" id="navbar-links">
        ${links.map(l=>`<li><a href="${l.href}" class="${l.id===activePage?'active':''}">${l.label}${l.badge?`<span class="nav-badge">${l.badge}</span>`:''}</a></li>`).join('')}
      </ul>
      <div class="navbar-right">
        <button class="theme-toggle" onclick="Theme.toggle()" title="Toggle theme">${isLight?'🌙 Dark':'☀️ Light'}</button>
        ${user ? `
          <div class="navbar-user" onclick="window.location.href='/profile.html?id=${user.id}'">
            ${avatarHtml(user.name, 26)}
            <span style="max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600">${escHtml(user.name.split(' ')[0])}</span>
            ${roleBadge(user.role)}
            <button class="btn btn-ghost btn-sm" style="padding:.12rem .38rem;font-size:.67rem;color:var(--ink3);margin-left:.1rem" onclick="event.stopPropagation();Auth.clear();window.location.href='/login.html'">✕</button>
          </div>` :
          `<a href="/login.html" class="btn btn-ghost btn-sm">Login</a>
           <a href="/signup.html" class="btn btn-primary btn-sm">Sign Up</a>`}
        <button class="navbar-menu-toggle" onclick="document.getElementById('navbar-links').classList.toggle('mobile-open')">☰</button>
      </div>`;
  }

  // Render navbar immediately (no waiting)
  buildNav(0);

  // Then fetch unread count in background and update badge only
  if (user) {
    api.unreadCount().then(r => {
      if (r.count > 0) {
        const msgLink = navEl.querySelector('a[href="/messages.html"]');
        if (msgLink && !msgLink.querySelector('.nav-badge')) {
          msgLink.insertAdjacentHTML('beforeend', `<span class="nav-badge">${r.count}</span>`);
        }
      }
    }).catch(() => {});
  }
}

// ── AI Chat Widget ─────────────────────────────────────────────────────────
function initChatWidget() {
  document.body.insertAdjacentHTML('beforeend', `
    <div class="chat-widget">
      <div class="chat-box" id="chat-box">
        <div class="chat-box-header">
          <div style="display:flex;align-items:center;gap:.42rem">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span style="font-size:.8rem;font-weight:700">Club Assistant</span>
          </div>
          <button class="btn btn-ghost btn-icon btn-sm" onclick="document.getElementById('chat-box').classList.remove('open')" style="font-size:.82rem">✕</button>
        </div>
        <div class="chat-box-msgs" id="chat-msgs">
          <div class="chat-msg-ai">Hi! Ask me anything about NIT KKR clubs</div>
        </div>
        <div class="chat-box-input">
          <input class="form-input" id="chat-input" placeholder="Ask about clubs…" style="font-size:.79rem" onkeydown="if(event.key==='Enter')sendChatMsg()">
          <button class="btn btn-primary btn-sm" onclick="sendChatMsg()">→</button>
        </div>
      </div>
      <button class="chat-toggle" onclick="document.getElementById('chat-box').classList.toggle('open')" title="Club Assistant">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    </div>`);
}
async function sendChatMsg() {
  const input = document.getElementById('chat-input'), msgs = document.getElementById('chat-msgs');
  const msg = input.value.trim(); if (!msg) return; input.value = '';
  msgs.insertAdjacentHTML('beforeend', `<div class="chat-msg-user">${escHtml(msg)}</div>`);
  const el = document.createElement('div'); el.className = 'chat-msg-ai'; el.innerHTML = '<span class="spinner" style="width:13px;height:13px"></span>';
  msgs.appendChild(el); msgs.scrollTop = msgs.scrollHeight;
  try { const r = await api.chat({ message: msg }); el.textContent = r.reply; }
  catch { el.textContent = 'Sorry, something went wrong.'; }
  msgs.scrollTop = msgs.scrollHeight;
}

// ── Footer ─────────────────────────────────────────────────────────────────
function renderFooter() {
  const el = document.getElementById('footer');
  if (!el) return;
  const year = new Date().getFullYear();
  el.innerHTML = `
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand-col">
        <a href="/index.html" class="footer-logo">
          <div>
            <div class="footer-logo-name" style="font-weight:800;font-family:var(--font-sans);letter-spacing:-0.02em;text-transform:uppercase"><span style="color:var(--red)">NIT</span> CLUB COMPASS</div>
          </div>
        </a>
        <p class="footer-tagline">Your guide to clubs, communities and college life at NIT Kurukshetra. Built by students, for students.</p>
        <div class="footer-socials">
          <a href="/forum.html"     class="footer-social" title="Forum">Forum</a>
          <a href="/events.html"    class="footer-social" title="Events">Events</a>
          <a href="/quiz.html"      class="footer-social" title="Quiz">Quiz</a>
        </div>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Quick Links</div>
        <a href="/index.html"     class="footer-link">Home</a>
        <a href="/clubs.html"     class="footer-link">All Clubs</a>
        <a href="/events.html"    class="footer-link">Events</a>
        <a href="/forum.html"     class="footer-link">Forum</a>
        <a href="/quiz.html"      class="footer-link">Club Quiz</a>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Domains</div>
        <a href="/clubs.html?domain=Technical"  class="footer-link">Technical</a>
        <a href="/clubs.html?domain=Cultural"   class="footer-link">Cultural</a>
        <a href="/clubs.html?domain=Sports"     class="footer-link">Sports</a>
        <a href="/clubs.html?domain=Literary"   class="footer-link">Literary</a>
        <a href="/clubs.html?domain=Social"     class="footer-link">Social</a>
        <a href="/clubs.html?domain=Management" class="footer-link">Management</a>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Account</div>
        <a href="/login.html"    class="footer-link">Login</a>
        <a href="/signup.html"   class="footer-link">Sign Up</a>
        <a href="/profile.html"  class="footer-link">My Profile</a>
        <div class="footer-col-title" style="margin-top:1.2rem">Resources</div>
        <a href="/quiz.html"        class="footer-link">Take the Quiz</a>
        <a href="/forum.html#polls" class="footer-link">Community Polls</a>
      </div>
    </div>
    <div class="footer-divider"></div>
    <div class="footer-bottom">
      <div class="footer-bottom-left">
        <span>© ${year} NIT Club Compass</span>
        <span class="footer-dot">·</span>
        <span>Made with ❤️ by NIT KKR Students</span>
      </div>
      <div class="footer-bottom-right">
        <span class="footer-status">
          <span class="footer-status-dot"></span>
          All systems operational
        </span>
        <span class="footer-dot">·</span>
        <span style="color:var(--ink3);font-size:.75rem">NIT Kurukshetra, Haryana</span>
      </div>
    </div>
  </div>`;
}
