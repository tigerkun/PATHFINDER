const params = new URLSearchParams(window.location.search);
const username = params.get('username') || '';

const loadingMsgs = [
    'Fetching GitHub metrics...',
    'Counting commits and PRs...',
    'Analyzing language distribution...',
    'Running AI career model...',
    'Building your roadmap...',
];
let msgIdx = 0;
const msgInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % loadingMsgs.length;
    document.getElementById('loading-msg').textContent = loadingMsgs[msgIdx];
}, 3000);

function showError(msg) {
    clearInterval(msgInterval);
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error-text').textContent = msg;
    document.getElementById('error-state').style.display = 'flex';
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[ch]));
}

function buildMetrics(m) {
    const items = [
        { key: 'Total Repos', val: m.total_repos ?? '—' },
        { key: 'Original Repos', val: m.original_repos ?? '—' },
        { key: 'Total Stars', val: m.total_stars ?? '—' },
        { key: 'Merged PRs', val: m.merged_prs ?? '—' },
        { key: 'Contributions', val: m.total_contributions_year ?? '—' },
        { key: 'Active Days', val: m.active_days_year ?? '—' },
        { key: 'Streak', val: m.current_streak_days ? m.current_streak_days + 'd' : '—' },
        { key: 'Followers', val: m.followers ?? '—' },
        { key: 'Languages', val: m.language_diversity ?? '—' },
        { key: 'Acc. Age', val: m.account_age_days ? Math.floor(m.account_age_days / 365) + 'yr' : '—' },
    ];
    document.getElementById('metrics-grid').innerHTML = items.map(i =>
        `<div class="metric-item"><div class="m-val">${escapeHtml(i.val)}</div><div class="m-key">${escapeHtml(i.key)}</div></div>`
    ).join('');
}

function buildScores(scores) {
    const labels = {
        overall: 'Overall', activity: 'Activity',
        diversity: 'Diversity', open_source: 'Open Source', consistency: 'Consistency'
    };
    document.getElementById('score-list').innerHTML = Object.entries(labels).map(([k, label]) => {
        const val = scores[k] ?? 0;
        const safeVal = Number.isFinite(Number(val)) ? Number(val) : 0;
        return `<div class="score-row">
  <div class="score-row-top">
    <span class="score-key">${escapeHtml(label)}</span>
    <span class="score-val">${safeVal}%</span>
  </div>
  <div class="score-bar"><div class="score-fill" data-width="${safeVal}%" style="width:0"></div></div>
</div>`;
    }).join('');
    setTimeout(() => {
        document.querySelectorAll('.score-fill').forEach(el => {
            el.style.width = el.dataset.width;
        });
    }, 100);
}

function buildTagList(id, items, colorClass) {
    const el = document.getElementById(id);
    if (!el || !Array.isArray(items)) return;
    const safeColorClass = ['green', 'red', 'blue', 'yellow'].includes(colorClass) ? colorClass : 'blue';
    el.innerHTML = items.map(item =>
        `<span class="tag ${safeColorClass}">${escapeHtml(item)}</span>`
    ).join('');
}

function buildRoadmap(phases) {
    const container = document.getElementById('roadmap');
    if (!Array.isArray(phases) || phases.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);font-size:0.88rem;">No roadmap data available.</p>';
        return;
    }
    container.innerHTML = phases.map((phase, i) => `
<div class="phase-card">
  <div class="phase-header" onclick="togglePhase(this)">
    <div class="phase-header-left">
      <div class="phase-dot"></div>
      <span class="phase-title">${escapeHtml(phase.phase || 'Phase ' + (i + 1))} — ${escapeHtml(phase.focus || '')}</span>
    </div>
    <div style="display:flex;align-items:center;gap:0.6rem;">
      <span class="phase-weeks">Weeks ${escapeHtml(phase.weeks || '')}</span>
      <span class="phase-toggle ${i === 0 ? 'open' : ''}">▼</span>
    </div>
  </div>
  <div class="phase-body ${i === 0 ? 'open' : ''}">
    <ul class="phase-task-list">
      ${(phase.tasks || []).map(t => `<li>${escapeHtml(t)}</li>`).join('')}
    </ul>
    ${phase.milestone ? `<div class="phase-milestone">🏁 <span>Milestone:</span> ${escapeHtml(phase.milestone)}</div>` : ''}
  </div>
</div>
`).join('');
}

function togglePhase(header) {
    const body = header.nextElementSibling;
    const toggle = header.querySelector('.phase-toggle');
    body.classList.toggle('open');
    toggle.classList.toggle('open');
}

function buildAltRoles(roles) {
    const container = document.getElementById('alt-roles');
    if (!Array.isArray(roles) || roles.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;">No alternatives generated.</p>';
        return;
    }
    container.innerHTML = roles.map(r => `
<div class="alt-role-row">
  <span class="alt-role-name">${escapeHtml(r.title)}</span>
  <div class="alt-score-bar">
    <div class="alt-score-fill" style="width:${Number.isFinite(Number(r.fit_score)) ? Number(r.fit_score) : 0}%"></div>
  </div>
  <span class="alt-score-num">${Number.isFinite(Number(r.fit_score)) ? Number(r.fit_score) : 0}%</span>
</div>
`).join('');
}

async function loadReport() {
    if (!username) { showError('No username provided. Please go back and enter a GitHub username.'); return; }
    document.getElementById('header-user').textContent = username;

    const apiUrl = `/api/v1/predict/${encodeURIComponent(username)}?${params.toString()}`;

    try {
        const res = await fetch(apiUrl);
        const json = await res.json();

        if (!res.ok || json.status === 'error') {
            showError(json.message || 'API request failed. Please check your .env keys and try again.');
            return;
        }

        const d = json.data;
        const m = json.metrics || {};

        clearInterval(msgInterval);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('report').style.display = 'block';

        const role = d.recommended_role || {};
        setText('confidence-tag', `${role.confidence || '—'}% Confidence Match`);
        setText('role-title', role.title);
        setText('role-def', role.definition);
        setText('role-scope', role.scope);

        const pct = d.match_pct || 0;
        document.getElementById('match-pct').textContent = pct + '%';
        document.getElementById('match-circle').style.setProperty('--pct', `${pct * 3.6}deg`);
        document.getElementById('match-circle').style.background =
            `conic-gradient(var(--accent) 0deg ${pct * 3.6}deg, var(--border) ${pct * 3.6}deg 360deg)`;

        const sal = d.indian_salary || {};
        setText('sal-fresher', sal.fresher || '₹4-8 LPA');
        setText('sal-mid', sal.mid || '₹10-18 LPA');
        setText('sal-senior', sal.senior || '₹20-35 LPA');

        buildScores(d.profile_score || {});
        buildMetrics(m);
        buildTagList('strengths-list', d.strengths, 'green');
        buildTagList('gaps-list', d.gaps, 'red');
        buildTagList('actions-list', d.action_items, 'blue');
        buildTagList('companies-list', d.top_companies, 'yellow');
        buildRoadmap(d.roadmap);
        buildAltRoles(d.alternative_roles);
        setText('verdict', d.verdict);
    } catch (err) {
        showError('Network error: ' + err.message + '. Is the server running?');
    }
}

window.togglePhase = togglePhase;
window.onload = loadReport;
