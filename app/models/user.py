"""
نموذج المستخدم
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    """نموذج المستخدم"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True,
                         nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='sales')  # admin, cashier, sales
    is_active = db.Column(db.Boolean, default=True)
    menu_config = db.Column(db.JSON)
    theme_config = db.Column(db.JSON)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    invoices = db.relationship('Invoice', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    api_keys = db.relationship(
        'ApiKey', backref='creator', lazy='dynamic', foreign_keys='ApiKey.created_by')
    activities = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        """تشفير كلمة المرور"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """تحديث آخر تسجيل دخول"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def is_admin(self):
        """هل المستخدم مدير؟"""
        return self.role == 'admin'

    def get_role_label(self):
        """الحصول على اسم الدور"""
        roles = {
            'admin': 'مدير',
            'cashier': 'كاشير',
            'sales': 'موظف مبيعات'
        }
        return roles.get(self.role, self.role)

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """تحميل المستخدم للجلسة"""
    return User.query.get(int(user_id))
