// Smooth interactions and validations
document.addEventListener('DOMContentLoaded', function() {
    
    // Password validation for registration form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password')?.value;
            const confirm = document.getElementById('confirm_password')?.value;
            const errorDiv = document.getElementById('error-message');

            if (password !== confirm) {
                e.preventDefault();
                errorDiv.textContent = "❌ Пароли не совпадают!";
                errorDiv.style.display = "block";
            } else if (password && password.length < 8) {
                e.preventDefault();
                errorDiv.textContent = "❌ Пароль должен быть не менее 8 символов.";
                errorDiv.style.display = "block";
            } else {
                errorDiv.style.display = "none";
            }
        });
    }
    
    // Smooth scroll effect for header on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.pageYOffset > 50) {
                navbar.style.boxShadow = "0 12px 40px rgba(0,0,0,0.2)";
            } else {
                navbar.style.boxShadow = "0 8px 32px rgba(0,0,0,0.15)";
            }
        }
    });
    
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Fade in animations for cards
    const cards = document.querySelectorAll('.dashboard-card, .task-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.animation = `slideUp 0.5s ease ${index * 0.1}s forwards`;
    });
    
    // Input focus effects
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'scale(1.01)';
        });
        input.addEventListener('blur', function() {
            this.style.transform = 'scale(1)';
        });
    });
});

// Add CSS animation keyframes dynamically if not already defined
if (!document.querySelector('style[data-animations]')) {
    const style = document.createElement('style');
    style.setAttribute('data-animations', 'true');
    style.textContent = `
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Navbar scroll indicator
function handleNavScroll() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'linear-gradient(135deg, rgba(26, 42, 108, 0.95) 0%, rgba(45, 62, 159, 0.95) 100%)';
    } else {
        navbar.style.background = 'linear-gradient(135deg, #1a2a6c 0%, #2d3e9f 100%)';
    }
}

window.addEventListener('scroll', handleNavScroll, { passive: true });