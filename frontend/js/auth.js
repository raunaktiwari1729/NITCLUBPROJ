const Auth = {
  save(token, user) {
    localStorage.setItem('ccc_token', token);
    localStorage.setItem('ccc_user', JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem('ccc_token');
    localStorage.removeItem('ccc_user');
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('ccc_user')); } catch { return null; }
  },
  getToken() { return localStorage.getItem('ccc_token'); },
  isLoggedIn() { return !!this.getToken() && !!this.getUser(); },
  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = '/login.html?next=' + encodeURIComponent(window.location.pathname);
    }
  },
  redirectIfLoggedIn() {
    if (this.isLoggedIn()) window.location.href = '/dashboard.html';
  }
};
