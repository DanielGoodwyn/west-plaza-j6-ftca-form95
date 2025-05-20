// Theme toggle: ☀️ (day), 🌙 (night), ⚙️ (system)
(function() {
    const MODES = ['day', 'night', 'system'];
    const ICONS = { day: '☀️', night: '🌙', system: '⚙️' };
    const CSS = {
        day: '/west-plaza-lawsuit/static/css/day.css',
        night: '/west-plaza-lawsuit/static/css/night.css',
        system: '' // Will be set dynamically
    };
    const STORAGE_KEY = 'theme-mode';
    let mode = localStorage.getItem(STORAGE_KEY) || 'system';

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'day';
    }

    function applyTheme(theme) {
        // Remove any existing theme stylesheet
        let themeLink = document.getElementById('theme-css');
        if (themeLink) themeLink.remove();
        // Determine which theme to use
        let useTheme = theme;
        if (theme === 'system') useTheme = getSystemTheme();
        if (useTheme !== 'system') {
            const link = document.createElement('link');
            link.id = 'theme-css';
            link.rel = 'stylesheet';
            link.href = CSS[useTheme];
            document.head.appendChild(link);
        }
    }

    function setIcon(theme) {
        let el = document.getElementById('theme-toggle-btn');
        if (el) el.textContent = ICONS[theme];
    }

    function cycleMode() {
        let idx = MODES.indexOf(mode);
        mode = MODES[(idx + 1) % MODES.length];
        localStorage.setItem(STORAGE_KEY, mode);
        applyTheme(mode);
        setIcon(mode);
    }

    // Add the toggle button to the top right
    function injectToggleBtn() {
        if (document.getElementById('theme-toggle-btn')) return;
        const btn = document.createElement('button');
        btn.id = 'theme-toggle-btn';
        btn.type = 'button';
        btn.style.position = 'fixed';
        btn.style.top = '18px';
        btn.style.right = '24px';
        btn.style.zIndex = '1000';
        btn.style.background = 'none';
        btn.style.border = 'none';
        btn.style.fontSize = '2rem';
        btn.style.cursor = 'pointer';
        btn.style.lineHeight = '1';
        btn.setAttribute('aria-label', 'Toggle theme');
        btn.addEventListener('click', cycleMode);
        document.body.appendChild(btn);
        setIcon(mode);
    }

    // Respond to system theme changes if in system mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        if (mode === 'system') applyTheme('system');
    });

    // Init
    document.addEventListener('DOMContentLoaded', function() {
        injectToggleBtn();
        applyTheme(mode);
        setIcon(mode);
    });
})();
