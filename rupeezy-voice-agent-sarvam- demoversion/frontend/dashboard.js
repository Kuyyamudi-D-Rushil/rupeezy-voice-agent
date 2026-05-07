const API_BASE_URL = window.RUPEEZY_API_BASE_URL || 'http://localhost:8000';

const leadsBody = document.getElementById('leads-body');
const errorBox = document.getElementById('error-box');
const refreshBtn = document.getElementById('refresh-btn');
const seedBtn = document.getElementById('seed-btn');
let demoWhatsappNumber = '';

const counters = {
    total: document.getElementById('total-count'),
    Hot: document.getElementById('hot-count'),
    Warm: document.getElementById('warm-count'),
    Cold: document.getElementById('cold-count')
};

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('hidden');
}

function clearError() {
    errorBox.textContent = '';
    errorBox.classList.add('hidden');
}

function scoreClass(status) {
    const normalized = String(status || '').toLowerCase();
    if (normalized === 'hot') return 'status-hot';
    if (normalized === 'warm') return 'status-warm';
    return 'status-cold';
}

function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleString([], {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function transcriptPreview(transcript) {
    const text = String(transcript || 'No transcript captured.');
    return text.length > 260 ? `${text.slice(0, 260)}...` : text;
}

function normalizePhone(phone) {
    const digits = String(phone || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.startsWith('91')) return digits.slice(2);
    return digits.length === 10 && /^[6-9]/.test(digits) ? digits : '';
}

function normalizeWhatsappNumber(phone) {
    const digits = String(phone || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.startsWith('91')) return digits;
    if (digits.length === 10 && /^[6-9]/.test(digits)) return `91${digits}`;
    return '';
}

function whatsappMessage(lead) {
    const hasName = lead.name && String(lead.name).toLowerCase() !== 'unknown lead';
    const greeting = hasName ? `Hi ${lead.name}` : 'Hi';
    return `${greeting}, thanks for speaking with Rupeezy. As discussed, you can become a Rupeezy Authorized Partner with zero joining fee, 100% brokerage share, and daily payouts via RISE Portal. Our RM will help you with the next steps and can call you back at your preferred time. Signup link: https://rupeezy.in/partner`;
}

function whatsappCell(lead) {
    const status = String(lead.lead_status || '').toLowerCase();
    const leadPhone = normalizePhone(lead.phone);
    const fallbackPhone = normalizeWhatsappNumber(demoWhatsappNumber);
    const whatsappPhone = leadPhone ? `91${leadPhone}` : fallbackPhone;
    if (!whatsappPhone) {
        return '<span class="muted-action">Phone not captured</span>';
    }
    if (status !== 'hot' && status !== 'warm') {
        return '<span class="muted-action">Only Warm/Hot</span>';
    }
    const label = leadPhone ? 'Send WhatsApp Follow-up' : 'Send WhatsApp Follow-up (Demo)';
    const url = `https://wa.me/${whatsappPhone}?text=${encodeURIComponent(whatsappMessage(lead))}`;
    return `<a class="whatsapp-btn" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
}

function renderStats(leads) {
    const counts = { total: leads.length, Hot: 0, Warm: 0, Cold: 0 };
    leads.forEach((lead) => {
        if (counts[lead.lead_status] !== undefined) {
            counts[lead.lead_status] += 1;
        }
    });
    counters.total.textContent = counts.total;
    counters.Hot.textContent = counts.Hot;
    counters.Warm.textContent = counts.Warm;
    counters.Cold.textContent = counts.Cold;
}

function renderLeads(leads) {
    if (!leads.length) {
        leadsBody.innerHTML = '<tr><td colspan="9" class="empty-cell">No leads yet. Use Add Demo Lead or complete a voice conversation.</td></tr>';
        return;
    }

    const sorted = [...leads].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    leadsBody.innerHTML = sorted.map((lead) => {
        const statusClass = scoreClass(lead.lead_status);
        return `
            <tr>
                <td>
                    <span class="lead-name">${escapeHtml(lead.name)}</span>
                    <span class="lead-phone">${escapeHtml(lead.phone)}</span>
                    <span class="lead-time">${escapeHtml(formatTime(lead.timestamp))}</span>
                </td>
                <td><span class="badge ${statusClass}">${escapeHtml(lead.lead_score)}</span></td>
                <td><strong class="${statusClass}">${escapeHtml(lead.lead_status)}</strong></td>
                <td class="text-cell">${escapeHtml(lead.main_objection)}</td>
                <td class="text-cell">${escapeHtml(lead.conversation_summary)}</td>
                <td class="text-cell">${escapeHtml(lead.next_action)}</td>
                <td class="text-cell">${escapeHtml(lead.handoff_status)}</td>
                <td class="transcript">${escapeHtml(transcriptPreview(lead.transcript))}</td>
                <td>${whatsappCell(lead)}</td>
            </tr>
        `;
    }).join('');
}

async function loadLeads() {
    clearError();
    leadsBody.innerHTML = '<tr><td colspan="9" class="empty-cell">Loading leads...</td></tr>';
    try {
        const response = await fetch(`${API_BASE_URL}/leads`, { signal: AbortSignal.timeout(10000) });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Could not load leads from backend.');
        }
        const data = await response.json();
        const leads = Array.isArray(data) ? data : Array.isArray(data.leads) ? data.leads : [];
        renderStats(leads);
        renderLeads(leads);
    } catch (error) {
        renderStats([]);
        leadsBody.innerHTML = '<tr><td colspan="9" class="empty-cell">Lead data unavailable.</td></tr>';
        showError(error.name === 'TimeoutError' ? 'Loading leads timed out. Please check that the backend is running.' : error.message);
    }
}

async function loadDashboardConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard-config`, { signal: AbortSignal.timeout(5000) });
        if (!response.ok) return;
        const data = await response.json();
        demoWhatsappNumber = data.demo_whatsapp_number || '';
    } catch (error) {
        console.warn('Dashboard config unavailable:', error);
    }
}

async function seedDemoLead() {
    clearError();
    seedBtn.disabled = true;
    try {
        const response = await fetch(`${API_BASE_URL}/seed-demo-lead`, { method: 'POST' });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Could not add demo lead.');
        }
        await loadLeads();
    } catch (error) {
        showError(error.message);
    } finally {
        seedBtn.disabled = false;
    }
}

refreshBtn.addEventListener('click', loadLeads);
seedBtn.addEventListener('click', seedDemoLead);
loadDashboardConfig().finally(loadLeads);
