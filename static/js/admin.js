/**
 * Scholarship Eligibility Filter - Admin Panel JavaScript
 * Handles scholarship and rule management
 */

// Global variables to store data
let scholarshipsData = [];
let currentScholarshipFilter = '';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadScholarships();
    setupFormHandlers();
});

/**
 * Load all scholarships with their rules
 */
async function loadScholarships() {
    try {
        const response = await fetch('/api/scholarships');
        const data = await response.json();
        
        if (data.success) {
            scholarshipsData = data.scholarships;
            displayScholarships(scholarshipsData);
            populateScholarshipDropdowns();
            displayRules();
        }
    } catch (error) {
        console.error('Error loading scholarships:', error);
        showNotification('Error loading scholarships', 'error');
    }
}

/**
 * Display scholarships in the list
 */
function displayScholarships(scholarships) {
    const container = document.getElementById('scholarshipsList');
    
    if (scholarships.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <p>No scholarships found. Create your first scholarship!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = scholarships.map(scholarship => `
        <div class="admin-item" data-id="${scholarship.id}">
            <div class="admin-item-header">
                <div>
                    <h4>${scholarship.name}</h4>
                    <span class="status-badge ${scholarship.is_active ? 'eligible-badge' : 'not-eligible-badge'}">
                        ${scholarship.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div class="admin-item-actions">
                    <button class="btn btn-small btn-secondary" onclick="editScholarship(${scholarship.id})">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-small btn-danger" onclick="deleteScholarship(${scholarship.id})">
                        🗑️ Delete
                    </button>
                </div>
            </div>
            <div class="admin-item-details">
                <p><strong>Amount:</strong> ₹${scholarship.amount.toLocaleString()}</p>
                <p><strong>Description:</strong> ${scholarship.description || 'No description'}</p>
            </div>
            <div class="rules-list">
                <h5>📏 Eligibility Rules (${scholarship.rules.length})</h5>
                ${scholarship.rules.length > 0 ? scholarship.rules.map(rule => `
                    <div class="rule-item">
                        <div class="rule-details">
                            <span class="rule-code">${rule.field} ${rule.operator} ${rule.value}</span>
                            <span> - ${rule.description || 'No description'}</span>
                        </div>
                        <div class="rule-actions">
                            <button class="btn btn-small btn-secondary" onclick="editRule(${rule.id})">✏️</button>
                            <button class="btn btn-small btn-danger" onclick="deleteRule(${rule.id})">🗑️</button>
                        </div>
                    </div>
                `).join('') : '<p class="no-data">No rules defined. Add rules to enable eligibility checking.</p>'}
            </div>
        </div>
    `).join('');
}

/**
 * Populate scholarship dropdowns in forms
 */
function populateScholarshipDropdowns() {
    const dropdowns = [
        document.getElementById('scholarshipFilter'),
        document.getElementById('ruleScholarship')
    ];
    
    dropdowns.forEach(dropdown => {
        if (!dropdown) return;
        
        // Keep the first option (placeholder)
        const firstOption = dropdown.options[0];
        dropdown.innerHTML = '';
        dropdown.appendChild(firstOption);
        
        // Add scholarship options
        scholarshipsData.forEach(scholarship => {
            const option = document.createElement('option');
            option.value = scholarship.id;
            option.textContent = scholarship.name;
            dropdown.appendChild(option);
        });
    });
}

/**
 * Display rules (optionally filtered by scholarship)
 */
function displayRules() {
    const container = document.getElementById('rulesList');
    
    // Collect all rules from all scholarships
    let allRules = [];
    scholarshipsData.forEach(scholarship => {
        scholarship.rules.forEach(rule => {
            allRules.push({
                ...rule,
                scholarshipName: scholarship.name
            });
        });
    });
    
    // Apply filter if set
    if (currentScholarshipFilter) {
        allRules = allRules.filter(rule => 
            rule.scholarship_id == currentScholarshipFilter
        );
    }
    
    if (allRules.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <p>No rules found. Add rules to scholarships to enable eligibility checking.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = allRules.map(rule => `
        <div class="admin-item" data-id="${rule.id}">
            <div class="admin-item-header">
                <div>
                    <h4>${rule.scholarshipName}</h4>
                    <span class="rule-code">${rule.field} ${rule.operator} ${rule.value}</span>
                </div>
                <div class="admin-item-actions">
                    <button class="btn btn-small btn-secondary" onclick="editRule(${rule.id})">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-small btn-danger" onclick="deleteRule(${rule.id})">
                        🗑️ Delete
                    </button>
                </div>
            </div>
            <div class="admin-item-details">
                <p><strong>Description:</strong> ${rule.description || 'No description'}</p>
                <p><strong>Error Message:</strong> ${rule.error_message || 'No error message set'}</p>
                <p><strong>Weight:</strong> ${rule.weight}</p>
            </div>
        </div>
    `).join('');
}

/**
 * Filter rules by scholarship
 */
function filterRules() {
    const filter = document.getElementById('scholarshipFilter');
    currentScholarshipFilter = filter.value;
    displayRules();
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

/**
 * Set up form submission handlers
 */
function setupFormHandlers() {
    // Create Scholarship Form
    const scholarshipForm = document.getElementById('createScholarshipForm');
    if (scholarshipForm) {
        scholarshipForm.addEventListener('submit', handleCreateScholarship);
    }
    
    // Create Rule Form
    const ruleForm = document.getElementById('createRuleForm');
    if (ruleForm) {
        ruleForm.addEventListener('submit', handleCreateRule);
    }
    
    // Edit Scholarship Form
    const editScholarshipForm = document.getElementById('editScholarshipForm');
    if (editScholarshipForm) {
        editScholarshipForm.addEventListener('submit', handleUpdateScholarship);
    }
    
    // Edit Rule Form
    const editRuleForm = document.getElementById('editRuleForm');
    if (editRuleForm) {
        editRuleForm.addEventListener('submit', handleUpdateRule);
    }
}

/**
 * Handle create scholarship form submission
 */
async function handleCreateScholarship(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('scholarshipName').value.trim(),
        description: document.getElementById('scholarshipDesc').value.trim(),
        amount: parseFloat(document.getElementById('scholarshipAmount').value),
        is_active: document.getElementById('scholarshipActive').checked
    };
    
    try {
        const response = await fetch('/api/scholarships', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Scholarship created successfully!', 'success');
            event.target.reset();
            document.getElementById('scholarshipActive').checked = true;
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to create scholarship', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Handle create rule form submission
 */
async function handleCreateRule(event) {
    event.preventDefault();
    
    const formData = {
        scholarship_id: parseInt(document.getElementById('ruleScholarship').value),
        field: document.getElementById('ruleField').value,
        operator: document.getElementById('ruleOperator').value,
        value: document.getElementById('ruleValue').value.trim(),
        weight: parseFloat(document.getElementById('ruleWeight').value) || 1.0,
        description: document.getElementById('ruleDescription').value.trim(),
        error_message: document.getElementById('ruleError').value.trim()
    };
    
    try {
        const response = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Rule added successfully!', 'success');
            event.target.reset();
            document.getElementById('ruleWeight').value = '1.0';
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to add rule', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Edit scholarship - open modal with data
 */
function editScholarship(scholarshipId) {
    const scholarship = scholarshipsData.find(s => s.id === scholarshipId);
    if (!scholarship) return;
    
    // Populate modal form
    document.getElementById('editScholarshipId').value = scholarship.id;
    document.getElementById('editScholarshipName').value = scholarship.name;
    document.getElementById('editScholarshipDesc').value = scholarship.description || '';
    document.getElementById('editScholarshipAmount').value = scholarship.amount;
    document.getElementById('editScholarshipActive').checked = scholarship.is_active;
    
    // Show modal
    openModal('editScholarshipModal');
}

/**
 * Handle update scholarship form submission
 */
async function handleUpdateScholarship(event) {
    event.preventDefault();
    
    const scholarshipId = document.getElementById('editScholarshipId').value;
    const formData = {
        name: document.getElementById('editScholarshipName').value.trim(),
        description: document.getElementById('editScholarshipDesc').value.trim(),
        amount: parseFloat(document.getElementById('editScholarshipAmount').value),
        is_active: document.getElementById('editScholarshipActive').checked
    };
    
    try {
        const response = await fetch(`/api/scholarships/${scholarshipId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Scholarship updated successfully!', 'success');
            closeModal('editScholarshipModal');
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to update scholarship', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Delete scholarship
 */
async function deleteScholarship(scholarshipId) {
    if (!confirm('Are you sure you want to delete this scholarship? All associated rules will also be deleted.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/scholarships/${scholarshipId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Scholarship deleted successfully!', 'success');
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to delete scholarship', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Edit rule - open modal with data
 */
function editRule(ruleId) {
    // Find the rule from scholarships data
    let rule = null;
    for (const scholarship of scholarshipsData) {
        rule = scholarship.rules.find(r => r.id === ruleId);
        if (rule) break;
    }
    
    if (!rule) return;
    
    // Populate modal form
    document.getElementById('editRuleId').value = rule.id;
    document.getElementById('editRuleField').value = rule.field;
    document.getElementById('editRuleOperator').value = rule.operator;
    document.getElementById('editRuleValue').value = rule.value;
    document.getElementById('editRuleWeight').value = rule.weight;
    document.getElementById('editRuleDescription').value = rule.description || '';
    document.getElementById('editRuleError').value = rule.error_message || '';
    
    // Show modal
    openModal('editRuleModal');
}

/**
 * Handle update rule form submission
 */
async function handleUpdateRule(event) {
    event.preventDefault();
    
    const ruleId = document.getElementById('editRuleId').value;
    const formData = {
        field: document.getElementById('editRuleField').value,
        operator: document.getElementById('editRuleOperator').value,
        value: document.getElementById('editRuleValue').value.trim(),
        weight: parseFloat(document.getElementById('editRuleWeight').value) || 1.0,
        description: document.getElementById('editRuleDescription').value.trim(),
        error_message: document.getElementById('editRuleError').value.trim()
    };
    
    try {
        const response = await fetch(`/api/rules/${ruleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Rule updated successfully!', 'success');
            closeModal('editRuleModal');
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to update rule', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Delete rule
 */
async function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Rule deleted successfully!', 'success');
            loadScholarships();
        } else {
            showNotification(data.error || 'Failed to delete rule', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    }
}

/**
 * Open a modal
 */
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

/**
 * Close a modal
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <span>${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#fee2e2' : type === 'success' ? '#d1fae5' : '#dbeafe'};
        color: ${type === 'error' ? '#dc2626' : type === 'success' ? '#059669' : '#2563eb'};
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1001;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 4000);
}
