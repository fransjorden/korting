/**
 * kort.ing - Main JavaScript
 */

// Mobile search toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileSearchToggle = document.getElementById('mobile-search-toggle');
    const mobileSearch = document.getElementById('mobile-search');

    if (mobileSearchToggle && mobileSearch) {
        mobileSearchToggle.addEventListener('click', function() {
            mobileSearch.classList.toggle('hidden');
            if (!mobileSearch.classList.contains('hidden')) {
                mobileSearch.querySelector('input').focus();
            }
        });
    }
});

/**
 * Copy coupon code to clipboard
 * @param {string} code - The coupon code to copy
 * @param {HTMLElement} button - The button element clicked
 */
function copyCode(code, button) {
    // Use modern clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code)
            .then(() => showCopySuccess(button))
            .catch(() => fallbackCopy(code, button));
    } else {
        fallbackCopy(code, button);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopy(code, button) {
    const textArea = document.createElement('textarea');
    textArea.value = code;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();

    try {
        document.execCommand('copy');
        showCopySuccess(button);
    } catch (err) {
        showToast('Kopiëren mislukt');
    }

    document.body.removeChild(textArea);
}

/**
 * Show copy success feedback
 */
function showCopySuccess(button) {
    const copyText = button.querySelector('.copy-text');
    const originalText = copyText.textContent;

    // Update button text
    copyText.textContent = 'Gekopieerd!';
    button.classList.add('bg-green-100');

    // Show toast notification
    showToast('✓ Code gekopieerd!');

    // Reset button after delay
    setTimeout(() => {
        copyText.textContent = originalText;
        button.classList.remove('bg-green-100');
    }, 2000);
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {number} duration - Display duration in ms
 */
function showToast(message, duration = 2000) {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create new toast
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Remove after duration
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Track outbound affiliate clicks (for analytics)
 * @param {string} dealId - The deal ID
 * @param {string} merchant - The merchant name
 */
function trackClick(dealId, merchant) {
    // In production, you'd send this to your analytics
    console.log(`Deal clicked: ${dealId} - ${merchant}`);

    // You could also send to Google Analytics, etc.
    if (typeof gtag === 'function') {
        gtag('event', 'deal_click', {
            'deal_id': dealId,
            'merchant': merchant
        });
    }
}

/**
 * Lazy load images with Intersection Observer
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check for native lazy loading support
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports native lazy loading
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src || img.src;
        });
    } else {
        // Fallback for older browsers
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');

        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        observer.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
});

/**
 * Handle image loading errors
 */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            // Use a placeholder for broken images
            if (!this.dataset.errorHandled) {
                this.dataset.errorHandled = 'true';
                this.src = 'https://via.placeholder.com/400x400?text=Geen+afbeelding';
            }
        });
    });
});

/**
 * Add keyboard accessibility for deal cards
 */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('article').forEach(card => {
        const mainLink = card.querySelector('a[href^="/deal/"]');
        if (mainLink) {
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.target === card) {
                    mainLink.click();
                }
            });
        }
    });
});
