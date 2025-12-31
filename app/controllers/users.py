"""
متحكم المستخدمين
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/')
@admin_required
def index():
    """قائمة المستخدمين"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')

    query = User.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )

    query = query.order_by(User.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return render_template('users/index.html',
                           page_title='إدارة المستخدمين',
                           users=users,
                           pagination=pagination,
                           search=search
                           )


@users_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    """إضافة مستخدم"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # التحقق من عدم تكرار اسم المستخدم
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود مسبقاً', 'error')
            return render_template('users/create.html', page_title='إضافة مستخدم')

        user = User(
            username=username,
            full_name=request.form.get('full_name'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            role=request.form.get('role', 'sales'),
            is_active=bool(request.form.get('is_active', True))
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='user',
            entity_id=user.id,
            description=f'إضافة مستخدم: {user.username}',
            ip_address=request.remote_addr
        )

        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/create.html',
                           page_title='إضافة مستخدم جديد'
                           )


@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    """تعديل مستخدم"""
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.phone = request.form.get('phone')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        user.is_active = bool(request.form.get('is_active'))

        # تغيير كلمة المرور إذا تم إدخالها
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='update',
            entity_type='user',
            entity_id=user.id,
            description=f'تعديل مستخدم: {user.username}',
            ip_address=request.remote_addr
        )

        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/edit.html',
                           page_title=f'تعديل: {user.full_name}',
                           user=user
                           )


@users_bp.route('/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle(id):
    """تفعيل/تعطيل مستخدم"""
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك تعطيل حسابك'})

    user.is_active = not user.is_active
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='toggle',
        entity_type='user',
        entity_id=user.id,
        description=f'{"تفعيل" if user.is_active else "تعطيل"} مستخدم: {user.username}',
        ip_address=request.remote_addr
    )

    return jsonify({
        'success': True,
        'message': f'تم {"تفعيل" if user.is_active else "تعطيل"} المستخدم',
        'is_active': user.is_active
    })


@users_bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """حذف مستخدم"""
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك حذف حسابك'})

    if user.invoices.count() > 0:
        return jsonify({'success': False, 'message': 'لا يمكن حذف المستخدم لوجود فواتير مرتبطة'})

    username = user.username
    db.session.delete(user)
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='delete',
        entity_type='user',
        entity_id=id,
        description=f'حذف مستخدم: {username}',
        ip_address=request.remote_addr
    )

    return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})


@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """الملف الشخصي"""
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.email = request.form.get('email')

        # تغيير كلمة المرور
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'error')
                return render_template('users/profile.html', page_title='الملف الشخصي')

            current_user.set_password(new_password)
            flash('تم تغيير كلمة المرور بنجاح', 'success')

        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')

    return render_template('users/profile.html',
                           page_title='الملف الشخصي'
                           )
