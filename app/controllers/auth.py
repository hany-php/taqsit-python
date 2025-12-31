"""
متحكم المصادقة
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.activity_log import ActivityLog

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('هذا الحساب معطل، يرجى التواصل مع المدير', 'error')
            return render_template('auth/login.html')

        # تسجيل الدخول
        login_user(user, remember=remember)
        user.update_last_login()

        # تسجيل النشاط
        ActivityLog.log(
            user_id=user.id,
            action='login',
            description='تسجيل دخول',
            ip_address=request.remote_addr
        )

        flash(f'مرحباً {user.full_name}!', 'success')

        # إعادة التوجيه للصفحة المطلوبة أو الرئيسية
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    # تسجيل النشاط
    ActivityLog.log(
        user_id=current_user.id,
        action='logout',
        description='تسجيل خروج',
        ip_address=request.remote_addr
    )

    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def index():
    """الصفحة الرئيسية - توجيه"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/sw.js')
def service_worker():
    """تقديم Service Worker من المسار الجذري"""
    from flask import send_from_directory, current_app
    import os
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'sw.js',
        mimetype='application/javascript'
    )


@auth_bp.route('/manifest.json')
def manifest():
    """تقديم Manifest من المسار الجذري"""
    from flask import send_from_directory, current_app
    import os
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'manifest.json',
        mimetype='application/json'
    )
