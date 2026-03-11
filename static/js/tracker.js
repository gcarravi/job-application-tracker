console.log("TRACKER JS LOADED");


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


// ===== TAB SWITCHING =====
function switchTab(tabId) {
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    ['tab-edit', 'tab-interview', 'tab-notes'].forEach(id => {
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

    // Save Interview button
    document.getElementById('saveInterviewBtn').addEventListener('click', function () {
        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return;

        fetch(`/save-interview/${jobId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                interview_type: document.getElementById('interviewType').value,
                date: document.getElementById('interviewDate').value,
                result: document.getElementById('interviewResult').value,
                notes: document.getElementById('interviewNotes').value,
            })
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


// Initialize Sortable in JS for drag and drop of the cards
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


// JS helper to handle empty states
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


function openEditModal(jobId) {

    fetch(`/get-job/${jobId}/`)
        .then(response => response.json())
        .then(data => {

            // Switch to edit mode UI
            setEditMode();

            // Populate detail header
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

            // Populate edit form
            document.getElementById('jobIdInput').value = data.id;
            document.querySelector('[name="company_name"]').value = data.company_name;
            document.querySelector('[name="company_location"]').value = data.company_location;
            document.querySelector('[name="company_website"]').value = data.company_website;
            document.querySelector('[name="job_title"]').value = data.job_title;
            document.querySelector('[name="salary_range"]').value = data.salary_range;
            document.querySelector('[name="status"]').value = data.status;
            document.querySelector('[name="date_applied"]').value = data.date_applied;
            document.querySelector('[name="notes"]').value = data.notes;

            // Populate notes tab
            document.getElementById('appNotesArea').value = data.notes;

            document.getElementById('modalSubmitText').innerText = 'Save Changes';

            // Load interview data
            fetch(`/get-interview/${data.id}/`)
                .then(r => r.json())
                .then(iv => {
                    if (iv.interview_type) document.getElementById('interviewType').value = iv.interview_type;
                    document.getElementById('interviewDate').value = iv.date || '';
                    document.getElementById('interviewResult').value = iv.result || '';
                    document.getElementById('interviewNotes').value = iv.notes || '';
                });

            const modalEl = document.getElementById('addJobModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        });
}
