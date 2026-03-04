console.log("TRACKER JS LOADED");


document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("addJobModal");
    const statusField = document.getElementById("id_status");
    const statusWrapper = document.getElementById("statusFieldWrapper");

    // When clicking column footer
    document.querySelectorAll(".board-footer").forEach(function (el) {
        el.addEventListener("click", function () {

            const status = this.dataset.status;

            // console.log("Clicked column status:", status);
            // console.log("Status field element:", statusField);

            if (statusField && status) {

                // Reset selection first
                // statusField.selectedIndex = 0;

                // Find matching option safely
                for (let i = 0; i < statusField.options.length; i++) {
                    if (statusField.options[i].value === status) {
                        statusField.selectedIndex = i;
                        break;
                    }
                }
            }

            // Hide status field
            statusWrapper.style.display = "none";
        });
    });



     // When clicking main Add Job button
    const mainAddBtn = document.querySelector('[data-bs-target="#addJobModal"]:not(.board-footer)');

    if (mainAddBtn) {
        mainAddBtn.addEventListener("click", function () {
            statusWrapper.style.display = "block";
            statusField.selectedIndex = 0; // reset
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