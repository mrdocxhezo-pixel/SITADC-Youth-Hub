/**
 * Accessibility Review Module - JavaScript Utilities
 * Provides client-side accessibility enhancements and preference management
 */

(function() {
  'use strict';

  // ─────────────────────────────────────────────────────────────────────────────
  // Accessibility Preference Management
  // ─────────────────────────────────────────────────────────────────────────────

  const AccessibilityPreferences = {
    // Default preferences
    defaults: {
      fontSize: 'MEDIUM',
      customFontSizePx: 16,
      colourTheme: 'SYSTEM',
      highContrast: false,
      reducedMotion: false,
      enhancedFocus: false,
      keyboardNavigationEnhanced: false,
      screenReaderOptimized: false,
      notificationTiming: 'DELAYED_5S',
      preferredLanguage: 'en',
      readingLineHeight: 1.5,
      readingLetterSpacing: 0,
      readingWordSpacing: 0,
      syncAcrossDevices: true
    },

    // Initialize preferences from server or localStorage
    init() {
      this.loadFromServer()
        .catch(() => this.loadFromStorage())
        .then(() => this.applyPreferences())
        .then(() => this.bindEvents());
    },

    // Load preferences from server API
    async loadFromServer() {
      const response = await fetch('/accessibility/api/preferences/', {
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': this.getCsrfToken()
        }
      });

      if (!response.ok) {
        throw new Error('Server preferences not available');
      }

      const data = await response.json();
      this.preferences = { ...this.defaults, ...data };
      this.saveToStorage();
    },

    // Load preferences from localStorage
    loadFromStorage() {
      try {
        const stored = localStorage.getItem('accessibility_preferences');
        if (stored) {
          this.preferences = { ...this.defaults, ...JSON.parse(stored) };
        } else {
          this.preferences = { ...this.defaults };
        }
      } catch (e) {
        this.preferences = { ...this.defaults };
      }
    },

    // Save preferences to localStorage
    saveToStorage() {
      try {
        localStorage.setItem('accessibility_preferences', JSON.stringify(this.preferences));
      } catch (e) {
        console.warn('Could not save accessibility preferences to storage');
      }
    },

    // Apply preferences to the document
    applyPreferences() {
      const p = this.preferences;
      const html = document.documentElement;
      const body = document.body;

      // Apply font size
      this.applyFontSize(p.fontSize, p.customFontSizePx);

      // Apply colour theme
      this.applyColourTheme(p.colourTheme);

      // Apply high contrast
      if (p.highContrast) {
        html.classList.add('high-contrast');
        body.classList.add('high-contrast');
      } else {
        html.classList.remove('high-contrast');
        body.classList.remove('high-contrast');
      }

      // Apply reduced motion
      if (p.reducedMotion) {
        html.classList.add('reduced-motion');
      } else {
        html.classList.remove('reduced-motion');
      }

      // Apply enhanced focus
      if (p.enhancedFocus) {
        html.classList.add('enhanced-focus');
      } else {
        html.classList.remove('enhanced-focus');
      }

      // Apply keyboard navigation enhancements
      if (p.keyboardNavigationEnhanced) {
        html.classList.add('kbd-enhanced');
      } else {
        html.classList.remove('kbd-enhanced');
      }

      // Apply screen reader optimizations
      if (p.screenReaderOptimized) {
        html.classList.add('sr-optimized');
      } else {
        html.classList.remove('sr-optimized');
      }

      // Apply reading enhancements
      if (p.readingLineHeight !== 1.5) {
        html.style.setProperty('--accessibility-line-height', p.readingLineHeight);
      }
      if (p.readingLetterSpacing !== 0) {
        html.style.setProperty('--accessibility-letter-spacing', `${p.readingLetterSpacing}em`);
      }
      if (p.readingWordSpacing !== 0) {
        html.style.setProperty('--accessibility-word-spacing', `${p.readingWordSpacing}em`);
      }
    },

    // Apply font size
    applyFontSize(size, customPx) {
      const html = document.documentElement;
      html.classList.remove('font-size-small', 'font-size-medium', 'font-size-large', 'font-size-xlarge');

      switch (size) {
        case 'SMALL':
          html.classList.add('font-size-small');
          break;
        case 'MEDIUM':
          html.classList.add('font-size-medium');
          break;
        case 'LARGE':
          html.classList.add('font-size-large');
          break;
        case 'EXTRA_LARGE':
          html.classList.add('font-size-xlarge');
          break;
        case 'CUSTOM':
          if (customPx) {
            html.style.fontSize = `${customPx}px`;
          }
          break;
      }
    },

    // Apply colour theme
    applyColourTheme(theme) {
      const html = document.documentElement;
      html.classList.remove('theme-light', 'theme-dark', 'theme-high-contrast-light', 'theme-high-contrast-dark', 'theme-sepia', 'theme-custom');

      switch (theme) {
        case 'LIGHT':
          html.classList.add('theme-light');
          break;
        case 'DARK':
          html.classList.add('theme-dark');
          break;
        case 'HIGH_CONTRAST_LIGHT':
          html.classList.add('theme-high-contrast-light');
          break;
        case 'HIGH_CONTRAST_DARK':
          html.classList.add('theme-high-contrast-dark');
          break;
        case 'SEPIA':
          html.classList.add('theme-sepia');
          break;
        case 'CUSTOM':
          html.classList.add('theme-custom');
          break;
        case 'SYSTEM':
        default:
          // Use system preference
          if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            html.classList.add('theme-dark');
          } else {
            html.classList.add('theme-light');
          }
          break;
      }
    },

    // Update a single preference
    async updatePreference(key, value) {
      this.preferences[key] = value;
      this.applyPreferences();
      this.saveToStorage();

      // Sync with server if enabled
      if (this.preferences.syncAcrossDevices) {
        try {
          await fetch('/accessibility/api/preferences/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ [key]: value })
          });
        } catch (e) {
          console.warn('Could not sync preference to server');
        }
      }
    },

    // Get CSRF token
    getCsrfToken() {
      const token = document.querySelector('[name=csrfmiddlewaretoken]');
      return token ? token.value : '';
    },

    // Bind UI events
    bindEvents() {
      // Font size selector
      document.querySelectorAll('[data-accessibility-font-size]').forEach(el => {
        el.addEventListener('change', (e) => {
          this.updatePreference('fontSize', e.target.value);
          if (e.target.value === 'CUSTOM') {
            // Show custom input
            document.querySelectorAll('[data-accessibility-custom-font-size]').forEach(input => {
              input.style.display = 'block';
            });
          } else {
            document.querySelectorAll('[data-accessibility-custom-font-size]').forEach(input => {
              input.style.display = 'none';
            });
          }
        });
      });

      // Custom font size input
      document.querySelectorAll('[data-accessibility-custom-font-size]').forEach(input => {
        input.addEventListener('change', (e) => {
          this.updatePreference('customFontSizePx', parseInt(e.target.value, 10));
        });
      });

      // Colour theme selector
      document.querySelectorAll('[data-accessibility-colour-theme]').forEach(el => {
        el.addEventListener('change', (e) => {
          this.updatePreference('colourTheme', e.target.value);
        });
      });

      // Toggle switches
      const toggles = {
        highContrast: '[data-accessibility-high-contrast]',
        reducedMotion: '[data-accessibility-reduced-motion]',
        enhancedFocus: '[data-accessibility-enhanced-focus]',
        keyboardNavigationEnhanced: '[data-accessibility-keyboard-nav]',
        screenReaderOptimized: '[data-accessibility-screen-reader]',
        syncAcrossDevices: '[data-accessibility-sync]'
      };

      Object.entries(toggles).forEach(([key, selector]) => {
        document.querySelectorAll(selector).forEach(el => {
          el.addEventListener('change', (e) => {
            this.updatePreference(key, e.target.checked);
          });
        });
      });

      // Notification timing
      document.querySelectorAll('[data-accessibility-notification-timing]').forEach(el => {
        el.addEventListener('change', (e) => {
          this.updatePreference('notificationTiming', e.target.value);
        });
      });

      // Language selector
      document.querySelectorAll('[data-accessibility-language]').forEach(el => {
        el.addEventListener('change', (e) => {
          this.updatePreference('preferredLanguage', e.target.value);
        });
      });

      // Reading enhancements
      document.querySelectorAll('[data-accessibility-line-height]').forEach(input => {
        input.addEventListener('change', (e) => {
          this.updatePreference('readingLineHeight', parseFloat(e.target.value));
        });
      });

      document.querySelectorAll('[data-accessibility-letter-spacing]').forEach(input => {
        input.addEventListener('change', (e) => {
          this.updatePreference('readingLetterSpacing', parseFloat(e.target.value));
        });
      });

      document.querySelectorAll('[data-accessibility-word-spacing]').forEach(input => {
        input.addEventListener('change', (e) => {
          this.updatePreference('readingWordSpacing', parseFloat(e.target.value));
        });
      });
    }
  };

  // ─────────────────────────────────────────────────────────────────────────────
  // Skip Link Handler
  // ─────────────────────────────────────────────────────────────────────────────

  function initSkipLinks() {
    const skipLinks = document.querySelectorAll('.skip-link');
    skipLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('href');
        if (targetId && targetId.startsWith('#')) {
          const target = document.querySelector(targetId);
          if (target) {
            e.preventDefault();
            target.focus();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      });
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Focus Management
  // ─────────────────────────────────────────────────────────────────────────────

  function initFocusManagement() {
    // Trap focus in modals
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        const modal = document.querySelector('.modal.show');
        if (modal) {
          const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    });

    // Restore focus when modal closes
    document.querySelectorAll('.modal').forEach(modal => {
      let lastFocusedElement = null;

      modal.addEventListener('show.bs.modal', () => {
        lastFocusedElement = document.activeElement;
      });

      modal.addEventListener('hidden.bs.modal', () => {
        if (lastFocusedElement) {
          lastFocusedElement.focus();
        }
      });
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Colour Contrast Checker
  // ─────────────────────────────────────────────────────────────────────────────

  function initContrastChecker() {
    const contrastForms = document.querySelectorAll('[data-contrast-check]');
    contrastForms.forEach(form => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fg = form.querySelector('[name="foreground"]').value;
        const bg = form.querySelector('[name="background"]').value;

        try {
          const response = await fetch('/accessibility/api/contrast-check/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            },
            body: JSON.stringify({ foreground: fg, background: bg })
          });

          const data = await response.json();
          displayContrastResult(form, data);
        } catch (err) {
          console.error('Contrast check failed:', err);
        }
      });
    });
  }

  function displayContrastResult(form, data) {
    const resultContainer = form.querySelector('[data-contrast-result]');
    if (!resultContainer) return;

    const passesAA = data.passes_aa_normal || data.passes_aa_large;
    const passesAAA = data.passes_aaa_normal || data.passes_aaa_large;

    resultContainer.innerHTML = `
      <div class="alert alert-${passesAA ? 'success' : 'danger'} mb-2">
        <strong>Ratio:</strong> ${data.ratio}:1
      </div>
      <div class="row g-2">
        <div class="col-6">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" ${data.passes_aa_normal ? 'checked' : ''} disabled>
            <label class="form-check-label small">
              WCAG AA Normal (4.5:1) - ${data.passes_aa_normal ? 'Pass' : 'Fail'}
            </label>
          </div>
        </div>
        <div class="col-6">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" ${data.passes_aa_large ? 'checked' : ''} disabled>
            <label class="form-check-label small">
              WCAG AA Large (3:1) - ${data.passes_aa_large ? 'Pass' : 'Fail'}
            </label>
          </div>
        </div>
        <div class="col-6">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" ${data.passes_aaa_normal ? 'checked' : ''} disabled>
            <label class="form-check-label small">
              WCAG AAA Normal (7:1) - ${data.passes_aaa_normal ? 'Pass' : 'Fail'}
            </label>
          </div>
        </div>
        <div class="col-6">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" ${data.passes_aaa_large ? 'checked' : ''} disabled>
            <label class="form-check-label small">
              WCAG AAA Large (4.5:1) - ${data.passes_aaa_large ? 'Pass' : 'Fail'}
            </label>
          </div>
        </div>
      </div>
    `;
    resultContainer.style.display = 'block';
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Notification Timing
  // ─────────────────────────────────────────────────────────────────────────────

  function initNotificationTiming() {
    // Override Bootstrap toast delay based on user preference
    const timing = localStorage.getItem('accessibility_notification_timing') || 'DELAYED_5S';
    const delays = {
      'IMMEDIATE': 0,
      'DELAYED_3S': 3000,
      'DELAYED_5S': 5000,
      'DELAYED_10S': 10000,
      'PERSISTENT': 0 // Will be handled by not auto-hiding
    };

    // Apply to all toasts
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('.toast').forEach(toast => {
        const bsToast = new bootstrap.Toast(toast, {
          delay: delays[timing] || 5000,
          autohide: timing !== 'PERSISTENT'
        });
        bsToast.show();
      });
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Language Support
  // ─────────────────────────────────────────────────────────────────────────────

  function initLanguageSupport() {
    const lang = localStorage.getItem('accessibility_preferred_language') || 'en';
    document.documentElement.lang = lang;

    // Update any elements with data-i18n attributes
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      // In a real app, you'd have a translation map
      // For now, we just set the lang attribute
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Initialize All
  // ─────────────────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    AccessibilityPreferences.init();
    initSkipLinks();
    initFocusManagement();
    initContrastChecker();
    initNotificationTiming();
    initLanguageSupport();

    // Listen for system preference changes
    if (window.matchMedia) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
      darkModeQuery.addEventListener('change', () => {
        const prefs = JSON.parse(localStorage.getItem('accessibility_preferences') || '{}');
        if (prefs.colourTheme === 'SYSTEM') {
          AccessibilityPreferences.applyColourTheme('SYSTEM');
        }
      });

      const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      reducedMotionQuery.addEventListener('change', () => {
        const prefs = JSON.parse(localStorage.getItem('accessibility_preferences') || '{}');
        if (!prefs.reducedMotion && reducedMotionQuery.matches) {
          // System prefers reduced motion but user hasn't explicitly set it
          // Could show a prompt here
        }
      });

      const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
      highContrastQuery.addEventListener('change', () => {
        // Could auto-enable high contrast mode
      });
    });
  });

  // Expose for global access
  window.AccessibilityPreferences = AccessibilityPreferences;
})();