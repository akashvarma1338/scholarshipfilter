/**
 * Scholarship Eligibility Filter - Main JavaScript
 * Handles form submission and API interactions
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    init();
});

/**
 * Initialize the application
 */
function init() {
    // Load available scholarships
    loadScholarships();
    
    // Set up form submission handler
    const form = document.getElementById('applicationForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

/**
 * Load available scholarships for preview
 */
async function loadScholarships() {
    const container = document.getElementById('scholarshipsList');
    if (!container) return;
    
    try {
        const response = await fetch('/api/scholarships');
        const data = await response.json();
        
        if (data.success && data.scholarships.length > 0) {
            // Display scholarships
            container.innerHTML = data.scholarships
                .filter(s => s.is_active)
                .map(scholarship => `
                    <div class="scholarship-card">
                        <h4>${scholarship.name}</h4>
                        <div class="amount">₹${scholarship.amount.toLocaleString()}</div>
                        <p class="description">${scholarship.description || 'No description available'}</p>
                        <p class="rules-count">📋 ${scholarship.rules.length} eligibility rule(s)</p>
                    </div>
                `).join('');
        } else {
            container.innerHTML = `
                <div class="no-results">
                    <p>No scholarships available at the moment.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading scholarships:', error);
        container.innerHTML = `
            <div class="no-results">
                <p>⚠️ Error loading scholarships. Please refresh the page.</p>
            </div>
        `;
    }
}

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handleFormSubmit(event) {
    // Prevent default form submission
    event.preventDefault();
    
    // Get form elements
    const form = event.target;
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    submitBtn.disabled = true;
    
    try {
        // Collect form data
        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            course: document.getElementById('course').value,
            year_of_study: parseInt(document.getElementById('year_of_study').value),
            marks_percentage: parseFloat(document.getElementById('marks_percentage').value),
            family_income: parseFloat(document.getElementById('family_income').value),
            category: document.getElementById('category').value,
            has_backlogs: document.getElementById('has_backlogs').checked,
            is_full_time: document.getElementById('is_full_time').checked
        };
        
        // Validate form data
        const validationError = validateFormData(formData);
        if (validationError) {
            showAlert(validationError, 'error');
            resetButton();
            return;
        }
        
        // Submit to API
        const response = await fetch('/api/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to results page
            window.location.href = `/results/${data.student.id}`;
        } else {
            showAlert(data.error || 'Failed to submit application', 'error');
            resetButton();
        }
        
    } catch (error) {
        console.error('Error:', error);
        showAlert('An error occurred. Please try again.', 'error');
        resetButton();
    }
    
    // Helper function to reset button state
    function resetButton() {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        submitBtn.disabled = false;
    }
}

/**
 * Validate form data before submission
 * @param {Object} data - Form data object
 * @returns {string|null} - Error message or null if valid
 */
function validateFormData(data) {
    // Check required fields
    if (!data.name) return 'Please enter your name';
    if (!data.email) return 'Please enter your email';
    if (!data.course) return 'Please select your course';
    if (!data.year_of_study) return 'Please select your year of study';
    if (data.marks_percentage === undefined || data.marks_percentage === null) {
        return 'Please enter your marks percentage';
    }
    if (data.family_income === undefined || data.family_income === null) {
        return 'Please enter your family income';
    }
    if (!data.category) return 'Please select your category';
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        return 'Please enter a valid email address';
    }
    
    // Validate marks percentage (0-100)
    if (data.marks_percentage < 0 || data.marks_percentage > 100) {
        return 'Marks percentage must be between 0 and 100';
    }
    
    // Validate income (must be positive)
    if (data.family_income < 0) {
        return 'Family income cannot be negative';
    }
    
    return null; // No errors
}

/**
 * Show an alert message to the user
 * @param {string} message - Message to display
 * @param {string} type - Alert type ('error', 'success', 'info')
 */
function showAlert(message, type = 'info') {
    // Remove any existing alerts
    const existingAlert = document.querySelector('.alert-toast');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert-toast alert-${type}`;
    alert.innerHTML = `
        <span class="alert-icon">${type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <span class="alert-message">${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add styles for alert toast
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 20px;
        background: ${type === 'error' ? '#fee2e2' : type === 'success' ? '#d1fae5' : '#dbeafe'};
        color: ${type === 'error' ? '#dc2626' : type === 'success' ? '#059669' : '#2563eb'};
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    // Add animation keyframes if not exists
    if (!document.getElementById('alert-styles')) {
        const style = document.createElement('style');
        style.id = 'alert-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .alert-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                opacity: 0.7;
            }
            .alert-close:hover {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add to page
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Format currency in Indian Rupees
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted amount
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Format percentage
 * @param {number} value - Value to format
 * @returns {string} - Formatted percentage
 */
function formatPercentage(value) {
    return `${value.toFixed(2)}%`;
}
