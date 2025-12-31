"""
نموذج سجل النشاط
"""
from datetime import datetime
from app import db


class ActivityLog(db.Model):
    """نموذج سجل النشاط"""
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def log(cls, user_id, action, entity_type=None, entity_id=None, description=None, ip_address=None):
        """تسجيل نشاط"""
        activity = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address
        )
        db.session.add(activity)
        db.session.commit()
        return activity

    @classmethod
    def get_recent(cls, limit=50):
        """جلب آخر النشاطات"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_by_user(cls, user_id, limit=50):
        """جلب نشاطات مستخدم"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()

    @classmethod
    def get_by_entity(cls, entity_type, entity_id):
        """جلب نشاطات كيان معين"""
        return cls.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(cls.created_at.desc()).all()

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ActivityLog {self.action}>'
