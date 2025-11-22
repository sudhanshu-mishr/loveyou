import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from forms import RegistrationForm, LoginForm, ProfileForm, MessageForm
from models import db, User, Swipe, Message, is_match


def create_app():
    app = Flask(__name__)
    # TODO: change this in production
    app.config['SECRET_KEY'] = 'change-this-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connect_pu.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    upload_root = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_root, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_root

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('discover'))
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('discover'))
        form = RegistrationForm()
        if form.validate_on_submit():
            existing = User.query.filter(
                (User.username == form.username.data) | (User.email == form.email.data)
            ).first()
            if existing:
                flash('Username or email already taken.', 'danger')
            else:
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password_hash=generate_password_hash(form.password.data),
                )
                db.session.add(user)
                db.session.commit()
                flash('Account created. Please log in.', 'success')
                return redirect(url_for('login'))
        return render_template('auth/register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('discover'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash('Welcome back!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('discover'))
            flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        form = ProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.name = form.name.data
            current_user.age = form.age.data
            current_user.gender = form.gender.data
            current_user.bio = form.bio.data
            current_user.interests = form.interests.data
            current_user.location = form.location.data

            file = form.avatar_file.data
            if file:
                filename = secure_filename(file.filename)
                if filename:
                    unique_name = f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(file_path)
                    current_user.avatar_filename = unique_name

            db.session.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('profile'))
        return render_template('profile/edit_profile.html', form=form)

    @app.route('/discover')
    @login_required
    def discover():
        # basic optional filters via query string
        gender_filter = request.args.get('gender') or ''
        min_age = request.args.get('min_age', type=int)
        max_age = request.args.get('max_age', type=int)
        location_filter = request.args.get('location') or ''

        swiped = Swipe.query.filter_by(user_id=current_user.id).all()
        swiped_ids = [s.target_id for s in swiped]
        swiped_ids.append(current_user.id)

        from sqlalchemy import not_

        query = User.query.filter(not_(User.id.in_(swiped_ids)))

        if gender_filter:
            query = query.filter(User.gender == gender_filter)
        if min_age is not None:
            query = query.filter(User.age >= min_age)
        if max_age is not None:
            query = query.filter(User.age <= max_age)
        if location_filter:
            like_pattern = f"%{location_filter}%"
            query = query.filter(User.location.ilike(like_pattern))

        candidate = query.first()
        return render_template(
            'swipe.html',
            candidate=candidate,
            gender_filter=gender_filter,
            min_age=min_age,
            max_age=max_age,
            location_filter=location_filter,
        )

    @app.route('/like/<int:user_id>', methods=['POST'])
    @login_required
    def like(user_id):
        if user_id == current_user.id:
            return redirect(url_for('discover'))
        target = User.query.get_or_404(user_id)
        existing = Swipe.query.filter_by(user_id=current_user.id, target_id=user_id).first()
        if not existing:
            swipe = Swipe(user_id=current_user.id, target_id=user_id, is_like=True)
            db.session.add(swipe)
            db.session.commit()
        if is_match(current_user.id, user_id):
            flash(f"It's a match with {target.display_name}!", 'success')
        return redirect(url_for('discover'))

    @app.route('/pass/<int:user_id>', methods=['POST'])
    @login_required
    def pass_user(user_id):
        if user_id == current_user.id:
            return redirect(url_for('discover'))
        existing = Swipe.query.filter_by(user_id=current_user.id, target_id=user_id).first()
        if not existing:
            swipe = Swipe(user_id=current_user.id, target_id=user_id, is_like=False)
            db.session.add(swipe)
            db.session.commit()
        return redirect(url_for('discover'))

    @app.route('/matches')
    @login_required
    def matches():
        match_users = User.get_matches(current_user.id)
        return render_template('matches.html', matches=match_users)

    @app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def chat(user_id):
        other = User.query.get_or_404(user_id)
        if not is_match(current_user.id, other.id):
            flash('You can only chat with people you matched with.', 'warning')
            return redirect(url_for('matches'))
        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(
                sender_id=current_user.id,
                receiver_id=other.id,
                body=form.body.data,
            )
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat', user_id=other.id))
        messages = Message.get_conversation(current_user.id, other.id)
        return render_template('chat.html', form=form, other=other, messages=messages)

    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0",debug=True)
