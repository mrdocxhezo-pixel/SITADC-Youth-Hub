// SITADC Youth Hub Settings Module

(function () {
    'use strict';

    // ============================================
    // Settings Navigation (Mobile)
    // ============================================
    const SettingsNav = (function () {
        const SELECTORS = {
            sidebar: '#settingsSidebar',
            toggle: '#mobileSettingsToggle',
            backdrop: '.settings-backdrop',
            navLinks: '.settings-nav .nav-link[href]'
        };

        let elements = {};
        let state = {
            isOpen: false
        };

        function cacheElements() {
            elements = {
                sidebar: document.querySelector(SELECTORS.sidebar),
                toggle: document.querySelector(SELECTORS.toggle),
                backdrop: document.querySelector(SELECTORS.backdrop),
                navLinks: document.querySelectorAll(SELECTORS.navLinks)
            };
        }

        function ensureBackdrop() {
            if (!elements.backdrop) {
                const backdrop = document.createElement('div');
                backdrop.className = 'settings-backdrop';
                backdrop.setAttribute('aria-hidden', 'true');
                document.body.appendChild(backdrop);
                elements.backdrop = backdrop;
            }
            return elements.backdrop;
        }

        function updateAria() {
            if (elements.toggle) {
                elements.toggle.setAttribute('aria-expanded', state.isOpen.toString());
                elements.toggle.setAttribute('aria-label', state.isOpen ? 'Close settings navigation' : 'Open settings navigation');
                const icon = elements.toggle.querySelector('i');
                if (icon) {
                    icon.className = state.isOpen ? 'bi bi-x-lg fs-5' : 'bi bi-gear fs-5';
                }
            }
            if (elements.sidebar) {
                elements.sidebar.setAttribute('aria-hidden', (!state.isOpen).toString());
            }
        }

        function updateBackdrop() {
            const backdrop = ensureBackdrop();
            if (state.isOpen && window.matchMedia('(max-width: 991.98px)').matches) {
                backdrop.classList.add('show');
            } else {
                backdrop.classList.remove('show');
            }
        }

        function updateBodyScroll() {
            if (state.isOpen && window.matchMedia('(max-width: 991.98px)').matches) {
                document.body.classList.add('settings-sidebar-open');
                document.body.style.top = `-${window.scrollY}px`;
            } else {
                const scrollY = document.body.style.top;
                document.body.classList.remove('settings-sidebar-open');
                document.body.style.top = '';
                if (scrollY) {
                    window.scrollTo(0, parseInt(scrollY, 10) * -1);
                }
            }
        }

        function open() {
            if (state.isOpen) return;
            state.isOpen = true;
            elements.sidebar.classList.add('show');
            updateAria();
            updateBackdrop();
            updateBodyScroll();
        }

        function close() {
            if (!state.isOpen) return;
            state.isOpen = false;
            elements.sidebar.classList.remove('show');
            updateAria();
            updateBackdrop();
            updateBodyScroll();
        }

        function toggle() {
            if (state.isOpen) {
                close();
            } else {
                open();
            }
        }

        function handleResize() {
            const isMobile = window.matchMedia('(max-width: 991.98px)').matches;
            if (!isMobile && state.isOpen) {
                close();
            }
            updateBackdrop();
            updateBodyScroll();
        }

        function handleKeydown(e) {
            if (e.key === 'Escape' && state.isOpen) {
                close();
            }
        }

        function handleBackdropClick(e) {
            if (e.target === elements.backdrop) {
                close();
            }
        }

        function handleNavLinkClick() {
            if (state.isOpen && window.matchMedia('(max-width: 991.98px)').matches) {
                setTimeout(close, 100);
            }
        }

        function bindEvents() {
            if (elements.toggle) {
                elements.toggle.addEventListener('click', toggle);
            }
            document.addEventListener('click', handleBackdropClick);
            document.addEventListener('keydown', handleKeydown);
            window.addEventListener('resize', handleResize);
            elements.navLinks.forEach(link => {
                link.addEventListener('click', handleNavLinkClick);
            });
        }

        function init() {
            cacheElements();
            if (!elements.sidebar) return;
            ensureBackdrop();
            bindEvents();
            updateAria();
            updateBackdrop();
        }

        return { init, open, close, toggle };
    })();

    // ============================================
    // Form Auto-save (AJAX)
    // ============================================
    const FormAutoSave = (function () {
        let saveTimers = new Map();

        function autoSave(form, section) {
            const formData = new FormData(form);
            formData.append('action', 'ajax_save');

            fetch(`/settings/ajax/save/${section}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message || 'Settings saved', 'success');
                } else {
                    showToast(data.error || 'Failed to save', 'danger');
                }
            })
            .catch(() => {
                showToast('Network error', 'danger');
            });
        }

        function showToast(message, type = 'info') {
            const toastContainer = document.getElementById('toast-container') || createToastContainer();
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            toastContainer.appendChild(toast);
            const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
            bsToast.show();
            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        }

        function createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1080';
            document.body.appendChild(container);
            return container;
        }

        function init() {
            // Add auto-save to forms with data-autosave attribute
            document.querySelectorAll('form[data-autosave]').forEach(form => {
                const section = form.dataset.autosave;
                const inputs = form.querySelectorAll('input, select, textarea');

                inputs.forEach(input => {
                    input.addEventListener('change', () => {
                        clearTimeout(saveTimers.get(form));
                        saveTimers.set(form, setTimeout(() => autoSave(form, section), 1000));
                    });
                });
            });
        }

        return { init };
    })();

    // ============================================
    // Theme Preview
    // ============================================
    const ThemePreview = (function () {
        function init() {
            const themeRadios = document.querySelectorAll('input[name="theme"]');
            const previewContainer = document.querySelector('.preview-container');

            if (!previewContainer) return;

            function updatePreview() {
                const theme = document.querySelector('input[name="theme"]:checked')?.value || 'system';
                if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    previewContainer.classList.add('dark-mode');
                } else {
                    previewContainer.classList.remove('dark-mode');
                }
            }

            themeRadios.forEach(radio => radio.addEventListener('change', updatePreview));
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updatePreview);
            updatePreview();
        }

        return { init };
    })();

    // ============================================
    // Password Strength
    // ============================================
    const PasswordStrength = (function () {
        function init() {
            const passwordInput = document.querySelector('[name="new_password1"]');
            const strengthBar = document.getElementById('passwordStrengthBar');
            const strengthText = document.getElementById('passwordStrengthText');

            if (!passwordInput || !strengthBar) return;

            passwordInput.addEventListener('input', function () {
                const password = this.value;
                let strength = 0;

                if (password.length >= 8) strength += 20;
                if (password.length >= 12) strength += 10;
                if (/[A-Z]/.test(password)) strength += 20;
                if (/[a-z]/.test(password)) strength += 20;
                if (/[0-9]/.test(password)) strength += 15;
                if (/[^A-Za-z0-9]/.test(password)) strength += 15;

                strength = Math.min(strength, 100);

                const bar = strengthBar.querySelector('.progress-bar');
                bar.style.width = strength + '%';

                if (strength < 40) {
                    bar.className = 'progress-bar bg-danger';
                    strengthText.textContent = 'Weak';
                } else if (strength < 70) {
                    bar.className = 'progress-bar bg-warning';
                    strengthText.textContent = 'Fair';
                } else {
                    bar.className = 'progress-bar bg-success';
                    strengthText.textContent = 'Strong';
                }
            });
        }

        return { init };
    })();

    // ============================================
    // Initialize on DOM Ready
    // ============================================
    document.addEventListener('DOMContentLoaded', function () {
        SettingsNav.init();
        FormAutoSave.init();
        ThemePreview.init();
        PasswordStrength.init();

        // Initialize Bootstrap tooltips
        if (window.bootstrap) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltipTriggerList.forEach(
                (tooltipTriggerEl) => new window.bootstrap.Tooltip(tooltipTriggerEl)
            );
        }
    });

    // Export for testing/debugging
    window.SITADC = window.SITADC || {};
    window.SITADC.Settings = {
        SettingsNav,
        FormAutoSave,
        ThemePreview,
        PasswordStrength
    };

})();