/**
 * Theme Switcher - Google Developer Standards
 * Handles theme switching, persistence, and system preference detection
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = 'light';
        this.systemPreference = this.getSystemPreference();
        this.init();
    }

    init() {
        // Load theme from localStorage or user preferences
        this.loadTheme();
        
        // Listen for system theme changes
        this.watchSystemPreference();
        
        // Apply other preferences
        this.applyAllPreferences();
    }

    /**
     * Load theme from localStorage, then server preferences
     */
    loadTheme() {
        // First check localStorage for immediate loading
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            // Fetch from server preferences
            this.fetchUserPreferences();
        }
    }

    /**
     * Fetch user preferences from server
     */
    async fetchUserPreferences() {
        try {
            const response = await fetch('/api/preferences/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Accept': 'application/json'
                }
            });

            // Check if response is JSON before parsing
            const contentType = response.headers.get('content-type');
            if (response.ok && contentType && contentType.includes('application/json')) {
                const data = await response.json();
                if (data.success && data.preferences) {
                    const prefs = data.preferences;

                    // Apply theme
                    this.setTheme(prefs.theme || 'light');

                    // Apply other visual preferences
                    this.applyPreferences(prefs);
                }
            } else {
                // API endpoint doesn't exist or returns HTML - use fallback
                this.setTheme('light');
            }
        } catch (error) {
            // Silently fall back to light theme - API might not be implemented yet
            this.setTheme('light');
        }
    }

    /**
     * Apply all user preferences
     */
    applyPreferences(prefs) {
        // Font size
        if (prefs.font_size) {
            document.documentElement.setAttribute('data-font-size', prefs.font_size);
            localStorage.setItem('font-size', prefs.font_size);
        }

        // High contrast
        if (prefs.high_contrast !== undefined) {
            document.documentElement.setAttribute('data-high-contrast', prefs.high_contrast);
            localStorage.setItem('high-contrast', prefs.high_contrast);
        }

        // Reduce animations
        if (prefs.reduce_animations !== undefined) {
            document.documentElement.setAttribute('data-reduce-animations', prefs.reduce_animations);
            localStorage.setItem('reduce-animations', prefs.reduce_animations);
        }
    }

    /**
     * Apply all preferences from localStorage on page load
     */
    applyAllPreferences() {
        // Font size
        const fontSize = localStorage.getItem('font-size');
        if (fontSize) {
            document.documentElement.setAttribute('data-font-size', fontSize);
        }

        // High contrast
        const highContrast = localStorage.getItem('high-contrast');
        if (highContrast) {
            document.documentElement.setAttribute('data-high-contrast', highContrast);
        }

        // Reduce animations
        const reduceAnimations = localStorage.getItem('reduce-animations');
        if (reduceAnimations) {
            document.documentElement.setAttribute('data-reduce-animations', reduceAnimations);
        }
    }

    /**
     * Set the theme
     */
    setTheme(theme) {
        this.currentTheme = theme;
        
        if (theme === 'auto') {
            // Use system preference
            const effectiveTheme = this.systemPreference;
            document.documentElement.setAttribute('data-theme', effectiveTheme);
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        // Save to localStorage for instant loading on next visit
        localStorage.setItem('theme', theme);
        
        // Update theme toggle buttons if they exist
        this.updateThemeButtons(theme);
    }

    /**
     * Get system color scheme preference
     */
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Watch for system theme changes
     */
    watchSystemPreference() {
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                this.systemPreference = e.matches ? 'dark' : 'light';
                
                // If current theme is auto, update immediately
                if (this.currentTheme === 'auto') {
                    this.setTheme('auto');
                }
            });
        }
    }

    /**
     * Update theme toggle buttons UI
     */
    updateThemeButtons(theme) {
        // Update radio buttons if they exist
        const themeRadios = document.querySelectorAll('input[name="theme"]');
        themeRadios.forEach(radio => {
            radio.checked = radio.value === theme;
        });

        // Update select dropdown if it exists
        const themeSelect = document.getElementById('theme-select');
        if (themeSelect) {
            themeSelect.value = theme;
        }
    }

    /**
     * Toggle between light and dark themes
     */
    toggle() {
        const currentEffectiveTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentEffectiveTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Save to server
        this.saveThemePreference(newTheme);
    }

    /**
     * Save theme preference to server
     */
    async saveThemePreference(theme) {
        try {
            const formData = new FormData();
            formData.append('theme', theme);

            const response = await fetch('/users/api/update-system-settings/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData
            });

            if (!response.ok) {
                console.error('Failed to save theme preference');
            }
        } catch (error) {
            console.error('Error saving theme preference:', error);
        }
    }

    /**
     * Get CSRF token from cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Apply font size setting
     */
    setFontSize(size) {
        document.documentElement.setAttribute('data-font-size', size);
        localStorage.setItem('font-size', size);
    }

    /**
     * Apply high contrast setting
     */
    setHighContrast(enabled) {
        document.documentElement.setAttribute('data-high-contrast', enabled);
        localStorage.setItem('high-contrast', enabled);
    }

    /**
     * Apply reduce animations setting
     */
    setReduceAnimations(enabled) {
        document.documentElement.setAttribute('data-reduce-animations', enabled);
        localStorage.setItem('reduce-animations', enabled);
    }
}

// Initialize theme switcher when DOM is ready
let themeSwitcher;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeSwitcher = new ThemeSwitcher();
    });
} else {
    themeSwitcher = new ThemeSwitcher();
}

// Export for use in other scripts
window.ThemeSwitcher = ThemeSwitcher;
window.themeSwitcher = themeSwitcher;