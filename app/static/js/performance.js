/**
 * Frontend Performance Optimizations for GrantThrive
 */

// Lazy loading for images
document.addEventListener('DOMContentLoaded', function() {
    // Image lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Form auto-save functionality
    initAutoSave();
    
    // Debounced search
    initDebouncedSearch();
    
    // Performance monitoring
    initPerformanceMonitoring();
});

// Auto-save for forms
function initAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const saveKey = `autosave_${form.id || 'form'}`;
        
        // Load saved data
        const savedData = localStorage.getItem(saveKey);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(name => {
                    const input = form.querySelector(`[name="${name}"]`);
                    if (input && input.type !== 'password') {
                        input.value = data[name];
                    }
                });
            } catch (e) {
                console.warn('Failed to load auto-saved data:', e);
            }
        }
        
        // Save data on input
        const saveData = debounce(() => {
            const data = {};
            inputs.forEach(input => {
                if (input.name && input.type !== 'password') {
                    data[input.name] = input.value;
                }
            });
            localStorage.setItem(saveKey, JSON.stringify(data));
        }, 1000);
        
        inputs.forEach(input => {
            input.addEventListener('input', saveData);
        });
        
        // Clear saved data on successful submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(saveKey);
        });
    });
}

// Debounced search functionality
function initDebouncedSearch() {
    const searchInputs = document.querySelectorAll('input[data-search]');
    
    searchInputs.forEach(input => {
        const searchUrl = input.dataset.search;
        const resultsContainer = document.querySelector(input.dataset.results);
        
        if (!searchUrl || !resultsContainer) return;
        
        const debouncedSearch = debounce(async (query) => {
            if (query.length < 2) {
                resultsContainer.innerHTML = '';
                return;
            }
            
            try {
                const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
                const results = await response.json();
                
                if (results.success) {
                    renderSearchResults(resultsContainer, results.data);
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300);
        
        input.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    });
}

// Performance monitoring
function initPerformanceMonitoring() {
    // Monitor page load performance
    window.addEventListener('load', () => {
        if ('performance' in window) {
            const perfData = performance.getEntriesByType('navigation')[0];
            const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
            
            if (loadTime > 3000) { // Log slow page loads (>3s)
                console.warn(`Slow page load: ${loadTime}ms`);
                // Could send to analytics service
            }
        }
    });
    
    // Monitor AJAX performance
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const start = performance.now();
        return originalFetch.apply(this, args).then(response => {
            const duration = performance.now() - start;
            if (duration > 2000) { // Log slow requests (>2s)
                console.warn(`Slow request: ${duration}ms - ${args[0]}`);
            }
            return response;
        });
    };
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function renderSearchResults(container, results) {
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="no-results">No results found</div>';
        return;
    }
    
    const html = results.map(item => `
        <div class="search-result">
            <h6><a href="${item.url}">${item.title}</a></h6>
            <p class="text-muted">${item.description}</p>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Cache management
const CacheManager = {
    set(key, data, ttl = 300000) { // 5 minutes default
        const item = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        };
        localStorage.setItem(`cache_${key}`, JSON.stringify(item));
    },
    
    get(key) {
        const item = localStorage.getItem(`cache_${key}`);
        if (!item) return null;
        
        try {
            const parsed = JSON.parse(item);
            if (Date.now() - parsed.timestamp > parsed.ttl) {
                localStorage.removeItem(`cache_${key}`);
                return null;
            }
            return parsed.data;
        } catch (e) {
            localStorage.removeItem(`cache_${key}`);
            return null;
        }
    },
    
    clear() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('cache_')) {
                localStorage.removeItem(key);
            }
        });
    }
};

// Export for use in other scripts
window.GrantThrivePerf = {
    debounce,
    CacheManager,
    renderSearchResults
};
