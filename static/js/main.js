/**
 * TestLearn - Main JavaScript File
 * Interactive features for the learning platform
 */

// ====== DOM Ready ======
document.addEventListener('DOMContentLoaded', function() {
    console.log('TestLearn initialized');
    
    // Initialize all components
    initMobileMenu();
    initQuizInteractions();
    initSearchFilters();
    initFormValidation();
    initAnimations();
});

// ====== Mobile Menu ======
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
}

// ====== Quiz Interactions ======
function initQuizInteractions() {
    const quizForm = document.querySelector('.quiz-form');
    const questionCards = document.querySelectorAll('.question-card');
    
    if (!quizForm) return;
    
    // Track answered questions
    questionCards.forEach(card => {
        const radioButtons = card.querySelectorAll('input[type="radio"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                card.classList.add('answered');
                // Highlight selected option
                card.querySelectorAll('.option-label').forEach(label => {
                    label.classList.remove('selected');
                });
                if (this.checked) {
                    this.closest('.option-label').classList.add('selected');
                }
            });
        });
    });
    
    // Confirm submission
    quizForm.addEventListener('submit', function(e) {
        const answeredCount = document.querySelectorAll('.question-card.answered').length;
        const totalCount = questionCards.length;
        
        if (answeredCount < totalCount) {
            const confirmed = confirm(
                `Вы ответили на ${answeredCount} из ${totalCount} вопросов.\n` +
                'Вы уверены, что хотите завершить тест?'
            );
            if (!confirmed) {
                e.preventDefault();
            }
        }
    });
}

// ====== Search & Filters ======
function initSearchFilters() {
    const searchInput = document.querySelector('.search-input');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const glossaryItems = document.querySelectorAll('.glossary-item');
    
    // Live search for glossary
    if (searchInput && glossaryItems.length > 0) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            glossaryItems.forEach(item => {
                const term = item.querySelector('.term')?.textContent.toLowerCase() || '';
                const definition = item.querySelector('.definition')?.textContent.toLowerCase() || '';
                
                if (term.includes(query) || definition.includes(query)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Filter buttons
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Apply filter
            if (filter === 'all') {
                document.querySelectorAll('.filterable-item').forEach(item => {
                    item.style.display = '';
                });
            } else {
                document.querySelectorAll('.filterable-item').forEach(item => {
                    if (item.dataset.category === filter) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
        });
    });
}

// ====== Form Validation ======
function initFormValidation() {
    const forms = document.querySelectorAll('.validated-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('invalid')) {
                    validateField(this);
                }
            });
        });
        
        form.addEventListener('submit', function(e) {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let errorMessage = '';
    
    // Required check
    if (field.required && !value) {
        isValid = false;
        errorMessage = 'Это поле обязательно';
    }
    // Email check
    else if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Введите корректный email';
        }
    }
    // Password check
    else if (type === 'password' && value) {
        if (value.length < 8) {
            isValid = false;
            errorMessage = 'Пароль должен содержать минимум 8 символов';
        } else if (!/[A-Z]/.test(value)) {
            isValid = false;
            errorMessage = 'Пароль должен содержать заглавную букву';
        } else if (!/[0-9]/.test(value)) {
            isValid = false;
            errorMessage = 'Пароль должен содержать цифру';
        }
    }
    // Username check
    else if (field.name === 'username' && value) {
        const usernameRegex = /^[a-zA-Z0-9_]{3,32}$/;
        if (!usernameRegex.test(value)) {
            isValid = false;
            errorMessage = 'Имя должно содержать 3-32 символа (буквы, цифры, _)';
        }
    }
    
    // Update UI
    const errorElement = field.parentElement.querySelector('.field-error');
    
    if (!isValid) {
        field.classList.add('invalid');
        field.classList.remove('valid');
        if (errorElement) {
            errorElement.textContent = errorMessage;
            errorElement.style.display = 'block';
        }
    } else {
        field.classList.remove('invalid');
        if (value) {
            field.classList.add('valid');
        } else {
            field.classList.remove('valid');
        }
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }
    
    return isValid;
}

// ====== Animations ======
function initAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });
    
    // Counter animation for stats
    animateCounters();
}

function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.dataset.target) || 0;
        const duration = 2000; // ms
        const step = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        // Start animation when visible
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// ====== Utility Functions ======
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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Export for use in other scripts
window.TestLearn = {
    validateField,
    formatDate,
    debounce
};
