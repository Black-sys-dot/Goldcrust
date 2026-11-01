/* ==========================================================================
   GOLDCRUST — storefront behaviour
   No framework, no build step. Cart state lives in localStorage so it survives
   navigation between the three pages.
   ========================================================================== */

/* ------------------------------------------------------------- helpers --- */
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const money = n => '₹' + Math.round(n).toLocaleString('en-IN');

/* Orders the customer placed on this browser. The ticket number is the
   order id; the copy and its live stage live on the Tickets page. */
const Tickets = {
  KEY: 'goldcrust.tickets.v1',
  ids() {
    try { return JSON.parse(localStorage.getItem(this.KEY)) || []; } catch { return []; }
  },
  remember(id) {
    if (!id) return;
    const ids = [id, ...this.ids().filter(item => item !== id)].slice(0, 20);
    localStorage.setItem(this.KEY, JSON.stringify(ids));
  },
};

function ticketCode(id) {
  return String(id || '').replace(/^(GC)(\d+)$/, '$1 $2');
}

function ticketStages(order) {
  const ready = order.mode === 'pickup' ? 'Ready' : 'On the way';
  const done = order.mode === 'pickup' ? 'Collected' : 'Delivered';
  return ['Received', 'Cooking', ready, done];
}

function ticketIndex(status) {
  return { confirmed: 0, preparing: 1, ready: 2, completed: 3 }[status] ?? -1;
}

function ticketNote(order) {
  const notes = {
    confirmed: 'The kitchen has your ticket and has not started yet.',
    preparing: 'Your food is on the fryer.',
    ready: order.mode === 'pickup'
      ? 'It is ready. Collect it from the counter.'
      : 'A rider is on the way to you.',
    completed: order.mode === 'pickup' ? 'Picked up. Enjoy it hot.' : 'Delivered. Enjoy it hot.',
  };
  return notes[order.status] || 'Waiting on the kitchen.';
}

function ticketCard(order) {
  const idx = ticketIndex(order.status);
  const when = order.created_at
    ? new Date(order.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    : '';
  const pay = order.payment_method === 'cod' ? 'Pay at counter' : 'Paid';
  const where = order.mode === 'pickup' ? 'Pickup' : 'Delivery';
  const place = order.mode === 'delivery' && order.address
    ? order.address
    : (order.branch && order.branch.address) || '';
  return `
    <div class="ticket-block">
    <article class="ticket">
      <header class="ticket__head">
        <span class="ticket__brand">GOLDCRUST</span>
        <span>${where}</span>
      </header>
      <div class="ticket__body">
        <p class="ticket__kicker">Ticket</p>
        <p class="ticket__code">${escapeHTML(ticketCode(order.ticket))}</p>
        <p class="ticket__for">${escapeHTML(order.name || '')}${when ? ` · ${escapeHTML(when)}` : ''}</p>
        <ol class="stages">
          ${ticketStages(order).map((label, i) => `
            <li class="${i < idx ? 'is-done' : ''} ${i === idx ? 'is-now' : ''}">
              <b></b><span>${label}</span>
            </li>`).join('')}
        </ol>
        <p class="ticket__note">${escapeHTML(ticketNote(order))}</p>
      </div>
      <div class="ticket__tear" aria-hidden="true"></div>
      <div class="ticket__foot">
        <ul class="ticket__items">
          ${(order.items || []).map(item => `
            <li>
              <span>${item.emoji || ''} ${item.qty} × ${escapeHTML(item.name)}</span>
              <small>${escapeHTML(item.option_text || '')}</small>
            </li>`).join('')}
        </ul>
        <div class="ticket__row"><span>${escapeHTML(order.branch?.name || '')}</span><span>${pay}</span></div>
        <div class="ticket__row ticket__place"><span>${escapeHTML(place)}</span></div>
        <div class="ticket__row ticket__total"><span>Total</span><span>${money(order.total || 0)}</span></div>
      </div>
    </article>
    <button type="button" class="btn btn--ghost btn--sm ticket-download" data-ticket="${escapeHTML(order.ticket)}">Download ticket</button>
    </div>`;
}

let ticketCanvasLoader;
function loadTicketCanvas() {
  if (window.html2canvas) return Promise.resolve();
  if (!ticketCanvasLoader) {
    ticketCanvasLoader = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Ticket image library failed to load'));
      document.head.append(script);
    });
  }
  return ticketCanvasLoader;
}

async function downloadTicket(article, code) {
  await loadTicketCanvas();
  const canvas = await window.html2canvas(article, {
    scale: 2,
    backgroundColor: '#23120a',
    useCORS: true,
  });
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
  if (!blob) throw new Error('empty');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Goldcrust-${code}.png`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

const escapeHTML = str => String(str).replace(/[&<>"']/g, c => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

const stars = (n, ink = false) =>
  `<span class="stars${ink ? ' stars--ink' : ''}">` +
  [1, 2, 3, 4, 5].map(i => `<span class="${i <= n ? '' : 'off'}">★</span>`).join('') +
  `</span>`;

const tagChip = t => {
  const map = {
    bestseller: ['tag--best', '★ Bestseller'],
    new:        ['tag--new', 'New'],
    spicy:      ['tag--spicy', '🌶 Spicy'],
    veg:        ['tag--veg', '● Veg'],
  };
  const hit = map[t];
  return hit ? `<span class="tag ${hit[0]}">${hit[1]}</span>` : '';
};

/* The plate always shows real food. `accent` is the small corner badge that
   flags what makes a dish different — heat, smoke, cheese, an occasion. */
const dish = (emoji, flat = false, accent = '') =>
  `<div class="dish${flat ? ' dish--flat' : ''}">
     <span class="dish__food">${emoji}</span>
     ${accent ? `<span class="dish__accent" aria-hidden="true">${accent}</span>` : ''}
   </div>`;

const ICONS = {
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
  bag:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l1 13H5L6 7z"/><path d="M9 7V5a3 3 0 0 1 6 0v2"/></svg>',
  heart:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20s-7-4.6-7-9.4A4 4 0 0 1 12 8a4 4 0 0 1 7 2.6C19 15.4 12 20 12 20z"/></svg>',
  thumb:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M7 10v9H4v-9h3zm3 9h7.3a2 2 0 0 0 2-1.6l1.2-6A2 2 0 0 0 18.5 9H14l.7-3.2A2 2 0 0 0 12.7 3L10 9v10z"/></svg>',
  home:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1v-8z"/></svg>',
  grid:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>',
  user:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="9" r="3.4"/><path d="M5 20a7 7 0 0 1 14 0"/><circle cx="12" cy="12" r="9.5"/></svg>',
  chat:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4V5z"/><circle cx="9" cy="10.5" r="1" fill="currentColor"/><circle cx="12.5" cy="10.5" r="1" fill="currentColor"/><circle cx="16" cy="10.5" r="1" fill="currentColor"/></svg>',
  pin:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s7-5.8 7-11a7 7 0 1 0-14 0c0 5.2 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>',
};

/* --------------------------------------------------------------- store --- */
const Store = {
  KEY: 'goldcrust.cart.v2',   // v1 keys could contain quotes — see lineKey()
  FAV: 'goldcrust.favs.v1',
  items: [],
  favs: [],
  listeners: [],

  load() {
    try { this.items = JSON.parse(localStorage.getItem(this.KEY)) || []; } catch { this.items = []; }
    try { this.favs  = JSON.parse(localStorage.getItem(this.FAV)) || []; } catch { this.favs  = []; }
  },
  save() {
    localStorage.setItem(this.KEY, JSON.stringify(this.items));
    localStorage.setItem(this.FAV, JSON.stringify(this.favs));
    this.listeners.forEach(fn => fn());
  },
  onChange(fn) { this.listeners.push(fn); fn(); },

  add(line) {
    // Identical item + identical options collapse into one line.
    const twin = this.items.find(i => i.key === line.key);
    if (twin) twin.qty += line.qty;
    else this.items.push(line);
    this.save();
  },
  setQty(key, qty) {
    const line = this.items.find(i => i.key === key);
    if (!line) return;
    if (qty <= 0) this.items = this.items.filter(i => i.key !== key);
    else line.qty = qty;
    this.save();
  },
  clear() { this.items = []; this.save(); },

  toggleFav(id) {
    this.favs = this.favs.includes(id) ? this.favs.filter(f => f !== id) : [...this.favs, id];
    this.save();
  },
  isFav(id) { return this.favs.includes(id); },

  get count()    { return this.items.reduce((n, i) => n + i.qty, 0); },
  get subtotal() { return this.items.reduce((n, i) => n + i.unit * i.qty, 0); },
  get bill() {
    const sub = this.subtotal;
    const delivery = sub === 0 || sub >= FEES.freeDeliveryOver ? 0 : FEES.delivery;
    const packaging = sub === 0 ? 0 : FEES.packaging;
    const tax = Math.round(sub * FEES.taxRate);
    return { sub, delivery, packaging, tax, total: sub + delivery + packaging + tax };
  },
};

/* --------------------------------------------------------------- toast --- */
function toast(msg, emoji = '🛒') {
  let host = $('.toast-host');
  if (!host) {
    host = document.createElement('div');
    host.className = 'toast-host';
    document.body.append(host);
  }
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `<span>${emoji}</span><span>${escapeHTML(msg)}</span>`;
  host.append(el);
  setTimeout(() => { el.classList.add('is-out'); setTimeout(() => el.remove(), 320); }, 2200);
}

/* ---------------------------------------------------------------- auth ----- */
const Auth = {
  user: null,
  listeners: [],
  onChange(fn) { this.listeners.push(fn); fn(this.user); },
  notify() { this.listeners.forEach(fn => fn(this.user)); },

  async check() {
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      this.user = data.logged_in ? data.user : null;
    } catch {
      this.user = null;
    }
    this.notify();
    return this.user;
  },

  async login(username, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    this.user = data.user;
    this.notify();
    await this.syncGuestTickets();
    return data.user;
  },

  async register(username, password) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    this.user = data.user;
    this.notify();
    await this.syncGuestTickets();
    return data.user;
  },

  async syncGuestTickets() {
    if (!this.user) return [];
    const ids = Tickets.ids();
    if (!ids || !ids.length) return [];
    try {
      const res = await fetch('/api/user/sync-tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_ids: ids }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.claimed || [];
      }
    } catch (e) {
      console.error('Failed to sync guest tickets', e);
    }
    return [];
  },

  async logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch {}
    this.user = null;
    this.notify();
  },
};

/* ----------------------------------------------------------- chrome -------
   Top bar, cart drawer and mobile tab bar are injected on every page so the
   markup stays in one place.
   ------------------------------------------------------------------------ */
function mountChrome(page) {
  const nav = [
    ['index.html', 'Home', 'home'],
    ['menu.html', 'Menu', 'menu'],
    ['tickets.html', 'Tickets', 'tickets'],
    ['kitchen.html', 'Kitchen', 'kitchen'],
  ];

  $('#chrome').innerHTML = `
    <header class="topbar">
      <div class="wrap topbar__inner">
        <a class="brand" href="index.html">
          <span class="brand__mark">🍗</span>
          <span class="brand__name">GOLDCRUST<span>Crispy · Golden</span></span>
        </a>

        <nav class="mainnav">
          ${nav.map(([href, label, id]) =>
            `<a href="${href}" class="${id === page ? 'is-active' : ''}">${label}</a>`).join('')}
        </nav>

        <div class="push"></div>

        <div class="locpill">
          ${ICONS.pin}
          <span><strong>Pune</strong><span>16 kitchens</span></span>
        </div>

        <div id="authSlot" class="auth-slot"></div>

        <button class="icon-btn cart-btn" id="openCart" aria-label="Open cart">
          ${ICONS.bag}
          <span class="cart-btn__count" id="cartCount">0</span>
        </button>
      </div>
    </header>

    <div class="overlay" id="overlay"></div>

    <aside class="drawer" id="drawer" aria-label="Your order">
      <div class="drawer__head">
        <h3>Your order</h3>
        <div class="push"></div>
        <button class="icon-btn" id="closeCart" aria-label="Close cart">✕</button>
      </div>
      <div class="drawer__body" id="cartBody"></div>
      <div class="drawer__foot" id="cartFoot"></div>
    </aside>

    <nav class="tabbar">
      <a href="menu.html" class="${page === 'menu' ? 'is-active' : ''}" aria-label="Menu">${ICONS.grid}</a>
      <a href="index.html#offers" aria-label="Offers">${ICONS.thumb}</a>
      <a href="index.html" class="tabbar__home" aria-label="Home">${ICONS.home}</a>
      <a href="tickets.html" class="${page === 'tickets' ? 'is-active' : ''}" aria-label="Tickets">${ICONS.user}</a>
      <a href="#" aria-label="Support">${ICONS.chat}</a>
    </nav>

    <div class="modal" id="authModal">
      <div class="modal__panel auth-modal__panel">
        <button class="icon-btn modal__close" id="closeAuth" aria-label="Close" type="button">✕</button>
        <div class="auth-box">
          <div class="auth-tabs">
            <button type="button" class="auth-tab is-active" id="tabLogin">Sign In</button>
            <button type="button" class="auth-tab" id="tabRegister">Create Account</button>
          </div>
          <form id="authForm" class="auth-form">
            <p class="hint" id="authHint">Sign in to save your orders and view all tickets across devices.</p>
            <div class="field">
              <label for="authUsername">Username</label>
              <input id="authUsername" type="text" placeholder="e.g. crunchy_fan" required autocomplete="username">
            </div>
            <div class="field">
              <label for="authPassword">Password</label>
              <input id="authPassword" type="password" placeholder="At least 6 characters" required autocomplete="current-password">
            </div>
            <p class="auth-error" id="authError" style="display:none"></p>
            <button type="submit" class="btn btn--primary btn--block btn--lg" id="authSubmit">Sign In</button>
          </form>
        </div>
      </div>
    </div>
  `;

  const overlay = $('#overlay'), drawer = $('#drawer');
  const openCart  = () => { overlay.classList.add('is-open'); drawer.classList.add('is-open'); };
  const closeCart = () => { overlay.classList.remove('is-open'); drawer.classList.remove('is-open'); };

  $('#openCart').addEventListener('click', openCart);
  $('#closeCart').addEventListener('click', closeCart);
  overlay.addEventListener('click', () => { closeCart(); closeModal(); closeAuth(); });

  const authSlot = $('#authSlot');
  const authModal = $('#authModal');
  const authForm = $('#authForm');
  const tabLogin = $('#tabLogin');
  const tabRegister = $('#tabRegister');
  const authHint = $('#authHint');
  const authSubmit = $('#authSubmit');
  const authError = $('#authError');
  let authMode = 'login';

  function setAuthMode(mode) {
    authMode = mode;
    authError.style.display = 'none';
    if (mode === 'login') {
      tabLogin.classList.add('is-active');
      tabRegister.classList.remove('is-active');
      authHint.textContent = 'Sign in to save your orders and track tickets across devices.';
      authSubmit.textContent = 'Sign In';
      $('#authPassword').autocomplete = 'current-password';
    } else {
      tabRegister.classList.add('is-active');
      tabLogin.classList.remove('is-active');
      authHint.textContent = 'Create a quick account so all your Goldcrust tickets stay saved.';
      authSubmit.textContent = 'Create Account';
      $('#authPassword').autocomplete = 'new-password';
    }
  }

  window.openAuth = (mode = 'login') => {
    setAuthMode(mode);
    authModal.classList.add('is-open');
    $('#authUsername').focus();
  };

  const closeAuth = () => {
    authModal.classList.remove('is-open');
    authError.style.display = 'none';
  };

  $('#closeAuth').addEventListener('click', closeAuth);
  authModal.addEventListener('click', e => {
    if (e.target === authModal) closeAuth();
  });
  tabLogin.addEventListener('click', () => setAuthMode('login'));
  tabRegister.addEventListener('click', () => setAuthMode('register'));

  authForm.addEventListener('submit', async e => {
    e.preventDefault();
    const username = $('#authUsername').value.trim();
    const password = $('#authPassword').value;
    authError.style.display = 'none';
    authSubmit.disabled = true;
    try {
      if (authMode === 'login') {
        await Auth.login(username, password);
      } else {
        await Auth.register(username, password);
      }
      closeAuth();
      authForm.reset();
    } catch (err) {
      authError.textContent = err.message;
      authError.style.display = 'block';
    } finally {
      authSubmit.disabled = false;
    }
  });

  function renderAuth(user) {
    if (!authSlot) return;
    if (user) {
      authSlot.innerHTML = `
        <div class="user-pill">
          <span class="user-name">👤 ${escapeHTML(user.username)}</span>
          <button type="button" class="btn-text" id="doLogout">Logout</button>
        </div>`;
      $('#doLogout')?.addEventListener('click', () => Auth.logout());
    } else {
      authSlot.innerHTML = `
        <button type="button" class="btn btn--ghost btn--sm auth-btn" id="openAuthBtn">Sign in</button>`;
      $('#openAuthBtn')?.addEventListener('click', () => window.openAuth('login'));
    }
  }

  Auth.onChange(renderAuth);
  Auth.check();

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeCart(); closeModal(); closeAuth(); }
  });

  window.openCart = openCart;

  Store.onChange(() => {
    const badge = $('#cartCount');
    badge.textContent = Store.count;
    badge.classList.toggle('is-on', Store.count > 0);
    renderCart();
  });
}

/* ----------------------------------------------------------- cart view --- */
function renderCart() {
  const body = $('#cartBody'), foot = $('#cartFoot');
  if (!body) return;

  if (!Store.items.length) {
    body.innerHTML = `
      <div class="empty">
        <i>🍗</i>
        <h4>Nothing in the bucket yet</h4>
        <p>Add something crispy and it will show up here.</p>
        <a class="btn btn--primary" href="menu.html" style="margin-top:20px">Browse the menu</a>
      </div>`;
    foot.innerHTML = '';
    return;
  }

  body.innerHTML = Store.items.map(line => `
    <div class="cart-line">
      <div class="cart-line__art">${line.emoji}</div>
      <div>
        <h4>${escapeHTML(line.name)}</h4>
        <p class="cart-line__opts">${escapeHTML(line.optionText || 'As it comes')}</p>
        <div class="cart-line__foot">
          <div class="stepper" data-key="${escapeHTML(line.key)}">
            <button data-step="-1" aria-label="Decrease">−</button>
            <span>${line.qty}</span>
            <button data-step="1" aria-label="Increase">+</button>
          </div>
          <span class="cart-line__price">${money(line.unit * line.qty)}</span>
        </div>
      </div>
    </div>
  `).join('');

  const b = Store.bill;
  foot.innerHTML = `
    <div class="totals">
      <div><span>Item total</span><span>${money(b.sub)}</span></div>
      <div><span>Delivery</span><span class="${b.delivery ? '' : 'is-free'}">${b.delivery ? money(b.delivery) : 'FREE'}</span></div>
      <div><span>Packaging</span><span>${money(b.packaging)}</span></div>
      <div><span>Taxes (5%)</span><span>${money(b.tax)}</span></div>
      <div class="grand"><span>To pay</span><span>${money(b.total)}</span></div>
    </div>
    ${b.delivery ? `<p style="font-size:.78rem;color:var(--cream-faint);margin-bottom:14px">
        Add ${money(FEES.freeDeliveryOver - b.sub)} more for free delivery.</p>` : ''}
    <a class="btn btn--primary btn--block btn--lg" href="checkout.html">Checkout · ${money(b.total)}</a>
  `;

  $$('.stepper', body).forEach(st => {
    st.addEventListener('click', e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const line = Store.items.find(i => i.key === st.dataset.key);
      Store.setQty(st.dataset.key, line.qty + Number(btn.dataset.step));
    });
  });
}

/* -------------------------------------------------------- item sheet ----- */
let modalEl = null;

/* Identity for a cart line: same dish + same options collapse into one row.
   Kept free of quotes and spaces so it can be dropped into a data- attribute. */
function lineKey(id, state) {
  return [
    id,
    ...Object.entries(state.choice).map(([g, c]) => `${g}-${c}`),
    ...state.addons.slice().sort(),
  ].join('__');
}

function optionGroupsFor(item) {
  const groups = [];
  if (['chicken', 'burgers', 'sides', 'combos', 'drinks'].includes(item.category)) groups.push('size');
  if (item.tags.includes('spicy') || item.category === 'chicken') groups.push('spice');
  groups.push('addons');
  return groups;
}

function openItem(id) {
  const item = MENU.find(i => i.id === id);
  if (!item) return;

  const groups = optionGroupsFor(item);
  const state = { qty: 1, choice: {}, addons: [] };
  groups.forEach(g => { if (!OPTION_GROUPS[g].multi) state.choice[g] = OPTION_GROUPS[g].choices[0].id; });

  if (!modalEl) {
    modalEl = document.createElement('div');
    modalEl.className = 'modal';
    modalEl.id = 'itemModal';
    document.body.append(modalEl);
  }

  const unit = () => {
    let p = item.price;
    Object.entries(state.choice).forEach(([g, cid]) => {
      p += OPTION_GROUPS[g].choices.find(c => c.id === cid).delta;
    });
    state.addons.forEach(aid => {
      p += OPTION_GROUPS.addons.choices.find(c => c.id === aid).delta;
    });
    return p;
  };

  modalEl.innerHTML = `
    <div class="modal__panel">
      <button class="modal__close" id="modalClose" aria-label="Close">✕</button>
      <div class="modal__art">
        <img class="modal__photo" src="assets/img/${item.id}.jpg" alt="${escapeHTML(item.name)}">
      </div>
      <div class="modal__body">
        <div class="modal__scroll">
          <div class="row gap-8" style="flex-wrap:wrap">${item.tags.map(tagChip).join('')}</div>
          <h2>${escapeHTML(item.name)}</h2>
          <div class="row gap-12" style="margin-bottom:12px">
            ${stars(item.rating)}
            <span style="font-size:.8rem;color:var(--cream-faint)">
              ${item.likes} likes · ${item.kcal} kcal · ${item.time} min
            </span>
          </div>
          <p class="modal__desc">${escapeHTML(item.desc)}</p>

          ${groups.map(g => {
            const grp = OPTION_GROUPS[g];
            return `
            <div class="optgroup">
              <div class="optgroup__label">
                <h4>${grp.label}</h4>
                <small>${grp.required ? 'Required' : 'Optional'}</small>
              </div>
              <div class="optlist">
                ${grp.choices.map((c, idx) => `
                  <label class="opt ${!grp.multi && idx === 0 ? 'is-on' : ''}"
                         data-group="${g}" data-choice="${c.id}">
                    <input type="${grp.multi ? 'checkbox' : 'radio'}" name="grp-${g}"
                           ${!grp.multi && idx === 0 ? 'checked' : ''}>
                    <span>${c.name}</span>
                    <b>${c.delta ? '+' + money(c.delta) : 'Included'}</b>
                  </label>`).join('')}
              </div>
            </div>`;
          }).join('')}
        </div>
        <div class="modal__foot">
          <div class="stepper stepper--solid" id="modalQty">
            <button data-step="-1" aria-label="Decrease">−</button>
            <span>1</span>
            <button data-step="1" aria-label="Increase">+</button>
          </div>
          <button class="btn btn--primary btn--lg" id="modalAdd" style="flex:1">
            Add · <span id="modalPrice">${money(unit())}</span>
          </button>
        </div>
      </div>
    </div>`;

  const refresh = () => {
    $('#modalPrice', modalEl).textContent = money(unit() * state.qty);
    $('#modalQty span', modalEl).textContent = state.qty;
  };

  /* Bound to `change` on the input rather than `click` on the label: a label
     click also forwards a synthetic click to its input, which would fire a
     click handler twice and cancel out every checkbox toggle. */
  $$('.opt', modalEl).forEach(opt => {
    const input = $('input', opt);
    input.addEventListener('change', () => {
      const { group, choice } = opt.dataset;
      if (OPTION_GROUPS[group].multi) {
        state.addons = input.checked
          ? [...state.addons, choice]
          : state.addons.filter(a => a !== choice);
        opt.classList.toggle('is-on', input.checked);
      } else {
        state.choice[group] = choice;
        $$(`.opt[data-group="${group}"]`, modalEl).forEach(o => o.classList.remove('is-on'));
        opt.classList.add('is-on');
      }
      refresh();
    });
  });

  $('#modalQty', modalEl).addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;
    state.qty = Math.max(1, state.qty + Number(btn.dataset.step));
    refresh();
  });

  $('#modalClose', modalEl).addEventListener('click', closeModal);

  $('#modalAdd', modalEl).addEventListener('click', () => {
    const parts = [
      ...Object.entries(state.choice).map(([g, cid]) =>
        OPTION_GROUPS[g].choices.find(c => c.id === cid).name),
      ...state.addons.map(aid => OPTION_GROUPS.addons.choices.find(c => c.id === aid).name),
    ];
    Store.add({
      key: lineKey(item.id, state),
      id: item.id, name: item.name, emoji: item.emoji,
      unit: unit(), qty: state.qty, optionText: parts.join(' · '),
      choices: { ...state.choice },
      addons: [...state.addons],
    });
    closeModal();
    toast(`${item.name} added`, '✅');
  });

  $('#overlay').classList.add('is-open');
  void modalEl.offsetHeight;          // flush layout so the transition has a start state
  modalEl.classList.add('is-open');
}

function closeModal() {
  if (modalEl) modalEl.classList.remove('is-open');
  const drawerOpen = $('#drawer')?.classList.contains('is-open');
  if (!drawerOpen) $('#overlay')?.classList.remove('is-open');
}

/* Quick-add straight from a card, using the cheapest defaults. */
function quickAdd(id) {
  const item = MENU.find(i => i.id === id);
  Store.add({
    key: item.id + '__default',
    id: item.id, name: item.name, emoji: item.emoji,
    unit: item.price, qty: 1, optionText: 'Regular',
    choices: {},
    addons: [],
  });
  toast(`${item.name} added`, '✅');
}

/* ------------------------------------------------------- card renderers -- */
function foodCard(item) {
  return `
    <article class="food-card" data-id="${item.id}">
      <div class="food-card__art">
        <div class="food-card__tags">${item.tags.slice(0, 2).map(tagChip).join('')}</div>
        <button class="food-card__fav ${Store.isFav(item.id) ? 'is-on' : ''}"
                data-fav="${item.id}" aria-label="Save ${escapeHTML(item.name)}">${ICONS.heart}</button>
        <button class="dish-open" data-open="${item.id}" style="width:100%"
                aria-label="View ${escapeHTML(item.name)}">${dish(item.emoji, false, item.accent)}</button>
      </div>
      <div class="food-card__body">
        <h3>${escapeHTML(item.name)}</h3>
        <p class="food-card__desc">${escapeHTML(item.desc)}</p>
        <div class="food-card__meta">${stars(item.rating)}<span>${item.likes}</span><span>· ${item.time} min</span></div>
        <div class="food-card__foot">
          <span class="price">${money(item.price)}${item.mrp ? `<s>${money(item.mrp)}</s>` : ''}</span>
          <button class="btn btn--primary btn--sm push" data-open="${item.id}">Add +</button>
        </div>
      </div>
    </article>`;
}

function featureCard(item) {
  return `
    <article class="feature-card">
      <button class="feature-card__like" data-fav="${item.id}"
              aria-label="Like ${escapeHTML(item.name)}">${ICONS.thumb}</button>
      <div class="feature-card__body">
        ${stars(item.rating, true)}
        <h3>${escapeHTML(item.name)}</h3>
        <p class="feature-card__meta">${item.likes} likes</p>
        <p class="feature-card__price">${money(item.price)}</p>
        <button class="btn btn--light btn--sm" data-open="${item.id}">Got it</button>
      </div>
      <div class="feature-card__art">${dish(item.emoji, false, item.accent)}</div>
    </article>`;
}

function favRow(item) {
  return `
    <article class="fav-row">
      <div class="fav-row__art">${dish(item.emoji, true, item.accent)}</div>
      <div>
        ${stars(item.rating)}
        <h3>${escapeHTML(item.name)}</h3>
        <p class="fav-row__meta">${item.likes} likes · ${money(item.price)}</p>
      </div>
      <div class="fav-row__right">
        <span class="price">${money(item.price)}</span>
        <button class="btn btn--light btn--sm" data-open="${item.id}">Got it</button>
      </div>
    </article>`;
}

/* Card clicks are delegated so re-rendered grids need no re-binding. */
document.addEventListener('click', async e => {
  const save = e.target.closest('.ticket-download');
  if (save) {
    const article = save.closest('.ticket-block')?.querySelector('.ticket');
    if (!article) return;
    save.disabled = true;
    const label = save.textContent;
    save.textContent = 'Saving…';
    try {
      await downloadTicket(article, save.dataset.ticket || 'ticket');
      toast('Ticket downloaded', '🎟️');
    } catch {
      toast('Could not download the ticket', '❌');
    }
    save.disabled = false;
    save.textContent = label;
    return;
  }

  const open = e.target.closest('[data-open]');
  if (open) { openItem(open.dataset.open); return; }

  const fav = e.target.closest('[data-fav]');
  if (fav) {
    const id = fav.dataset.fav;
    Store.toggleFav(id);
    fav.classList.toggle('is-on', Store.isFav(id));
    toast(Store.isFav(id) ? 'Saved to favourites' : 'Removed from favourites', '❤️');
  }
});

Store.load();
