// Main JavaScript file for Structural Vision

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initAlerts();
    initForms();
    initAnimations();
});

// Auto-hide alerts after 5 seconds
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
}

// Form enhancements
function initForms() {
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.textContent;
                submitBtn.setAttribute('data-original-text', originalText);
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
                
                // Add loading spinner or text
                if (submitBtn.classList.contains('btn-primary')) {
                    submitBtn.textContent = 'Processing...';
                }
            }
        });
    });

    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"][minlength]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            const strength = getPasswordStrength(this.value);
            updatePasswordStrengthIndicator(this, strength);
        });
    });
}

// Password strength calculation
function getPasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    return strength;
}

// Update password strength indicator
function updatePasswordStrengthIndicator(input, strength) {
    let indicator = input.parentElement.querySelector('.password-strength');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'password-strength';
        input.parentElement.appendChild(indicator);
    }
    
    const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    const strengthClass = ['very-weak', 'weak', 'fair', 'good', 'strong'];
    
    indicator.textContent = strengthText[strength] || 'Very Weak';
    indicator.className = 'password-strength ' + (strengthClass[strength] || 'very-weak');
}

// Add subtle animations
function initAnimations() {
    // Fade in elements
    const fadeElements = document.querySelectorAll('.feature-card, .stat-card, .action-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'opacity 0.5s, transform 0.5s';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                observer.unobserve(entry.target);
            }
        });
    });
    
    fadeElements.forEach(el => {
        observer.observe(el);
    });
}

// CSRF Token handling for AJAX requests
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
}

// Fetch wrapper with authentication
async function authenticatedFetch(url, options = {}) {
    const token = getCookie('access_token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (token) {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    const response = await fetch(url, mergedOptions);
    
    if (response.status === 401) {
        // Redirect to login if unauthorized
        window.location.href = '/login';
        return null;
    }
    
    return response;
}

// Cookie helper functions
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

// Export functions for use in other scripts
window.structuralVision = {
    authenticatedFetch,
    getCookie,
    setCookie,
    deleteCookie,
    getCSRFToken
};