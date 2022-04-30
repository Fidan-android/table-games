from flask_marshmallow import Marshmallow
from models import *

# Объект маршмеллоу для преобразований
ma = Marshmallow()


# Класс схема, в которую происходит преобразования, она наследуюется от переданной нами Модели
class ProductJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True


class UserJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True


class OrderProductsJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrderProducts
        load_instance = True


class TempCartJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TempCart
        load_instance = True


class OrderJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True


class TokenJsonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Token
        load_instance = True
