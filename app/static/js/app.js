/**
 * نظام تقسيط - JavaScript الرئيسي
 */

// Toggle Sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
    sidebar.classList.toggle('active');
    
    // حفظ الحالة
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
}

// Go Back - الرجوع للصفحة السابقة
function goBack() {
    // التحقق من وجود تاريخ للتصفح
    if (document.referrer && document.referrer.includes(window.location.host)) {
        history.back();
    } else {
        // إذا لم يكن هناك صفحة سابقة، اذهب للرئيسية
        window.location.href = '/';
    }
}

// استعادة حالة الـ Sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }
    
    // إخفاء زر الرجوع في الصفحة الرئيسية
    const backBtn = document.querySelector('.btn-back');
    if (backBtn && window.location.pathname === '/') {
        backBtn.style.display = 'none';
    }
});

// Modal Functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// إغلاق Modal عند النقر خارجها
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// إغلاق Modal بـ Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            activeModal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});

// Show Alert
function showAlert(type, message) {
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span class="material-icons-round">
            ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'info'}
        </span>
        ${message}
        <button class="close-btn" onclick="this.parentElement.remove()">
            <span class="material-icons-round">close</span>
        </button>
    `;
    
    container.appendChild(alert);
    
    // رسائل الخطأ والتحذير لا تختفي تلقائياً - فقط بالنقر على زر الإغلاق
    if (type !== 'error' && type !== 'warning') {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    const pageContent = document.querySelector('.page-content');
    if (pageContent) {
        pageContent.parentNode.insertBefore(container, pageContent);
    }
    return container;
}

// Confirm Delete
async function confirmDeleteAction(url, message = 'هل أنت متأكد من الحذف؟') {
    if (!confirm(message)) return false;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', data.message);
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('error', data.message);
        }
    } catch (error) {
        showAlert('error', 'حدث خطأ أثناء العملية');
    }
}

// Format Money
function formatMoney(amount, currency = 'ج.م') {
    if (amount === null || amount === undefined) amount = 0;
    return parseFloat(amount).toLocaleString('ar-EG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + ' ' + currency;
}

// Format Date
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ar-EG');
}

// AJAX Form Submit
function ajaxFormSubmit(form, callback) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = form.querySelector('[type="submit"]');
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="material-icons-round">hourglass_empty</span> جار الحفظ...';
        }
        
        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (callback) {
                callback(data);
            } else if (data.success) {
                showAlert('success', data.message);
                if (data.redirect) {
                    setTimeout(() => location.href = data.redirect, 1000);
                }
            } else {
                showAlert('error', data.message);
            }
        } catch (error) {
            showAlert('error', 'حدث خطأ أثناء العملية');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span class="material-icons-round">save</span> حفظ';
            }
        }
    });
}

// Search Autocomplete
function setupAutocomplete(inputId, url, callback) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    let debounceTimer;
    
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        
        debounceTimer = setTimeout(async () => {
            const query = this.value.trim();
            if (query.length < 2) return;
            
            try {
                const response = await fetch(`${url}?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (callback) {
                    callback(data);
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300);
    });
}

// Number Input - Allow Arabic/English numbers
document.addEventListener('input', function(e) {
    if (e.target.type === 'number') {
        // تحويل الأرقام العربية لإنجليزية
        const arabicNums = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
        let value = e.target.value;
        
        arabicNums.forEach((num, i) => {
            value = value.replace(new RegExp(num, 'g'), i);
        });
        
        e.target.value = value;
    }
});

// Print Element
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>طباعة</title>
            <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                body { font-family: 'Cairo', sans-serif; padding: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 10px; text-align: right; }
                th { background: #f5f5f5; }
            </style>
        </head>
        <body>
            ${element.innerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});
