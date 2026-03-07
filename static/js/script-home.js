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

// Pricing Toggle
document.getElementById('yearlyToggle')?.addEventListener('change', function () {
    const yearly = this.checked;
    const priceDisplay = document.getElementById('priceDisplay');
    const billingInfo = document.getElementById('billingInfo');
    const ctaText = document.getElementById('ctaText');
    const monthlyLabel = document.getElementById('monthlyLabel');
    const yearlyLabel = document.getElementById('yearlyLabel');

    if (yearly) {
        priceDisplay.textContent = '$6';
        billingInfo.textContent = 'Billed as $76/year';
        ctaText.textContent = 'Start Plus — $6/mo';
        monthlyLabel.className = 'text-secondary';
        yearlyLabel.className = 'fw-semibold';
        yearlyLabel.style.color = 'var(--teal)';
    } else {
        priceDisplay.textContent = '$9';
        billingInfo.textContent = '';
        ctaText.textContent = 'Start Plus — $9/mo';
        monthlyLabel.className = 'fw-semibold';
        monthlyLabel.style.color = 'var(--teal)';
        yearlyLabel.className = 'text-secondary';
        yearlyLabel.style.color = '';
    }
});

// Initialize
updateDate();
