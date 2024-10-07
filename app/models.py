
from datetime import datetime 
from app import db

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True,index = True)  
    username = db.Column(db.String(80),unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)  
    hashed_password = db.Column(db.String(128), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  
    role = db.Column(db.String(10)) 

    __table_args__ = (
        db.CheckConstraint("role IN ('seller', 'buyer')", name='check_role_valid'),
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True,index = True) 
    name = db.Column(db.String(80), nullable = False)
    description = db.Column(db.String(120),nullable =False)
    price = db.Column(db.Integer,nullable = False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock = db.Column(db.Integer,nullable = True)
    
    
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyername = db.Column(db.String, db.ForeignKey('user.username'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f"<Order {self.id}>"


class Cart(db.Model):
    __tablename__  = "cart"
    
    id = db.Column(db.Integer, primary_key = True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False)
    quantity = db.Column(db.Integer, nullable = False, default = 1)
    added_at = db.Column(db.DateTime, default = datetime.utcnow)
    user = db.relationship('User', backref = 'cart_items')
    product = db.relationship('Product', backref = 'cart_item')
    
    def __repr__(self):
        return f"<Cart {self.id}, User {self.buyer_id}, Product {self.product_id}>"   