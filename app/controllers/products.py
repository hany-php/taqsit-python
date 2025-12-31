"""
متحكم المنتجات
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required
from app.utils.helpers import get_pagination_info

products_bp = Blueprint('products', __name__)


@products_bp.route('/')
@login_required
def index():
    """قائمة المنتجات"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')
    category_id = request.args.get('category', type=int)

    query = Product.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.barcode.ilike(search_term),
                Product.brand.ilike(search_term)
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    query = query.order_by(Product.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    categories = Category.get_all_with_count()

    return render_template('products/index.html',
                           page_title='إدارة المنتجات',
                           products=products,
                           categories=categories,
                           pagination=pagination,
                           search=search,
                           category_id=category_id
                           )


@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """إضافة منتج"""
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            category_id=request.form.get('category_id') or None,
            barcode=request.form.get('barcode'),
            sku=request.form.get('sku'),
            cash_price=request.form.get('cash_price', 0, type=float),
            installment_price=request.form.get(
                'installment_price', 0, type=float),
            cost_price=request.form.get('cost_price', 0, type=float),
            quantity=request.form.get('quantity', 0, type=int),
            min_quantity=request.form.get('min_quantity', 5, type=int),
            brand=request.form.get('brand'),
            model=request.form.get('model'),
            warranty_months=request.form.get('warranty_months', 0, type=int),
            is_active=bool(request.form.get('is_active', True))
        )

        db.session.add(product)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='product',
            entity_id=product.id,
            description=f'إضافة منتج: {product.name}',
            ip_address=request.remote_addr
        )

        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('products.index'))

    categories = Category.get_all_with_count()
    return render_template('products/create.html',
                           page_title='إضافة منتج جديد',
                           categories=categories
                           )


@products_bp.route('/<int:id>')
@login_required
def show(id):
    """عرض منتج"""
    product = Product.query.get_or_404(id)
    return render_template('products/show.html',
                           page_title=f'المنتج: {product.name}',
                           product=product
                           )


@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """تعديل منتج"""
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category_id = request.form.get('category_id') or None
        product.barcode = request.form.get('barcode')
        product.sku = request.form.get('sku')
        product.cash_price = request.form.get('cash_price', 0, type=float)
        product.installment_price = request.form.get(
            'installment_price', 0, type=float)
        product.cost_price = request.form.get('cost_price', 0, type=float)
        product.quantity = request.form.get('quantity', 0, type=int)
        product.min_quantity = request.form.get('min_quantity', 5, type=int)
        product.brand = request.form.get('brand')
        product.model = request.form.get('model')
        product.warranty_months = request.form.get(
            'warranty_months', 0, type=int)
        product.is_active = bool(request.form.get('is_active'))

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='update',
            entity_type='product',
            entity_id=product.id,
            description=f'تعديل منتج: {product.name}',
            ip_address=request.remote_addr
        )

        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('products.index'))

    categories = Category.get_all_with_count()
    return render_template('products/edit.html',
                           page_title=f'تعديل: {product.name}',
                           product=product,
                           categories=categories
                           )


@products_bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """حذف منتج"""
    product = Product.query.get_or_404(id)

    # التحقق من عدم وجود فواتير مرتبطة
    if product.invoice_items.count() > 0:
        if request.is_json:
            return jsonify({'success': False, 'message': 'لا يمكن حذف المنتج لوجود فواتير مرتبطة'})
        flash('لا يمكن حذف المنتج لوجود فواتير مرتبطة', 'error')
        return redirect(url_for('products.index'))

    name = product.name
    db.session.delete(product)
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='delete',
        entity_type='product',
        entity_id=id,
        description=f'حذف منتج: {name}',
        ip_address=request.remote_addr
    )

    if request.is_json:
        return jsonify({'success': True, 'message': 'تم حذف المنتج بنجاح'})

    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('products.index'))


@products_bp.route('/search')
@login_required
def search():
    """بحث في المنتجات (API)"""
    q = request.args.get('q', '')
    products = Product.search(q)
    return jsonify([p.to_dict() for p in products])
