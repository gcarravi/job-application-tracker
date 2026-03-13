// Toggle Sidebar
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('show');
}

// Update Date
function updateDate() {
    const now = new Date();
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    document.getElementById('currentDay').textContent = days[now.getDay()];
    document.getElementById('currentDate').textContent = months[now.getMonth()] + ' ' + now.getDate() + ', ' + now.getFullYear();
}

// Initialize
if (document.getElementById('currentDay')) {
    updateDate();
}

// User avatar dropdown
const userAvatarBtn = document.getElementById('userAvatarBtn');
const userDropdownMenu = document.getElementById('userDropdownMenu');
if (userAvatarBtn && userDropdownMenu) {
    userAvatarBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        userDropdownMenu.classList.toggle('open');
    });
    userDropdownMenu.addEventListener('click', function (e) {
        e.stopPropagation();
    });
    document.addEventListener('click', function () {
        userDropdownMenu.classList.remove('open');
    });
}
