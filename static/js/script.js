// Simple interaction for the "Start preparing" link
document.querySelector('.btn-start').addEventListener('click', function(e) {
    e.preventDefault();
    alert("Let's begin your journey to the Gold medal!");
});

// Smooth scroll effect for the header
window.onscroll = function() {
    const header = document.querySelector(".navbar");
    if (window.pageYOffset > 50) {
        header.style.padding = "5px 50px";
        header.style.background = "rgba(26, 42, 108, 0.95)";
    } else {
        header.style.padding = "10px 50px";
        header.style.background = "#1a2a6c";
    }
};
document.getElementById('registerForm').addEventListener('submit', function(e) {
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm_password').value;
    const errorDiv = document.getElementById('error-message');

    // Simple frontend validation
    if (password !== confirm) {
        e.preventDefault(); // Stop form from submitting
        errorDiv.textContent = "Passwords do not match!";
        errorDiv.style.display = "block";
    } else if (password.length < 6) {
        e.preventDefault();
        errorDiv.textContent = "Password must be at least 6 characters.";
        errorDiv.style.display = "block";
    } else {
        errorDiv.style.display = "none";
    }
});