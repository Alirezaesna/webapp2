// Main JavaScript functions for Qard al-Hasanah System

document.addEventListener('DOMContentLoaded', function() {
  // Enable tooltips everywhere
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Enable popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // Auto-hide alerts after 5 seconds
  setTimeout(function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);
  
  // Function to format numbers as currency
  window.formatCurrency = function(amount) {
    return parseFloat(amount).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };
  
  // Function to calculate monthly installment
  window.calculateMonthlyInstallment = function(amount, duration) {
    if (amount > 0 && duration > 0) {
      return amount / duration;
    }
    return 0;
  };
  
  // Function to calculate loan completion percentage
  window.calculateCompletionPercentage = function(paidAmount, totalAmount) {
    if (totalAmount > 0) {
      return (paidAmount / totalAmount) * 100;
    }
    return 0;
  };
  
  // Function to confirm deletion actions
  window.confirmDelete = function(message) {
    return confirm(message || 'Are you sure you want to delete this item? This action cannot be undone.');
  };
  
  // Function to toggle password visibility
  window.togglePasswordVisibility = function(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      passwordInput.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  };
  
  // Handle print functionality
  const printButtons = document.querySelectorAll('.btn-print');
  printButtons.forEach(function(button) {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      window.print();
    });
  });
  
  // Handle dynamic form fields
  const conditionalFields = document.querySelectorAll('[data-condition-field]');
  conditionalFields.forEach(function(field) {
    const triggerFieldId = field.dataset.conditionField;
    const triggerField = document.getElementById(triggerFieldId);
    const conditionValue = field.dataset.conditionValue;
    
    if (triggerField) {
      const updateVisibility = function() {
        if (triggerField.type === 'checkbox') {
          if ((conditionValue === 'true' && triggerField.checked) || 
              (conditionValue === 'false' && !triggerField.checked)) {
            field.style.display = 'block';
          } else {
            field.style.display = 'none';
          }
        } else {
          if (triggerField.value === conditionValue) {
            field.style.display = 'block';
          } else {
            field.style.display = 'none';
          }
        }
      };
      
      updateVisibility(); // Initial state
      triggerField.addEventListener('change', updateVisibility);
    }
  });
});
