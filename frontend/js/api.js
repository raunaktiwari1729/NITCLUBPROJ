// API_BASE is defined in config.js (loaded before this script in every HTML page)

const api = {
  async req(method, path, body, auth = true) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth) { const tok = localStorage.getItem('ccc_token'); if (tok) headers['Authorization'] = `Bearer ${tok}`; }
    const res = await fetch(API_BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  },
  get:   (p, auth=true) => api.req('GET',    p, null, auth),
  post:  (p, b, auth=true) => api.req('POST', p, b,   auth),
  patch: (p, b)          => api.req('PATCH',  p, b),
  del:   (p)             => api.req('DELETE', p),

  // Auth
  signup:        b => api.post('/api/auth/signup',  b, false),
  login:         b => api.post('/api/auth/login',   b, false),
  me:            () => api.get('/api/auth/me'),
  updateProfile: b => api.patch('/api/auth/profile', b),

  // Users
  searchUsers: q  => api.get(`/api/users/search?q=${encodeURIComponent(q)}`),
  getUser:     id => api.get(`/api/users/${id}`),
  profile:     id => api.get(`/api/profile/${id}`),

  // Clubs
  clubs:      q    => api.get(`/api/clubs${q||''}`, false),
  club:       id   => api.get(`/api/clubs/${id}`,   false),
  updateClub: (id,b) => api.patch(`/api/clubs/${id}`, b),
  createClub: b    => api.post('/api/clubs', b),
  deleteClub: id   => api.del(`/api/clubs/${id}`),

  // Quiz
  quizQuestions: () => api.get('/api/quiz/questions', false),
  submitQuiz:    b  => api.post('/api/quiz/submit', b),
  quizResult:    () => api.get('/api/quiz/result'),

  // Bookmarks
  bookmarks:      () => api.get('/api/bookmarks'),
  addBookmark:    b  => api.post('/api/bookmarks', b),
  removeBookmark: id => api.del(`/api/bookmarks/${id}`),

  // Watchlist
  watchlist:       () => api.get('/api/watchlist'),
  addWatchlist:    b  => api.post('/api/watchlist', b),
  updateWatchlist: (id,b) => api.patch(`/api/watchlist/${id}`, b),
  removeWatchlist: id => api.del(`/api/watchlist/${id}`),

  // Forum posts  ← renamed: post() → getPost() to avoid collision with HTTP post()
  posts:       q  => api.get(`/api/posts/v2${q||''}`, false),
  getPost:     id => api.get(`/api/posts/${id}`,       false),
  createPost:  b  => api.post('/api/posts', b),
  createAnonPost: b => api.post('/api/posts/anon', b),
  upvote:      id => api.post(`/api/posts/${id}/upvote`, {}),
  deletePost:  id => api.del(`/api/posts/${id}`),

  // Comments
  comments:   id    => api.get(`/api/posts/${id}/comments`, false),
  addComment: (id,b) => api.post(`/api/posts/${id}/comments`, b),
  delComment: id    => api.del(`/api/comments/${id}`),

  // Events
  events:           q  => api.get(`/api/events${q||''}`, false),
  createEvent:      b  => api.post('/api/events', b),
  deleteEvent:      id => api.del(`/api/events/${id}`),
  toggleInterested: id => api.post(`/api/events/${id}/interested`, {}),

  // Reviews
  reviews:      id => api.get(`/api/reviews/${id}`, false),
  createReview: b  => api.post('/api/reviews', b),
  deleteReview: id => api.del(`/api/reviews/${id}`),

  // Polls
  polls:      () => api.get('/api/polls', false),
  createPoll: b  => api.post('/api/polls', b),
  votePoll:   (id,idx) => api.post(`/api/polls/${id}/vote/${idx}`, {}),
  deletePoll: id => api.del(`/api/polls/${id}`),

  // Messages
  sendDM:      b  => api.post('/api/dm', b),
  dmThread:    id => api.get(`/api/dm/${id}`),
  dmThreads:   () => api.get('/api/dm/threads/list'),
  unreadCount: () => api.get('/api/dm/unread/count'),

  // AI Chat
  chat: b => api.post('/api/chat', b),
};
