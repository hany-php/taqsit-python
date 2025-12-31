"""
Decorators للصلاحيات
"""
from functools import wraps
from flask import flash, redirect, url_for, jsonify, request
from flask_login import current_user


def admin_required(f):
    """يتطلب صلاحية مدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('auth.login'))

        if current_user.role != 'admin':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'ليس لديك صلاحية لهذا الإجراء'}), 403
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """يتطلب أحد الأدوار المحددة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'ليس لديك صلاحية لهذا الإجراء'}), 403
                flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_key_required(f):
    """يتطلب مفتاح API صالح"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models.api_key import ApiKey

        # جلب المفتاح من الـ Header
        api_key = request.headers.get('X-API-KEY')

        if not api_key:
            return jsonify({
                'success': False,
                'error': 'مفتاح API مطلوب',
                'error_code': 'MISSING_API_KEY'
            }), 401

        # التحقق من المفتاح
        key_data = ApiKey.validate(api_key)

        if not key_data:
            return jsonify({
                'success': False,
                'error': 'مفتاح API غير صالح أو منتهي الصلاحية',
                'error_code': 'INVALID_API_KEY'
            }), 401

        # إضافة بيانات المفتاح للـ request
        request.api_key = key_data

        return f(*args, **kwargs)
    return decorated_function


def log_activity(action, entity_type=None):
    """تسجيل النشاط تلقائياً"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)

            # تسجيل النشاط بعد نجاح العملية
            if current_user.is_authenticated:
                from app.models.activity_log import ActivityLog

                entity_id = kwargs.get('id') or kwargs.get(
                    'product_id') or kwargs.get('customer_id')

                ActivityLog.log(
                    user_id=current_user.id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    ip_address=request.remote_addr
                )

            return result
        return decorated_function
    return decorator
