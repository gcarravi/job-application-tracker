console.log("TRACKER JS LOADED");

// Reads a value from the browser's cookies by name. In this app it's used exclusively to retrieve Django's CSRF token: 'X-CSRFToken': getCookie('csrftoken')
// Django sets a cookie called csrftoken automatically. Every fetch() POST request in tracker.js must include this token in the request header, otherwise Django rejects the request with a 403 Forbidden error.
// On regular HTML forms, {% csrf_token %} handles this automatically by inserting a hidden <input>. But because the tracker uses AJAX (fetch()), there's no form being submitted — so the token has to be pulled manually from the cookie and added to the request header instead.
function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

const STATUS_LABELS = {
    'wishlist': 'Wishlist',
    'applied': 'Applied',
    'interviewing': 'Interviewing',
    'offer': 'Offer',
    'rejected': 'Rejected',
    'ghosted': 'Ghosted',
    'follow_up': 'Follow Up',
};

let userContacts = [];


// ===== TAB SWITCHING: hides/shows the relevant div panels =====
function switchTab(tabId) {
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    ['tab-edit', 'tab-interview', 'tab-notes', 'tab-documents'].forEach(id => {
        document.getElementById(id).style.display = id === tabId ? '' : 'none';
    });
}


// ===== MODAL MODE HELPERS =====
function setAddMode() {
    document.getElementById('addModeHeader').style.display = '';
    document.getElementById('editModeHeader').style.display = 'none';
    document.getElementById('modalTabBar').style.display = 'none';
    document.getElementById('tab-interview').style.display = 'none';
    document.getElementById('tab-notes').style.display = 'none';
    document.getElementById('tab-documents').style.display = 'none';
    document.getElementById('tab-edit').style.display = '';
    document.getElementById('notesInEditTab').style.display = '';
    document.querySelectorAll('.modal-tab-btn').forEach((btn, i) => {
        btn.classList.toggle('active', i === 0);
    });
}

function setEditMode() {
    document.getElementById('addModeHeader').style.display = 'none';
    document.getElementById('editModeHeader').style.display = '';
    document.getElementById('modalTabBar').style.display = 'flex';
    document.getElementById('notesInEditTab').style.display = 'none';
    switchTab('tab-edit');
}

function populateContactSelect(selectEl, selectedId) {
    selectEl.innerHTML = '<option value="">— None —</option>';
    userContacts.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name + (c.job_title ? ` — ${c.job_title}` : '');
        if (String(c.id) === String(selectedId)) opt.selected = true;
        selectEl.appendChild(opt);
    });
}

// Form reset, tab clicks, column footer clicks, Add Interview Round button, Save Documents, Save Notes
document.addEventListener("DOMContentLoaded", function () {

    const statusField = document.getElementById("id_status");
    const statusWrapper = document.getElementById("statusFieldWrapper");

    function resetModalForAdd() {
        document.getElementById("jobIdInput").value = "";
        document.getElementById("modalTitle").innerText = "New Application";
        document.getElementById("modalSubmitText").innerText = "Save Application";
        document.getElementById("jobForm").reset();
        setAddMode();
    }

    // Tab button clicks
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });

    // When clicking column footer
    document.querySelectorAll(".board-footer").forEach(function (el) {
        el.addEventListener("click", function () {
            resetModalForAdd();

            const status = this.dataset.status;
            if (statusField && status) {
                for (let i = 0; i < statusField.options.length; i++) {
                    if (statusField.options[i].value === status) {
                        statusField.selectedIndex = i;
                        break;
                    }
                }
            }
            statusWrapper.style.display = "none";
        });
    });

    // When clicking main Add Application button
    const mainAddBtn = document.querySelector('[data-bs-target="#addJobModal"]:not(.board-footer)');
    if (mainAddBtn) {
        mainAddBtn.addEventListener("click", function () {
            resetModalForAdd();
            statusWrapper.style.display = "block";
            statusField.selectedIndex = 0;
        });
    }

    // Add Interview Round button
    document.getElementById('addInterviewRoundBtn').addEventListener('click', function () {
        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return;
        if (document.querySelector('.iv-unsaved')) return; // one unsaved at a time

        const container = document.getElementById('interviewRoundsContainer');
        const emptyState = container.querySelector('.iv-empty-state');
        if (emptyState) emptyState.remove();

        const existingCount = container.querySelectorAll('.interview-round-card').length;
        const card = createRoundCard(
            { id: null, interview_type: 'Human Resources', date: '', result: '', notes: '' },
            existingCount + 1,
            jobId
        );
        container.prepend(card);
        card.querySelector('.iv-date').focus();
    });

    // Save Documents button
    document.getElementById('saveDocumentsBtn').addEventListener('click', function () {
        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return;
        const selectedIds = Array.from(document.querySelectorAll('.doc-attach-cb:checked')).map(cb => parseInt(cb.value));
        fetch(`/update-job-documents/${jobId}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ document_ids: selectedIds })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const modalEl = document.getElementById('addJobModal');
                bootstrap.Modal.getInstance(modalEl)?.hide();
            }
        });
    });

    // Save Notes button
    document.getElementById('saveNotesBtn').addEventListener('click', function () {
        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return;

        const notes = document.getElementById('appNotesArea').value;

        fetch(`/update-job/${jobId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                status: document.querySelector('[name="status"]').value,
                notes: notes,
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.querySelector('[name="notes"]').value = notes;
                const modalEl = document.getElementById('addJobModal');
                bootstrap.Modal.getInstance(modalEl)?.hide();
            }
        });
    });
});


// Initialises SortableJS drag-and-drop on all .board-body columns
document.addEventListener('DOMContentLoaded', function() {

    const columns = document.querySelectorAll('.board-body');

    columns.forEach(column => {
        new Sortable(column, {
            group: 'jobs',
            animation: 150,
            ghostClass: 'dragging',
            onEnd: function(evt) {
                const jobId = evt.item.dataset.jobId;
                const newStatus = evt.to.dataset.status;

                if (evt.from !== evt.to) {
                    evt.item.dataset.status = newStatus;
                    updateEmptyState(evt.to);
                    updateEmptyState(evt.from);

                    fetch(`/update-job-status/${jobId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({status: newStatus})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.success) {
                            console.error('Failed to update status:', data.error);
                            evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
                        }
                    })
                    .catch(err => {
                        console.error('AJAX error:', err);
                        evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
                    });
                }
            }
        });
    });
});

// Handles the form submit event (decides create vs. AJAX edit based on whether jobIdInput has a value)
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("jobForm");

    form.addEventListener("submit", function(e) {
        e.preventDefault();

        const jobId = document.getElementById("jobIdInput").value;
        if (!jobId) {
            this.submit(); // normal create
            return;
        }

        fetch(`/update-job/${jobId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                status: document.querySelector('[name="status"]').value,
                notes: document.querySelector('[name="notes"]').value,
                job_title: document.querySelector('[name="job_title"]').value,
                salary_range: document.querySelector('[name="salary_range"]').value,
                recruiter_id: document.getElementById('recruiterSelect').value,
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.job-card[data-job-id='${jobId}']`);
                if (!card) return;

                const newStatus = document.querySelector('[name="status"]').value;
                const sourceColumn = card.closest('.board-body');
                const targetColumn = document.querySelector(`.board-body[data-status='${newStatus}']`);

                if (sourceColumn && targetColumn) {
                    targetColumn.appendChild(card);
                    card.dataset.status = newStatus;
                    updateEmptyState(sourceColumn);
                    updateEmptyState(targetColumn);
                }

                // Update card text
                const newTitle = document.querySelector('[name="job_title"]').value;
                if (newTitle) {
                    const titleEl = card.querySelector('.job-title');
                    if (titleEl) titleEl.innerText = newTitle;
                }

                const modalEl = document.getElementById('addJobModal');
                bootstrap.Modal.getInstance(modalEl)?.hide();
            }
        });
    });
});


// JS helper to handle empty states. It removes any existing "No applications" message, then adds one back only if no job cards remain. This keeps the empty state accurate without a page reload

function updateEmptyState(columnBody) {
    if (!columnBody) return;
    columnBody.querySelectorAll('.empty-state').forEach(el => el.remove());
    if (columnBody.querySelectorAll('.job-card').length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.classList.add('empty-state');
        emptyDiv.innerText = "No applications";
        columnBody.appendChild(emptyDiv);
    }
}

// Watches the status <select> for changes and fires the live status update + card move
document.addEventListener('DOMContentLoaded', function () {

    const statusSelect = document.querySelector('[name="status"]');

    statusSelect.addEventListener('change', function () {
        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return;

        const newStatus = this.value;

        // Update status pill in detail header
        const pill = document.getElementById('detailStatusPill');
        if (pill) {
            pill.className = `modal-status-pill ${newStatus}`;
            pill.innerText = STATUS_LABELS[newStatus] || newStatus;
        }

        fetch(`/update-job-status/${jobId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.job-card[data-job-id='${jobId}']`);
                const sourceColumn = card ? card.closest('.board-body') : null;
                const targetColumn = document.querySelector(`.board-body[data-status='${newStatus}']`);

                if (card && targetColumn) {
                    targetColumn.appendChild(card);
                    card.dataset.status = newStatus;
                    updateEmptyState(sourceColumn);
                    updateEmptyState(targetColumn);
                }
            } else {
                console.error("Failed to update status");
            }
        });
    });
});


function deleteJob(event, jobId) {
    event.stopPropagation();

    fetch(`/delete-job/${jobId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const card = document.querySelector(`.job-card[data-job-id='${jobId}']`);
            if (card) {
                const column = card.closest('.board-body');
                card.remove();
                updateEmptyState(column);
            }
        } else {
            console.error('Failed to delete job:', data.error);
        }
    })
    .catch(err => console.error('Delete error:', err));
}

// fires two fetch() calls in parallel using Promise.all() — one to get the job data, one to get the user's contacts
function openEditModal(jobId) {
    Promise.all([
        fetch(`/get-job/${jobId}/`).then(r => r.json()),
        fetch(`/contacts/api/`).then(r => r.json()),
    ])
    .then(([data, contactsData]) => {
        userContacts = contactsData.contacts;

        setEditMode();

        document.getElementById('detailTitle').innerText = data.job_title;

        let meta = '';
        if (data.company_name) meta += `<span class="meta-chip"><i class="fas fa-building"></i> ${data.company_name}</span>`;
        if (data.company_location) meta += `<span class="meta-chip"><i class="fas fa-map-marker-alt"></i> ${data.company_location}</span>`;
        if (data.salary_range) meta += `<span class="meta-chip"><i class="fas fa-pound-sign"></i> ${data.salary_range}</span>`;
        if (data.date_applied) meta += `<span class="meta-chip"><i class="fas fa-calendar-alt"></i> ${data.date_applied}</span>`;
        document.getElementById('detailMeta').innerHTML = meta;

        const pill = document.getElementById('detailStatusPill');
        pill.className = `modal-status-pill ${data.status}`;
        pill.innerText = STATUS_LABELS[data.status] || data.status;

        document.getElementById('jobIdInput').value = data.id;
        document.querySelector('[name="company_name"]').value = data.company_name;
        document.querySelector('[name="company_location"]').value = data.company_location;
        document.querySelector('[name="company_website"]').value = data.company_website;
        document.querySelector('[name="job_title"]').value = data.job_title;
        document.querySelector('[name="salary_range"]').value = data.salary_range;
        document.querySelector('[name="status"]').value = data.status;
        document.querySelector('[name="date_applied"]').value = data.date_applied;
        document.querySelector('[name="notes"]').value = data.notes;

        populateContactSelect(document.getElementById('recruiterSelect'), data.recruiter_id);

        document.getElementById('appNotesArea').value = data.notes;
        document.getElementById('modalSubmitText').innerText = 'Save Changes';

        loadInterviews(data.id);
        loadDocuments(data.id, data.document_ids || []);

        const modalEl = document.getElementById('addJobModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    });
}


// ===== DOCUMENTS TAB =====

let allUserDocuments = [];

function loadDocuments(jobId, attachedIds) {
    fetch('/documents/api/')
        .then(r => r.json())
        .then(data => {
            allUserDocuments = data.documents;
            renderDocumentCheckList(attachedIds.map(String));
        });
}

function renderDocumentCheckList(attachedIds) {
    const container = document.getElementById('documentCheckList');
    if (allUserDocuments.length === 0) {
        container.innerHTML = '<p style="color:#9ca3af;font-size:0.875rem;">No documents in your library yet. <a href="/documents/" style="color:var(--teal);">Upload documents here</a>.</p>';
        return;
    }
    container.innerHTML = '';
    allUserDocuments.forEach(doc => {
        const uid = `doc-cb-${doc.id}`;
        const isChecked = attachedIds.includes(String(doc.id));
        const row = document.createElement('div');
        row.className = 'iv-interviewer-cb-row';
        row.style.cssText = 'display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0;border-bottom:1px solid #f3f4f6;';
        row.innerHTML = `
            <input type="checkbox" class="doc-attach-cb" id="${uid}" value="${doc.id}"${isChecked ? ' checked' : ''}>
            <label for="${uid}" style="font-size:0.875rem;color:#111827;cursor:pointer;flex:1;margin:0;">
                ${doc.name}
                <span style="font-size:0.75rem;color:#9ca3af;margin-left:0.375rem;">${doc.file_type}</span>
            </label>
            <a href="${doc.url}" target="_blank" rel="noopener"
               style="font-size:0.75rem;color:var(--teal);text-decoration:none;"
               title="Download">
                <i class="fas fa-download"></i>
            </a>
        `;
        container.appendChild(row);
    });
}


// ===== INTERVIEW ROUNDS =====

function loadInterviews(jobId) {
    fetch(`/get-interviews/${jobId}/`)
        .then(r => r.json())
        .then(data => {
            console.log('[loadInterviews] response:', JSON.stringify(data.interviews));
            renderInterviewRounds(data.interviews, jobId);
        });
}

function renderInterviewRounds(interviews, jobId) {
    const container = document.getElementById('interviewRoundsContainer');
    container.innerHTML = '';

    if (interviews.length === 0) {
        container.innerHTML = '<p class="iv-empty-state">No interview rounds yet. Click "Add Interview Round" to get started.</p>';
        return;
    }

    // interviews are oldest-first; display newest-first, Round 1 = oldest
    const total = interviews.length;
    interviews.slice().reverse().forEach((iv, idx) => {
        const roundNum = total - idx;
        container.appendChild(createRoundCard(iv, roundNum, jobId));
    });
}

function createRoundCard(iv, roundNum, jobId) {
    const isNew = !iv.id;
    const card = document.createElement('div');
    card.className = 'interview-round-card' + (isNew ? ' iv-unsaved' : '');

    card.innerHTML = `
        <div class="interview-round-label">Round ${roundNum}</div>
        <div class="row g-3 mb-3">
            <div class="col-md-6">
                <label class="modal-label">Interview Type <span class="iv-required">*</span></label>
                <select class="form-control iv-type" required>
                    <option value="Human Resources"${iv.interview_type === 'Human Resources' ? ' selected' : ''}>Human Resources</option>
                    <option value="Design Interview"${iv.interview_type === 'Design Interview' ? ' selected' : ''}>Design Interview</option>
                    <option value="Technical Interview"${iv.interview_type === 'Technical Interview' ? ' selected' : ''}>Technical Interview</option>
                    <option value="Technical Hands On"${iv.interview_type === 'Technical Hands On' ? ' selected' : ''}>Technical Hands On</option>
                    <option value="Final"${iv.interview_type === 'Final' ? ' selected' : ''}>Final</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="modal-label">Date &amp; Time <span class="iv-required">*</span></label>
                <input type="datetime-local" class="form-control iv-date" value="${iv.date || ''}" required>
            </div>
        </div>
        <div class="mb-3">
            <label class="modal-label">Result <span class="modal-optional">(optional)</span></label>
            <input type="text" class="form-control iv-result" value="${iv.result || ''}" placeholder="e.g. Passed, Pending...">
        </div>
        <div class="mb-3">
            <label class="modal-label">Notes <span class="modal-optional">(optional)</span></label>
            <textarea class="form-control iv-notes" rows="3" placeholder="Questions asked, key points, follow-ups...">${iv.notes || ''}</textarea>
        </div>
        <div class="mb-3 iv-interviewers-section">
            <label class="modal-label">Interviewer(s) <span class="modal-optional">(optional)</span></label>
            <div class="iv-interviewers-list"></div>
        </div>
        <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn-modal-cancel delete-round-btn">
                <i class="fas fa-trash-alt me-1"></i> Delete
            </button>
            <button type="button" class="btn-teal save-round-btn">
                <i class="fas fa-save me-1"></i> Save
            </button>
        </div>
    `;

    const interviewersList = card.querySelector('.iv-interviewers-list');
    const selectedIds = (iv.interviewer_ids || []).map(String);
    console.log(`[createRoundCard] round ${roundNum} iv.interviewer_ids:`, iv.interviewer_ids, '→ selectedIds:', selectedIds);
    if (userContacts.length === 0) {
        card.querySelector('.iv-interviewers-section').style.display = 'none';
    } else {
        userContacts.forEach(c => {
            const uid = `iv-cb-${roundNum}-${c.id}`;
            const isChecked = selectedIds.includes(String(c.id));
            const wrapper = document.createElement('div');
            wrapper.className = 'iv-interviewer-cb-row';
            wrapper.innerHTML = `
                <input type="checkbox" class="iv-interviewer-cb" id="${uid}" value="${c.id}"${isChecked ? ' checked' : ''}>
                <label for="${uid}">${c.name}${c.job_title ? ` <span class="iv-cb-title">— ${c.job_title}</span>` : ''}</label>
            `;
            interviewersList.appendChild(wrapper);
        });
    }

    // Save
    card.querySelector('.save-round-btn').addEventListener('click', function () {
        const typeEl = card.querySelector('.iv-type');
        const dateEl = card.querySelector('.iv-date');
        let valid = true;

        if (!typeEl.value) {
            typeEl.style.borderColor = '#dc3545';
            valid = false;
        } else {
            typeEl.style.borderColor = '';
        }

        if (!dateEl.value) {
            dateEl.style.borderColor = '#dc3545';
            if (valid) dateEl.focus();
            valid = false;
        } else {
            dateEl.style.borderColor = '';
        }

        if (!valid) return;

        const saveBtn = card.querySelector('.save-round-btn');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Saving…';

        const selectedInterviewerIds = Array.from(card.querySelectorAll('.iv-interviewer-cb:checked')).map(cb => parseInt(cb.value));
        console.log('[IV Save] sending interviewer_ids:', selectedInterviewerIds);

        const url = isNew ? `/save-interview/${jobId}/` : `/update-interview/${iv.id}/`;
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({
                interview_type: typeEl.value,
                date: dateEl.value,
                result: card.querySelector('.iv-result').value,
                notes: card.querySelector('.iv-notes').value,
                interviewer_ids: selectedInterviewerIds,
            })
        })
        .then(r => r.json())
        .then(data => {
            console.log('[IV Save] server response:', data);
            if (data.success) {
                // Re-sync the recruiter select to avoid stale display
                const currentRecruiterId = document.getElementById('recruiterSelect').value;
                loadInterviews(jobId);
                // Restore recruiter selection in case DOM re-render affected it
                document.getElementById('recruiterSelect').value = currentRecruiterId;
            } else {
                console.error('Save interview failed:', data.error || 'Unknown error');
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i> Save failed — retry';
            }
        })
        .catch(err => {
            console.error('Save interview error:', err);
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i> Save failed — retry';
        });
    });

    // Delete
    card.querySelector('.delete-round-btn').addEventListener('click', function () {
        if (isNew) {
            card.remove();
            const container = document.getElementById('interviewRoundsContainer');
            if (!container.querySelector('.interview-round-card')) {
                container.innerHTML = '<p class="iv-empty-state">No interview rounds yet. Click "Add Interview Round" to get started.</p>';
            }
            return;
        }
        fetch(`/delete-interview/${iv.id}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then(r => r.json())
        .then(data => { if (data.success) loadInterviews(jobId); });
    });

    return card;
}
