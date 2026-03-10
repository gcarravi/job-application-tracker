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


document.addEventListener("DOMContentLoaded", function () {

    const statusField = document.getElementById("id_status");
    const statusWrapper = document.getElementById("statusFieldWrapper");

    function resetModalForAdd() {
        document.getElementById("jobIdInput").value = "";
        document.getElementById("modalTitle").innerText = "New Application";
        document.getElementById("modalSubmitText").innerText = "Save Application";
        document.getElementById("jobForm").reset();
    }

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

            // Hide status field (column footer pre-selects it)
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
});


// Initialize Sortable in JS for drag and drop of the cards
document.addEventListener('DOMContentLoaded', function() {

    const columns = document.querySelectorAll('.board-body');

    columns.forEach(column => {
        new Sortable(column, {
            group: 'jobs',          // allow dragging between columns
            animation: 150,
            ghostClass: 'dragging',
            onEnd: function(evt) {
                const jobId = evt.item.dataset.jobId;
                const newStatus = evt.to.dataset.status;

                // Only send AJAX if the card actually moved
                if (evt.from !== evt.to) {

                    // Update card's data-status so CSS border colour matches new column
                    evt.item.dataset.status = newStatus;

                    // Update empty states for source and target columns
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
                            // Optionally, revert card to original column
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

    // Helper to get CSRF token
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
                notes: document.querySelector('[name="notes"]').value
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.job-card[data-job-id='${jobId}']`);
                if (!card) return; // safety: card must exist

                const newStatus = document.querySelector('[name="status"]').value;

                const sourceColumn = card.closest('.board-body');
                const targetColumn = document.querySelector(`.board-body[data-status='${newStatus}']`);

                if (sourceColumn && targetColumn) {
                    // Move card
                    targetColumn.appendChild(card);
                    card.dataset.status = newStatus;

                    // Update empty states
                    updateEmptyState(sourceColumn);
                    updateEmptyState(targetColumn);
                }

                // Close modal
                const modalEl = document.getElementById('addJobModal');
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();
            }
        });
    });
});




// JS helper to handle empty states
function updateEmptyState(columnBody) {

    console.log("Inside updateEmptyState");

    if (!columnBody) return; // safety check
    // Remove existing empty-state divs
    columnBody.querySelectorAll('.empty-state').forEach(el => el.remove());

    // If no cards, add empty-state
    if (columnBody.querySelectorAll('.job-card').length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.classList.add('empty-state');
        emptyDiv.innerText = "No applications";
        columnBody.appendChild(emptyDiv);
    }
}




// Handles opening and updating the cards on the board.
document.addEventListener('DOMContentLoaded', function () {

    console.log("** Do I still use this function?? **");

    const statusSelect = document.querySelector('[name="status"]');

    statusSelect.addEventListener('change', function () {

        const jobId = document.getElementById('jobIdInput').value;
        if (!jobId) return; // Ignore if creating new job

        const newStatus = this.value;

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
    event.stopPropagation(); // prevent opening the edit modal

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

            const modalEl = document.getElementById('addJobModal');
            const modal = new bootstrap.Modal(modalEl);

            document.getElementById('modalTitle').innerText = "Update Application";

            document.getElementById('jobIdInput').value = data.id;

            document.querySelector('[name="company_name"]').value = data.company_name;
            document.querySelector('[name="company_location"]').value = data.company_location;
            document.querySelector('[name="company_website"]').value = data.company_website;
            document.querySelector('[name="job_title"]').value = data.job_title;
            document.querySelector('[name="salary_range"]').value = data.salary_range;
            document.querySelector('[name="status"]').value = data.status;
            document.querySelector('[name="date_applied"]').value = data.date_applied;
            document.querySelector('[name="notes"]').value = data.notes;

            // Change button text
            document.querySelector('#jobForm button[type="submit"]').innerText = "Update";

            modal.show();
        });
}