// SITADC Youth Hub Base Scripts

(function () {
    'use strict';

    // ============================================
    // Sidebar Navigation Module
    // ============================================
    const Sidebar = (function () {
        const STORAGE_KEY = 'sitadc_sidebar_state';
        const SELECTORS = {
            sidebar: '#sidebar',
            sidebarToggle: '#sidebarToggle',
            sidebarClose: '#sidebarClose',
            backdrop: '.sidebar-backdrop',
            body: 'body',
            navLinks: '.dashboard-sidebar .nav-link[href]'
        };

        let elements = {};
        let state = {
            isOpen: false,
            wasOpen: false,
            lastFocusedElement: null
        };

        // Initialize DOM elements
        function cacheElements() {
            elements = {
                sidebar: document.querySelector(SELECTORS.sidebar),
                sidebarToggle: document.querySelector(SELECTORS.sidebarToggle),
                sidebarClose: document.querySelector(SELECTORS.sidebarClose),
                backdrop: document.querySelector(SELECTORS.backdrop),
                body: document.querySelector(SELECTORS.body),
                navLinks: document.querySelectorAll(SELECTORS.navLinks)
            };
        }

        // Create backdrop element if it doesn't exist
        function ensureBackdrop() {
            if (!elements.backdrop) {
                const backdrop = document.createElement('div');
                backdrop.className = 'sidebar-backdrop';
                backdrop.setAttribute('aria-hidden', 'true');
                document.body.appendChild(backdrop);
                elements.backdrop = backdrop;
            }
            return elements.backdrop;
        }

        // Load state from localStorage
        function loadState() {
            try {
                const stored = localStorage.getItem(STORAGE_KEY);
                if (stored) {
                    const parsed = JSON.parse(stored);
                    state.wasOpen = parsed.isOpen === true;
                }
            } catch (e) {
                // Ignore localStorage errors
            }
        }

        // Save state to localStorage
        function saveState() {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify({ isOpen: state.isOpen }));
            } catch (e) {
                // Ignore localStorage errors
            }
        }

        // Update ARIA attributes
        function updateAria() {
            if (elements.sidebarToggle) {
                elements.sidebarToggle.setAttribute('aria-expanded', state.isOpen.toString());
                elements.sidebarToggle.setAttribute('aria-label', state.isOpen ? 'Close navigation' : 'Open navigation');
                // Update icon
                const icon = elements.sidebarToggle.querySelector('i');
                if (icon) {
                    icon.className = state.isOpen ? 'bi bi-x-lg fs-4' : 'bi bi-list fs-4';
                }
            }
            if (elements.sidebarClose) {
                elements.sidebarClose.setAttribute('aria-expanded', state.isOpen.toString());
            }
            if (elements.sidebar) {
                elements.sidebar.setAttribute('aria-hidden', (!state.isOpen).toString());
            }
        }

        // Update backdrop visibility
        function updateBackdrop() {
            const backdrop = ensureBackdrop();
            if (state.isOpen && window.matchMedia('(max-width: 767.98px)').matches) {
                backdrop.classList.add('show');
            } else {
                backdrop.classList.remove('show');
            }
        }

        // Update body scroll lock
        function updateBodyScroll() {
            if (state.isOpen && window.matchMedia('(max-width: 767.98px)').matches) {
                elements.body.classList.add('sidebar-open');
                elements.body.style.top = `-${window.scrollY}px`;
            } else {
                const scrollY = elements.body.style.top;
                elements.body.classList.remove('sidebar-open');
                elements.body.style.top = '';
                if (scrollY) {
                    window.scrollTo(0, parseInt(scrollY, 10) * -1);
                }
            }
        }

        // Focus management
        function trapFocus() {
            if (!state.isOpen) return;

            const focusableElements = elements.sidebar.querySelectorAll(
                'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );

            if (focusableElements.length > 0) {
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];

                function handleTab(e) {
                    if (e.key !== 'Tab') return;

                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            e.preventDefault();
                            lastElement.focus();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            e.preventDefault();
                            firstElement.focus();
                        }
                    }
                }

                elements.sidebar.addEventListener('keydown', handleTab);
                elements.sidebar._focusTrapHandler = handleTab;

                // Focus first element
                firstElement.focus();
            }
        }

        function releaseFocus() {
            if (elements.sidebar._focusTrapHandler) {
                elements.sidebar.removeEventListener('keydown', elements.sidebar._focusTrapHandler);
                elements.sidebar._focusTrapHandler = null;
            }

            // Restore focus to toggle button
            if (elements.sidebarToggle) {
                elements.sidebarToggle.focus();
            }
        }

        // Open sidebar
        function open() {
            if (state.isOpen) return;

            state.lastFocusedElement = document.activeElement;
            state.isOpen = true;

            elements.sidebar.classList.add('show');
            updateAria();
            updateBackdrop();
            updateBodyScroll();
            trapFocus();
            saveState();

            // Emit custom event
            document.dispatchEvent(new CustomEvent('sidebar:open', { detail: { sidebar: elements.sidebar } }));
        }

        // Close sidebar
        function close() {
            if (!state.isOpen) return;

            state.isOpen = false;

            elements.sidebar.classList.remove('show');
            updateAria();
            updateBackdrop();
            updateBodyScroll();
            releaseFocus();
            saveState();

            // Emit custom event
            document.dispatchEvent(new CustomEvent('sidebar:close', { detail: { sidebar: elements.sidebar } }));
        }

        // Toggle sidebar
        function toggle() {
            if (state.isOpen) {
                close();
            } else {
                open();
            }
        }

        // Handle resize
        function handleResize() {
            const isMobile = window.matchMedia('(max-width: 767.98px)').matches;

            if (!isMobile && state.isOpen) {
                // On desktop, sidebar should always be visible
                close();
            } else if (isMobile && state.wasOpen && !state.isOpen) {
                // Restore state on mobile if it was previously open
                // Only if user hasn't explicitly closed it this session
            }

            updateBackdrop();
            updateBodyScroll();
        }

        // Handle escape key
        function handleKeydown(e) {
            if (e.key === 'Escape' && state.isOpen) {
                close();
            }
        }

        // Handle backdrop click
        function handleBackdropClick() {
            if (state.isOpen) {
                close();
            }
        }

        // Handle navigation link clicks (close on mobile after navigation)
        function handleNavLinkClick() {
            if (state.isOpen && window.matchMedia('(max-width: 767.98px)').matches) {
                // Small delay to allow navigation to start
                setTimeout(close, 100);
            }
        }

        // Initialize event listeners
        function bindEvents() {
            if (elements.sidebarToggle) {
                elements.sidebarToggle.addEventListener('click', toggle);
            }

            if (elements.sidebarClose) {
                elements.sidebarClose.addEventListener('click', close);
            }

            // Backdrop click
            document.addEventListener('click', function (e) {
                if (e.target === elements.backdrop) {
                    handleBackdropClick();
                }
            });

            // Escape key
            document.addEventListener('keydown', handleKeydown);

            // Resize handler
            window.addEventListener('resize', handleResize);

            // Navigation links
            elements.navLinks.forEach(link => {
                link.addEventListener('click', handleNavLinkClick);
            });
        }

        // Initialize sidebar
        function init() {
            cacheElements();
            loadState();

            if (!elements.sidebar) {
                return;
            }

            ensureBackdrop();
            bindEvents();

            // Apply initial state on mobile
            if (state.wasOpen && window.matchMedia('(max-width: 767.98px)').matches) {
                // Don't auto-open on load, but restore if explicitly set
                // We'll respect the saved state only if it was explicitly set by user interaction
            }

            updateAria();
            updateBackdrop();
        }

        // Public API
        return {
            init,
            open,
            close,
            toggle,
            getState: () => ({ ...state }),
            getElements: () => ({ ...elements })
        };
    })();

    // ============================================
    // Initialize on DOM Ready
    // ============================================
    document.addEventListener('DOMContentLoaded', function () {
        // Dynamically set the current year in the footer
        const yearSpan = document.getElementById('current-year');
        if (yearSpan) {
            yearSpan.textContent = new Date().getFullYear();
        }

        // Initialize Sidebar
        Sidebar.init();

        // Initialize Bootstrap Toasts
        if (window.bootstrap) {
            const toastElList = document.querySelectorAll('.toast');
            const toastList = [...toastElList].map((toastEl) => new window.bootstrap.Toast(toastEl));
            toastList.forEach((toast) => toast.show());

            // Initialize Bootstrap Tooltips
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltipTriggerList.forEach(
                (tooltipTriggerEl) => new window.bootstrap.Tooltip(tooltipTriggerEl)
            );
        }

        // Keep tabbed content usable independently of the Bootstrap CDN.
        const tabTriggers = [...document.querySelectorAll('[data-bs-toggle="tab"]')];
        const activateTab = (trigger) => {
            const targetSelector = trigger.getAttribute('data-bs-target');
            const target = targetSelector ? document.querySelector(targetSelector) : null;
            if (!target) return;

            const tabList = trigger.closest('[role="tablist"]');
            const tabContent = target.closest('.tab-content');
            tabList?.querySelectorAll('[role="tab"]').forEach((tab) => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            tabContent?.querySelectorAll('[role="tabpanel"]').forEach((panel) => {
                panel.classList.remove('active', 'show');
            });
            trigger.classList.add('active');
            trigger.setAttribute('aria-selected', 'true');
            target.classList.add('active', 'show');
        };

        tabTriggers.forEach((trigger, index) => {
            trigger.addEventListener('click', () => activateTab(trigger));
            trigger.addEventListener('keydown', (event) => {
                if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                event.preventDefault();
                let nextIndex = index;
                if (event.key === 'ArrowLeft')
                    nextIndex = (index - 1 + tabTriggers.length) % tabTriggers.length;
                if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabTriggers.length;
                if (event.key === 'Home') nextIndex = 0;
                if (event.key === 'End') nextIndex = tabTriggers.length - 1;
                tabTriggers[nextIndex].focus();
                activateTab(tabTriggers[nextIndex]);
            });
        });

        // Confirmation Dialog Handlers
        const confirmButtons = document.querySelectorAll('[data-confirm]');
        confirmButtons.forEach((button) => {
            button.addEventListener('click', function (e) {
                if (
                    !confirm(this.getAttribute('data-confirm') || 'Are you sure you want to proceed?')
                ) {
                    e.preventDefault();
                }
            });
        });
    });

    // Export for testing/debugging
    window.SITADC = window.SITADC || {};
    window.SITADC.Sidebar = Sidebar;

})();