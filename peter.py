from flask import Flask, render_template, request, redirect, url_for, flash, session , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from functools import wraps
from flask import abort
from flask_login import current_user
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Add this line

    def _init_(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.is_admin = False  # By default, users are not admins

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password,password)

# Ensure this runs once, e.g., when you first set up the application
with app.app_context():
    db.create_all()

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/')
def home():
    name = session.get('name')
    # Assuming you have a list of watches to display on the homepage
    watches = [
        {'id': 1, 'name': 'Watch 1', 'price': 100},
        {'id': 2, 'name': 'Watch 2', 'price': 200},
        # Add more watches as needed
    ]
    return render_template('index.html', name=name, watches=watches)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {e}', 'danger')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            session['email'] = user.email
            session['name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html', user=user)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/make_admin/<string:email>')
def make_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        flash(f'{email} has been granted admin rights.', 'success')
    else:
        flash(f'User with email {email} not found.', 'danger')
    return redirect(url_for('home'))


categories = {
    'Gant': [
        {'model': 'Gant Watch Model 1', 'price': '$200', 'image': 'watches/gantwatch1.jpg'},
        {'model': 'Gant Watch Model 2', 'price': '$250', 'image': 'watches/gantwatch2.jpg'},
        {'model': 'Gant Watch Model 3', 'price': '$220', 'image': 'watches/gantwatch3.jpg'},
        {'model': 'Gant Watch Model 4', 'price': '$270', 'image': 'watches/gantwatch4.jpg'},
        {'model': 'Gant Watch Model 5', 'price': '$230', 'image': 'watches/gantwatch5.jpg'},
        {'model': 'Gant Watch Model 6', 'price': '$280', 'image': 'watches/gantwatch6.jpg'},
    ],
    'Boss': [
        {'model': 'Boss Watch Model 1', 'price': '$300', 'image': 'watches/bosswatch.jpg'},
        {'model': 'Boss Watch Model 2', 'price': '$350', 'image': 'watches/bosswatch2.jpg'},
        {'model': 'Boss Watch Model 3', 'price': '$310', 'image': 'watches/bosswatch3.jpg'},
        {'model': 'Boss Watch Model 4', 'price': '$360', 'image': 'watches/bosswatch4.jpg'},
        {'model': 'Boss Watch Model 5', 'price': '$320', 'image': 'watches/bosswatch5.jpg'},
        {'model': 'Boss Watch Model 6', 'price': '$370', 'image': 'watches/bosswatch6.jpg'},
    ],
    'AP': [
        {'model': 'AP Watch Model 1', 'price': '$500', 'image': 'watches/apwatch1.jpg'},
        {'model': 'AP Watch Model 2', 'price': '$550', 'image': 'watches/apwatch2.jpg'},
        {'model': 'AP Watch Model 3', 'price': '$520', 'image': 'watches/apwatch3.jpg'},
        {'model': 'AP Watch Model 4', 'price': '$570', 'image': 'watches/apwatch4.jpg'},
        {'model': 'AP Watch Model 5', 'price': '$530', 'image': 'watches/apwatch5.jpg'},
        {'model': 'AP Watch Model 6', 'price': '$580', 'image': 'watches/apwatch6.jpg'},
    ],
    'Rolex': [
        {'model': 'Rolex Watch model 1 ', 'price': '$1000', 'image': 'watches/rolexwatch1.jpg'},
        {'model': 'Rolex Watch Model 2', 'price': '$1050', 'image': 'watches/rolexwatch2.jpg'},
        {'model': 'Rolex Watch Model 3', 'price': '$1020', 'image': 'watches/rolexwatch3.jpg'},
        {'model': 'Rolex Watch Model 4', 'price': '$1070', 'image': 'watches/rolexwatch4.jpg'},
        {'model': 'Rolex Watch Model 5', 'price': '$1030', 'image': 'watches/rolexwatch5.jpg'},
        {'model': 'Rolex Watch Model 6', 'price': '$1080', 'image': 'watches/rolexwatch6.jpg'},
    ],
    'Hublot': [
        {'model': 'Hublot Watch Model 1', 'price': '$800', 'image': 'watches/hublot_watch1.jpg'},
        {'model': 'Hublot Watch Model 2', 'price': '$850', 'image': 'watches/hublot_watch2.jpg'},
        {'model': 'Hublot Watch Model 3', 'price': '$820', 'image': 'watches/hublot_watch3.jpg'},
        {'model': 'Hublot Watch Model 4', 'price': '$870', 'image': 'watches/hublot_watch4.jpg'},
        {'model': 'Hublot Watch Model 5', 'price': '$830', 'image': 'watches/hublot_watch5.jpg'},
        {'model': 'Hublot Watch Model 6', 'price': '$880', 'image': 'watches/hublot_watch6.jpg'},
    ],
    'Armani': [
        {'model': 'Armani Watch Model 1', 'price': '$400', 'image': 'watches/armani_watch1.jpg'},
        {'model': 'Armani Watch Model 2', 'price': '$450', 'image': 'watches/armani_watch2.jpg'},
        {'model': 'Armani Watch Model 3', 'price': '$420', 'image': 'watches/armani_watch3.jpg'},
        {'model': 'Armani Watch Model 4', 'price': '$470', 'image': 'watches/armani_watch4.jpg'},
        {'model': 'Armani Watch Model 5', 'price': '$430', 'image': 'watches/armani_watch5.jpg'},
        {'model': 'Armani Watch Model 6', 'price': '$480', 'image': 'watches/armani_watch6.jpg'},
    ],
    'Omega': [
        {'model': 'Omega Watch Model 1', 'price': '$600', 'image': 'watches/omega_watch1.jpg'},
        {'model': 'Omega Watch Model 2', 'price': '$650', 'image': 'watches/omega_watch2.jpg'},
        {'model': 'Omega Watch Model 3', 'price': '$620', 'image': 'watches/omega_watch3.jpg'},
        {'model': 'Omega Watch Model 4', 'price': '$670', 'image': 'watches/omega_watch4.jpg'},
        {'model': 'Omega Watch Model 5', 'price': '$630', 'image': 'watches/omega_watch5.jpg'},
        {'model': 'Omega Watch Model 6', 'price': '$680', 'image': 'watches/omega_watch6.jpg'},
    ],
    'Patek Philippe': [
        {'model': 'Patek Philippe Watch Model 1', 'price': '$1200', 'image': 'watches/patek_watch1.jpg'},
        {'model': 'Patek Philippe Watch Model 2', 'price': '$1250', 'image': 'watches/patek_watch2.jpg'},
        {'model': 'Patek Philippe Watch Model 3', 'price': '$1220', 'image': 'watches/patek_watch3.jpg'},
        {'model': 'Patek Philippe Watch Model 4', 'price': '$1270', 'image': 'watches/patek_watch4.jpg'},
        {'model': 'Patek Philippe Watch Model 5', 'price': '$1230', 'image': 'watches/patek_watch5.jpg'},
        {'model': 'Patek Philippe Watch Model 6', 'price': '$1280', 'image': 'watches/patek_watch6.jpg'},
    ],
    'Tag Heuer': [
        {'model': 'TAG Heuer Watch Model 1', 'price': '$700', 'image': 'watches/tag_watch1.jpg'},
        {'model': 'TAG Heuer Watch Model 2', 'price': '$750', 'image': 'watches/tag_watch2.jpg'},
        {'model': 'TAG Heuer Watch Model 3', 'price': '$720', 'image': 'watches/tag_watch3.jpg'},
        {'model': 'TAG Heuer Watch Model 4', 'price': '$770', 'image': 'watches/tag_watch4.jpg'},
        {'model': 'TAG Heuer Watch Model 5', 'price': '$730', 'image': 'watches/tag_watch5.jpg'},
        {'model': 'TAG Heuer Watch Model 6', 'price': '$780', 'image': 'watches/tag_watch6.jpg'},
    ],
    'Tissot': [
        {'model': 'Tissot Watch Model 1', 'price': '$500', 'image': 'watches/tissot_watch1.jpg'},
        {'model': 'Tissot Watch Model 2', 'price': '$550', 'image': 'watches/tissot_watch2.jpg'},
        {'model': 'Tissot Watch Model 3', 'price': '$520', 'image': 'watches/tissot_watch3.jpg'},
        {'model': 'Tissot Watch Model 4', 'price': '$570', 'image': 'watches/tissot_watch4.jpg'},
        {'model': 'Tissot Watch Model 5', 'price': '$530', 'image': 'watches/tissot_watch5.jpg'},
        {'model': 'Tissot Watch Model 6', 'price': '$580', 'image': 'watches/tissot_watch6.jpg'},
    ],
    'Citizen': [
        {'model': 'Citizen Watch Model 1', 'price': '$300', 'image': 'watches/citizen_watch1.jpg'},
        {'model': 'Citizen Watch Model 2', 'price': '$350', 'image': 'watches/citizen_watch2.jpg'},
        {'model': 'Citizen Watch Model 3', 'price': '$320', 'image': 'watches/citizen_watch3.jpg'},
        {'model': 'Citizen Watch Model 4', 'price': '$370', 'image': 'watches/citizen_watch4.jpg'},
        {'model': 'Citizen Watch Model 5', 'price': '$330', 'image': 'watches/citizen_watch5.jpg'},
        {'model': 'Citizen Watch Model 6', 'price': '$380', 'image': 'watches/citizen_watch6.jpg'},
    ],
    'Seiko': [
        {'model': 'Seiko Watch Model 1', 'price': '$400', 'image': 'watches/seiko_watch1.jpg'},
        {'model': 'Seiko Watch Model 2', 'price': '$450', 'image': 'watches/seiko_watch2.jpg'},
        {'model': 'Seiko Watch Model 3', 'price': '$420', 'image': 'watches/seiko_watch3.jpg'},
        {'model': 'Seiko Watch Model 4', 'price': '$470', 'image': 'watches/seiko_watch4.jpg'},
        {'model': 'Seiko Watch Model 5', 'price': '$430', 'image': 'watches/seiko_watch5.jpg'},
        {'model': 'Seiko Watch Model 6', 'price': '$480', 'image': 'watches/seiko_watch6.jpg'},
  ]
}



watch_data = {
    ('Rolex', 'gold', 'green'): ('rolex_gold_green.jpg', 15000),
    ('Rolex', 'gold', 'Blue'): ('rolex_gold_blue.jpg', 15500),
    ('Rolex', 'Silver', 'green'): ('rolex_silver_green.jpg', 15500),
    ('Rolex', 'Silver', 'Blue'): ('rolex_silver_blue.jpg', 15500),
    ('Gant', 'Silver', 'green'): ('gant_silver_green.jpg', 5000),
    ('Gant', 'Silver', 'Blue'): ('gant_silver_blue.jpg', 5000),
    ('Gant', 'Gold', 'green'): ('gant_gold_green.jpg', 5000),
    ('Gant', 'Gold', 'Blue'): ('gant_gold_blue.jpg', 5000),
    ('Patek Philippe', 'Gold', 'White'): ('PatekPhilippe_gold_white.jpg', 30000),
    ('Patek Philippe', 'Gold', 'Blue'): ('PatekPhilippe_gold_blue.jpg', 30000),
    ('Patek Philippe', 'Black', 'White'): ('PatekPhilippe_black_white.jpg', 30000),
    ('Patek Philippe', 'Black', 'Blue'): ('PatekPhilippe_black_blue.jpg', 30000),
    ('Boss', 'Black', 'White'): ('boss_black_white.jpg', 4000),
    ('Boss', 'Black', 'Blue'): ('boss_black_blue.jpg', 4000),
    ('Boss', 'Silver', 'White'): ('boss_silver_white.jpg', 4000),
    ('Boss', 'Silver', 'Blue'): ('boss_silver_blue.jpg', 4000),
    }


@app.route('/watches/<category>')
def watch_category(category):
    if category in categories:
        watches = categories[category]
        return render_template('category.html', category=category, watches=watches)
    return "Category not found", 404

@app.route('/watches')
def watches():
    return render_template('watches.html')

@app.route('/watches/<brand_name>')
def brand(brand_name):
    # Example logic to handle the brand and render a template
    return render_template('watches.html', brand_name=brand_name)

@app.route('/customize')
def customize():
    return render_template('customize.html')  # Ensure you have a customize.html template

from flask import render_template, request

@app.route('/confirm', methods=['POST'])
def confirm():
    model = request.form.get('model')
    color = request.form.get('color')
    inner_color = request.form.get('inner_color')
    
    key = (model, color, inner_color)
    
    if key in watch_data:
        image_url, price = watch_data[key]
    else:
        return "Error: The selected combination does not exist.", 400
    
    image_url = f'images/{image_url}'
    
    return render_template('confirm.html', model=model, color=color, inner_color=inner_color, image_url=image_url, price=price)

    
@app.route('/sale')
def sale():
    return render_template('sale.html')

# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# About page
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/special')
def special():
    return render_template('3D.html')


WATCHES = {
    'Gant': [
        {'model': 'Gant Watch Model 1', 'price': 200, 'image': 'watches/gantwatch1.jpg'},
        {'model': 'Gant Watch Model 2', 'price': 250, 'image': 'watches/gantwatch2.jpg'},
        {'model': 'Gant Watch Model 3', 'price': 220, 'image': 'watches/gantwatch3.jpg'},
        {'model': 'Gant Watch Model 4', 'price': 270, 'image': 'watches/gantwatch4.jpg'},
        {'model': 'Gant Watch Model 5', 'price': 230, 'image': 'watches/gantwatch5.jpg'},
        {'model': 'Gant Watch Model 6', 'price': 280, 'image': 'watches/gantwatch6.jpg'},
    ],
    'Boss': [
        {'model': 'Boss Watch Model 1', 'price': 300, 'image': 'watches/bosswatch.jpg'},
        {'model': 'Boss Watch Model 2', 'price': 350, 'image': 'watches/bosswatch2.jpg'},
        {'model': 'Boss Watch Model 3', 'price': 310, 'image': 'watches/bosswatch3.jpg'},
        {'model': 'Boss Watch Model 4', 'price': 360, 'image': 'watches/bosswatch4.jpg'},
        {'model': 'Boss Watch Model 5', 'price': 320, 'image': 'watches/bosswatch5.jpg'},
        {'model': 'Boss Watch Model 6', 'price': 370, 'image': 'watches/bosswatch6.jpg'},
    ],
    'AP': [
        {'model': 'AP Watch Model 1', 'price': 500, 'image': 'watches/apwatch1.jpg'},
        {'model': 'AP Watch Model 2', 'price': 550, 'image': 'watches/apwatch2.jpg'},
        {'model': 'AP Watch Model 3', 'price': 520, 'image': 'watches/apwatch3.jpg'},
        {'model': 'AP Watch Model 4', 'price': 570, 'image': 'watches/apwatch4.jpg'},
        {'model': 'AP Watch Model 5', 'price': 530, 'image': 'watches/apwatch5.jpg'},
        {'model': 'AP Watch Model 6', 'price': 580, 'image': 'watches/apwatch6.jpg'},
    ],
    'Rolex': [ 
        {'model': 'Rolex Watch model 1', 'price': 1000, 'image': 'watches/rolexwatch1.jpg'},
        {'model': 'Rolex Watch Model 2', 'price': 1050, 'image': 'watches/rolexwatch2.jpg'},
        {'model': 'Rolex Watch Model 3', 'price': 1020, 'image': 'watches/rolexwatch3.jpg'},
        {'model': 'Rolex Watch Model 4', 'price': 1070, 'image': 'watches/rolexwatch4.jpg'},
        {'model': 'Rolex Watch Model 5', 'price': 1030, 'image': 'watches/rolexwatch5.jpg'},
        {'model': 'Rolex Watch Model 6', 'price': 1080, 'image': 'watches/rolexwatch6.jpg'},
    ],
    'Hublot': [
        {'model': 'Hublot Watch Model 1', 'price': 800, 'image': 'watches/hublot_watch1.jpg'},
        {'model': 'Hublot Watch Model 2', 'price': 850, 'image': 'watches/hublot_watch2.jpg'},
        {'model': 'Hublot Watch Model 3', 'price': 820, 'image': 'watches/hublot_watch3.jpg'},
        {'model': 'Hublot Watch Model 4', 'price': 870, 'image': 'watches/hublot_watch4.jpg'},
        {'model': 'Hublot Watch Model 5', 'price': 830, 'image': 'watches/hublot_watch5.jpg'},
        {'model': 'Hublot Watch Model 6', 'price': 880, 'image': 'watches/hublot_watch6.jpg'},
    ],
    'Armani': [
        {'model': 'Armani Watch Model 1', 'price': 400, 'image': 'watches/armani_watch1.jpg'},
        {'model': 'Armani Watch Model 2', 'price': 450, 'image': 'watches/armani_watch2.jpg'},
        {'model': 'Armani Watch Model 3', 'price': 420, 'image': 'watches/armani_watch3.jpg'},
        {'model': 'Armani Watch Model 4', 'price': 470, 'image': 'watches/armani_watch4.jpg'},
        {'model': 'Armani Watch Model 5', 'price': 430, 'image': 'watches/armani_watch5.jpg'},
        {'model': 'Armani Watch Model 6', 'price': 480, 'image': 'watches/armani_watch6.jpg'},
    ],
    'Omega': [
        {'model': 'Omega Watch Model 1', 'price': 600, 'image': 'watches/omega_watch1.jpg'},
        {'model': 'Omega Watch Model 2', 'price': 650, 'image': 'watches/omega_watch2.jpg'},
        {'model': 'Omega Watch Model 3', 'price': 620, 'image': 'watches/omega_watch3.jpg'},
        {'model': 'Omega Watch Model 4', 'price': 670, 'image': 'watches/omega_watch4.jpg'},
        {'model': 'Omega Watch Model 5', 'price': 630, 'image': 'watches/omega_watch5.jpg'},
        {'model': 'Omega Watch Model 6', 'price': 680, 'image': 'watches/omega_watch6.jpg'},
    ],
    'Patek Philippe': [
        {'model': 'Patek Philippe Watch Model 1', 'price': 1200, 'image': 'watches/patek_watch1.jpg'},
        {'model': 'Patek Philippe Watch Model 2', 'price': 1250, 'image': 'watches/patek_watch2.jpg'},
        {'model': 'Patek Philippe Watch Model 3', 'price': 1220, 'image': 'watches/patek_watch3.jpg'},
        {'model': 'Patek Philippe Watch Model 4', 'price': 1270, 'image': 'watches/patek_watch4.jpg'},
        {'model': 'Patek Philippe Watch Model 5', 'price': 1230, 'image': 'watches/patek_watch5.jpg'},
        {'model': 'Patek Philippe Watch Model 6', 'price': 1280, 'image': 'watches/patek_watch6.jpg'},
    ],
    'Tag Heuer': [
        {'model': 'TAG Heuer Watch Model 1', 'price': 700, 'image': 'watches/tag_watch1.jpg'},
        {'model': 'TAG Heuer Watch Model 2', 'price': 750, 'image': 'watches/tag_watch2.jpg'},
        {'model': 'TAG Heuer Watch Model 3', 'price': 720, 'image': 'watches/tag_watch3.jpg'},
        {'model': 'TAG Heuer Watch Model 4', 'price': 770, 'image': 'watches/tag_watch4.jpg'},
        {'model': 'TAG Heuer Watch Model 5', 'price': 730, 'image': 'watches/tag_watch5.jpg'},
        {'model': 'TAG Heuer Watch Model 6', 'price': 780, 'image': 'watches/tag_watch6.jpg'},
    ],
    'Tissot': [
        {'model': 'Tissot Watch Model 1', 'price': 500, 'image': 'watches/tissot_watch1.jpg'},
        {'model': 'Tissot Watch Model 2', 'price': 550, 'image': 'watches/tissot_watch2.jpg'},
        {'model': 'Tissot Watch Model 3', 'price': 520, 'image': 'watches/tissot_watch3.jpg'},
        {'model': 'Tissot Watch Model 4', 'price': 570, 'image': 'watches/tissot_watch4.jpg'},
        {'model': 'Tissot Watch Model 5', 'price': 530, 'image': 'watches/tissot_watch5.jpg'},
        {'model': 'Tissot Watch Model 6', 'price': 580, 'image': 'watches/tissot_watch6.jpg'},
    ],
    'Citizen': [
        {'model': 'Citizen Watch Model 1', 'price': 300, 'image': 'watches/citizen_watch1.jpg'},
        {'model': 'Citizen Watch Model 2', 'price': 350, 'image': 'watches/citizen_watch2.jpg'},
        {'model': 'Citizen Watch Model 3', 'price': 310, 'image': 'watches/citizen_watch3.jpg'},
        {'model': 'Citizen Watch Model 4', 'price': 360, 'image': 'watches/citizen_watch4.jpg'},
        {'model': 'Citizen Watch Model 5', 'price': 320, 'image': 'watches/citizen_watch5.jpg'},
        {'model': 'Citizen Watch Model 6', 'price': 370, 'image': 'watches/citizen_watch6.jpg'},
    ],
    'Seiko': [
        {'model': 'Seiko Watch Model 1', 'price': 250, 'image': 'watches/seiko_watch1.jpg'},
        {'model': 'Seiko Watch Model 2', 'price': 300, 'image': 'watches/seiko_watch2.jpg'},
        {'model': 'Seiko Watch Model 3', 'price': 270, 'image': 'watches/seiko_watch3.jpg'},
        {'model': 'Seiko Watch Model 4', 'price': 320, 'image': 'watches/seiko_watch4.jpg'},
        {'model': 'Seiko Watch Model 5', 'price': 280, 'image': 'watches/seiko_watch5.jpg'},
        {'model': 'Seiko Watch Model 6', 'price': 330, 'image': 'watches/seiko_watch6.jpg'},
    ],
}


@app.route('/cart')
def view_cart():
    # Retrieve cart items from session
    cart_items = session.get('cart_items', [])
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add_to_cart/<string:watch_id>', methods=['POST'])
def add_to_cart(watch_id):
    # Retrieve watch data from WATCHES based on watch_id
    watch_data = None
    for brand, watches in WATCHES.items():
        for watch in watches:
            if watch['model'].replace(' ', '_') == watch_id:
                watch_data = watch
                break
        if watch_data:
            break
    
    if watch_data:
        # Initialize cart in session if not already
        cart_items = session.get('cart_items', [])
        
        # Add the new item to the cart
        cart_items.append({
            'id': watch_id,
            'name': watch_data['model'],
            'price': watch_data['price'],
            'image': watch_data['image']  # Add image URL to cart item
        })
        session['cart_items'] = cart_items

    return redirect(url_for('view_cart'))


sale_items = [
    {'id': 1, 'name': 'Omega Seamaster', 'price': 4500, 'original_price': 5000, 'image': 'sale/Omega Seamaster1.jpg'},
    {'id': 2, 'name': 'TAG Heuer Carrera', 'price': 2800, 'original_price': 3200, 'image': 'sale/TAG Heuer Carrera1.jpg'},
    {'id': 3, 'name': 'Rolex Daytona', 'price': 11500, 'original_price': 12500, 'image': 'sale/Rolex Daytona1.jpg'},
    {'id': 4, 'name': 'Patek Philippe Nautilus', 'price': 24000, 'original_price': 26000, 'image': 'sale/Patek Philippe Nautilus1.jpg'},
    {'id': 5, 'name': 'Breitling Navitimer', 'price': 8000, 'original_price': 9000, 'image': 'sale/Breitling Navitimer1.jpg'},
    {'id': 6, 'name': 'Cartier Tank', 'price': 3500, 'original_price': 4200, 'image': 'sale/Cartier Tank1.jpg'},
    {'id': 7, 'name': 'Omega Speedmaster', 'price': 5200, 'original_price': 6000, 'image': 'sale/Omega Speedmaster2.jpg'},
    {'id': 8, 'name': 'Rolex Submariner', 'price': 9500, 'original_price': 10500, 'image': 'sale/Rolex Submariner1.jpg'}
]

@app.route('/remove_from_cart/<string:watch_id>', methods=['POST'])
def remove_from_cart(watch_id):
    # Retrieve cart items from session
    cart_items = session.get('cart_items', [])
    
    # Remove item from cart
    cart_items = [item for item in cart_items if item['id'] != watch_id]
    session['cart_items'] = cart_items

    return redirect(url_for('view_cart'))



@app.route('/news')
def news():
    return render_template('news.html')






if __name__ == '__main__':
    app.run(debug=True)
