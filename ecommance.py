import os
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
db = SQLAlchemy()


# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///product.db'



app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['JWT_SECRET_KEY'] = 'my_ecommance_key'


db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    cart = db.relationship('Cart')


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship('Products')


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not email or not password:
        return jsonify({'Error': 'email and password is required'}), 401
    elif len(password) < 4 or len(email) < 4:
        return jsonify({'Error': 'password and email should be greater than 3'}), 401
    elif user:
        return jsonify({'Error': 'Email already existed'}), 401


    hashed_password = bcrypt.generate_password_hash(password)

    user = User(name=name, email=email, password=hashed_password)

    db.session.add(user)
    db.session.commit()

    return jsonify({'Message': 'User created successfully'})


@app.route('/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user_id': user.id
        }), 200
    
    return jsonify({'Error': 'Invalid password and email, try again or create an account'}), 401
        

    

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()

    if not users:
        return jsonify({'Error': 'No user accounts yet, create one'})

    display_users = []
    for user in users:
        display_users.append(
            {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        )
    return jsonify(display_users)



@app.route('/products', methods=['GET'])
def get_product():
    products = Products.query.all()

    products_list = []
    if products:    
        for product in products:
            products_list.append(
                {
                    'id': product.id, 
                    'name': product.name, 
                    'price': product.price
                }
            )
        return jsonify(products_list)
    return jsonify({'error': 'No product was found'})


@app.route('/products/<int:id>', methods=['GET'])
def get_a_products(id):
    product = Products.query.filter_by(id=id).first()

    if product:
        return jsonify(
            {
                'id': product.id, 
                'name': product.name, 
                'price': product.price
            }
        )

    return jsonify({'Error': 'Product Id was not found'})


@app.route('/products', methods=['POST'])
def create_products():
    data = request.get_json()
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({'error': 'Missing name or price data'})

    name = data['name']
    price = data['price']

    products = Products(name=name, price=price)

    try:
        db.session.add(products)
        db.session.commit()

        return jsonify({
            'message': 'Product created successfully', 
            'id': products.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Eje Product creation failed. Name don already exist.'}), 400


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Products.query.filter_by(id=id).first()
    data = request.get_json()

    if not product:
        return jsonify({'Error': 'Oga Product Id is not found'})

    name = data['name']
    price = data['price']
    if name:
        product.name = name

    if price:
        product.price = price

    update = jsonify(
        {
            'id': product.id,
            'name': product.name,
            'price': product.price
        }
    )

    db.session.commit()

    return update
        




@app.route('/products/<int:id>', methods=['DELETE'])
def delete_products(id):
    product = Products.query.filter_by(id=id).first()

    if not product:
        return jsonify({'Error': 'Eje Product Id was not found'})

    db.session.delete(product)
    db.session.commit()

    return jsonify({'Success': 'Product deleted successfully'})



# Cart
@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart_item():
    user_id = int(get_jwt_identity())

    carts = Cart.query.filter_by(user_id=user_id).all()

    grand_total = 0
    cart_items = []
    for cart in carts:

        subtotal = cart.product.price * cart.quantity
        grand_total += subtotal

        
        cart_items.append(
            {
                'cart_id': cart.cart_id,
                'product_id': cart.product.id,
                'product_name': cart.product.name,
                'product_price': cart.product.price,
                'quantity': cart.quantity,
                'subtotal': subtotal

            }
        )

    return jsonify(
        {
            'cart': cart_items,
            'grand_total': grand_total
        }
    )

@app.route('/cart/<int:id>', methods=['GET'])
@jwt_required()
def get_a_cart(id):
    user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(cart_id=id, user_id=user_id).first()

    if not cart:
        return jsonify({'Error': 'No cart Id was found'})

    subtotal = cart.product.price * cart.quantity
    return jsonify(
                {
                    'cart_id': cart.cart_id,
                    'product_name': cart.product.name,
                    'cart_price': cart.product.price,
                    'quantity': cart.quantity,
                    'cart_subtotal': subtotal
                }
            ) 


@app.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        return jsonify({'Error': 'Quantity must be positive'}), 400

    

    product = db.session.get(Products, product_id)

    if not product:
        return jsonify({'Error': 'Product does not exist'}), 404

    existing_product = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing_product:
        existing_product.quantity += quantity
    else:
        carts = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(carts)
    
    db.session.commit()
    return jsonify({'success': 'Item successfully added to cart'})




if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000)