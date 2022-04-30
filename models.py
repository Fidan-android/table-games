from flask_sqlalchemy import SQLAlchemy

# Объект орм с ссылкой на базу
db = SQLAlchemy()


# Модель Продуктов, отражает все свойства таблицы
class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String())
    price = db.Column(db.Float)
    stockCount = db.Column(db.Integer)
    publisher = db.Column(db.String())
    product_image = db.Column(db.String())

    # Конструктор класса модели
    def __init__(self, name, price, stock_count, publisher, product_image):
        self.name = name
        self.price = price
        self.stockCount = stock_count
        self.publisher = publisher
        self.product_image = product_image


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin = db.Column(db.Boolean)
    login = db.Column(db.String())
    first_name = db.Column(db.String())
    name = db.Column(db.String())
    password = db.Column(db.String())
    reg_date = db.Column(db.DateTime)

    tokens = db.relationship('Token', backref='tokens')

    def __init__(self, admin, login, first_name, name, password, reg_date):
        self.admin = admin
        self.login = login
        self.first_name = first_name
        self.name = name
        self.password = password
        self.reg_date = reg_date


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address = db.Column(db.String)
    amount = db.Column(db.Float)
    status = db.Column(db.String)
    comment = db.Column(db.String)

    users = db.relationship('User', backref='user')

    def __init__(self, user_id, address, amount, status, comment):
        self.user_id = user_id
        self.address = address
        self.amount = amount
        self.status = status
        self.comment = comment


class OrderProducts(db.Model):
    __tablename__ = 'order_products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    count = db.Column(db.Integer)

    products = db.relationship('Product', backref='product')
    orders = db.relationship('Order', backref='order')

    def __init__(self, product_id, order_id, count):
        self.product_id = product_id
        self.order_id = order_id
        self.count = count


# Вторая временная корзина для хранения выбранных товаров.
class TempCart(db.Model):
    __tablename__ = 'temp_cart'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer)  # ,# db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer)  # , #db.ForeignKey('user.id'))
    count = db.Column(db.Integer)

    def __init__(self, product_id, user_id, count):
        self.product_id = product_id
        self.user_id = user_id
        self.count = count


# Временная таблица для хранения токен-строк, по которым можно получить информацию по аккаунту.
class Token(db.Model):
    __tablename__ = 'token'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String())

    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token