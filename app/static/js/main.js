// ReelToDigit Dynamic Order Wizard & Calculation Logic

document.addEventListener('DOMContentLoaded', () => {
    // Dynamic pricing init
    const cassetteInput = document.getElementById('cassette_count');
    if (cassetteInput) {
        cassetteInput.addEventListener('input', updatePricing);
        updatePricing();
    }

    // Profile Dropdown Toggle
    const profileBtn = document.getElementById('profileDropdownBtn');
    const profileMenu = document.getElementById('profileDropdownMenu');
    if (profileBtn && profileMenu) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileMenu.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
                profileMenu.classList.add('hidden');
            }
        });
    }
});

async function updatePricing() {
    const input = document.getElementById('cassette_count');
    if (!input) return;

    const count = parseInt(input.value) || 1;

    try {
        const formData = new FormData();
        formData.append('cassette_count', count);

        const response = await fetch('/orders/calculate', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            
            const countEl = document.getElementById('summary_count');
            const subtotalEl = document.getElementById('summary_subtotal');
            const shippingEl = document.getElementById('summary_shipping');
            const totalEl = document.getElementById('summary_total');

            if (countEl) countEl.textContent = data.count;
            if (subtotalEl) subtotalEl.textContent = `$${data.subtotal.toFixed(2)}`;
            if (shippingEl) shippingEl.textContent = `$${data.shipping.toFixed(2)}`;
            if (totalEl) totalEl.textContent = `$${data.total.toFixed(2)}`;
        }
    } catch (err) {
        console.error('Pricing calculation error:', err);
    }
}
