# خطة تنفيذ نظام تقسيط (Python + PostgreSQL)

## نظرة عامة على المشروع

نظام **"تقسيط"** هو نظام متكامل لإدارة مبيعات التقسيط يتضمن:
- إدارة المنتجات والتصنيفات
- إدارة العملاء والضامنين
- إنشاء الفواتير (نقدي/تقسيط)
- متابعة الأقساط والمدفوعات
- لوحة تحكم شاملة مع إحصائيات
- تقارير متقدمة (أرباح، تدفق نقدي، أداء الموظفين)
- API للتكامل الخارجي
- نظام صلاحيات متعدد المستويات

---

## التقنيات المستخدمة

| المكون | التقنية |
|--------|---------|
| Backend Framework | **Flask** |
| ORM | **SQLAlchemy** |
| Database | **PostgreSQL** |
| Template Engine | **Jinja2** |
| Authentication | **Flask-Login** |
| Forms | **Flask-WTF** |
| Migration | **Flask-Migrate (Alembic)** |
| API | **Flask-RESTful** أو blueprints |

---

## هيكل المشروع

```
taqsit-python/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # إعدادات التطبيق
│   ├── models/                  # نماذج قاعدة البيانات
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── category.py
│   │   ├── invoice.py
│   │   ├── installment.py
│   │   ├── payment.py
│   │   └── setting.py
│   ├── controllers/             # Controllers (blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── products.py
│   │   ├── categories.py
│   │   ├── customers.py
│   │   ├── invoices.py
│   │   ├── installments.py
│   │   ├── payments.py
│   │   ├── users.py
│   │   ├── reports.py
│   │   ├── settings.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v2.py
│   ├── templates/               # قوالب Jinja2
│   │   ├── layouts/
│   │   │   └── master.html
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   ├── products/
│   │   ├── customers/
│   │   ├── invoices/
│   │   ├── installments/
│   │   ├── payments/
│   │   ├── reports/
│   │   └── settings/
│   ├── static/                  # ملفات ثابتة
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   │   └── icons/
│   └── utils/                   # أدوات مساعدة
│       ├── __init__.py
│       ├── helpers.py
│       └── decorators.py
├── migrations/                  # Alembic migrations
├── requirements.txt
├── .env.example
├── run.py                       # نقطة الدخول
└── README.md
```

---

## مخطط قاعدة البيانات (PostgreSQL)

### جدول users (المستخدمين)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'sales', -- admin, cashier, sales
    is_active BOOLEAN DEFAULT TRUE,
    menu_config JSONB,
    theme_config JSONB,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول categories (التصنيفات)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    icon VARCHAR(50),
    color VARCHAR(20) DEFAULT '#1e88e5',
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول products (المنتجات)
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    barcode VARCHAR(50),
    sku VARCHAR(50),
    cash_price DECIMAL(10,2) NOT NULL,
    installment_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    quantity INTEGER DEFAULT 0,
    min_quantity INTEGER DEFAULT 5,
    image VARCHAR(255),
    brand VARCHAR(100),
    model VARCHAR(100),
    warranty_months INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول customers (العملاء)
```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    phone2 VARCHAR(20),
    national_id VARCHAR(20),
    national_id_image VARCHAR(255),
    address TEXT,
    city VARCHAR(50),
    work_address TEXT,
    work_phone VARCHAR(20),
    guarantor_name VARCHAR(100),
    guarantor_phone VARCHAR(20),
    guarantor_national_id VARCHAR(20),
    credit_limit DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول invoices (الفواتير)
```sql
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    user_id INTEGER REFERENCES users(id),
    invoice_type VARCHAR(20) NOT NULL, -- cash, installment
    total_amount DECIMAL(10,2) NOT NULL,
    down_payment DECIMAL(10,2) DEFAULT 0,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    remaining_amount DECIMAL(10,2) DEFAULT 0,
    monthly_installment DECIMAL(10,2),
    installment_months INTEGER,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, cancelled
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول invoice_items (بنود الفاتورة)
```sql
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(200),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول installments (الأقساط)
```sql
CREATE TABLE installments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    remaining_amount DECIMAL(10,2),
    due_date DATE NOT NULL,
    paid_date DATE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, partial, paid, overdue
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول payments (المدفوعات)
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id),
    installment_id INTEGER REFERENCES installments(id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) DEFAULT 'cash', -- cash, card, transfer
    receipt_number VARCHAR(50),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول settings (الإعدادات)
```sql
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_group VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول api_keys (مفاتيح API)
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول activity_log (سجل النشاط)
```sql
CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    description TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
