"""
متحكم الإعدادات
"""
import os
import glob
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.setting import Setting
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required

settings_bp = Blueprint('settings', __name__)


def get_backup_dir():
    """الحصول على مسار مجلد النسخ الاحتياطية في المجلد الرئيسي"""
    # المجلد الرئيسي للمشروع (خارج app)
    project_root = os.path.dirname(current_app.root_path)
    backup_dir = os.path.join(project_root, 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir


def get_backups():
    """جلب قائمة النسخ الاحتياطية"""
    backup_dir = get_backup_dir()

    backups = []
    # جلب جميع أنواع الملفات: sql, zip, json
    patterns = ['*.sql', '*.zip', '*.json']
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(os.path.join(backup_dir, pattern)))

    for filepath in all_files:
        filename = os.path.basename(filepath)
        stats = os.stat(filepath)
        size = stats.st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size} bytes"

        # تحديد نوع النسخة بالعربي
        if 'backup_full' in filename:
            backup_type = 'نسخة كاملة'
            backup_icon = 'all_inclusive'
        elif 'backup_db' in filename:
            backup_type = 'قاعدة بيانات فقط'
            backup_icon = 'storage'
        elif 'backup_files' in filename:
            backup_type = 'ملفات وصور فقط'
            backup_icon = 'folder'
        else:
            backup_type = 'نسخة'
            backup_icon = 'backup'

        backups.append({
            'filename': filename,
            'size': size_str,
            'date': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M'),
            'type': backup_type,
            'icon': backup_icon
        })

    return sorted(backups, key=lambda x: x['date'], reverse=True)


@settings_bp.route('/')
@admin_required
def index():
    """صفحة الإعدادات"""
    from app.models.installment_plan import InstallmentPlan

    settings = Setting.get_all_dict()
    backups = get_backups()
    installment_plans = InstallmentPlan.get_all_plans()

    return render_template('settings/index.html',
                           page_title='إعدادات النظام',
                           settings=settings,
                           backups=backups,
                           installment_plans=installment_plans
                           )


@settings_bp.route('/store', methods=['POST'])
@admin_required
def store():
    """حفظ الإعدادات"""
    # جمع كل الإعدادات من الفورم
    settings_to_save = {}

    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            settings_to_save[setting_key] = value

    # معالجة checkboxes
    section = request.form.get('section', '')
    checkbox_fields = {
        'installment': ['auto_apply_late_fee'],
        'appearance': ['show_animations'],
        'print': ['print_logo', 'auto_print_invoice']
    }

    if section in checkbox_fields:
        for field in checkbox_fields[section]:
            if f'setting_{field}' not in request.form:
                settings_to_save[field] = '0'
            else:
                settings_to_save[field] = '1'

    # حفظ الإعدادات
    Setting.update_multiple(settings_to_save)

    ActivityLog.log(
        user_id=current_user.id,
        action='update',
        entity_type='settings',
        description='تحديث إعدادات النظام',
        ip_address=request.remote_addr
    )

    flash('تم حفظ الإعدادات بنجاح', 'success')
    return redirect(url_for('settings.index'))


@settings_bp.route('/backup/create', methods=['POST'])
@admin_required
def backup_create():
    """إنشاء نسخة احتياطية"""
    import json
    import zipfile
    import shutil

    backup_type = request.form.get(
        'backup_type', 'full')  # full, database, files

    try:
        backup_dir = get_backup_dir()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if backup_type == 'database':
            # نسخة قاعدة البيانات فقط
            filename = f"backup_db_{timestamp}.json"
            filepath = os.path.join(backup_dir, filename)
            export_database_to_json(filepath)

        elif backup_type == 'files':
            # نسخة الملفات فقط
            filename = f"backup_files_{timestamp}.zip"
            filepath = os.path.join(backup_dir, filename)
            project_root = os.path.dirname(current_app.root_path)
            export_files_to_zip(filepath, project_root)

        else:
            # نسخة كاملة (قاعدة بيانات + ملفات)
            filename = f"backup_full_{timestamp}.zip"
            filepath = os.path.join(backup_dir, filename)

            # إنشاء zip مؤقت
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # تصدير قاعدة البيانات
                db_file = os.path.join(backup_dir, f"temp_db_{timestamp}.json")
                export_database_to_json(db_file)
                zipf.write(db_file, 'database.json')
                os.remove(db_file)

                # إضافة الملفات المهمة
                project_root = os.path.dirname(current_app.root_path)
                add_project_files_to_zip(zipf, project_root)

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='backup',
            description=f'إنشاء نسخة احتياطية ({backup_type}): {filename}',
            ip_address=request.remote_addr
        )

        flash(f'تم إنشاء النسخة الاحتياطية بنجاح: {filename}', 'success')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('settings.index') + '#section-backup')


def export_database_to_json(filepath):
    """تصدير قاعدة البيانات إلى ملف JSON"""
    import json
    from app.models.product import Product
    from app.models.category import Category
    from app.models.customer import Customer
    from app.models.invoice import Invoice, InvoiceItem
    from app.models.installment import Installment
    from app.models.payment import Payment
    from app.models.user import User

    data = {
        'exported_at': datetime.now().isoformat(),
        'version': '1.0',
        'settings': {},
        'categories': [],
        'products': [],
        'customers': [],
        'invoices': [],
        'invoice_items': [],
        'installments': [],
        'payments': []
    }

    # تصدير الإعدادات
    settings = Setting.query.all()
    for s in settings:
        data['settings'][s.setting_key] = s.setting_value

    # تصدير التصنيفات
    for cat in Category.query.all():
        data['categories'].append({
            'id': cat.id,
            'name': cat.name,
            'description': getattr(cat, 'description', ''),
            'is_active': getattr(cat, 'is_active', True)
        })

    # تصدير المنتجات
    for prod in Product.query.all():
        data['products'].append({
            'id': prod.id,
            'name': prod.name,
            'cash_price': float(prod.cash_price) if prod.cash_price else 0,
            'installment_price': float(prod.installment_price) if prod.installment_price else 0,
            'cost_price': float(prod.cost_price) if prod.cost_price else 0,
            'category_id': prod.category_id,
            'barcode': prod.barcode or '',
            'quantity': prod.quantity or 0,
            'is_active': prod.is_active
        })

    # تصدير العملاء
    for cust in Customer.query.all():
        data['customers'].append({
            'id': cust.id,
            'full_name': cust.full_name,
            'phone': cust.phone,
            'address': getattr(cust, 'address', ''),
            'national_id': getattr(cust, 'national_id', '')
        })

    # تصدير الفواتير
    for inv in Invoice.query.all():
        data['invoices'].append({
            'id': inv.id,
            'customer_id': inv.customer_id,
            'invoice_type': inv.invoice_type,
            'total_amount': float(inv.total_amount) if inv.total_amount else 0,
            'paid_amount': float(inv.paid_amount) if inv.paid_amount else 0,
            'status': inv.status,
            'created_at': inv.created_at.isoformat() if inv.created_at else None
        })

    # تصدير عناصر الفواتير
    for item in InvoiceItem.query.all():
        data['invoice_items'].append({
            'id': item.id,
            'invoice_id': item.invoice_id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price) if item.unit_price else 0,
            'total_price': float(item.total_price) if item.total_price else 0
        })

    # تصدير الأقساط
    for inst in Installment.query.all():
        data['installments'].append({
            'id': inst.id,
            'invoice_id': inst.invoice_id,
            'installment_number': inst.installment_number,
            'amount': float(inst.amount) if inst.amount else 0,
            'paid_amount': float(inst.paid_amount) if inst.paid_amount else 0,
            'remaining_amount': float(inst.remaining_amount) if inst.remaining_amount else 0,
            'due_date': inst.due_date.isoformat() if inst.due_date else None,
            'paid_date': inst.paid_date.isoformat() if inst.paid_date else None,
            'status': inst.status
        })

    # تصدير المدفوعات
    for pay in Payment.query.all():
        data['payments'].append({
            'id': pay.id,
            'installment_id': pay.installment_id,
            'amount': float(pay.amount) if pay.amount else 0,
            'payment_date': pay.payment_date.isoformat() if pay.payment_date else None,
            'payment_method': getattr(pay, 'payment_method', 'cash')
        })

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_files_to_zip(filepath, root_path):
    """تصدير ملفات المشروع إلى ZIP"""
    import zipfile

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        add_project_files_to_zip(zipf, root_path)


def add_project_files_to_zip(zipf, root_path):
    """إضافة جميع ملفات المشروع إلى ZIP"""

    # الملفات والمجلدات التي يجب تجاهلها
    ignore_patterns = [
        '__pycache__', '.git', '.venv', 'venv', 'env',
        '*.pyc', '*.pyo', '.env', '.idea', '.vscode',
        'node_modules', '.pytest_cache', 'backups'
    ]

    # المجلدات المهمة للنسخ
    important_items = [
        'app',           # كود التطبيق
        'static',        # الملفات الثابتة (CSS, JS, Images)
        'templates',     # قوالب HTML إن وجدت خارج app
        'migrations',    # ملفات الـ migrations
        'config.py',     # ملف الإعدادات
        'requirements.txt',
        'run.py',
        'wsgi.py',
        '.env.example'
    ]

    def should_ignore(path):
        """التحقق إذا كان يجب تجاهل الملف/المجلد"""
        for pattern in ignore_patterns:
            if pattern in path:
                return True
        return False

    for item in important_items:
        item_path = os.path.join(root_path, item)

        if os.path.isfile(item_path):
            # إضافة ملف
            if not should_ignore(item_path):
                zipf.write(item_path, item)

        elif os.path.isdir(item_path):
            # إضافة مجلد
            for root, dirs, files in os.walk(item_path):
                # تجاهل المجلدات غير المرغوبة
                dirs[:] = [d for d in dirs if not should_ignore(d)]

                for file in files:
                    file_path = os.path.join(root, file)
                    if not should_ignore(file_path):
                        arcname = os.path.relpath(file_path, root_path)
                        zipf.write(file_path, arcname)


@settings_bp.route('/backup/<filename>/download')
@admin_required
def backup_download(filename):
    """تحميل نسخة احتياطية"""
    backup_dir = get_backup_dir()
    filepath = os.path.join(backup_dir, secure_filename(filename))

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)

    flash('الملف غير موجود', 'error')
    return redirect(url_for('settings.index'))


@settings_bp.route('/backup/<filename>/delete', methods=['POST'])
@admin_required
def backup_delete(filename):
    """حذف نسخة احتياطية"""
    backup_dir = get_backup_dir()
    filepath = os.path.join(backup_dir, secure_filename(filename))

    if os.path.exists(filepath):
        os.remove(filepath)

        ActivityLog.log(
            user_id=current_user.id,
            action='delete',
            entity_type='backup',
            description=f'حذف نسخة احتياطية: {filename}',
            ip_address=request.remote_addr
        )

        return jsonify({'success': True, 'message': 'تم حذف النسخة الاحتياطية'})

    return jsonify({'success': False, 'message': 'الملف غير موجود'})


@settings_bp.route('/backup/restore', methods=['POST'])
@admin_required
def backup_restore():
    """استعادة نسخة احتياطية"""
    if 'backup_file' not in request.files:
        flash('يرجى اختيار ملف', 'error')
        return redirect(url_for('settings.index'))

    file = request.files['backup_file']
    if file.filename == '':
        flash('يرجى اختيار ملف', 'error')
        return redirect(url_for('settings.index'))

    # هنا يمكن إضافة منطق استعادة النسخة الاحتياطية

    ActivityLog.log(
        user_id=current_user.id,
        action='restore',
        entity_type='backup',
        description=f'محاولة استعادة نسخة احتياطية: {file.filename}',
        ip_address=request.remote_addr
    )

    flash('تم استلام ملف النسخة الاحتياطية. الاستعادة قيد التطوير.', 'warning')
    return redirect(url_for('settings.index'))


@settings_bp.route('/test-print')
@admin_required
def test_print():
    """صفحة طباعة تجريبية"""
    settings = Setting.get_all_dict()
    return render_template('settings/test_print.html', settings=settings)


@settings_bp.route('/activity-log')
@admin_required
def activity_log():
    """سجل النشاط"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    activities = pagination.items

    return render_template('settings/activity_log.html',
                           page_title='سجل النشاط',
                           activities=activities,
                           pagination=pagination
                           )


@settings_bp.route('/api-docs')
@admin_required
def api_docs():
    """توثيق API"""
    return render_template('settings/api_docs.html',
                           page_title='توثيق API'
                           )


@settings_bp.route('/api-keys')
@admin_required
def api_keys():
    """إدارة مفاتيح API"""
    from app.models.api_key import ApiKey

    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    new_key = request.args.get('new_key')

    return render_template('settings/api_keys.html',
                           page_title='إدارة مفاتيح API',
                           api_keys=keys,
                           new_key=new_key
                           )


@settings_bp.route('/api-keys/create', methods=['POST'])
@admin_required
def api_key_create():
    """إنشاء مفتاح API جديد"""
    from app.models.api_key import ApiKey

    name = request.form.get('name')
    expires_at_str = request.form.get('expires_at')

    if not name:
        flash('اسم المفتاح مطلوب', 'error')
        return redirect(url_for('settings.api_keys'))

    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d')
        except ValueError:
            pass

    try:
        api_key = ApiKey.create_key(
            name=name,
            created_by=current_user.id,
            expires_at=expires_at
        )

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='api_key',
            entity_id=api_key.id,
            description=f'إنشاء مفتاح API: {name}',
            ip_address=request.remote_addr
        )

        flash('تم إنشاء المفتاح بنجاح', 'success')
        return redirect(url_for('settings.api_keys', new_key=api_key.api_key))

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('settings.api_keys'))


@settings_bp.route('/api-keys/<int:id>/toggle', methods=['POST'])
@admin_required
def api_key_toggle(id):
    """تفعيل/تعطيل مفتاح API"""
    from app.models.api_key import ApiKey

    api_key = ApiKey.query.get(id)

    if not api_key:
        return jsonify({'success': False, 'message': 'المفتاح غير موجود'})

    try:
        api_key.is_active = not api_key.is_active
        db.session.commit()

        action = 'تفعيل' if api_key.is_active else 'تعطيل'
        ActivityLog.log(
            user_id=current_user.id,
            action='update',
            entity_type='api_key',
            entity_id=api_key.id,
            description=f'{action} مفتاح API: {api_key.name}',
            ip_address=request.remote_addr
        )

        return jsonify({'success': True, 'message': f'تم {action} المفتاح بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@settings_bp.route('/api-keys/<int:id>/delete', methods=['POST'])
@admin_required
def api_key_delete(id):
    """حذف مفتاح API"""
    from app.models.api_key import ApiKey

    api_key = ApiKey.query.get(id)

    if not api_key:
        return jsonify({'success': False, 'message': 'المفتاح غير موجود'})

    try:
        name = api_key.name
        db.session.delete(api_key)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='delete',
            entity_type='api_key',
            description=f'حذف مفتاح API: {name}',
            ip_address=request.remote_addr
        )

        return jsonify({'success': True, 'message': 'تم حذف المفتاح بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# ============== خطط التقسيط ==============

@settings_bp.route('/installment-plans')
@admin_required
def installment_plans():
    """صفحة خطط التقسيط"""
    from app.models.installment_plan import InstallmentPlan

    plans = InstallmentPlan.get_all_plans()

    return render_template('settings/installment_plans.html',
                           page_title='خطط التقسيط',
                           plans=plans
                           )


@settings_bp.route('/installment-plans/create', methods=['POST'])
@admin_required
def installment_plan_create():
    """إنشاء خطة تقسيط جديدة"""
    from app.models.installment_plan import InstallmentPlan

    name = request.form.get('name')
    months = request.form.get('months', type=int)
    interest_rate = request.form.get('interest_rate', 0, type=float)
    min_down_payment = request.form.get('min_down_payment', 0, type=float)
    is_active = request.form.get('is_active') == 'on'

    if not name or not months:
        flash('اسم الخطة وعدد الأشهر مطلوبان', 'error')
        return redirect(url_for('settings.installment_plans'))

    try:
        plan = InstallmentPlan(
            name=name,
            months=months,
            interest_rate=interest_rate,
            min_down_payment=min_down_payment,
            is_active=is_active
        )

        db.session.add(plan)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='installment_plan',
            entity_id=plan.id,
            description=f'إنشاء خطة تقسيط: {name}',
            ip_address=request.remote_addr
        )

        flash('تم إنشاء الخطة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('settings.index') + '#section-installment')


@settings_bp.route('/installment-plans/<int:id>/update', methods=['POST'])
@admin_required
def installment_plan_update(id):
    """تحديث خطة تقسيط"""
    from app.models.installment_plan import InstallmentPlan

    plan = InstallmentPlan.query.get(id)

    if not plan:
        flash('الخطة غير موجودة', 'error')
        return redirect(url_for('settings.installment_plans'))

    try:
        plan.name = request.form.get('name', plan.name)
        plan.months = request.form.get('months', plan.months, type=int)
        plan.interest_rate = request.form.get(
            'interest_rate', plan.interest_rate, type=float)
        plan.min_down_payment = request.form.get(
            'min_down_payment', plan.min_down_payment, type=float)
        plan.is_active = request.form.get('is_active') == 'on'

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='update',
            entity_type='installment_plan',
            entity_id=plan.id,
            description=f'تحديث خطة تقسيط: {plan.name}',
            ip_address=request.remote_addr
        )

        flash('تم تحديث الخطة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('settings.index') + '#section-installment')


@settings_bp.route('/installment-plans/<int:id>/delete', methods=['POST'])
@admin_required
def installment_plan_delete(id):
    """حذف خطة تقسيط"""
    from app.models.installment_plan import InstallmentPlan

    plan = InstallmentPlan.query.get(id)

    if not plan:
        return jsonify({'success': False, 'message': 'الخطة غير موجودة'})

    try:
        name = plan.name
        db.session.delete(plan)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='delete',
            entity_type='installment_plan',
            description=f'حذف خطة تقسيط: {name}',
            ip_address=request.remote_addr
        )

        return jsonify({'success': True, 'message': 'تم حذف الخطة بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
