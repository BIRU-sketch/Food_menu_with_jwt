from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import jwt
from dotenv import load_dotenv
import os
from datetime import datetime,timezone,timedelta

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
secret_key=os.getenv("SECRET_KEY")
admin_username=os.getenv("ADMIN_USERNAME")
admin_password=os.getenv("ADMIN_PASSWORD")
id = os.getenv("ID")
db = SQLAlchemy(app)
app.jinja_env.filters['from_json'] = json.loads

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100), nullable=False, default='Guest')
    items = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='Pending')

    def to_dict(self):
        return {
            'id': self.id,
            'customer': self.customer,
            'items': json.loads(self.items),
            'quantity': self.quantity,
            'total_price': self.total_price,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }


with app.app_context():
    db.create_all()


def load_menu():
    with open('menu.json', 'r') as f:
        return json.load(f)


def admin_login_redirect():
    response = jsonify({
        'error': 'Expired Token',
        'redirect': url_for('login')
    })
    response.delete_cookie('admin_token')
    return response, 401


def get_admin_payload():
    token = request.headers.get('Authorization') or request.cookies.get('admin_token')
    if token and token.startswith('Bearer '):
        token = token[7:]

    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return "Expired"
    except jwt.InvalidTokenError:
        return "Invalid"
    

    if payload.get('name') != admin_username or payload.get('sub') != id or payload.get('role') != 'admin':
        return "Invalid"

    return payload


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method =='POST':
        data=request.get_json()
        name=data.get('name')
        password=data.get('password')
        if name==admin_username and password==admin_password:
            payload={
                "name":name,
                "sub":id,
                "role":"admin",
                "iat":datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc)+timedelta(minutes=30)
            }
            token=jwt.encode(payload,secret_key,algorithm='HS256')
            response = jsonify({'token': token})
            response.set_cookie(
                'admin_token', token, max_age=30 * 60,
                httponly=True, samesite='Lax'
            )
            return response, 200
        else:
            return jsonify({"status":"error"}),401
    return render_template('login.html')
@app.route('/menu', methods=['GET'])
def menu():
    return jsonify(load_menu())


@app.route('/order', methods=['POST'])
def place_order():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Order must contain at least one item.'}), 400

    menu = load_menu()
    order_items = []
    total = 0
    total_qty = 0

    for item in data:
        name = item.get('name')
        qty = item.get('quantity')

        if name not in menu:
            return jsonify({'error': 'Unknown item: ' + str(name)}), 400

        price = menu[name]['price']
        subtotal = price * qty
        total += subtotal
        total_qty += qty

        order_items.append({
            'name': name,
            'quantity': qty,
            'price': price,
            'subtotal': subtotal
        })

    new_order = Order(
        customer='Guest',
        items=json.dumps(order_items),
        quantity=total_qty,
        total_price=total,
        status='Pending'
    )
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'message': 'Order saved!', 'order': new_order.to_dict()}), 201


@app.route('/orders', methods=['GET'])
def orders():
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in all_orders])


@app.route('/admin/orders', methods=['GET', 'POST'])
def admin_orders():
    admin_payload = get_admin_payload()
    if admin_payload == "Expired":
        return admin_login_redirect()
    elif admin_payload == "Invalid":
        return "Unauthorized", 403
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        action = request.form.get('action')
        target = Order.query.get(order_id)

        if target:
            if action == 'cancel':
                target.status = 'Cancelled'
                db.session.commit()
            elif action == 'delete':
                db.session.delete(target)
                db.session.commit()

        return redirect(url_for('admin_orders'))

    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=all_orders)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    admin_payload = get_admin_payload()
    if admin_payload == "Expired":
        return admin_login_redirect()
    elif admin_payload == "Invalid":
        return "Unauthorized", 403
    if request.method == 'POST':
        customer = request.form.get('customer') or 'Guest'
        food_name = request.form.get('food_name')
        quantity = int(request.form.get('quantity') or 1)
        total_price = float(request.form.get('total_price') or 0)
        items = [{
            'name': food_name,
            'quantity': quantity,
            'price': total_price / quantity if quantity else total_price,
            'subtotal': total_price
        }]
        new_order = Order(
            customer=customer,
            items=json.dumps(items),
            quantity=quantity,
            total_price=total_price,
            status='Pending'
        )
        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for('admin_orders'))

    menu = load_menu()
    return render_template('admin_add.html', menu=menu)


if __name__ == "__main__":
    app.run(debug=True)