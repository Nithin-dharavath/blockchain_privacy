// ===================================
// PRIVACY PLATFORM - ENHANCED JS
// Advanced Animations & Interactions
// ===================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize all features
    initAnimations();
    initNavigation();
    initForms();
    initCharts();
    initNotifications();
    initLoadingStates();
    initParticles();
    
    console.log('🚀 Privacy Platform initialized with advanced animations');
});

// ===================================
// ANIMATIONS
// ===================================

function initAnimations() {
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add('animate-slide-in');
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards and stat boxes
    document.querySelectorAll('.card, .stat-card, .metric-box, .technique-card').forEach(el => {
        observer.observe(el);
    });
    
    // Stagger animation for table rows
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach((row, index) => {
        row.style.animation = `slide-in-up 0.5s ease-out ${index * 0.05}s both`;
    });
}

// ===================================
// NAVIGATION
// ===================================

function initNavigation() {
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Add shadow on scroll
        if (currentScroll > 50) {
            navbar.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.5)';
            navbar.style.backdropFilter = 'blur(30px)';
        } else {
            navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.3)';
            navbar.style.backdropFilter = 'blur(20px)';
        }
        
        lastScroll = currentScroll;
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ===================================
// FORMS
// ===================================

function initForms() {
    // Add floating label effect
    const inputs = document.querySelectorAll('.form-control, .form-select');
    
    inputs.forEach(input => {
        // Focus effect
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Validation styling
        input.addEventListener('invalid', function(e) {
            e.preventDefault();
            this.classList.add('is-invalid');
            
            // Create error message if doesn't exist
            if (!this.nextElementSibling || !this.nextElementSibling.classList.contains('invalid-feedback')) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'invalid-feedback';
                errorMsg.style.display = 'block';
                errorMsg.textContent = this.validationMessage;
                this.parentNode.appendChild(errorMsg);
            }
        });
        
        input.addEventListener('input', function() {
            if (this.validity.valid) {
                this.classList.remove('is-invalid');
                const errorMsg = this.parentNode.querySelector('.invalid-feedback');
                if (errorMsg) errorMsg.remove();
            }
        });
    });
    
    // Form submission with loading state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise animate-spin"></i> Processing...';
                
                // Re-enable after 5 seconds (fallback)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });
}

// ===================================
// CHARTS & VISUALIZATIONS
// ===================================

function initCharts() {
    // Animate progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    
    const animateProgressBar = (bar) => {
        const targetWidth = bar.getAttribute('style').match(/width:\s*([0-9.]+)%/);
        if (targetWidth) {
            const width = parseFloat(targetWidth[1]);
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.transition = 'width 1.5s cubic-bezier(0.65, 0, 0.35, 1)';
                bar.style.width = `${width}%`;
            }, 100);
        }
    };
    
    const progressObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateProgressBar(entry.target);
                progressObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    progressBars.forEach(bar => progressObserver.observe(bar));
    
    // Animate stat values (counting up)
    const statValues = document.querySelectorAll('.stat-value');
    
    const animateValue = (element) => {
        const target = parseFloat(element.textContent);
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target.toFixed(2);
                clearInterval(timer);
            } else {
                element.textContent = current.toFixed(2);
            }
        }, 16);
    };
    
    const statObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateValue(entry.target);
                statObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    statValues.forEach(stat => statObserver.observe(stat));
}

// ===================================
// NOTIFICATIONS
// ===================================

function initNotifications() {
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Add close button if doesn't exist
        if (!alert.querySelector('.btn-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'btn-close btn-close-white';
            closeBtn.setAttribute('data-bs-dismiss', 'alert');
            alert.appendChild(closeBtn);
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slide-in-right 0.5s ease-out reverse';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

// ===================================
// LOADING STATES
// ===================================

function initLoadingStates() {
    // Show loading spinner on page navigation
    const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!this.getAttribute('download')) {
                showLoadingOverlay();
            }
        });
    });
}

function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = `
        <div class="spinner-border text-primary spinner-border-custom animate-glow" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(overlay);
}

// ===================================
// PARTICLES BACKGROUND
// ===================================

function initParticles() {
    const canvas = document.createElement('canvas');
    canvas.id = 'particles-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.opacity = '0.3';
    document.body.insertBefore(canvas, document.body.firstChild);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = 50;
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2 + 1;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        
        draw() {
            ctx.fillStyle = `rgba(139, 92, 246, ${Math.random() * 0.5 + 0.3})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        // Draw connections
        particles.forEach((p1, i) => {
            particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 150) {
                    ctx.strokeStyle = `rgba(139, 92, 246, ${0.2 * (1 - distance / 150)})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slide-in-right 0.5s ease-out reverse';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Format numbers
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}
