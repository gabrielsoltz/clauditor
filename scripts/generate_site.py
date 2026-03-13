#!/usr/bin/env python3
# ruff: noqa: E501
"""Generate the GitHub Pages site from YAML check definitions.

Usage:
    python scripts/generate_site.py
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
CHECKS_DIR = REPO_ROOT / "clauditor" / "checks"
OUTPUT_DIR = REPO_ROOT / "site"
OUTPUT_FILE = OUTPUT_DIR / "index.html"


def load_checks() -> list[dict]:
    checks = []
    for yaml_file in sorted(CHECKS_DIR.glob("*.yaml")):
        with yaml_file.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                if isinstance(data.get("scope"), list):
                    data["scope"] = [str(s) for s in data["scope"]]
                checks.append(data)
    checks.sort(key=lambda c: c.get("id", ""))
    return checks


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clauditor — Security Checks</title>
  <style>
    :root {
      --bg: #0d1117;
      --bg-card: #161b22;
      --bg-hover: #1c2128;
      --border: #30363d;
      --text: #c9d1d9;
      --muted: #8b949e;
      --accent: #58a6ff;
      --critical: #f85149;
      --high: #e3b341;
      --medium: #58a6ff;
      --low: #3fb950;
      --info: #a5a5ff;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-height: 100vh; }

    /* Header */
    header { border-bottom: 1px solid var(--border); padding: 20px 32px; display: flex; align-items: center; gap: 14px; }
    .logo { font-size: 28px; }
    header h1 { font-size: 20px; font-weight: 700; color: #fff; }
    header p { font-size: 13px; color: var(--muted); margin-top: 2px; }
    header a { color: var(--accent); text-decoration: none; }
    header a:hover { text-decoration: underline; }

    main { padding: 24px 32px; max-width: 1600px; margin: 0 auto; }

    /* Stats */
    .stats { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
    .stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 22px; min-width: 110px; }
    .stat-card .value { font-size: 26px; font-weight: 700; color: #fff; line-height: 1; }
    .stat-card .label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px; }
    .stat-card.critical .value { color: var(--critical); }
    .stat-card.high .value { color: var(--high); }
    .stat-card.medium .value { color: var(--medium); }
    .stat-card.low .value { color: var(--low); }

    /* Filters */
    .filters { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; }
    .filters input, .filters select { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); padding: 7px 12px; font-size: 13px; outline: none; }
    .filters input { min-width: 260px; }
    .filters input:focus, .filters select:focus { border-color: var(--accent); }
    .filters select option { background: var(--bg-card); }
    .btn-reset { background: none; border: 1px solid var(--border); border-radius: 6px; color: var(--muted); cursor: pointer; padding: 7px 12px; font-size: 13px; }
    .btn-reset:hover { border-color: var(--muted); color: var(--text); }
    .count { margin-left: auto; font-size: 13px; color: var(--muted); white-space: nowrap; }

    /* Table */
    .table-wrap { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
    table { width: 100%; border-collapse: collapse; }
    thead th { background: var(--bg); border-bottom: 1px solid var(--border); color: var(--muted); cursor: pointer; font-size: 11px; font-weight: 600; letter-spacing: 0.6px; padding: 10px 16px; text-align: left; text-transform: uppercase; user-select: none; white-space: nowrap; }
    thead th:hover { color: var(--text); }
    thead th.sort-asc::after { content: ' ↑'; color: var(--accent); }
    thead th.sort-desc::after { content: ' ↓'; color: var(--accent); }
    tbody tr.check-row { border-bottom: 1px solid var(--border); cursor: pointer; transition: background 0.1s; }
    tbody tr.check-row:last-child { border-bottom: none; }
    tbody tr.check-row:hover, tbody tr.check-row.active { background: var(--bg-hover); }
    tbody td { font-size: 13px; padding: 11px 16px; vertical-align: middle; }
    td.col-id { font-family: 'SFMono-Regular', Consolas, monospace; font-weight: 600; color: var(--accent); white-space: nowrap; }
    td.col-name { font-weight: 500; color: #fff; }

    /* Badges */
    .badge { border-radius: 20px; display: inline-block; font-size: 10px; font-weight: 700; letter-spacing: 0.4px; padding: 2px 9px; text-transform: uppercase; white-space: nowrap; }
    .sev-CRITICAL { background: #3d0f0f; color: var(--critical); border: 1px solid var(--critical); }
    .sev-HIGH     { background: #3d2200; color: var(--high);     border: 1px solid var(--high); }
    .sev-MEDIUM   { background: #0d2744; color: var(--medium);   border: 1px solid var(--medium); }
    .sev-LOW      { background: #0d2d12; color: var(--low);      border: 1px solid var(--low); }
    .sev-INFO     { background: #1a1a3d; color: var(--info);     border: 1px solid var(--info); }

    .scope-tag { background: #1c2745; border-radius: 4px; color: #79c0ff; display: inline-block; font-size: 10px; font-weight: 600; margin: 1px 2px; padding: 2px 7px; }
    .type-tag  { background: #1e1e2e; border-radius: 4px; color: #cba6f7; display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 7px; white-space: nowrap; }
    .cat-tag   { background: #1e2d1e; border-radius: 4px; color: #7ee787; display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 7px; white-space: nowrap; }
    .fix-yes   { background: #0d2d12; color: var(--low);  border: 1px solid var(--low);    border-radius: 20px; font-size: 10px; font-weight: 700; padding: 2px 9px; }
    .fix-no    { background: #1c2128; color: var(--muted); border: 1px solid var(--border); border-radius: 20px; font-size: 10px; font-weight: 700; padding: 2px 9px; }

    /* Detail panel */
    tr.detail-row td { padding: 0; }
    .detail-panel { background: #070d14; border-top: 2px solid var(--accent); display: grid; gap: 20px; grid-template-columns: 1fr 1fr; padding: 24px 24px 24px 32px; }
    .detail-full { grid-column: 1 / -1; }
    .detail-section h4 { color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; text-transform: uppercase; }
    .detail-section p { color: var(--text); font-size: 13px; line-height: 1.7; white-space: pre-wrap; }
    .detail-section pre { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; color: #a5d6ff; font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; line-height: 1.6; overflow-x: auto; padding: 12px 14px; white-space: pre-wrap; word-break: break-word; }
    .detail-section a { color: var(--accent); display: block; font-size: 12px; margin-bottom: 4px; overflow: hidden; text-decoration: none; text-overflow: ellipsis; white-space: nowrap; }
    .detail-section a:hover { text-decoration: underline; }
    .detail-meta { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .detail-meta .kv { font-size: 12px; color: var(--muted); }
    .detail-meta .kv span { color: var(--text); }

    /* Empty state */
    .no-results { color: var(--muted); font-size: 14px; padding: 56px; text-align: center; }

    /* Footer */
    footer { border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; margin-top: 40px; padding: 18px 32px; text-align: center; }
    footer a { color: var(--accent); text-decoration: none; }

    @media (max-width: 900px) {
      main, header, footer { padding-left: 16px; padding-right: 16px; }
      .detail-panel { grid-template-columns: 1fr; }
      .detail-full { grid-column: 1; }
      .filters input { min-width: 100%; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo">🪂</div>
  <div>
    <h1>Clauditor — Security Checks</h1>
    <p>Security configuration scanner for Claude Code &nbsp;·&nbsp;
       <a href="https://github.com/gabrielsoltz/clauditor" target="_blank" rel="noopener">GitHub</a> &nbsp;·&nbsp;
       <a href="https://pypi.org/project/clauditor/" target="_blank" rel="noopener">PyPI</a>
    </p>
  </div>
</header>

<main>
  <div class="stats" id="stats"></div>

  <div class="filters">
    <input type="search" id="search" placeholder="🔍  Search ID, name, description, threat…">
    <select id="f-severity"><option value="">All Severities</option></select>
    <select id="f-scope"><option value="">All Scopes</option></select>
    <select id="f-category"><option value="">All Categories</option></select>
    <select id="f-type"><option value="">All Check Types</option></select>
    <select id="f-fix">
      <option value="">Fix Available?</option>
      <option value="true">Yes</option>
      <option value="false">No</option>
    </select>
    <button class="btn-reset" id="btn-reset">✕ Reset</button>
    <span class="count" id="result-count"></span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-col="id">ID</th>
          <th data-col="name">Name</th>
          <th data-col="severity">Severity</th>
          <th data-col="scope">Scope</th>
          <th data-col="category">Category</th>
          <th data-col="check_type">Check Type</th>
          <th data-col="fix_available">Fix</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</main>

<footer>
  Auto-generated from <a href="https://github.com/gabrielsoltz/clauditor/tree/main/checks" target="_blank" rel="noopener">YAML check definitions</a>
  on every push to main &nbsp;·&nbsp;
  <a href="https://github.com/gabrielsoltz/clauditor" target="_blank" rel="noopener">Clauditor on GitHub</a>
</footer>

<script>
  const CHECKS = __CHECKS_JSON__;

  // ── State ──────────────────────────────────────────────────────────────────
  let sortCol = 'id', sortDir = 1, openId = null;

  // ── Init ───────────────────────────────────────────────────────────────────
  populateFilters();
  renderStats();
  render();

  // ── Populate filter dropdowns ──────────────────────────────────────────────
  function populateFilters() {
    function uniq(key, flat) {
      return [...new Set(CHECKS.flatMap(c => flat ? (c[key] || []) : [c[key]]))].filter(Boolean).sort();
    }
    function fill(id, vals) {
      const el = document.getElementById(id);
      vals.forEach(v => {
        const o = document.createElement('option');
        o.value = v; o.textContent = v;
        el.appendChild(o);
      });
    }
    fill('f-severity', ['CRITICAL','HIGH','MEDIUM','LOW','INFO'].filter(s => uniq('severity').includes(s)));
    fill('f-scope',    uniq('scope', true));
    fill('f-category', uniq('category'));
    fill('f-type',     uniq('check_type'));
  }

  // ── Stats bar ──────────────────────────────────────────────────────────────
  function renderStats() {
    const cnt = s => CHECKS.filter(c => c.severity === s).length;
    document.getElementById('stats').innerHTML = `
      <div class="stat-card"><div class="value">${CHECKS.length}</div><div class="label">Total Checks</div></div>
      <div class="stat-card critical"><div class="value">${cnt('CRITICAL')}</div><div class="label">Critical</div></div>
      <div class="stat-card high"><div class="value">${cnt('HIGH')}</div><div class="label">High</div></div>
      <div class="stat-card medium"><div class="value">${cnt('MEDIUM')}</div><div class="label">Medium</div></div>
      <div class="stat-card low"><div class="value">${cnt('LOW')}</div><div class="label">Low</div></div>
    `;
  }

  // ── Filter ─────────────────────────────────────────────────────────────────
  function getFiltered() {
    const q    = document.getElementById('search').value.toLowerCase();
    const fSev  = document.getElementById('f-severity').value;
    const fScope= document.getElementById('f-scope').value;
    const fCat  = document.getElementById('f-category').value;
    const fType = document.getElementById('f-type').value;
    const fFix  = document.getElementById('f-fix').value;

    return CHECKS.filter(c => {
      if (fSev   && c.severity   !== fSev)                        return false;
      if (fScope && !(c.scope||[]).includes(fScope))              return false;
      if (fCat   && c.category   !== fCat)                        return false;
      if (fType  && c.check_type !== fType)                       return false;
      if (fFix   && String(c.fix_available) !== fFix)             return false;
      if (q) {
        const hay = [c.id, c.name, c.description, c.threat, c.category, c.check_type, c.remediation]
          .join(' ').toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  // ── Sort ───────────────────────────────────────────────────────────────────
  function getSorted(checks) {
    return [...checks].sort((a, b) => {
      let av = a[sortCol], bv = b[sortCol];
      if (Array.isArray(av)) av = av.join(',');
      if (Array.isArray(bv)) bv = bv.join(',');
      av = String(av ?? '').toLowerCase();
      bv = String(bv ?? '').toLowerCase();
      return av < bv ? -sortDir : av > bv ? sortDir : 0;
    });
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  function render() {
    const checks = getSorted(getFiltered());
    const tbody  = document.getElementById('tbody');
    tbody.innerHTML = '';

    document.getElementById('result-count').textContent =
      checks.length === CHECKS.length
        ? `${CHECKS.length} checks`
        : `${checks.length} of ${CHECKS.length}`;

    // Sort indicators
    document.querySelectorAll('thead th[data-col]').forEach(th => {
      th.classList.remove('sort-asc', 'sort-desc');
      if (th.dataset.col === sortCol)
        th.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');
    });

    if (!checks.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="no-results">No checks match the current filters.</td></tr>`;
      return;
    }

    checks.forEach(c => {
      const scopes = (c.scope || []).map(s => `<span class="scope-tag">${esc(s)}</span>`).join('');
      const isOpen = openId === c.id;

      // ── Main row
      const tr = document.createElement('tr');
      tr.className = 'check-row' + (isOpen ? ' active' : '');
      tr.dataset.id = c.id;
      tr.innerHTML = `
        <td class="col-id">${esc(c.id)}</td>
        <td class="col-name">${esc(c.name)}</td>
        <td><span class="badge sev-${c.severity}">${esc(c.severity)}</span></td>
        <td>${scopes}</td>
        <td><span class="cat-tag">${esc(c.category || '')}</span></td>
        <td><span class="type-tag">${esc(c.check_type || '')}</span></td>
        <td><span class="${c.fix_available ? 'fix-yes' : 'fix-no'}">${c.fix_available ? 'Yes' : 'No'}</span></td>
      `;
      tr.addEventListener('click', () => toggle(c.id));
      tbody.appendChild(tr);

      // ── Detail row
      if (isOpen) {
        const cfg  = JSON.stringify(c.check_config || {}, null, 2);
        const refs = (c.references || []).map(r =>
          `<a href="${esc(r)}" target="_blank" rel="noopener">${esc(r)}</a>`).join('');

        const det = document.createElement('tr');
        det.className = 'detail-row';
        det.innerHTML = `<td colspan="7">
          <div class="detail-panel">
            <div class="detail-section detail-full">
              <h4>Description</h4>
              <p>${esc(c.description || '')}</p>
            </div>
            <div class="detail-section detail-full">
              <h4>Threat</h4>
              <p>${esc(c.threat || '')}</p>
            </div>
            <div class="detail-section">
              <h4>Remediation</h4>
              <pre>${esc(c.remediation || '')}</pre>
            </div>
            <div class="detail-section">
              <h4>Check Config</h4>
              <pre>${esc(cfg)}</pre>
            </div>
            ${refs ? `<div class="detail-section detail-full"><h4>References</h4>${refs}</div>` : ''}
          </div>
        </td>`;
        tbody.appendChild(det);
      }
    });
  }

  function toggle(id) { openId = openId === id ? null : id; render(); }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Event listeners ────────────────────────────────────────────────────────
  ['search','f-severity','f-scope','f-category','f-type','f-fix'].forEach(id =>
    document.getElementById(id).addEventListener('input', () => { openId = null; render(); })
  );

  document.getElementById('btn-reset').addEventListener('click', () => {
    ['search','f-severity','f-scope','f-category','f-type','f-fix'].forEach(id => {
      const el = document.getElementById(id);
      el.tagName === 'INPUT' ? el.value = '' : el.selectedIndex = 0;
    });
    openId = null;
    render();
  });

  document.querySelectorAll('thead th[data-col]').forEach(th =>
    th.addEventListener('click', () => {
      sortCol === th.dataset.col ? sortDir *= -1 : (sortCol = th.dataset.col, sortDir = 1);
      render();
    })
  );
</script>
</body>
</html>
"""


def generate(checks: list[dict]) -> str:
    checks_json = json.dumps(checks, ensure_ascii=False, indent=2)
    return HTML_TEMPLATE.replace("__CHECKS_JSON__", checks_json)


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = load_checks()
    html = generate(checks)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE} with {len(checks)} checks.")
