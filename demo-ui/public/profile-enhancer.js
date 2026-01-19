/**
 * Yonca AI — Enhanced User Profile Dropdown
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * FREE Google OAuth Fields (no paid APIs needed):
 * ═══════════════════════════════════════════════════════════════════════════
 * - name, email, picture, given_name, family_name
 * - locale, email_verified, hosted_domain, google_id
 * 
 * Custom JS is the OFFICIAL Chainlit extension mechanism!
 * See: https://docs.chainlit.io/customisation/custom-js
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';
    
    const CONFIG = {
        checkInterval: 500,
        maxAttempts: 60,
        debug: true
    };
    
    const log = (...args) => CONFIG.debug && console.log('[Yonca Profile]', ...args);
    
    // Locale to flag mapping
    const FLAGS = {
        'az': '🇦🇿', 'en': '🇬🇧', 'en-US': '🇺🇸', 'ru': '🇷🇺', 
        'tr': '🇹🇷', 'de': '🇩🇪', 'fr': '🇫🇷'
    };
    
    /**
     * Inject styles for enhanced dropdown
     */
    function injectStyles() {
        if (document.getElementById('yonca-profile-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'yonca-profile-styles';
        style.textContent = `
            .yonca-profile-card {
                padding: 12px 16px;
                min-width: 240px;
            }
            .yonca-profile-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 8px;
            }
            .yonca-profile-avatar {
                width: 48px;
                height: 48px;
                border-radius: 50%;
                border: 2px solid #A8E6CF;
                object-fit: cover;
            }
            .yonca-profile-avatar-fallback {
                width: 48px;
                height: 48px;
                border-radius: 50%;
                background: linear-gradient(135deg, #2D5A27, #4CAF50);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                font-weight: 600;
            }
            .yonca-profile-info h3 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
            }
            .yonca-profile-info p {
                margin: 2px 0 0;
                font-size: 12px;
                color: #6B7280;
            }
            .yonca-profile-badges {
                display: flex;
                gap: 6px;
                margin-top: 8px;
                flex-wrap: wrap;
            }
            .yonca-badge {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
            }
            .yonca-badge-locale {
                background: linear-gradient(135deg, #A8E6CF, #D4EDDA);
                color: #1B4D1F;
            }
            .yonca-badge-domain {
                background: #E5E7EB;
                color: #374151;
            }
            .yonca-badge-verified {
                background: #D1FAE5;
                color: #065F46;
            }
            .yonca-divider {
                height: 1px;
                background: #E5E7EB;
                margin: 8px 0;
            }
        `;
        document.head.appendChild(style);
        log('Styles injected');
    }
    
    /**
     * Create enhanced profile card HTML
     */
    function createProfileCard(userData) {
        const { identifier, display_name, metadata = {} } = userData;
        
        const name = display_name || metadata.name || identifier;
        const email = metadata.email || identifier;
        const picture = metadata.image || metadata.picture;
        const locale = metadata.locale;
        const domain = metadata.hosted_domain;
        const verified = metadata.email_verified;
        
        log('Building card with:', { name, email, picture, locale, domain, verified });
        
        // Avatar HTML
        const avatarHtml = picture 
            ? `<img src="${picture}" alt="Profile" class="yonca-profile-avatar" referrerpolicy="no-referrer" />`
            : `<div class="yonca-profile-avatar-fallback">${(name || 'U')[0].toUpperCase()}</div>`;
        
        // Badges
        const badges = [];
        if (locale) {
            const flag = FLAGS[locale] || FLAGS[locale?.split('-')[0]] || '🌍';
            badges.push(`<span class="yonca-badge yonca-badge-locale">${flag} ${locale.toUpperCase()}</span>`);
        }
        if (domain) {
            badges.push(`<span class="yonca-badge yonca-badge-domain">🏢 ${domain}</span>`);
        }
        if (verified) {
            badges.push(`<span class="yonca-badge yonca-badge-verified">✓ Verified</span>`);
        }
        
        return `
            <div class="yonca-profile-card">
                <div class="yonca-profile-header">
                    ${avatarHtml}
                    <div class="yonca-profile-info">
                        <h3>${name}</h3>
                        <p>${email}</p>
                    </div>
                </div>
                ${badges.length ? `
                    <div class="yonca-profile-badges">
                        ${badges.join('')}
                    </div>
                ` : ''}
                <div class="yonca-divider"></div>
            </div>
        `;
    }
    
    /**
     * Fetch user data from Chainlit API
     */
    async function fetchUserData() {
        try {
            const response = await fetch('/user', { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                log('Fetched user data:', data);
                return data;
            }
        } catch (e) {
            log('Failed to fetch user data:', e);
        }
        return null;
    }
    
    /**
     * Enhance the dropdown menu when it opens
     */
    async function enhanceDropdown(menu) {
        if (menu.querySelector('.yonca-profile-card')) {
            log('Card already exists');
            return;
        }
        
        const userData = await fetchUserData();
        if (!userData) {
            log('No user data available');
            return;
        }
        
        const cardContainer = document.createElement('div');
        cardContainer.innerHTML = createProfileCard(userData);
        
        // Insert at top of dropdown
        const firstChild = menu.firstElementChild;
        if (firstChild) {
            menu.insertBefore(cardContainer.firstElementChild, firstChild);
        } else {
            menu.appendChild(cardContainer.firstElementChild);
        }
        
        log('Profile card inserted');
    }
    
    /**
     * Watch for dropdown menu to appear
     */
    function setupDropdownObserver() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Look for dropdown content (Radix UI pattern)
                        const dropdown = node.matches('[role="menu"]') 
                            ? node 
                            : node.querySelector?.('[role="menu"]');
                        
                        if (dropdown) {
                            log('Dropdown detected');
                            setTimeout(() => enhanceDropdown(dropdown), 50);
                        }
                    }
                }
            }
        });
        
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
        
        log('Dropdown observer active');
    }
    
    /**
     * Initialize
     */
    function init() {
        log('═══════════════════════════════════════════════');
        log('Yonca Profile Enhancement v2.0');
        log('Using FREE Google OAuth fields only');
        log('═══════════════════════════════════════════════');
        
        injectStyles();
        setupDropdownObserver();
        
        // Also enhance any existing dropdown
        const existingMenu = document.querySelector('[role="menu"]');
        if (existingMenu) {
            enhanceDropdown(existingMenu);
        }
    }
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
