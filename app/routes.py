from flask import request, jsonify
import jwt
import datetime
import hashlib 
from .models import User, Product
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
                user_role=user_role
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
    
    @app.route('/product/<int:product_id>', methods=['PUT'])
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