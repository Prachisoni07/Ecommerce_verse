from flask import request, jsonify
import jwt
import datetime 
import hashlib 
from .models import User, Product, Order, Cart
from app import db

SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d7e9'

def register_routes(app):
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
        user = User.query.filter((User.username == username)).one()

        if user and user.hashed_password == hashlib.sha256(hashed_password.encode()).hexdigest():
                token = jwt.encode({
                    'username' : user.username,
                    'role' : user.role,
                    "exp" : datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                },SECRET_KEY, algorithm='HS256')

                return jsonify({'message': 'Login successful', 'token': token}), 200
        else:
                return jsonify({'message': 'Login unsuccessful', 'role': 'seller'}), 400

  
                
    @app.route('/product', methods=['POST'])
    def create_product():
      
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1] 
            else:
                return jsonify({"error": "Invalid token format"}), 401

            print(f"Extracted Token: {token}") 

           
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # print(f"Decoded Token: {decoded_token}")  

            user_role = decoded_token.get('role')
            username = decoded_token.get('username')
            user= User.query.filter(username == User.username).first()
            if not user_role:
                return jsonify({"error": "Token doesn't contain user_role"}), 403

            # Check if the user is a seller
            if user_role != 'seller':
                return jsonify({"error": "Only sellers can create products"}), 403

            # Proceed with product creation
            data = request.get_json()

            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                user_id=user.id
            )
            db.session.add(new_product)
            db.session.commit()

            return jsonify({"message": "Product created successfully", "product": {
                "name": new_product.name,
                "description": new_product.description,
                "price": new_product.price
            }}), 201

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            print(f"JWT Decode Error: {str(e)}")
            return jsonify({"error": "Invalid token"}), 401
        except IndexError:
            return jsonify({"error": "Bearer token is not provided properly"}), 401



    @app.route('/products', methods=['GET'])
    def get_all_products():
        products = Product.query.all()
        output = []

        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price
            }
            output.append(product_data)

        return jsonify({"products": output})

    @app.route('/product/<int:product_id>', methods=['GET'])
    
    def get_product(product_id):
        product = Product.query.get_or_404(product_id)

        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price
        }

        return jsonify({"product": product_data})
    
    @app.route('/update_product/<int:product_id>', methods=['PUT'])
    def update_product(product_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            else:
                return jsonify({"error": "Invalid token format"}), 401

            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_role = decoded_token.get('role')

            if user_role != 'seller':
                return jsonify({"error": "Only sellers can update products"}), 403

            product = Product.query.get_or_404(product_id)
            data = request.get_json()

            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.price = data.get('price', product.price)

            db.session.commit()

            return jsonify({"message": "Product updated successfully", "product": {
                "name": product.name,
                "description": product.description,
                "price": product.price
            }})

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": "Invalid token"}), 401
        
    @app.route('/delete_product/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        token = request.headers.get('Authorization')
        if not token:
                return jsonify({"error": "Token is missing"}), 401

        try:
                if token.startswith("Bearer "):
                    token = token.split(" ")[1]
                else:
                    return jsonify({"error": "Invalid token format"}), 401

                decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_role = decoded_token.get('role')

                if user_role != 'seller':
                    return jsonify({"error": "Only sellers can delete products"}), 403

                product = Product.query.get_or_404(product_id )
                db.session.delete(product)
                db.session.commit()

                return jsonify({"message": "Product deleted successfully"})

        except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
                return jsonify({"error": "Invalid token"}), 401
            
            
    
    @app.route('/cart', methods = ['POST'])
    def add_to_cart():
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            else:
                return jsonify({"error": "Invalid token format"}), 401
            
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_name =  decoded_token.get('username')
            print(user_name,"dcfvgbhjxdcfgvhbj")
            user = User.query.filter_by(username = user_name).first()
            print(user,"xdctfgvhbjnkmdfgcvh")
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity',1)
            
            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404
            
            cart_item = Cart.query.filter_by(buyer_id = user.id, product_id = product.id).first()
            
            if cart_item:
            # If the product is already in the cart, increase the quantity
                cart_item.quantity += quantity
            else:
            # If not, create a new cart item
                new_cart_item = Cart(
                    buyer_id=user.id,
                    product_id=product.id,
                    quantity=quantity
                )
                db.session.add(new_cart_item)

            db.session.commit()

            return jsonify({"message": "Product added to cart successfully"}), 201

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401         
        
        
        
    @app.route('/get_cart', methods=['GET'])
    def get_cart_items():
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            else:
                return jsonify({"error": "Invalid token format"}), 401

            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = decoded_token.get('username')

            user = User.query.filter_by(username=username).first()

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

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
                    
            
    # @app.route('/place_order', methods=['POST'])
    # def place_order():
    #     token = request.headers.get('Authorization')

    #     if not token:
    #         return jsonify({"error": "Token is missing"}), 401

    #     try:
    #         if token.startswith("Bearer "):
    #             token = token.split(" ")[1]
    #         else:
    #             return jsonify({"error": "Invalid token format"}), 401

    #         decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #         user_role = decoded_token.get('role')
    #         username = decoded_token.get('username') 
            
    #         if user_role != 'buyer':
    #             return jsonify({"error": "Only buyers can place orders"}), 403
    #         user=User.query.filter(username == User.username).first()
            
    #         data = request.get_json()
    #         product_id = data.get('product_id')
    #         quantity = data.get('quantity')

    #         product = Product.query.filter(product_id == Product.id ).first()
    #         if not product:
    #             return jsonify({"error": "Product not found"}), 404

    #         new_order = Order(
    #             product_id=product.id,
    #             buyername=username,
    #             quantity=quantity,
    #             order_date=datetime.datetime.utcnow(),
    #             status="pending"
    #         )
    #         print(new_order.product_id,"aghlkhgfdssdfghjhgfdsdfghjj")
    #         db.session.add(new_order)
    #         db.session.commit()

    #         return jsonify({
    #             "message": "Order placed successfully",
    #             "order": {
    #                 "id": new_order.id,
    #                 "product_name": product.name,
    #                 "quantity": new_order.quantity,
    #                 "status": new_order.status,
    #                 "order_date": new_order.order_date
    #             }
    #         }), 201

    #     except jwt.ExpiredSignatureError:
    #         return jsonify({"error": "Token has expired"}), 401
    #     except jwt.InvalidTokenError:
    #         return jsonify({"error": "Invalid token"}), 401
    
    
    
    # @app.route('/seller_orders', methods=['GET'])
    # def get_seller_order_history():
    #     print("headers:",request.headers)
    #     token = request.headers.get('Authorization')

    #     if not token:
    #         return jsonify({"error": "Token is missing"}), 401

    #     try:
    #         if token.startswith("Bearer "):
    #             token = token.split(" ")[1]
    #         else:
    #             return jsonify({"error": "Invalid token format"}), 401

    #         decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #         user_role = decoded_token.get('role')
    #         username = decoded_token.get('username')

    #         # Ensure the user is a seller
    #         if user_role != 'seller':
    #             return jsonify({"error": "Only sellers can view order history"}), 403

    #         # Get the seller (user) and their products
    #         seller = User.query.filter_by(username=username).first()
    #         if not seller:
    #             return jsonify({"error": "Seller not found"}), 404

    #         # Get all products for this seller
    #         seller_products = Product.query.filter_by(seller_id=seller.id).all()  # Assuming there's a `seller_id` field in Product
    #         if not seller_products:
    #             return jsonify({"message": "No products found for this seller"}), 404

    #         # Get all orders for seller's products
    #         product_ids = [product.id for product in seller_products]
    #         orders = Order.query.filter(Order.product_id.in_(product_ids)).all()

    #         # Prepare the order history response
    #         order_history = []
    #         for order in orders:
    #             product = Product.query.get(order.product_id)
    #             order_data = {
    #                 'order_id': order.id,
    #                 'product_name': product.name,
    #                 'buyer': order.buyernamed,
    #                 'quantity': order.quantity,
    #                 'order_date': order.order_date,
    #                 'status': order.status
    #             }
    #             order_history.append(order_data)

    #         return jsonify({"orders": order_history}), 200

    #     except jwt.ExpiredSignatureError:
    #         return jsonify({"error": "Token has expired"}), 401
    #     except jwt.InvalidTokenError:
    #         return jsonify({"error": "Invalid token"}), 401
    #     except Exception as e:
    #         return jsonify({"error": str(e)}), 500
