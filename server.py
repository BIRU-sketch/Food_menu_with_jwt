from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.jinja_env.filters['from_json'] = json.loads


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100), nullable=False, default='Guest')
    items = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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


@app.route('/')
def home():
    return render_template('index.html')


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
