// State variables
let currentLeads = [];
let currentFilter = {
  status: '',
  owner: '',
  country: '',
  q: ''
};

document.addEventListener('DOMContentLoaded', () => {
  fetchDashboardMetrics();
  fetchLeads();

  // Search input enter key
  document.getElementById('filter-search').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') applyFilters();
  });
});

// View switching
function switchView(viewId, element) {
  document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
  document.getElementById(viewId).style.display = 'block';

  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  element.classList.add('active');

  const titles = {
    'leads-view': 'Mini Lead Management System',
    'dedupe-view': 'AI-Assisted Lead Deduplication',
    'source-view': 'AI Source Channel Extractor',
    'ingest-view': 'Website Form Ingest Simulator',
    'profile-view': 'Candidate Profile & Engineering Overview'
  };
  document.getElementById('header-title').innerText = titles[viewId] || 'Lead Management';
}

// Fetch Dashboard Metrics
async function fetchDashboardMetrics() {
  try {
    const res = await fetch('/dashboard');
    const data = await res.json();

    document.getElementById('metric-total').innerText = data.total_leads.toLocaleString();

    // High intent (Qualified + Won)
    const qualified = (data.by_status['Qualified'] || 0) + (data.by_status['Closed Won'] || 0);
    document.getElementById('metric-qualified').innerText = qualified.toLocaleString();

    // Top channel
    let topChannel = 'N/A';
    let maxChannelCount = 0;
    for (const [ch, count] of Object.entries(data.by_channel)) {
      if (count > maxChannelCount) {
        maxChannelCount = count;
        topChannel = ch;
      }
    }
    document.getElementById('metric-top-channel').innerText = topChannel;
    document.getElementById('metric-channel-sub').innerText = `${maxChannelCount} leads attributed`;

    // Render Status Bars
    renderBreakdown('status-breakdown', data.by_status, data.total_leads, '#6366f1');
    // Render Channel Bars
    renderBreakdown('channel-breakdown', data.by_channel, data.total_leads, '#a855f7');
  } catch (err) {
    console.error('Error fetching dashboard metrics:', err);
  }
}

function renderBreakdown(containerId, dataMap, total, barColor) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  const sorted = Object.entries(dataMap).sort((a, b) => b[1] - a[1]);
  for (const [key, count] of sorted) {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    const item = document.createElement('div');
    item.className = 'breakdown-item';
    item.innerHTML = `
      <span style="width: 110px; font-weight: 500; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${key}</span>
      <div class="breakdown-bar-bg">
        <div class="breakdown-bar-fill" style="width: ${pct}%; background-color: ${barColor};"></div>
      </div>
      <span style="width: 70px; text-align: right; color: var(--text-secondary); font-size: 0.8rem;">${count} (${pct}%)</span>
    `;
    container.appendChild(item);
  }
}

// Fetch Leads
async function fetchLeads() {
  const tableBody = document.getElementById('leads-table-body');
  tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-muted);">Loading leads...</td></tr>`;

  const params = new URLSearchParams();
  if (currentFilter.status) params.append('status', currentFilter.status);
  if (currentFilter.owner) params.append('owner', currentFilter.owner);
  if (currentFilter.country) params.append('country', currentFilter.country);
  if (currentFilter.q) params.append('q', currentFilter.q);
  params.append('limit', '50');

  try {
    const res = await fetch(`/leads?${params.toString()}`);
    const leads = await res.json();
    currentLeads = leads;
    renderLeadsTable(leads);
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--danger); padding:20px;">Failed to load leads</td></tr>`;
  }
}

function renderLeadsTable(leads) {
  const tableBody = document.getElementById('leads-table-body');
  tableBody.innerHTML = '';

  if (!leads || leads.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 40px; color: var(--text-muted);">No matching leads found</td></tr>`;
    return;
  }

  leads.forEach(lead => {
    const tr = document.createElement('tr');

    const statusClass = getStatusClass(lead.lead_status);
    const displayName = lead.full_name || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || 'Unnamed';
    const channelTag = lead.source_channel ? `<span class="channel-tag">${lead.source_channel}</span>` : `<span style="color:var(--text-muted);">-</span>`;

    tr.innerHTML = `
      <td>
        <div style="font-weight: 600;">${displayName}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${lead.job_title || ''}</div>
      </td>
      <td>${lead.company_name || '<span style="color:var(--text-muted);">-</span>'}</td>
      <td>
        <div>${lead.email || '-'}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${lead.phone_number || ''}</div>
      </td>
      <td><span class="status-pill ${statusClass}">${lead.lead_status || 'New'}</span></td>
      <td>${channelTag}</td>
      <td>${lead.contact_owner || '<span style="color:var(--text-muted);">-</span>'}</td>
      <td>
        <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.8rem;" onclick="openLeadModal(${lead.id})">Edit</button>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

function getStatusClass(status) {
  const s = (status || '').toLowerCase();
  if (s.includes('won')) return 'status-won';
  if (s.includes('lost')) return 'status-lost';
  if (s.includes('qual')) return 'status-qualified';
  if (s.includes('opp')) return 'status-opportunity';
  if (s.includes('conn')) return 'status-connected';
  if (s.includes('contact')) return 'status-contacted';
  return 'status-new';
}

function applyFilters() {
  currentFilter.q = document.getElementById('filter-search').value.trim();
  currentFilter.status = document.getElementById('filter-status').value;
  currentFilter.country = document.getElementById('filter-country').value.trim();
  currentFilter.owner = document.getElementById('filter-owner').value.trim();
  fetchLeads();
}

function resetFilters() {
  document.getElementById('filter-search').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-country').value = '';
  document.getElementById('filter-owner').value = '';
  currentFilter = { status: '', owner: '', country: '', q: '' };
  fetchLeads();
}

function triggerExport() {
  const params = new URLSearchParams();
  if (currentFilter.status) params.append('status', currentFilter.status);
  if (currentFilter.owner) params.append('owner', currentFilter.owner);
  if (currentFilter.country) params.append('country', currentFilter.country);
  if (currentFilter.q) params.append('q', currentFilter.q);
  window.location.href = `/leads/export?${params.toString()}`;
}

// Modal handling
let selectedLead = null;

async function openLeadModal(leadId) {
  try {
    const res = await fetch(`/leads/${leadId}`);
    selectedLead = await res.json();

    document.getElementById('modal-lead-id').value = selectedLead.id;
    document.getElementById('modal-lead-header').innerText = `${selectedLead.full_name || 'No Name'} — ${selectedLead.company_name || 'No Company'}`;
    document.getElementById('modal-lead-contact').innerText = `Email: ${selectedLead.email || 'N/A'} | Phone: ${selectedLead.phone_number || 'N/A'} | Country: ${selectedLead.country || 'N/A'}`;
    
    document.getElementById('modal-lead-status').value = selectedLead.lead_status || 'New';
    document.getElementById('modal-lead-owner').value = selectedLead.contact_owner || '';
    document.getElementById('modal-lead-notes').value = selectedLead.notes || '';
    document.getElementById('modal-lead-source').innerText = `Channel: ${selectedLead.source_channel || 'N/A'} | Detail: ${selectedLead.source_detail || 'N/A'}`;

    document.getElementById('lead-modal').classList.add('active');
  } catch (err) {
    alert('Error loading lead details');
  }
}

function closeModal() {
  document.getElementById('lead-modal').classList.remove('active');
}

async function saveLeadChanges() {
  const leadId = document.getElementById('modal-lead-id').value;
  const status = document.getElementById('modal-lead-status').value;
  const owner = document.getElementById('modal-lead-owner').value;
  const notes = document.getElementById('modal-lead-notes').value;

  try {
    const res = await fetch(`/leads/${leadId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_status: status,
        contact_owner: owner,
        notes: notes
      })
    });

    if (res.ok) {
      closeModal();
      fetchLeads();
      fetchDashboardMetrics();
    } else {
      alert('Failed to update lead');
    }
  } catch (err) {
    alert('Network error saving lead');
  }
}

// AI Deduplication View
async function runDeduplication() {
  const threshold = parseFloat(document.getElementById('dedupe-threshold').value);
  const spinner = document.getElementById('dedupe-spinner');
  const resultsSummary = document.getElementById('dedupe-results-summary');
  const dedupeList = document.getElementById('dedupe-list');

  spinner.style.display = 'inline';
  dedupeList.innerHTML = `<div style="padding: 20px; color: var(--text-muted);">Processing candidates with blocking algorithm...</div>`;

  try {
    const res = await fetch(`/leads/dedupe-candidates?min_confidence=${threshold}`, {
      method: 'POST'
    });
    const data = await res.json();
    spinner.style.display = 'none';

    resultsSummary.innerText = `Found ${data.total_candidates} duplicate candidate pair(s) with confidence >= ${Math.round(threshold*100)}%`;
    dedupeList.innerHTML = '';

    if (data.groups.length === 0) {
      dedupeList.innerHTML = `<div style="padding: 20px; color: var(--text-muted);">No duplicates found with the selected threshold.</div>`;
      return;
    }

    data.groups.slice(0, 40).forEach(pair => {
      const item = document.createElement('div');
      item.className = 'dedupe-item';

      const confClass = pair.confidence_level === 'HIGH' ? 'conf-high' : 'conf-med';
      
      item.innerHTML = `
        <div class="lead-box">
          <h4>#${pair.lead_id_1} ${pair.lead_1_name || 'No Name'}</h4>
          <div style="color:var(--text-secondary);">${pair.lead_1_email || 'No email'}</div>
          <div style="color:var(--text-muted); font-size: 0.8rem;">${pair.lead_1_company || 'No company'}</div>
        </div>
        
        <div class="dedupe-vs">
          <span class="confidence-badge ${confClass}">${Math.round(pair.confidence_score * 100)}% MATCH</span>
          <div style="font-size: 0.75rem; color: var(--text-secondary); max-width: 200px; text-align: center;">${pair.reason}</div>
        </div>

        <div class="lead-box">
          <h4>#${pair.lead_id_2} ${pair.lead_2_name || 'No Name'}</h4>
          <div style="color:var(--text-secondary);">${pair.lead_2_email || 'No email'}</div>
          <div style="color:var(--text-muted); font-size: 0.8rem;">${pair.lead_2_company || 'No company'}</div>
        </div>
      `;
      dedupeList.appendChild(item);
    });

    if (data.groups.length > 40) {
      const more = document.createElement('div');
      more.style.textAlign = 'center';
      more.style.color = 'var(--text-muted)';
      more.style.padding = '12px';
      more.innerText = `+ ${data.groups.length - 40} additional duplicate candidates detected.`;
      dedupeList.appendChild(more);
    }

  } catch (err) {
    spinner.style.display = 'none';
    dedupeList.innerHTML = `<div style="color: var(--danger);">Error running deduplication engine</div>`;
  }
}

// AI Source Extractor Sandbox
async function testExtractSource() {
  const notes = document.getElementById('sample-note-input').value;
  const orig = document.getElementById('sample-orig-source').value;
  const resultBox = document.getElementById('source-extract-result');
  const jsonPre = document.getElementById('source-extract-json');

  try {
    const res = await fetch('/leads/extract-source', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes, original_source: orig })
    });
    const data = await res.json();
    resultBox.style.display = 'block';
    jsonPre.innerText = JSON.stringify(data, null, 2);
  } catch (err) {
    alert('Error testing source extractor');
  }
}

function fillSampleNote(type) {
  const input = document.getElementById('sample-note-input');
  const orig = document.getElementById('sample-orig-source');
  if (type === 1) {
    input.value = "Referred by Michael Zhang, warm intro. Connected, sending proposal.";
    orig.value = "Referrals";
  } else if (type === 2) {
    input.value = "Googled us and ended up on the book-a-demo page before booking a demo.";
    orig.value = "Organic Search";
  } else if (type === 3) {
    input.value = "Connected on LinkedIn after commenting on our post. Wants pricing call.";
    orig.value = "Social Media";
  }
  testExtractSource();
}

// Ingest Simulator
async function submitIngest() {
  const payload = {
    name: document.getElementById('ingest-name').value,
    email: document.getElementById('ingest-email').value,
    phone: document.getElementById('ingest-phone').value,
    company: document.getElementById('ingest-company').value,
    country: document.getElementById('ingest-country').value,
    message: document.getElementById('ingest-message').value,
    form_name: "Website Demo Form",
    page_url: "/pricing"
  };

  const resultBox = document.getElementById('ingest-result');
  const badge = document.getElementById('ingest-status-badge');
  const jsonPre = document.getElementById('ingest-result-json');

  try {
    const res = await fetch('/leads/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    resultBox.style.display = 'block';
    if (data.status === 'updated') {
      badge.innerHTML = `<span style="color:#f59e0b;">● Existing Lead Updated (Matched by ${data.matched_by})</span>`;
    } else {
      badge.innerHTML = `<span style="color:#10b981;">● New Lead Created</span>`;
    }
    jsonPre.innerText = JSON.stringify(data, null, 2);

    fetchLeads();
    fetchDashboardMetrics();
  } catch (err) {
    alert('Failed to submit form ingest');
  }
}
