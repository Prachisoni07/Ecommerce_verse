from flask import request, jsonify
from flask_jwt_extended import (
        JWTManager, create_access_token, jwt_required, get_jwt_identity
)
import datetime 
import hashlib 
from .models import User, Product, Order, Cart
from app import db

SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d7e9'

jwt = JWTManager()

def register_routes(app):
    app.config['JWT_SECRET_KEY'] = SECRET_KEY
    jwt.init_app(app)
    
    @app.route('/signin', methods=['POST'])
    def sign_in():
        data = request.get_json()

        password = hashlib.sha256(data['hashed_password'].encode()).hexdigest()

        new_user = User(
            username=data['username'],
            email=data['email'],
            hashed_password=password, 
            role=data['role']
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User created successfully', 'user': {
            'email': new_user.email,
            'username': new_user.username,
            'role': new_user.role
        }}), 201

    @app.route('/login', methods=['POST'])
    def login():
        data= request.get_json()
        username= data['username']
        hashed_password = data['hashed_password']
        user = User.query.filter_by(username = username).first()

        if user and user.hashed_password == hashlib.sha256(hashed_password.encode()).hexdigest():
                acess_token = create_access_token(identity={
                    'username' : user.username,
                    'role' : user.role,
                    'user_id':user.id
                }, expires_delta= datetime.timedelta(hours=1))

                return jsonify({'message': 'Login successful', 'acess_token': acess_token}), 200
        else:
                return jsonify({'message': 'Login unsuccessful', 'role': 'seller'}), 400

  
                
    @app.route('/product', methods=['POST'])
    @jwt_required()
    def create_product():
            current_user = get_jwt_identity()
            user_role = current_user.get('role')
            username = current_user.get('username')
            user= User.query.filter_by(username = username).first()
            
            if user_role != 'seller':
                return jsonify({"error": "Only sellers can create products"}), 403

            # Proceed with product creation
            data = request.get_json()

            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                user_id=user.id,
                stock = data['stock']
            )
            db.session.add(new_product)
            db.session.commit()

            return jsonify({"message": "Product created successfully", "product": {
                "name": new_product.name,
                "description": new_product.description,
                "price": new_product.price, 
                "stock": new_product.stock
            }}), 201


    @app.route('/products', methods=['GET'])
    def get_all_products():
        products = Product.query.all()
        output = []

        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock':product.stock
            }
            output.append(product_data)

        return jsonify({"products": output})

    @app.route('/get_product/<int:product_id>', methods=['GET'])
    
    def get_product(product_id):
        product = Product.query.get_or_404(product_id)

        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock':product.stock
        }

        return jsonify({"product": product_data})
    
    @app.route('/update_product/<int:product_id>', methods=['PUT'])
    @jwt_required()
    def update_product(product_id):
            current_user = get_jwt_identity()
            user_role = current_user.get('role')

            if user_role != 'seller':
                return jsonify({"error": "Only sellers can update products"}), 403

            product = Product.query.get_or_404(product_id)
            data = request.get_json()

            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.price = data.get('price', product.price)
            product.stock = data.get('stock', product.stock)

            db.session.commit()

            return jsonify({"message": "Product updated successfully", "product": {
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock
            }})
        
    @app.route('/delete_product/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def delete_product(product_id):
        current_user = get_jwt_identity()  
        
        # Ensure current_user is a dictionary or has the correct structure
        user_role = current_user.get('role') if isinstance(current_user, dict) else None

        if user_role != 'seller':
            return jsonify({"error": "Only sellers can delete products"}), 403

        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
            
        return jsonify({"message": "Product deleted successfully"})
 
    
    @app.route('/cart', methods = ['POST'])
    @jwt_required()
    def add_to_cart():
            current_user = get_jwt_identity()   
        
            
            user = User.query.filter_by(username = current_user['username']).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity',1)
            
            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404
            
            cart_item = Cart.query.filter_by(buyer_id = user.id, product_id = product.id).first()
            
            if quantity > product.stock: 
                return jsonify({"error": "Not Enough Stock Available"}), 404
            
            if cart_item :
               
                cart_item.quantity += quantity
            else:
                new_cart_item = Cart(
                    buyer_id=user.id,
                    product_id=product.id,
                    quantity=quantity
                )
                db.session.add(new_cart_item)

            db.session.commit()

            return jsonify({"message": "Product added to cart successfully"}), 201

        
        
    @app.route('/get_cart', methods=['GET'])
    @jwt_required()
    def get_cart_items():
            current_user = get_jwt_identity()
            

            user = User.query.filter_by(username=current_user['username']).first()

            if not user:
                return jsonify({"error": "User not found"}), 404

            cart_items = Cart.query.filter_by(buyer_id=user.id).all()

            if not cart_items:
                return jsonify({"message": "Cart is empty"}), 200

            cart = []
            for item in cart_items:
                cart.append({
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price": item.product.price
                })

            return jsonify({"cart": cart})

    @app.route('/remove_item/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def remove_item(product_id):
            current_user = get_jwt_identity()
            user =User.query.get(current_user["user_id"])
            if user.role !='buyer':
                return jsonify({"message": "Access denied: Sellers cannot remove cart items."}), 403
            cart_item = Cart.query.filter_by(buyer_id=user.id, product_id=product_id).first()
            if not cart_item:
                return jsonify({"message": "Product not found in cart."}), 200

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                db.session.commit()
                return jsonify({'message': 'Product quantity decreased by 1', 'quantity': cart_item.quantity}), 200
            else: 
                db.session.delete(cart_item)
                db.session.commit()
                return jsonify({"message: Product removed from cart"})                

    
    @app.route('/place_order', methods =['POST'])
    @jwt_required()
    def place_order_from_card():
        current_user = get_jwt_identity()
        user = User.query.filter_by(username = current_user['username']).first()
        
        cart_items = Cart.query.filter_by(buyer_id =user.id).all()
        
        if not cart_items:
            return jsonify({"error": "your cart is empty"}), 400
        
        total_order_price = 0
        for item in cart_items:
            order = Order(
                buyername = user.username,
                product_id = item.product_id,
                quantity = item.quantity,
                total_price = item.product.price * item.quantity
           )
            db.session.add(order)
            
            for item in cart_items:
                product = item.product
                if product.stock - item.quantity >= 0 :
                    product.stock = product.stock - item.quantity
                else:
                    return jsonify({"error": "Not Enough Stock Available"}), 404
                
            
            total_order_price += order.total_price
            db.session.delete(item)
            
        db.session.commit()
        
        return jsonify({"message": "order placed successfully","total_price": total_order_price}) 
    
           
 
    
    
   