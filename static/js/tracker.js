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