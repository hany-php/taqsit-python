"""
نماذج قاعدة البيانات
"""
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.installment import Installment
from app.models.payment import Payment
from app.models.setting import Setting
from app.models.api_key import ApiKey
from app.models.activity_log import ActivityLog

__all__ = [
    'User',
    'Category',
    'Product',
    'Customer',
    'Invoice',
    'InvoiceItem',
    'Installment',
    'Payment',
    'Setting',
    'ApiKey',
    'ActivityLog',
]
