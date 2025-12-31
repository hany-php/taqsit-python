"""
متحكم التصنيفات
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.category import Category
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/')
@login_required
def index():
    """قائمة التصنيفات"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')

    query = Category.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Category.name.ilike(search_term),
                Category.description.ilike(search_term)
            )
        )

    query = query.order_by(Category.sort_order, Category.name)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = pagination.items
    all_categories = Category.query.order_by(
        Category.sort_order, Category.name).all()

    return render_template('categories/index.html',
                           page_title='إدارة التصنيفات',
                           categories=categories,
                           all_categories=all_categories,
                           pagination=pagination,
                           search=search
                           )


@categories_bp.route('/store', methods=['POST'])
@login_required
def store():
    """إضافة/تعديل تصنيف (AJAX)"""
    category_id = request.form.get('id', type=int)

    if category_id:
        # تعديل
        category = Category.query.get_or_404(category_id)
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.icon = request.form.get('icon')
        category.color = request.form.get('color', '#1e88e5')
        action_text = 'تعديل'
    else:
        # إضافة
        category = Category(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon=request.form.get('icon'),
            color=request.form.get('color', '#1e88e5')
        )
        db.session.add(category)
        action_text = 'إضافة'

    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='create' if not category_id else 'update',
        entity_type='category',
        entity_id=category.id,
        description=f'{action_text} تصنيف: {category.name}',
        ip_address=request.remote_addr
    )

    return jsonify({
        'success': True,
        'message': f'تم {action_text} التصنيف بنجاح',
        'category': category.to_dict()
    })


@categories_bp.route('/<int:id>')
@login_required
def show(id):
    """عرض منتجات التصنيف"""
    category = Category.query.get_or_404(id)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = category.products.order_by(db.desc('id')).paginate(
        page=page, per_page=per_page, error_out=False
    )
    products = pagination.items

    all_categories = Category.query.order_by(
        Category.sort_order, Category.name).all()

    return render_template('categories/show.html',
                           page_title=f'منتجات التصنيف: {category.name}',
                           category=category,
                           products=products,
                           categories=all_categories,
                           pagination=pagination
                           )


@categories_bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """حذف تصنيف"""
    category = Category.query.get_or_404(id)

    # نقل المنتجات لتصنيف آخر أو بدون تصنيف
    move_to = request.form.get('move_to_category', type=int)

    from app.models.product import Product
    Product.query.filter_by(category_id=id).update(
        {'category_id': move_to or None})

    name = category.name
    db.session.delete(category)
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='delete',
        entity_type='category',
        entity_id=id,
        description=f'حذف تصنيف: {name}',
        ip_address=request.remote_addr
    )

    if request.is_json:
        return jsonify({'success': True, 'message': 'تم حذف التصنيف بنجاح'})

    flash('تم حذف التصنيف بنجاح', 'success')
    return redirect(url_for('categories.index'))
