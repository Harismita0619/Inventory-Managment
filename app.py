from flask import Flask, render_template,request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)

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

@app.route('/')
def index():
    return render_template('index.html',
    product_count=Product.query.count())

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

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


@app.route('/products/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product_id}" deleted.', 'success')
    return redirect(url_for('products'))


@app.route('/location')
def locations():
    return render_template('locations.html')

@app.route('/movements')
def movements():
    return render_template('movements.html')

@app.route('/report')
def report():
    return render_template('report.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)