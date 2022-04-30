import json
import os
from datetime import datetime

from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

from marsh_models import *
import secrets

# Создание приложения Flask и указание папки со статичными данными по типу css, js.
app = Flask(__name__, static_folder="static_folder")

# Коннект к нашей базе данных под названием table_games
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:admin@localhost:5432/table_games"
# Отключаем отслеживание изменений базы
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Папка с закачанными файлами
app.config['images'] = 'img/'

# Инициализируем переменную базы данных с помощью нашего приложения и его конфигурации
db.init_app(app)

# Импорт моделей в виде таблиц в нашу базу
migrate = Migrate(app, db)

# Инициализация маршмеллоу
# Маршмеллоу: библиотека для форматирования данных из вида модели в вид JSON
ma.init_app(app)

# Включаем CORS политику для браузеров
CORS(app)


# Пример описания конечного пути, куда можно будет послать запрос (по-простому end-point)
@app.route('/', methods=['GET'])
def main_route():
    return jsonify({"test": "test"})


# End-point для работы с продуктами. В параметрах указаны возможные типа запросов
# здесь можно GET(для получения списка продуктов) и POST (для дальнейшего добавления продуктов)
@app.route('/products', methods=['GET', 'POST', 'PUT'])
def products_route():
    if request.method == 'GET':
        products = Product.query.filter(Product.stockCount > 0).order_by(Product.id).all()

        # ProductJsonSchema - схема преобразования модели в JSON, в качестве
        # параметра передано many=True для обработки нескольких данных
        productSchema = ProductJsonSchema(many=True)

        # Преобразование в JSON необходимо для отправки результата на фронт в текстовом виде
        # с помощью dump происходит преобразование переданных данных
        result = productSchema.dump(products)

        # отправка JSON на фронт
        return jsonify({"products": result})

    if request.method == 'POST':
        # проверка заголовка запроса, в котором должен быть токен для доступа
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})
        # получаем объект токена из базы, чтобы получить идентификатор пользователя
        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            # если токена нет
            return jsonify({"message": "no token", "code": "401"})
        # получаем самого пользователя, чей тоекн
        user: User = User.query.filter(User.id == token.user_id).first()

        if not user.admin:
            # создание товара только для администратора
            return jsonify({"message": "permission denied", "code": "403"})
        # получаем все данные из формы
        name = request.form.get('name')
        price = request.form.get('price')
        stockCount = request.form.get('stockCount')
        publisher = request.form.get('publisher')
        file = request.files.get("product_image", '')
        filename = None

        if file:
            # если в форме есть фотка, то сохраняем ее в статическую папку фотографий
            # и название заносим в базу
            filename = secure_filename(str(datetime.now()) + '-' + file.filename)
            file.save(
                os.path.join(app.root_path, 'static_folder/' + app.config['images'],
                             filename))
        # создаем объект продукта
        product: Product = Product(name, price, stockCount, publisher, filename)
        # добавляем в открытую сессию базы
        db.session.add(product)
        # сохраняем сессию
        db.session.commit()
        return jsonify({"message": "success"})

    # метод для администратора, чтобы добавлять количество товара на складе
    if request.method == 'PUT':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            return jsonify({"message": "no token", "code": "401"})

        data = request.get_json()
        # получаем продукт по идентификатору
        product: Product = Product.query.filter(Product.id == data['product_id']).first()

        if product is None:
            return jsonify({"message": "error", "code": "403"})

        # изменяем данные и сохраняем базу
        product.stockCount += 1
        db.session.commit()

        return jsonify({"message": "success"}), 200


@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    # получение адрес на сервере к картинке по переданному имени файла
    return str(url_for('static', filename=app.config['images'] + filename))


@app.route('/image', methods=['POST'])
def set_image():
    # изменение фотографии у продукта
    if request.method == 'POST':
        product_id = request.form.get("product_id")
        file = request.files.get("product_image", '')
        filename = None

        if file:
            filename = secure_filename(str(datetime.now()) + '-' + file.filename)
            file.save(
                os.path.join(app.root_path, 'static_folder/' + app.config['images'],
                             filename))
            print('upload_image filename: ' + filename)
            product: Product = Product.query.filter(Product.id == product_id).first()
            product.product_image = filename
            db.session.commit()

        return "success"


# получение информации об одном товаре
@app.route('/product/<product_id>', methods=['GET'])
def product_route(product_id):
    if request.method == 'GET':
        product = Product.query.filter(Product.id == product_id).first()

        if product is None:
            return jsonify({"message": "The product not found"}), 404

        productSchema = ProductJsonSchema()
        result = productSchema.dump(product)

        # отправка JSON на фронт
        return jsonify({"product_info": result, "code": "200"})


# End-point логин для авторизации в приложении
@app.route('/login', methods=['POST'])
def login_route():
    if request.method == 'POST':
        body = request.get_json()

        login = body['login']
        password = body['password']

        check_login: User = User.query.filter(User.login == login).first()
        if check_login is None:
            return jsonify({"response": "not authorized", "code": "401"})

        if not password == check_login.password:
            return jsonify({"response": "not authorized", "code": "401"})

        # generate token
        generated_token = secrets.token_urlsafe(24)
        # add token to db
        token_model = Token(check_login.id, generated_token)
        db.session.add(token_model)
        db.session.commit()

        return jsonify({"message": "success", "token": generated_token}), 200


# End-point для выхода из аккаунта
@app.route('/logout', methods=['GET'])
def logout_route():
    if request.method == 'GET':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token_delete = Token.query.filter(Token.token == authorization[7:])
        print(authorization)
        if token_delete.first() is None:
            return jsonify({"message": "error", "code": "403"})

        token_delete.delete()
        db.session.commit()

        return jsonify({'message': "success", "code": "200"})


# End-point registration для регистрации в приложении
@app.route('/registration', methods=['POST'])
def registration_route():
    if request.method == 'POST':
        body = request.get_json()

        first_name = body['firstname']
        name = body['name']
        login = body['login']
        admin = False
        password = body['password']
        reg_date = datetime.now()

        check_login = User.query.filter(User.login == login).first()
        if check_login is not None:
            return jsonify({"message": "The user already exists", "code": "403"})

        user = User(admin, login, first_name, name, password, reg_date)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User was created successfully", "code": "200"})


# End-point order для получения и создания заказа
@app.route('/order', methods=['POST', 'PUT'])
def order_route():
    if request.method == 'POST':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            return jsonify({"message": "no token", "code": "401"})

        data = request.get_json()
        if data is None:
            return jsonify({"message": "error", "code": "403"})

        address = data['address']
        status = "В ожидании"
        comment = data['comment']
        amount = data['amount']
        if data['products'] is None:
            return jsonify({"message": "Order will not be created without products", "code": "403"})

        new_order = Order(token.user_id, address, amount, status, comment)
        db.session.add(new_order)
        db.session.commit()

        order = Order.query.order_by(Order.id.desc()).first()
        products = []

        for product in data['products']:
            products.append(OrderProducts(product['product_id'], order.id, product['count']))
        db.session.add_all(products)

        TempCart.query.filter(TempCart.user_id == token.user_id).delete()
        db.session.commit()

        return jsonify({"message": "success"}), 200

    if request.method == 'PUT':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            return jsonify({"message": "no token", "code": "401"})

        data = request.get_json()
        if data['order_id'] is None or data['status'] is None:
            return jsonify({"message": "error", "code": "403"})

        order = Order.query.filter(Order.id == data['order_id']).first()
        if order is None:
            return jsonify({"message": "error", "code": "403"})

        order.status = data['status']
        db.session.commit()

        return jsonify({"message": "success"}), 200


# End-point cart для получения и создания заказа
@app.route('/cart', methods=['GET', 'POST'])
def cart_route():
    if request.method == 'GET':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        user: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if user is None:
            return jsonify({"message": "no token", "code": "401"})

        result = db.session.execute(
            'select tc.id, tc.product_id, tc.count, p.name, p.product_image, p.price, p."stockCount" '
            'from temp_cart as "tc" left join product as "p" '
            'on p.id = tc.product_id where tc.user_id = :val '
            'order by tc.id', {'val': user.user_id}).fetchall()

        return jsonify({"products_cart": [dict(row) for row in result]})

    if request.method == 'POST':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        user: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if user is None:
            return jsonify({"message": "no token", "code": "401"})

        body = request.get_json()

        if body is None:
            return jsonify({"message": "Body is null", "code": "403"})

        # данные из формы
        product_id = body['product_id']
        count = body['count']

        search_temp_cart: TempCart = TempCart.query.filter(
            TempCart.product_id == product_id and TempCart.user_id == user.user_id)

        if search_temp_cart.first() is None:
            # создание новой модели
            temp_cart_item = TempCart(product_id, user.user_id, count)
            db.session.add(temp_cart_item)
        elif search_temp_cart.first().count + count == 0:
            search_temp_cart.delete()
        else:
            # изменение существующей модели
            search_temp_cart.first().count += count

        product: Product = Product.query.filter(Product.id == product_id).first()
        product.stockCount -= count
        db.session.commit()

        return "success"


@app.route('/profile', methods=['GET', 'POST'])
def profile_route():
    # получение сведений о профиле и своих заказах
    if request.method == 'GET':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            return jsonify({"message": "no token", "code": "401"})

        user: User = User.query.filter(User.id == token.user_id).first()
        userJson = UserJsonSchema()
        result_user = userJson.dump(user)

        del result_user['id']
        del result_user['password']

        # order_by это функция ORM для сортировки записей по переданному полю
        query_orders: Order = Order.query.filter(Order.user_id == token.user_id)\
            .order_by(Order.id)\
            .all()
        if query_orders is None:
            return jsonify({"message": "no orders"})
        orderJson = OrderJsonSchema(many=True)
        orders = orderJson.dump(query_orders)

        result = []
        for order in orders:
            # ORM не подходит для таких сложных запросов, поэтому проще самому писать
            # sql запросы и выполнять их через базу
            query = db.session.execute(
                'select p.id, p.name as "product_name", '
                'p.product_image, op.count as "product_count", p.price as "product_price" '
                'from order_products as "op" inner join product as "p" on p.id = op.product_id '
                'where op.order_id = :val '
                'group by p.name, p.id, p.product_image, p.price, op.count', {'val': order['id']}).fetchall()
            order.update({"products": [dict(row) for row in query]})
            result.append(order)

        return jsonify({"profile": result_user, "orders": result})

    # измнение своего профиля
    if request.method == 'POST':
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return jsonify({"message": "no token", "code": "401"})

        token: Token = Token.query.filter(Token.token == authorization[7:]).first()
        if token is None:
            return jsonify({"message": "no token", "code": "401"})

        body = request.get_json()

        if body is None:
            return jsonify({"message": "Body is null", "code": "403"})

        # данные из формы
        first_name = body['first_name']
        name = body['name']

        user: User = User.query.filter(User.id == token.user_id).first()
        user.first_name = first_name
        user.name = name
        db.session.commit()

        return jsonify({"message": "success"})


# End-point для поиска
@app.route('/search', methods=['POST'])
def search_product():
    if request.method == 'POST':
        body = request.get_json()

        if body is None:
            return jsonify({"message": "Body is null", "code": "403"})

        # получаем слово поиска
        tag = body['tag']

        # формируем строку для поиска
        search = "%{}%".format(tag)
        # поиск всех продуктов, которые подходят по наименованию под переданные текст,
        # вне зависимости от регистра
        products = Product.query.filter(Product.name.ilike(search)).all()
        productSchema = ProductJsonSchema(many=True)

        # Преобразование в JSON необходимо для отправки результата на фронт в текстовом виде
        # с помощью dump происходит преобразование переданных данных
        result = productSchema.dump(products)

        # отправка JSON на фронт
        return jsonify({"products": result})


# End-point для получения заказов админу
@app.route('/admin/orders', methods=['GET'])
def admin_orders_route():
    if request.method == 'GET':
        query_orders: Order = Order.query\
            .order_by(Order.id)\
            .all()

        orderJson = OrderJsonSchema(many=True)
        orders = orderJson.dump(query_orders)

        result = []
        # также собственный сложный для ORM sql запрос
        for order in orders:
            query = db.session.execute(
                'select p.id, p.name as "product_name", '
                'p.product_image, op.count as "product_count", p.price as "product_price", '
                'concat(u.first_name, \' \', u.name) as "user" '
                'from order_products as "op" '
                'inner join product as "p" '
                'on p.id = op.product_id '
                'inner join "order" as "o" '
                'inner join "user" as "u" on u.id = o.user_id '
                'on o.id = op.product_id '
                'where op.order_id = :val '
                'group by p.name, p.id, p.product_image, p.price, op.count, '
                'u.first_name, u.name', {'val': order['id']}).fetchall()
            order.update({"products": [dict(row) for row in query]})
            result.append(order)

        return jsonify({"orders": result})


if __name__ == '__main__':
    app.run(debug=True)
