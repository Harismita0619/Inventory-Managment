from flask import Flask, render_template,request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)

# DB model
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    movements = db.relationship('ProductMovement', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.product_id}>'

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)

    def __repr__(self):
        return f'<Location {self.location_id}>'

class ProductMovement(db.Model):
    movement_id   = db.Column(db.String(50), primary_key=True)
    timestamp     = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    to_location   = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    product_id    = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    qty           = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Movement {self.movement_id}>'

# helper
def compute_balance():
    balance = {}   # key: (product_id, location_id) → qty

    movements = ProductMovement.query.order_by(ProductMovement.timestamp).all()
    for m in movements:
        if m.to_location:
            key = (m.product_id, m.to_location)
            balance[key] = balance.get(key, 0) + m.qty
        if m.from_location:
            key = (m.product_id, m.from_location)
            balance[key] = balance.get(key, 0) - m.qty

    result = [
        {'product': p, 'location': l, 'qty': q}
        for (p, l), q in balance.items()
        if q != 0
    ]
    result.sort(key=lambda x: (x['product'], x['location']))
    return result

# Dashboard    
@app.route('/')
def index():
    return render_template('index.html',
    product_count=Product.query.count(),
    location_count=Location.query.count(),
    movement_count=ProductMovement.query.count()
    )

# Product Features
@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

# Product Add Feature
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        pid = request.form['product_id'].strip()
        if not pid:
            flash('Product ID cannot be empty.', 'error')
        elif Product.query.get(pid):
            flash(f'Product "{pid}" already exists.', 'error')
        else:
            db.session.add(Product(product_id=pid))
            db.session.commit()
            flash(f'Product "{pid}" added successfully!', 'success')
            return redirect(url_for('products'))
    return render_template('product_form.html', action='Add', product=None)

# Product Edit Features
@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        new_id = request.form['product_id'].strip()
        if not new_id:
            flash('Product ID cannot be empty.', 'error')
        elif new_id != product_id and Product.query.get(new_id):
            flash(f'Product "{new_id}" already exists.', 'error')
        else:
            if new_id != product_id:
                ProductMovement.query.filter_by(product_id=product_id).update({'product_id': new_id})
                db.session.delete(product)
                db.session.flush()
                db.session.add(Product(product_id=new_id))
            db.session.commit()
            flash('Product updated!', 'success')
            return redirect(url_for('products'))
    return render_template('product_form.html', action='Edit', product=product)

# Product Delete Features
@app.route('/products/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product_id}" deleted.', 'success')
    return redirect(url_for('products'))

# Location Features
@app.route('/locations')
def locations():
    all_locations = Location.query.all()
    return render_template('locations.html', locations=all_locations)

# Location Add Features
@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        lid = request.form['location_id'].strip()
        if not lid:
            flash('Location ID cannot be empty.', 'error')
        elif Location.query.get(lid):
            flash(f'Location "{lid}" already exists.', 'error')
        else:
            db.session.add(Location(location_id=lid))
            db.session.commit()
            flash(f'Location "{lid}" added successfully!', 'success')
            return redirect(url_for('locations'))
    return render_template('location_form.html', action='Add', location=None)

# Location Edit Features
@app.route('/locations/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        new_id = request.form['location_id'].strip()
        if not new_id:
            flash('Location ID cannot be empty.', 'error')
        elif new_id != location_id and Location.query.get(new_id):
            flash(f'Location "{new_id}" already exists.', 'error')
        else:
            if new_id != location_id:
                ProductMovement.query.filter_by(from_location=location_id).update({'from_location': new_id})
                ProductMovement.query.filter_by(to_location=location_id).update({'to_location': new_id})
                db.session.delete(location)
                db.session.flush()
                db.session.add(Location(location_id=new_id))
            db.session.commit()
            flash('Location updated!', 'success')
            return redirect(url_for('locations'))
    return render_template('location_form.html', action='Edit', location=location)

# Location Delete Features
@app.route('/locations/delete/<location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    db.session.delete(location)
    db.session.commit()
    flash(f'Location "{location_id}" deleted.', 'success')
    return redirect(url_for('locations'))

# Movements feature
@app.route('/movements')
def movements():
    all_movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    return render_template('movements.html', movements=all_movements)

# Movements Add Feature
@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    products  = Product.query.all()
    locs      = Location.query.all()
    if request.method == 'POST':
        mid      = request.form['movement_id'].strip()
        pid      = request.form['product_id']
        from_loc = request.form.get('from_location', '').strip() or None
        to_loc   = request.form.get('to_location', '').strip() or None
        qty      = request.form['qty']

        if not mid:
            flash('Movement ID cannot be empty.', 'error')
        elif ProductMovement.query.get(mid):
            flash(f'Movement ID "{mid}" already exists.', 'error')
        elif not from_loc and not to_loc:
            flash('At least one of From Location or To Location must be filled.', 'error')
        else:
            try:
                qty = int(qty)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                flash('Quantity must be a positive integer.', 'error')
            else:
                movement = ProductMovement(
                    movement_id=mid,
                    product_id=pid,
                    from_location=from_loc,
                    to_location=to_loc,
                    qty=qty
                )
                db.session.add(movement)
                db.session.commit()
                flash('Movement recorded!', 'success')
                return redirect(url_for('movements'))

    return render_template('movement_form.html', action='Add', movement=None,
                           products=products, locations=locs)

# Movement edit feature
@app.route('/movements/edit/<movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    products = Product.query.all()
    locs     = Location.query.all()
    if request.method == 'POST':
        from_loc = request.form.get('from_location', '').strip() or None
        to_loc   = request.form.get('to_location', '').strip() or None
        qty      = request.form['qty']

        if not from_loc and not to_loc:
            flash('At least one of From Location or To Location must be filled.', 'error')
        else:
            try:
                qty = int(qty)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                flash('Quantity must be a positive integer.', 'error')
            else:
                movement.product_id    = request.form['product_id']
                movement.from_location = from_loc
                movement.to_location   = to_loc
                movement.qty           = qty
                db.session.commit()
                flash('Movement updated!', 'success')
                return redirect(url_for('movements'))

    return render_template('movement_form.html', action='Edit', movement=movement,
                           products=products, locations=locs)

# Movement delete Feature
@app.route('/movements/delete/<movement_id>', methods=['POST'])
def delete_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    db.session.delete(movement)
    db.session.commit()
    flash('Movement deleted.', 'success')
    return redirect(url_for('movements'))

# Report Module
@app.route('/report')
def report():
    balance = compute_balance()
    return render_template('report.html', balance=balance)

# Seed Data
@app.route('/seed')
def seed():
    for p in ['ProductA', 'ProductB', 'ProductC', 'ProductD']:
        if not Product.query.get(p):
            db.session.add(Product(product_id=p))

    for l in ['LocationX', 'LocationY', 'LocationZ', 'LocationW']:
        if not Location.query.get(l):
            db.session.add(Location(location_id=l))

    db.session.commit()

    import random, uuid
    products  = ['ProductA', 'ProductB', 'ProductC', 'ProductD']
    locations = ['LocationX', 'LocationY', 'LocationZ', 'LocationW']

    movements = [
        ('ProductA', None, 'LocationX', 50),
        ('ProductB', None, 'LocationX', 40),
        ('ProductC', None, 'LocationY', 30),
        ('ProductD', None, 'LocationZ', 25),
        ('ProductA', 'LocationX', 'LocationY', 20),
        ('ProductB', 'LocationX', 'LocationZ', 15),
        ('ProductA', None, 'LocationW', 60),
        ('ProductB', None, 'LocationW', 35),
        ('ProductC', None, 'LocationX', 45),
        ('ProductD', None, 'LocationY', 20),
        ('ProductA', 'LocationY', 'LocationZ', 10),
        ('ProductB', 'LocationZ', 'LocationY', 5),
        ('ProductC', 'LocationX', 'LocationW', 15),
        ('ProductD', 'LocationZ', 'LocationX', 10),
        ('ProductA', 'LocationW', 'LocationX', 25),
        ('ProductB', 'LocationW', 'LocationY', 20),
        ('ProductC', 'LocationW', None, 5),
        ('ProductD', 'LocationX', None, 8),
        ('ProductA', 'LocationX', 'LocationY', 12),
        ('ProductB', 'LocationY', 'LocationZ', 10),
    ]

    for i, (pid, frm, to, qty) in enumerate(movements):
        mid = f'MOV{i+1:03}'
        if not ProductMovement.query.get(mid):
            db.session.add(ProductMovement(
                movement_id=mid,
                product_id=pid,
                from_location=frm,
                to_location=to,
                qty=qty
            ))

    db.session.commit()
    flash(' Sample data seeded successfully!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)