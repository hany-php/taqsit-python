"""
نموذج مفاتيح API
"""
from datetime import datetime
import secrets
from app import db


class ApiKey(db.Model):
    """نموذج مفتاح API"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(255), unique=True,
                        nullable=False, index=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_key():
        """إنشاء مفتاح API جديد"""
        return f"tq_{secrets.token_urlsafe(32)}"

    @classmethod
    def create_key(cls, name, description=None, created_by=None, expires_at=None):
        """إنشاء مفتاح جديد"""
        api_key = cls(
            name=name,
            api_key=cls.generate_key(),
            description=description,
            created_by=created_by,
            expires_at=expires_at
        )
        db.session.add(api_key)
        db.session.commit()
        return api_key

    @classmethod
    def validate(cls, key):
        """التحقق من صلاحية المفتاح"""
        api_key = cls.query.filter_by(api_key=key, is_active=True).first()

        if not api_key:
            return None

        # التحقق من انتهاء الصلاحية
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # تحديث آخر استخدام
        api_key.last_used_at = datetime.utcnow()
        db.session.commit()

        return api_key

    @property
    def is_expired(self):
        """هل انتهت صلاحية المفتاح؟"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()

    @property
    def key_preview(self):
        """معاينة مختصرة للمفتاح"""
        if self.api_key:
            return self.api_key[:15] + '...' + self.api_key[-5:]
        return None

    def to_dict(self, include_key=False):
        """تحويل لـ Dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_key:
            data['api_key'] = self.api_key
        else:
            data['api_key_preview'] = self.api_key[:10] + \
                '...' if self.api_key else None

        return data

    def __repr__(self):
        return f'<ApiKey {self.name}>'
