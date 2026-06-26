// ── API helper ────────────────────────────────────────────────────────────────
const api = {
  async req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const r = await fetch('/api' + path, opts);
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || r.statusText);
    }
    if (r.status === 204) return null;
    return r.json();
  },
  get:    (p)      => api.req('GET',    p),
  post:   (p, b)   => api.req('POST',   p, b),
  put:    (p, b)   => api.req('PUT',    p, b),
  delete: (p)      => api.req('DELETE', p),
};

// ── State ──────────────────────────────────────────────────────────────────────
const state = {
  projects: [], requirements: [], persons: [], commits: [], tests: [],
  tickets: [], currentPage: 'dashboard', currentProject: null,
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function badge(cls, label) {
  return `<span class="badge badge-${cls}">${esc(label)}</span>`;
}

function statusBadge(s)   { return badge(s, s.replace('_',' ')); }
function priorityBadge(p) { return badge(p, p); }
function resultBadge(r)   { return badge(r, r); }
function typeBadge(t)     { return badge(t, t); }

function fmtDate(d) {
  if (!d) return '–';
  return new Date(d).toLocaleString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' });
}

function fmtDateShort(d) {
  if (!d) return '–';
  return new Date(d).toLocaleDateString('de-DE');
}

function avatar(name) {
  return (name || '?').charAt(0).toUpperCase();
}

function notify(msg, type = 'success') {
  const el = document.createElement('div');
  el.style.cssText = `position:fixed;top:18px;right:22px;z-index:9999;padding:12px 20px;border-radius:8px;font-size:13px;font-weight:600;box-shadow:0 4px 20px rgba(0,0,0,.4);background:${type==='success'?'#22c55e':type==='error'?'#ef4444':'#4f6ef7'};color:#fff;transition:opacity .4s`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 2800);
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function showModal(html, onClose) {
  const bd = document.createElement('div');
  bd.className = 'modal-backdrop';
  bd.innerHTML = html;
  bd.addEventListener('click', e => { if (e.target === bd) { bd.remove(); onClose?.(); } });
  document.body.appendChild(bd);
  return bd;
}

function closeModal() {
  document.querySelector('.modal-backdrop')?.remove();
}

// ── Navigation ────────────────────────────────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('#sidebar nav a').forEach(a => a.classList.toggle('active', a.dataset.page === page));
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + page));
  state.currentPage = page;
  renderPage(page);
}

async function renderPage(page) {
  await loadAll();
  switch (page) {
    case 'dashboard':     renderDashboard(); break;
    case 'tickets':       renderTickets(); break;
    case 'requirements':  renderRequirements(); break;
    case 'commits':       renderCommits(); break;
    case 'tests':         renderTests(); break;
    case 'persons':       renderPersons(); break;
    case 'projects':      renderProjects(); break;
  }
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadAll() {
  [state.projects, state.requirements, state.persons, state.commits, state.tests] =
    await Promise.all([
      api.get('/projects/'),
      api.get('/requirements/'),
      api.get('/persons/'),
      api.get('/commits/'),
      api.get('/tests/'),
    ]);
  const qs = state.currentProject ? `?project_id=${state.currentProject}` : '';
  state.tickets = await api.get('/tickets/' + qs);
}

// ── Project selector ──────────────────────────────────────────────────────────
function renderProjectSelector() {
  const sel = $('project-filter');
  if (!sel) return;
  sel.innerHTML = '<option value="">Alle Projekte</option>' +
    state.projects.map(p => `<option value="${p.id}" ${state.currentProject==p.id?'selected':''}>${esc(p.key)} – ${esc(p.name)}</option>`).join('');
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function renderDashboard() {
  const t = state.tickets;
  const open   = t.filter(x => x.status === 'open').length;
  const ip     = t.filter(x => x.status === 'in_progress').length;
  const closed = t.filter(x => x.status === 'closed').length;
  const crit   = t.filter(x => x.priority === 'critical').length;

  $('page-dashboard').innerHTML = `
    <div class="metrics">
      <div class="metric"><div class="value">${t.length}</div><div class="label">Tickets gesamt</div></div>
      <div class="metric"><div class="value" style="color:var(--info)">${open}</div><div class="label">Offen</div></div>
      <div class="metric"><div class="value" style="color:var(--accent)">${ip}</div><div class="label">In Bearbeitung</div></div>
      <div class="metric"><div class="value" style="color:var(--success)">${closed}</div><div class="label">Geschlossen</div></div>
      <div class="metric"><div class="value" style="color:var(--danger)">${crit}</div><div class="label">Kritisch</div></div>
      <div class="metric"><div class="value" style="color:var(--warning)">${state.commits.length}</div><div class="label">Commits</div></div>
      <div class="metric"><div class="value" style="color:#a78bfa">${state.requirements.length}</div><div class="label">Anforderungen</div></div>
      <div class="metric"><div class="value" style="color:var(--info)">${state.tests.length}</div><div class="label">Tests</div></div>
    </div>

    <div class="card">
      <div class="card-title">🔗 Letzte Tickets mit Traceability</div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Schlüssel</th><th>Titel</th><th>Status</th><th>Anford.</th><th>Commits</th><th>Tests</th>
          </tr></thead>
          <tbody>
            ${t.slice(0, 10).map(tk => `
              <tr onclick="openTicketDetail(${tk.id})">
                <td><span class="ticket-key">${esc(tk.key)}</span></td>
                <td>${esc(tk.title)}</td>
                <td>${statusBadge(tk.status)}</td>
                <td>${tk.req_count}</td>
                <td>${tk.commit_count}</td>
                <td>${tk.test_count}</td>
              </tr>`).join('') || '<tr><td colspan="6" class="empty-state">Noch keine Tickets</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;
}

// ── Tickets ───────────────────────────────────────────────────────────────────
function renderTickets() {
  renderProjectSelector();
  const cont = $('page-tickets');
  cont.innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Tickets</h3>
      <button class="btn btn-primary" onclick="openNewTicketModal()">＋ Neues Ticket</button>
    </div>
    <div class="filter-bar">
      <input type="text" id="ticket-search" placeholder="Suchen …" oninput="filterTickets()">
      <select id="ticket-status-filter" onchange="filterTickets()">
        <option value="">Alle Status</option>
        <option>open</option><option>in_progress</option><option>in_review</option>
        <option>testing</option><option>closed</option><option>rejected</option>
      </select>
      <select id="ticket-priority-filter" onchange="filterTickets()">
        <option value="">Alle Prioritäten</option>
        <option>low</option><option>medium</option><option>high</option><option>critical</option>
      </select>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table id="ticket-table">
          <thead><tr>
            <th>Schlüssel</th><th>Titel</th><th>Status</th><th>Priorität</th>
            <th>Bearbeiter</th><th>Anford.</th><th>Commits</th><th>Tests</th><th>Aktualisiert</th>
          </tr></thead>
          <tbody id="ticket-tbody"></tbody>
        </table>
      </div>
    </div>`;
  filterTickets();
}

function filterTickets() {
  const search   = ($('ticket-search')?.value || '').toLowerCase();
  const status   = $('ticket-status-filter')?.value || '';
  const priority = $('ticket-priority-filter')?.value || '';
  let rows = state.tickets;
  if (search)   rows = rows.filter(t => t.key.toLowerCase().includes(search) || t.title.toLowerCase().includes(search));
  if (status)   rows = rows.filter(t => t.status === status);
  if (priority) rows = rows.filter(t => t.priority === priority);

  $('ticket-tbody').innerHTML = rows.map(t => `
    <tr onclick="openTicketDetail(${t.id})">
      <td><span class="ticket-key">${esc(t.key)}</span></td>
      <td>${esc(t.title)}</td>
      <td>${statusBadge(t.status)}</td>
      <td>${priorityBadge(t.priority)}</td>
      <td>${t.assignee ? esc(t.assignee.username) : '<span class="text-muted">–</span>'}</td>
      <td>${t.req_count}</td>
      <td>${t.commit_count}</td>
      <td>${t.test_count}</td>
      <td class="text-muted">${fmtDateShort(t.updated_at)}</td>
    </tr>`).join('') || '<tr><td colspan="9" class="empty-state">Keine Tickets gefunden</td></tr>';
}

// ── Ticket detail modal ────────────────────────────────────────────────────────
async function openTicketDetail(id) {
  const ticket = await api.get(`/tickets/${id}`);
  const trace  = await api.get(`/tickets/${id}/traceability`);

  const reqOpts  = state.requirements.map(r => `<option value="${r.id}">${esc(r.key)} – ${esc(r.title)}</option>`).join('');
  const commOpts = state.commits.map(c => `<option value="${c.id}">${esc(c.sha.slice(0,10))} – ${esc(c.message.slice(0,60))}</option>`).join('');
  const testOpts = state.tests.map(t => `<option value="${t.id}">[${t.test_type}] ${esc(t.title)}</option>`).join('');
  const persOpts = state.persons.map(p => `<option value="${p.id}">${esc(p.username)}</option>`).join('');

  const bd = showModal(`
    <div class="modal modal-wide">
      <div class="modal-header">
        <div>
          <span class="ticket-key" style="font-size:14px">${esc(ticket.key)}</span>
          <span class="modal-title" style="margin-left:10px">${esc(ticket.title)}</span>
        </div>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>

      <div class="flex gap-8 mb-20" style="flex-wrap:wrap">
        ${statusBadge(ticket.status)}
        ${priorityBadge(ticket.priority)}
        <span class="text-muted text-sm">Bearbeiter: ${ticket.assignee?.username || '–'}</span>
        <span class="text-muted text-sm">Erstellt: ${fmtDate(ticket.created_at)}</span>
      </div>

      <div class="tabs">
        <div class="tab active" onclick="switchTab(this,'tab-details')">Details</div>
        <div class="tab" onclick="switchTab(this,'tab-trace')">🔗 Traceability</div>
        <div class="tab" onclick="switchTab(this,'tab-commits')">Commits</div>
        <div class="tab" onclick="switchTab(this,'tab-tests')">Tests</div>
        <div class="tab" onclick="switchTab(this,'tab-comments')">Kommentare (${ticket.comments.length})</div>
      </div>

      <!-- DETAILS -->
      <div id="tab-details" class="tab-content active">
        <div class="form-group">
          <label>Beschreibung</label>
          <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:13px;white-space:pre-wrap">${esc(ticket.description) || '<em style="color:var(--muted)">Keine Beschreibung</em>'}</div>
        </div>
        <div class="form-group">
          <label>Verknüpfte Anforderungen</label>
          ${ticket.requirements.length ? ticket.requirements.map(r => `
            <div class="trace-item" style="margin-bottom:6px">
              <strong class="ticket-key">${esc(r.key)}</strong>
              ${r.url ? `<a href="${esc(r.url)}" target="_blank" style="margin-left:8px;font-size:11px">🔗 Link</a>` : ''}
              <div style="margin-top:4px;color:var(--muted);font-size:12px">${esc(r.title)}</div>
            </div>`).join('') : '<div class="text-muted">Keine Anforderungen verknüpft</div>'}
        </div>
        <div class="flex gap-8" style="justify-content:flex-end;margin-top:12px">
          <button class="btn btn-ghost btn-sm" onclick="openEditTicketModal(${ticket.id})">✏️ Bearbeiten</button>
          <button class="btn btn-danger btn-sm" onclick="deleteTicket(${ticket.id})">🗑 Löschen</button>
        </div>
      </div>

      <!-- TRACEABILITY -->
      <div id="tab-trace" class="tab-content">
        <div style="padding:8px 0">
          <div class="trace-label" style="font-size:12px;color:var(--accent2);font-weight:700;margin-bottom:12px">📋 ANFORDERUNGEN → TICKET → COMMITS → TESTS</div>

          <div style="margin-bottom:16px">
            <div class="trace-label">ANFORDERUNGEN</div>
            ${trace.requirements.length ? trace.requirements.map(r => `
              <div class="trace-item">
                <strong class="ticket-key">${esc(r.key)}</strong> ${esc(r.title)}
                ${r.url ? `<a href="${esc(r.url)}" target="_blank" style="margin-left:8px;font-size:11px;color:var(--info)">🔗 Spec</a>` : ''}
              </div>`).join('') : '<div class="text-muted text-sm">Keine Anforderungen</div>'}
          </div>

          <div style="margin-bottom:16px">
            <div class="trace-label">TICKET</div>
            <div class="trace-item">
              <span class="ticket-key">${esc(trace.ticket.key)}</span>
              <span style="margin-left:10px">${esc(trace.ticket.title)}</span>
              <span style="margin-left:10px">${statusBadge(trace.ticket.status)}</span>
            </div>
          </div>

          <div style="margin-bottom:16px">
            <div class="trace-label">GIT COMMITS</div>
            ${trace.commits.length ? trace.commits.map(c => `
              <div class="trace-item">
                ${c.git_url ? `<a href="${esc(c.git_url)}" target="_blank" class="sha-link">${esc(c.sha)}</a>` : `<span class="sha-link">${esc(c.sha)}</span>`}
                <strong>${esc(c.message.split('\n')[0])}</strong>
                <div class="text-sm text-muted" style="margin-top:3px">
                  ${c.author ? `👤 ${esc(c.author)}` : ''} ${c.committed_at ? `· 📅 ${fmtDate(c.committed_at)}` : ''}
                </div>
              </div>`).join('') : '<div class="text-muted text-sm">Keine Commits</div>'}
          </div>

          <div>
            <div class="trace-label">TESTS</div>
            ${trace.tests.length ? trace.tests.map(t => `
              <div class="trace-item">
                ${typeBadge(t.type)} ${resultBadge(t.result)}
                <strong style="margin-left:8px">${esc(t.title)}</strong>
                <div class="text-sm text-muted" style="margin-top:3px">
                  ${t.tester ? `👤 ${esc(t.tester)}` : ''} ${t.run_at ? `· 📅 ${fmtDate(t.run_at)}` : ''}
                </div>
              </div>`).join('') : '<div class="text-muted text-sm">Keine Tests</div>'}
          </div>
        </div>
      </div>

      <!-- COMMITS -->
      <div id="tab-commits" class="tab-content">
        <div class="form-group">
          <label>Commit verknüpfen</label>
          <div class="flex gap-8">
            <select id="link-commit-sel" style="flex:1">${commOpts}</select>
            <button class="btn btn-primary btn-sm" onclick="linkCommitToTicket(${ticket.id})">Verknüpfen</button>
          </div>
        </div>
        <div id="ticket-commits-list">
          ${ticket.commits.map(c => `
            <div class="trace-item flex align-center justify-between">
              <div>
                ${c.git_url ? `<a href="${esc(c.git_url)}" target="_blank" class="sha-link">${esc(c.sha.slice(0,10))}</a>` : `<span class="sha-link">${esc(c.sha.slice(0,10))}</span>`}
                <span style="margin-left:8px">${esc(c.message.split('\n')[0].slice(0,80))}</span>
                <div class="text-sm text-muted">${c.author ? esc(c.author.username) : ''} · ${fmtDate(c.committed_at)}</div>
              </div>
              <button class="btn btn-ghost btn-xs" onclick="unlinkCommit(${ticket.id}, ${c.id})">✕</button>
            </div>`).join('') || '<div class="text-muted">Noch keine Commits</div>'}
        </div>
      </div>

      <!-- TESTS -->
      <div id="tab-tests" class="tab-content">
        <div class="form-group">
          <label>Test verknüpfen</label>
          <div class="flex gap-8">
            <select id="link-test-sel" style="flex:1">${testOpts}</select>
            <button class="btn btn-primary btn-sm" onclick="linkTestToTicket(${ticket.id})">Verknüpfen</button>
          </div>
        </div>
        <div id="ticket-tests-list">
          ${ticket.tests.map(t => `
            <div class="trace-item flex align-center justify-between">
              <div>
                ${typeBadge(t.test_type)} ${resultBadge(t.result)}
                <span style="margin-left:8px">${esc(t.title)}</span>
                <div class="text-sm text-muted">${t.tester ? esc(t.tester.username) : ''} · ${fmtDate(t.run_at)}</div>
              </div>
              <button class="btn btn-ghost btn-xs" onclick="unlinkTest(${ticket.id}, ${t.id})">✕</button>
            </div>`).join('') || '<div class="text-muted">Noch keine Tests</div>'}
        </div>
      </div>

      <!-- COMMENTS -->
      <div id="tab-comments" class="tab-content">
        <div id="comments-stream">
          ${ticket.comments.map(c => `
            <div class="comment">
              <div class="comment-avatar">${avatar(c.author?.username)}</div>
              <div class="comment-body">
                <div class="comment-meta">${c.author ? esc(c.author.username) : 'Anonym'} · ${fmtDate(c.created_at)}</div>
                <div class="comment-text">${esc(c.body)}</div>
              </div>
            </div>`).join('')}
        </div>
        <div style="margin-top:16px">
          <div class="form-group">
            <label>Bearbeiter</label>
            <select id="comment-author-sel">
              <option value="">– anonym –</option>
              ${persOpts}
            </select>
          </div>
          <div class="form-group">
            <textarea id="comment-text" placeholder="Kommentar schreiben …" rows="4"></textarea>
          </div>
          <button class="btn btn-primary btn-sm" onclick="submitComment(${ticket.id})">Kommentar senden</button>
        </div>
      </div>
    </div>`);
}

function switchTab(el, tabId) {
  const modal = el.closest('.modal');
  modal.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  modal.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  modal.querySelector('#' + tabId).classList.add('active');
}

// ── New / Edit Ticket modal ───────────────────────────────────────────────────
function openNewTicketModal() {
  const projOpts = state.projects.map(p => `<option value="${p.id}">${esc(p.key)} – ${esc(p.name)}</option>`).join('');
  const persOpts = state.persons.map(p => `<option value="${p.id}">${esc(p.username)}</option>`).join('');
  const reqList  = state.requirements.map(r => `
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:6px;cursor:pointer">
      <input type="checkbox" value="${r.id}" style="width:auto;margin-top:3px">
      <span><strong class="ticket-key">${esc(r.key)}</strong> ${esc(r.title)}</span>
    </label>`).join('');

  showModal(`
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title">Neues Ticket</span>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="form-group">
        <label>Projekt *</label>
        <select id="nt-project">${projOpts}</select>
      </div>
      <div class="form-group">
        <label>Titel *</label>
        <input type="text" id="nt-title" placeholder="Ticket-Titel …">
      </div>
      <div class="form-group">
        <label>Beschreibung</label>
        <textarea id="nt-desc" rows="4" placeholder="Beschreibung …"></textarea>
      </div>
      <div class="flex gap-8">
        <div class="form-group" style="flex:1">
          <label>Status</label>
          <select id="nt-status">
            <option value="open">open</option><option value="in_progress">in_progress</option>
            <option value="in_review">in_review</option><option value="testing">testing</option>
            <option value="closed">closed</option><option value="rejected">rejected</option>
          </select>
        </div>
        <div class="form-group" style="flex:1">
          <label>Priorität</label>
          <select id="nt-priority">
            <option value="low">low</option><option value="medium" selected>medium</option>
            <option value="high">high</option><option value="critical">critical</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>Bearbeiter</label>
        <select id="nt-assignee"><option value="">– kein –</option>${persOpts}</select>
      </div>
      <div class="form-group">
        <label>Anforderungen verknüpfen</label>
        <div style="max-height:180px;overflow-y:auto;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px" id="nt-reqs">
          ${reqList || '<div class="text-muted text-sm">Keine Anforderungen vorhanden</div>'}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewTicket()">Ticket erstellen</button>
      </div>
    </div>`);
}

async function saveNewTicket() {
  const projId = parseInt($('nt-project').value);
  const title  = $('nt-title').value.trim();
  if (!title) { notify('Titel ist pflicht', 'error'); return; }
  const reqIds = [...document.querySelectorAll('#nt-reqs input:checked')].map(x => parseInt(x.value));
  try {
    await api.post('/tickets/', {
      project_id: projId,
      title, description: $('nt-desc').value,
      status: $('nt-status').value,
      priority: $('nt-priority').value,
      assignee_id: $('nt-assignee').value ? parseInt($('nt-assignee').value) : null,
      requirement_ids: reqIds,
    });
    closeModal();
    notify('Ticket erstellt');
    await renderPage('tickets');
  } catch(e) { notify(e.message, 'error'); }
}

async function openEditTicketModal(id) {
  const t = await api.get(`/tickets/${id}`);
  const projOpts = state.projects.map(p => `<option value="${p.id}" ${p.id==t.project_id?'selected':''}>${esc(p.key)} – ${esc(p.name)}</option>`).join('');
  const persOpts = state.persons.map(p => `<option value="${p.id}" ${p.id==t.assignee_id?'selected':''}>${esc(p.username)}</option>`).join('');
  const linkedIds = new Set(t.requirements.map(r => r.id));
  const reqList = state.requirements.map(r => `
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:6px;cursor:pointer">
      <input type="checkbox" value="${r.id}" ${linkedIds.has(r.id)?'checked':''} style="width:auto;margin-top:3px">
      <span><strong class="ticket-key">${esc(r.key)}</strong> ${esc(r.title)}</span>
    </label>`).join('');

  closeModal();
  showModal(`
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title">Ticket bearbeiten – ${esc(t.key)}</span>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="form-group">
        <label>Titel *</label>
        <input type="text" id="et-title" value="${esc(t.title)}">
      </div>
      <div class="form-group">
        <label>Beschreibung</label>
        <textarea id="et-desc" rows="4">${esc(t.description)}</textarea>
      </div>
      <div class="flex gap-8">
        <div class="form-group" style="flex:1">
          <label>Status</label>
          <select id="et-status">
            ${['open','in_progress','in_review','testing','closed','rejected'].map(s=>`<option value="${s}" ${t.status===s?'selected':''}>${s}</option>`).join('')}
          </select>
        </div>
        <div class="form-group" style="flex:1">
          <label>Priorität</label>
          <select id="et-priority">
            ${['low','medium','high','critical'].map(p=>`<option value="${p}" ${t.priority===p?'selected':''}>${p}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>Bearbeiter</label>
        <select id="et-assignee"><option value="">– kein –</option>${persOpts}</select>
      </div>
      <div class="form-group">
        <label>Anforderungen</label>
        <div style="max-height:180px;overflow-y:auto;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px" id="et-reqs">
          ${reqList || '<div class="text-muted text-sm">Keine Anforderungen</div>'}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveEditTicket(${id})">Speichern</button>
      </div>
    </div>`);
}

async function saveEditTicket(id) {
  const title = $('et-title').value.trim();
  if (!title) { notify('Titel ist pflicht', 'error'); return; }
  const reqIds = [...document.querySelectorAll('#et-reqs input:checked')].map(x => parseInt(x.value));
  try {
    await api.put(`/tickets/${id}`, {
      title, description: $('et-desc').value,
      status: $('et-status').value, priority: $('et-priority').value,
      assignee_id: $('et-assignee').value ? parseInt($('et-assignee').value) : null,
      requirement_ids: reqIds,
    });
    closeModal();
    notify('Ticket gespeichert');
    await renderPage(state.currentPage);
  } catch(e) { notify(e.message, 'error'); }
}

async function deleteTicket(id) {
  if (!confirm('Ticket wirklich löschen?')) return;
  await api.delete(`/tickets/${id}`);
  closeModal();
  notify('Ticket gelöscht');
  await renderPage('tickets');
}

// ── Link commit / test to ticket ──────────────────────────────────────────────
async function linkCommitToTicket(ticketId) {
  const cid = parseInt($('link-commit-sel').value);
  if (!cid) return;
  try {
    await api.post(`/tickets/${ticketId}/commits`, { ids: [cid] });
    notify('Commit verknüpft');
    closeModal();
    await openTicketDetail(ticketId);
  } catch(e) { notify(e.message, 'error'); }
}

async function unlinkCommit(ticketId, commitId) {
  await api.delete(`/tickets/${ticketId}/commits/${commitId}`);
  notify('Commit entfernt');
  closeModal();
  await openTicketDetail(ticketId);
}

async function linkTestToTicket(ticketId) {
  const tid = parseInt($('link-test-sel').value);
  if (!tid) return;
  try {
    await api.post(`/tickets/${ticketId}/tests`, { ids: [tid] });
    notify('Test verknüpft');
    closeModal();
    await openTicketDetail(ticketId);
  } catch(e) { notify(e.message, 'error'); }
}

async function unlinkTest(ticketId, testId) {
  await api.delete(`/tickets/${ticketId}/tests/${testId}`);
  notify('Test entfernt');
  closeModal();
  await openTicketDetail(ticketId);
}

async function submitComment(ticketId) {
  const body = $('comment-text').value.trim();
  if (!body) return;
  const authorId = $('comment-author-sel').value ? parseInt($('comment-author-sel').value) : null;
  try {
    await api.post(`/tickets/${ticketId}/comments`, { body, author_id: authorId });
    notify('Kommentar gespeichert');
    closeModal();
    await openTicketDetail(ticketId);
  } catch(e) { notify(e.message, 'error'); }
}

// ── Requirements ──────────────────────────────────────────────────────────────
function renderRequirements() {
  const projOpts = state.projects.map(p => `<option value="${p.id}">${esc(p.key)}</option>`).join('');
  $('page-requirements').innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Anforderungen</h3>
      <button class="btn btn-primary" onclick="openNewReqModal()">＋ Neue Anforderung</button>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Schlüssel</th><th>Titel</th><th>Beschreibung</th><th>Link</th><th>Projekt</th><th>Aktionen</th></tr></thead>
          <tbody>
            ${state.requirements.map(r => {
              const proj = state.projects.find(p => p.id === r.project_id);
              return `<tr>
                <td><span class="ticket-key">${esc(r.key)}</span></td>
                <td>${esc(r.title)}</td>
                <td class="text-muted" style="max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(r.description)}</td>
                <td>${r.url ? `<a href="${esc(r.url)}" target="_blank">🔗 Öffnen</a>` : '–'}</td>
                <td>${proj ? `<span class="ticket-key">${esc(proj.key)}</span>` : '–'}</td>
                <td>
                  <button class="btn btn-ghost btn-xs" onclick="openEditReqModal(${r.id})" style="margin-right:4px">✏️</button>
                  <button class="btn btn-danger btn-xs" onclick="deleteReq(${r.id})">🗑</button>
                </td>
              </tr>`;
            }).join('') || '<tr><td colspan="6" class="empty-state">Keine Anforderungen</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;
}

function openNewReqModal(prefillProjectId) {
  const projOpts = state.projects.map(p => `<option value="${p.id}" ${p.id==prefillProjectId?'selected':''}>${esc(p.key)} – ${esc(p.name)}</option>`).join('');
  showModal(`
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title">Neue Anforderung</span>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="form-group"><label>Projekt *</label><select id="nr-project">${projOpts}</select></div>
      <div class="form-group"><label>Schlüssel * (z.B. SRS-001)</label><input type="text" id="nr-key" placeholder="SRS-001"></div>
      <div class="form-group"><label>Titel *</label><input type="text" id="nr-title" placeholder="Titel der Anforderung"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="nr-desc" rows="4"></textarea></div>
      <div class="form-group"><label>URL / Hyperlink zur Spezifikation</label><input type="text" id="nr-url" placeholder="https://…"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewReq()">Speichern</button>
      </div>
    </div>`);
}

async function saveNewReq() {
  const key = $('nr-key').value.trim();
  const title = $('nr-title').value.trim();
  if (!key || !title) { notify('Schlüssel und Titel sind Pflichtfelder', 'error'); return; }
  try {
    await api.post('/requirements/', {
      project_id: parseInt($('nr-project').value),
      key, title, description: $('nr-desc').value, url: $('nr-url').value,
    });
    closeModal(); notify('Anforderung erstellt');
    await renderPage('requirements');
  } catch(e) { notify(e.message, 'error'); }
}

async function openEditReqModal(id) {
  const r = await api.get(`/requirements/${id}`);
  const projOpts = state.projects.map(p => `<option value="${p.id}" ${p.id==r.project_id?'selected':''}>${esc(p.key)}</option>`).join('');
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Anforderung bearbeiten</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Projekt</label><select id="er-project">${projOpts}</select></div>
      <div class="form-group"><label>Schlüssel</label><input type="text" id="er-key" value="${esc(r.key)}"></div>
      <div class="form-group"><label>Titel</label><input type="text" id="er-title" value="${esc(r.title)}"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="er-desc" rows="4">${esc(r.description)}</textarea></div>
      <div class="form-group"><label>URL</label><input type="text" id="er-url" value="${esc(r.url)}"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveEditReq(${id})">Speichern</button>
      </div>
    </div>`);
}

async function saveEditReq(id) {
  try {
    await api.put(`/requirements/${id}`, {
      project_id: parseInt($('er-project').value),
      key: $('er-key').value, title: $('er-title').value,
      description: $('er-desc').value, url: $('er-url').value,
    });
    closeModal(); notify('Anforderung gespeichert');
    await renderPage('requirements');
  } catch(e) { notify(e.message, 'error'); }
}

async function deleteReq(id) {
  if (!confirm('Anforderung löschen?')) return;
  await api.delete(`/requirements/${id}`);
  notify('Anforderung gelöscht');
  await renderPage('requirements');
}

// ── Commits ───────────────────────────────────────────────────────────────────
function renderCommits() {
  const persOpts = state.persons.map(p => `<option value="${p.id}">${esc(p.username)}</option>`).join('');
  $('page-commits').innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Git Commits</h3>
      <button class="btn btn-primary" onclick="openNewCommitModal()">＋ Commit erfassen</button>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table>
          <thead><tr><th>SHA</th><th>Commit-Nachricht</th><th>Autor</th><th>Git-Server</th><th>Datum</th><th>Aktionen</th></tr></thead>
          <tbody>
            ${state.commits.map(c => `
              <tr>
                <td>${c.git_url ? `<a href="${esc(c.git_url)}" target="_blank" class="sha-link">${esc(c.sha.slice(0,10))}</a>` : `<span class="sha-link">${esc(c.sha.slice(0,10))}</span>`}</td>
                <td style="max-width:300px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(c.message.split('\n')[0])}</td>
                <td>${c.author ? esc(c.author.username) : '–'}</td>
                <td class="text-muted text-sm" style="max-width:160px;overflow:hidden;text-overflow:ellipsis">${c.author?.git_server ? `<a href="${esc(c.author.git_server)}" target="_blank" class="text-sm">${esc(c.author.git_server)}</a>` : '–'}</td>
                <td class="text-muted">${fmtDate(c.committed_at)}</td>
                <td><button class="btn btn-danger btn-xs" onclick="deleteCommit(${c.id})">🗑</button></td>
              </tr>`).join('') || '<tr><td colspan="6" class="empty-state">Keine Commits</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;
}

function openNewCommitModal() {
  const persOpts = state.persons.map(p => `<option value="${p.id}">${esc(p.username)} (${esc(p.git_server||'–')})</option>`).join('');
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Commit erfassen</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>SHA *</label><input type="text" id="nc-sha" placeholder="abc1234…" class="mono"></div>
      <div class="form-group"><label>Commit-Nachricht</label><textarea id="nc-msg" rows="3"></textarea></div>
      <div class="form-group"><label>Autor (Person)</label><select id="nc-author"><option value="">– kein –</option>${persOpts}</select></div>
      <div class="form-group"><label>URL zum Commit (Git-Server)</label><input type="text" id="nc-url" placeholder="https://github.com/…/commit/abc1234"></div>
      <div class="form-group"><label>Commit-Datum</label><input type="datetime-local" id="nc-date"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewCommit()">Speichern</button>
      </div>
    </div>`);
}

async function saveNewCommit() {
  const sha = $('nc-sha').value.trim();
  if (!sha) { notify('SHA ist Pflicht', 'error'); return; }
  try {
    await api.post('/commits/', {
      sha, message: $('nc-msg').value,
      author_id: $('nc-author').value ? parseInt($('nc-author').value) : null,
      git_url: $('nc-url').value,
      committed_at: $('nc-date').value ? new Date($('nc-date').value).toISOString() : null,
    });
    closeModal(); notify('Commit gespeichert');
    await renderPage('commits');
  } catch(e) { notify(e.message, 'error'); }
}

async function deleteCommit(id) {
  if (!confirm('Commit löschen?')) return;
  await api.delete(`/commits/${id}`);
  notify('Commit gelöscht');
  await renderPage('commits');
}

// ── Tests ─────────────────────────────────────────────────────────────────────
function renderTests() {
  $('page-tests').innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Tests</h3>
      <button class="btn btn-primary" onclick="openNewTestModal()">＋ Neuer Test</button>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Titel</th><th>Typ</th><th>Ergebnis</th><th>Tester</th><th>Ausgeführt am</th><th>Aktionen</th></tr></thead>
          <tbody>
            ${state.tests.map(t => `
              <tr>
                <td>${esc(t.title)}</td>
                <td>${typeBadge(t.test_type)}</td>
                <td>${resultBadge(t.result)}</td>
                <td>${t.tester ? esc(t.tester.username) : '–'}</td>
                <td class="text-muted">${fmtDate(t.run_at)}</td>
                <td>
                  <button class="btn btn-ghost btn-xs" style="margin-right:4px" onclick="openEditTestModal(${t.id})">✏️</button>
                  <button class="btn btn-danger btn-xs" onclick="deleteTest(${t.id})">🗑</button>
                </td>
              </tr>`).join('') || '<tr><td colspan="6" class="empty-state">Keine Tests</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;
}

function openNewTestModal() {
  const persOpts = state.persons.map(p => `<option value="${p.id}">${esc(p.username)}</option>`).join('');
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Neuer Test</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Titel *</label><input type="text" id="ntest-title" placeholder="Testbeschreibung"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="ntest-desc" rows="3"></textarea></div>
      <div class="flex gap-8">
        <div class="form-group" style="flex:1">
          <label>Typ</label>
          <select id="ntest-type"><option value="unit">unit</option><option value="integration">integration</option><option value="system">system</option></select>
        </div>
        <div class="form-group" style="flex:1">
          <label>Ergebnis</label>
          <select id="ntest-result"><option value="pending">pending</option><option value="passed">passed</option><option value="failed">failed</option></select>
        </div>
      </div>
      <div class="form-group"><label>Tester</label><select id="ntest-tester"><option value="">– kein –</option>${persOpts}</select></div>
      <div class="form-group"><label>Ausführungszeitpunkt</label><input type="datetime-local" id="ntest-run"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewTest()">Speichern</button>
      </div>
    </div>`);
}

async function saveNewTest() {
  const title = $('ntest-title').value.trim();
  if (!title) { notify('Titel ist Pflicht', 'error'); return; }
  try {
    await api.post('/tests/', {
      title, description: $('ntest-desc').value,
      test_type: $('ntest-type').value, result: $('ntest-result').value,
      tester_id: $('ntest-tester').value ? parseInt($('ntest-tester').value) : null,
      run_at: $('ntest-run').value ? new Date($('ntest-run').value).toISOString() : null,
    });
    closeModal(); notify('Test gespeichert');
    await renderPage('tests');
  } catch(e) { notify(e.message, 'error'); }
}

async function openEditTestModal(id) {
  const t = await api.get(`/tests/${id}`);
  const persOpts = state.persons.map(p => `<option value="${p.id}" ${p.id==t.tester_id?'selected':''}>${esc(p.username)}</option>`).join('');
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Test bearbeiten</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Titel</label><input type="text" id="etest-title" value="${esc(t.title)}"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="etest-desc" rows="3">${esc(t.description)}</textarea></div>
      <div class="flex gap-8">
        <div class="form-group" style="flex:1"><label>Typ</label>
          <select id="etest-type">${['unit','integration','system'].map(v=>`<option value="${v}" ${t.test_type===v?'selected':''}>${v}</option>`).join('')}</select>
        </div>
        <div class="form-group" style="flex:1"><label>Ergebnis</label>
          <select id="etest-result">${['pending','passed','failed'].map(v=>`<option value="${v}" ${t.result===v?'selected':''}>${v}</option>`).join('')}</select>
        </div>
      </div>
      <div class="form-group"><label>Tester</label><select id="etest-tester"><option value="">– kein –</option>${persOpts}</select></div>
      <div class="form-group"><label>Ausführungszeitpunkt</label><input type="datetime-local" id="etest-run" value="${t.run_at ? new Date(t.run_at).toISOString().slice(0,16) : ''}"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveEditTest(${id})">Speichern</button>
      </div>
    </div>`);
}

async function saveEditTest(id) {
  try {
    await api.put(`/tests/${id}`, {
      title: $('etest-title').value, description: $('etest-desc').value,
      test_type: $('etest-type').value, result: $('etest-result').value,
      tester_id: $('etest-tester').value ? parseInt($('etest-tester').value) : null,
      run_at: $('etest-run').value ? new Date($('etest-run').value).toISOString() : null,
    });
    closeModal(); notify('Test gespeichert');
    await renderPage('tests');
  } catch(e) { notify(e.message, 'error'); }
}

async function deleteTest(id) {
  if (!confirm('Test löschen?')) return;
  await api.delete(`/tests/${id}`);
  notify('Test gelöscht');
  await renderPage('tests');
}

// ── Persons ───────────────────────────────────────────────────────────────────
function renderPersons() {
  $('page-persons').innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Personen / Entwickler</h3>
      <button class="btn btn-primary" onclick="openNewPersonModal()">＋ Person hinzufügen</button>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Benutzername</th><th>Name</th><th>E-Mail</th><th>Git-Server</th><th>Aktionen</th></tr></thead>
          <tbody>
            ${state.persons.map(p => `
              <tr>
                <td><strong>${esc(p.username)}</strong></td>
                <td>${esc(p.full_name) || '–'}</td>
                <td>${p.email ? `<a href="mailto:${esc(p.email)}">${esc(p.email)}</a>` : '–'}</td>
                <td>${p.git_server ? `<a href="${esc(p.git_server)}" target="_blank" class="text-sm">${esc(p.git_server)}</a>` : '–'}</td>
                <td>
                  <button class="btn btn-ghost btn-xs" style="margin-right:4px" onclick="openEditPersonModal(${p.id})">✏️</button>
                  <button class="btn btn-danger btn-xs" onclick="deletePerson(${p.id})">🗑</button>
                </td>
              </tr>`).join('') || '<tr><td colspan="5" class="empty-state">Keine Personen erfasst</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;
}

function openNewPersonModal() {
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Person hinzufügen</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Benutzername *</label><input type="text" id="np-user" placeholder="jdoe"></div>
      <div class="form-group"><label>Vollständiger Name</label><input type="text" id="np-name" placeholder="Jane Doe"></div>
      <div class="form-group"><label>E-Mail</label><input type="email" id="np-email" placeholder="jane@example.com"></div>
      <div class="form-group"><label>Git-Server URL (z.B. https://github.com/jdoe)</label><input type="text" id="np-git" placeholder="https://github.com/jdoe"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewPerson()">Speichern</button>
      </div>
    </div>`);
}

async function saveNewPerson() {
  const username = $('np-user').value.trim();
  if (!username) { notify('Benutzername ist Pflicht', 'error'); return; }
  try {
    await api.post('/persons/', { username, full_name: $('np-name').value, email: $('np-email').value, git_server: $('np-git').value });
    closeModal(); notify('Person gespeichert');
    await renderPage('persons');
  } catch(e) { notify(e.message, 'error'); }
}

async function openEditPersonModal(id) {
  const p = await api.get(`/persons/${id}`);
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Person bearbeiten</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Benutzername</label><input type="text" id="ep-user" value="${esc(p.username)}"></div>
      <div class="form-group"><label>Name</label><input type="text" id="ep-name" value="${esc(p.full_name)}"></div>
      <div class="form-group"><label>E-Mail</label><input type="email" id="ep-email" value="${esc(p.email)}"></div>
      <div class="form-group"><label>Git-Server URL</label><input type="text" id="ep-git" value="${esc(p.git_server)}"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveEditPerson(${id})">Speichern</button>
      </div>
    </div>`);
}

async function saveEditPerson(id) {
  try {
    await api.put(`/persons/${id}`, { username: $('ep-user').value, full_name: $('ep-name').value, email: $('ep-email').value, git_server: $('ep-git').value });
    closeModal(); notify('Person gespeichert');
    await renderPage('persons');
  } catch(e) { notify(e.message, 'error'); }
}

async function deletePerson(id) {
  if (!confirm('Person löschen?')) return;
  await api.delete(`/persons/${id}`);
  notify('Person gelöscht');
  await renderPage('persons');
}

// ── Projects ──────────────────────────────────────────────────────────────────
function renderProjects() {
  $('page-projects').innerHTML = `
    <div class="flex justify-between align-center mb-20">
      <h3>Projekte</h3>
      <button class="btn btn-primary" onclick="openNewProjectModal()">＋ Neues Projekt</button>
    </div>
    <div style="display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">
      ${state.projects.map(p => `
        <div class="card">
          <div class="flex justify-between align-center mb-12">
            <span class="ticket-key" style="font-size:16px">${esc(p.key)}</span>
            <div class="flex gap-8">
              <button class="btn btn-ghost btn-xs" onclick="openEditProjectModal(${p.id})">✏️</button>
              <button class="btn btn-danger btn-xs" onclick="deleteProject(${p.id})">🗑</button>
            </div>
          </div>
          <div style="font-size:15px;font-weight:600;margin-bottom:6px">${esc(p.name)}</div>
          <div class="text-muted text-sm">${esc(p.description)}</div>
          ${p.git_base_url ? `<div style="margin-top:8px"><a href="${esc(p.git_base_url)}" target="_blank" class="text-sm">🔗 ${esc(p.git_base_url)}</a></div>` : ''}
          <div class="text-muted text-sm" style="margin-top:10px">Erstellt: ${fmtDateShort(p.created_at)}</div>
        </div>`).join('') || '<div class="empty-state"><div class="icon">📁</div>Noch keine Projekte</div>'}
    </div>`;
}

function openNewProjectModal() {
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Neues Projekt</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Schlüssel * (2–8 Zeichen, z.B. PROJ)</label><input type="text" id="nproj-key" placeholder="PROJ" maxlength="8"></div>
      <div class="form-group"><label>Name *</label><input type="text" id="nproj-name" placeholder="Mein Projekt"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="nproj-desc" rows="3"></textarea></div>
      <div class="form-group"><label>Git-Basis-URL (Standard-Remote)</label><input type="text" id="nproj-git" placeholder="https://github.com/user/repo"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveNewProject()">Erstellen</button>
      </div>
    </div>`);
}

async function saveNewProject() {
  const key = $('nproj-key').value.trim().toUpperCase();
  const name = $('nproj-name').value.trim();
  if (!key || !name) { notify('Schlüssel und Name sind Pflichtfelder', 'error'); return; }
  try {
    await api.post('/projects/', { key, name, description: $('nproj-desc').value, git_base_url: $('nproj-git').value });
    closeModal(); notify('Projekt erstellt');
    await renderPage('projects');
  } catch(e) { notify(e.message, 'error'); }
}

async function openEditProjectModal(id) {
  const p = await api.get(`/projects/${id}`);
  showModal(`
    <div class="modal">
      <div class="modal-header"><span class="modal-title">Projekt bearbeiten</span><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="form-group"><label>Schlüssel</label><input type="text" id="ep-key" value="${esc(p.key)}"></div>
      <div class="form-group"><label>Name</label><input type="text" id="ep-pname" value="${esc(p.name)}"></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="ep-desc" rows="3">${esc(p.description)}</textarea></div>
      <div class="form-group"><label>Git-Basis-URL</label><input type="text" id="ep-pgit" value="${esc(p.git_base_url)}"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="closeModal()">Abbrechen</button>
        <button class="btn btn-primary" onclick="saveEditProject(${id})">Speichern</button>
      </div>
    </div>`);
}

async function saveEditProject(id) {
  try {
    await api.put(`/projects/${id}`, { key: $('ep-key').value, name: $('ep-pname').value, description: $('ep-desc').value, git_base_url: $('ep-pgit').value });
    closeModal(); notify('Projekt gespeichert');
    await renderPage('projects');
  } catch(e) { notify(e.message, 'error'); }
}

async function deleteProject(id) {
  if (!confirm('Projekt und alle zugehörigen Tickets löschen?')) return;
  await api.delete(`/projects/${id}`);
  notify('Projekt gelöscht');
  await renderPage('projects');
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // project filter in topbar
  const sel = $('project-filter');
  if (sel) sel.addEventListener('change', e => {
    state.currentProject = e.target.value ? parseInt(e.target.value) : null;
    renderPage(state.currentPage);
  });
  navigate('dashboard');
});
