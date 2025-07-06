// PyFastStack - Modern JavaScript with smooth interactions

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initThemeToggle();
    initMobileMenu();
    initNavbarScroll();
    initAlerts();
    initForms();
    initAnimations();
    initTooltips();
});

// Theme Toggle with smooth transitions
function initThemeToggle() {
    const themeToggles = document.querySelectorAll('.theme-toggle');
    const html = document.documentElement;
    
    // Check for saved theme preference or default to light
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply theme
    if (currentTheme === 'dark') {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }
    
    // Update toggle state
    updateThemeToggle(currentTheme);
    
    themeToggles.forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const isDark = html.classList.contains('dark');
            const newTheme = isDark ? 'light' : 'dark';
            
            // Add transition class
            html.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            
            // Update theme
            if (newTheme === 'dark') {
                html.classList.add('dark');
            } else {
                html.classList.remove('dark');
            }
            
            localStorage.setItem('theme', newTheme);
            
            // Update all toggles
            updateThemeToggle(newTheme);
            
            // Trigger custom event
            window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
        });
    });
}

function updateThemeToggle(theme) {
    const sliders = document.querySelectorAll('.theme-toggle-slider');
    const sunIcons = document.querySelectorAll('.sun-icon');
    const moonIcons = document.querySelectorAll('.moon-icon');
    
    if (theme === 'dark') {
        sliders.forEach(slider => slider.style.transform = 'translateX(20px)');
        sunIcons.forEach(icon => icon.classList.add('hidden'));
        moonIcons.forEach(icon => icon.classList.remove('hidden'));
    } else {
        sliders.forEach(slider => slider.style.transform = 'translateX(0)');
        sunIcons.forEach(icon => icon.classList.remove('hidden'));
        moonIcons.forEach(icon => icon.classList.add('hidden'));
    }
}

// Mobile Menu with smooth animations
function initMobileMenu() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const navMenuMobile = document.querySelector('.nav-menu-mobile');
    
    if (!mobileMenuButton || !navMenuMobile) {
        console.warn('Mobile menu elements not found', {
            button: mobileMenuButton,
            menu: navMenuMobile
        });
        return;
    }
    
    console.log('Mobile menu initialized');
    
    let isOpen = false;
    
    // Toggle menu function
    const toggleMenu = () => {
        isOpen = !isOpen;
        
        if (isOpen) {
            // Show menu
            navMenuMobile.classList.remove('hidden');
            navMenuMobile.classList.add('active');
            mobileMenuButton.setAttribute('aria-expanded', 'true');
            mobileMenuButton.classList.add('active');
            
            // Prevent body scroll when menu is open
            document.body.style.overflow = 'hidden';
        } else {
            // Hide menu
            navMenuMobile.classList.add('hidden');
            navMenuMobile.classList.remove('active');
            mobileMenuButton.setAttribute('aria-expanded', 'false');
            mobileMenuButton.classList.remove('active');
            
            // Restore body scroll
            document.body.style.overflow = '';
        }
    };
    
    mobileMenuButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Mobile menu button clicked', { isOpen });
        toggleMenu();
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (isOpen && !navMenuMobile.contains(e.target) && !mobileMenuButton.contains(e.target)) {
            toggleMenu();
        }
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen) {
            toggleMenu();
        }
    });
    
    // Close menu on window resize to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 1024 && isOpen) {
            toggleMenu();
        }
    });
}

// Navbar scroll effects
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Hide/show navbar on scroll
        if (currentScroll > lastScroll && currentScroll > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
}

// Enhanced alerts with animations
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.className = 'absolute top-3 right-3 text-2xl leading-none hover:opacity-70 transition-opacity';
        closeBtn.addEventListener('click', () => dismissAlert(alert));
        alert.appendChild(closeBtn);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            dismissAlert(alert);
        }, 5000);
    });
}

function dismissAlert(alert) {
    alert.style.transform = 'translateX(100%)';
    alert.style.opacity = '0';
    
    setTimeout(() => {
        alert.remove();
    }, 300);
}

// Enhanced form interactions
function initForms() {
    // Form submission loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalContent = submitBtn.innerHTML;
                submitBtn.setAttribute('data-original-content', originalContent);
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                `;
            }
        });
    });
    
    // Password strength indicator with visual feedback
    const passwordInputs = document.querySelectorAll('input[type="password"][name="password"]');
    passwordInputs.forEach(input => {
        const strengthContainer = document.createElement('div');
        strengthContainer.className = 'mt-2';
        input.parentElement.appendChild(strengthContainer);
        
        input.addEventListener('input', function() {
            const strength = getPasswordStrength(this.value);
            updatePasswordStrengthIndicator(strengthContainer, strength);
        });
    });
    
    // Input animations
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
    });
}

// Advanced password strength calculation
function getPasswordStrength(password) {
    let strength = 0;
    
    // Length checks
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (password.length >= 16) strength++;
    
    // Character variety checks
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    // Common patterns to avoid
    if (!/(.)\1{2,}/.test(password)) strength++; // No repeated characters
    if (!/^[0-9]+$/.test(password)) strength++; // Not just numbers
    
    return Math.min(strength, 5);
}

// Visual password strength indicator
function updatePasswordStrengthIndicator(container, strength) {
    const strengthLevels = [
        { label: 'Very Weak', class: 'bg-red-500', width: '20%' },
        { label: 'Weak', class: 'bg-orange-500', width: '40%' },
        { label: 'Fair', class: 'bg-yellow-500', width: '60%' },
        { label: 'Good', class: 'bg-blue-500', width: '80%' },
        { label: 'Strong', class: 'bg-green-500', width: '100%' }
    ];
    
    const level = strengthLevels[Math.min(strength, 4)];
    
    container.innerHTML = `
        <div class="flex items-center gap-2">
            <div class="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div class="h-full ${level.class} transition-all duration-300" style="width: ${level.width}"></div>
            </div>
            <span class="text-xs font-medium text-slate-600 dark:text-slate-400">${level.label}</span>
        </div>
    `;
}

// Smooth scroll animations
function initAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Add elements to observe
    const animatedElements = document.querySelectorAll(
        '.feature-card, .stat-card, .action-card, .dashboard-section, .profile-card, .settings-section'
    );
    
    animatedElements.forEach((el, index) => {
        el.style.animationDelay = `${index * 50}ms`;
        observer.observe(el);
    });
    
    // Parallax effect for hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallax = hero.querySelector('.hero-content');
            if (parallax) {
                parallax.style.transform = `translateY(${scrolled * 0.5}px)`;
                parallax.style.opacity = 1 - (scrolled * 0.002);
            }
        });
    }
}

// Tooltips
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(el => {
        let tooltip;
        
        el.addEventListener('mouseenter', (e) => {
            const text = el.getAttribute('data-tooltip');
            tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-3 py-2 text-sm text-white bg-slate-900 dark:bg-slate-700 rounded-lg shadow-lg opacity-0 transition-opacity duration-200';
            tooltip.textContent = text;
            
            document.body.appendChild(tooltip);
            
            const rect = el.getBoundingClientRect();
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 10);
        });
        
        el.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    tooltip.remove();
                }, 200);
            }
        });
    });
}

// CSRF Token handling
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

// Enhanced fetch wrapper with authentication
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
    
    const csrfToken = getCSRFToken();
    if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method)) {
        defaultOptions.headers['X-CSRFToken'] = csrfToken;
    }
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (response.status === 401) {
            // Store current location and redirect to login
            sessionStorage.setItem('redirectUrl', window.location.pathname);
            window.location.href = '/login';
            return null;
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Cookie helpers
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=Lax`;
}

// Smooth page transitions
window.addEventListener('beforeunload', () => {
    document.body.style.opacity = '0';
});

// Export utilities for use in other scripts
window.pyFastStack = {
    authenticatedFetch,
    getCookie,
    setCookie,
    deleteCookie,
    getCSRFToken,
    showAlert: (message, type = 'info') => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} mx-4 mt-6 animate-slide-down fixed top-16 right-0 left-0 z-50 max-w-md mx-auto`;
        alertDiv.innerHTML = `
            <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${type === 'success' ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>' : 
                  type === 'error' ? '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>' :
                  '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path>'}
            </svg>
            <span>${message}</span>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            dismissAlert(alertDiv);
        }, 5000);
    }
};