"""
نموذج الإعدادات
"""
from datetime import datetime
from app import db


class Setting(db.Model):
    """نموذج الإعداد"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True,
                            nullable=False, index=True)
    setting_value = db.Column(db.Text)
    setting_group = db.Column(db.String(50), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        """جلب قيمة إعداد"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def set(cls, key, value, group='general'):
        """تعيين قيمة إعداد"""
        setting = cls.query.filter_by(setting_key=key).first()

        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                setting_group=group
            )
            db.session.add(setting)

        db.session.commit()
        return setting

    @classmethod
    def get_group(cls, group):
        """جلب إعدادات مجموعة"""
        settings = cls.query.filter_by(setting_group=group).all()
        return {s.setting_key: s.setting_value for s in settings}

    @classmethod
    def get_all_dict(cls):
        """جلب كل الإعدادات كـ Dictionary"""
        settings = cls.query.all()
        return {s.setting_key: s.setting_value for s in settings}

    @classmethod
    def update_multiple(cls, settings_dict):
        """تحديث مجموعة إعدادات"""
        for key, value in settings_dict.items():
            cls.set(key, value)

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_group': self.setting_group,
        }

    def __repr__(self):
        return f'<Setting {self.setting_key}>'
