from flask import Flask, render_template, request, flash, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
from datetime import datetime

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'you shall not pass'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    about_me = db.Column(db.String(300), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<users {self.id}>"


class Genres(db.Model):
    genre_id = db.Column(db.Integer, primary_key=True)
    name_genre = db.Column(db.String(30), unique=True)
    urls = db.Column(db.String(150))

    def __repr__(self):
        return f"<genres {self.genre_id}>"


class Articles(db.Model):
    article_id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.genre_id'))
    title = db.Column(db.String(70), unique=True, nullable=False)
    content = db.Column(db.Text, unique=True, nullable=False)
    tm_posted = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<articles {self.article_id}>'


@app.before_request
def before_request():
    """
    Функция обновляет время последнего посещения пользователя
    """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@login.user_loader
def load_user(id):
    return Users.query.get(int(id))


@app.errorhandler(404)
def not_found_error(error):
    """
    Функция обработки кода 404
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Функция обработки кода 500
    """
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/')
def home():
    """
    Главная страница блога. Отображение всех статей.
    """
    show_all_articles = db.session.query(Articles, Genres, Users).join(Genres).join(Users)\
        .order_by(Articles.tm_posted.desc()).all()
    return render_template('home.html', articles=show_all_articles, genres=db.session.query(Genres).all())


@app.route('/astronomy')
def astronomy():
    """
    Главная страница блога. Отображение статей по астрономии.
    """
    show_all_articles = db.session.query(Articles, Genres, Users).join(Genres).join(Users) \
        .filter(Genres.name_genre == 'Астрономия').all()
    return render_template('home.html', articles=show_all_articles, genres=db.session.query(Genres).all())


@app.route('/electronics')
def electronics():
    """
    Главная страница блога. Отображение статей по электронике.
    """
    show_all_articles = db.session.query(Articles, Genres, Users).join(Genres).join(Users) \
        .filter(Genres.name_genre == 'Электроника').all()
    return render_template('home.html', articles=show_all_articles, genres=db.session.query(Genres).all())


@app.route('/optics')
def optics():
    """
    Главная страница блога. Отображение статей по оптике.
    """
    show_all_articles = db.session.query(Articles, Genres, Users).join(Genres).join(Users) \
        .filter(Genres.name_genre == 'Оптика').all()
    return render_template('home.html', articles=show_all_articles, genres=db.session.query(Genres).all())


@app.route('/nuclear_physics')
def nuclear_physics():
    """
    Главная страница блога. Отображение статей по ядерной физике.
    """
    show_all_articles = db.session.query(Articles, Genres, Users).join(Genres).join(Users)\
        .filter(Genres.name_genre == 'Ядерная физика').all()
    return render_template('home.html', articles=show_all_articles, genres=db.session.query(Genres).all())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница авторизации
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        print(request.form.get('remember_me'))

        try:
            user = Users.query.filter_by(email=request.form['email']).first()
            if user is None or not check_password_hash(user.psw, request.form['password']):
                flash('Неверный email или пароль', category='error')
                return redirect(url_for('login'))
            login_user(user, remember=True) if request.form.get('remember_me') else login_user(user, remember=False)
            return redirect(url_for('home'))

        except Exception as e:
            print('Ошибка извлечения данных из БД', e)
    return render_template('login2.html', is_authenticated=current_user.is_authenticated,
                           genres=db.session.query(Genres).all())


@app.route('/logout')
def logout():
    """
    Деавторизация
    """
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации
    """
    if request.method == 'POST':
        if request.form['password'] == request.form['repeat_password']:
            try:
                hash = generate_password_hash(request.form['password'])
                u = Users(name=request.form['name'], email=request.form['email'], psw=hash)
                db.session.add(u)  # добавить данные в сессию
                db.session.flush()  # добавить данные в таблицу (в памяти устройства)
                db.session.commit()  # сохранить изменения
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                print('Ошибка добавления в БД', e)
        else:
            flash('Пароли не совпадают', category='error')
    db.session.close()
    return render_template('register.html', genres=db.session.query(Genres).all())


@app.route('/profile/<username>')
@login_required
def profile(username):
    """
    Страница профиля пользователя
    """
    if current_user.is_authenticated:
        user = Users.query.filter_by(name=username).first_or_404()
        show_user_articles = db.session.query(Articles, Users).join(Users).filter(Users.name == username).all()
        return render_template('profile.html', user=user, articles=show_user_articles,
                               genres=db.session.query(Genres).all())
    return redirect(url_for('login'))


@app.route('/profile_settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    """
    Страница настроек профиля пользователя
    """
    if request.method == 'POST':
        if request.form['account_change']:
            current_user.name = request.form['account_change']
        if request.form['about']:
            current_user.about_me = request.form['about']
        db.session.commit()
        return redirect(url_for('profile', username=current_user.name))
    return render_template('profile_settings.html', genres=db.session.query(Genres).all())


@app.route('/profile/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    """
    Страница добавления статьи в блог
    """
    if request.method == 'POST':
        try:
            u = Articles(author_id=Users.query.filter_by(name=current_user.name).first().id,
                         genre_id=Genres.query.filter_by(name_genre=request.form['add_genre']).first().genre_id,
                         title=request.form['add_title'], content=request.form['add_text'], tm_posted=datetime.utcnow())
            db.session.add(u)
            db.session.flush()
            db.session.commit()
            return redirect(url_for('profile', username=current_user.name))
        except Exception as e:
            db.session.rollback()
            print('Ошибка добавления в БД', e)
    return render_template('add_article.html', genres=db.session.query(Genres).all())


if __name__ == '__main__':
    app.run(debug=True)


