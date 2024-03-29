import os
import secrets

from flask import (render_template,
                   redirect,
                   url_for,
                   request,
                   flash,
                   abort)

from flask_login import login_user, current_user, logout_user, login_required
from FlaskBlogApp.forms import SignupForm, LoginForm, NewArticleForm, AccountUpdateForm, NewOfferForm
from FlaskBlogApp import app, db, bcrypt
from FlaskBlogApp.models import User, Article, Offer

from PIL import Image


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('errors/404.html'), 404


@app.errorhandler(415)
def unsupported_media_type(e):
    # note that we set the 415 status explicitly
    return render_template('errors/415.html'), 415


# To size είναι ένα tuple της μορφής (640, 480)
def image_save(image, where, size):
    random_filename = secrets.token_hex(12)
    file_name, file_extension = os.path.splitext(image.filename)
    image_filename = random_filename + file_extension
    image_path = os.path.join(app.root_path, 'static/images', where, image_filename)
    img = Image.open(image)
    img.thumbnail(size)
    img.save(image_path)
    return image_filename


@app.route("/index/")
@app.route("/")
def root():
    return render_template("index.html")


@app.route("/articles/")
@login_required
def articles():
    page = request.args.get("page", 1, type=int)
    the_articles = Article.query.order_by(Article.date_created.desc()).paginate(per_page=5, page=page)
    return render_template("articles.html", articles=the_articles)


@app.route("/offers/")
@login_required
def offers():
    page = request.args.get("page", 1, type=int)
    the_offers = Offer.query.order_by(Offer.date_created.desc()).paginate(per_page=5, page=page)
    return render_template("offers.html", offers=the_offers)


@app.route("/articles_by_author/<int:author_id>")
def articles_by_author(author_id):
    user = User.query.get_or_404(author_id)
    page = request.args.get("page", 1, type=int)
    the_articles = Article.query.filter_by(author=user).order_by(Article.date_created.desc()).paginate(per_page=5, page=page)
    return render_template("articles_by_author.html", articles=the_articles, author=user)


@app.route("/offers_by_author/<int:author_id>")
def offers_by_author(author_id):
    user = User.query.get_or_404(author_id)
    page = request.args.get("page", 1, type=int)
    the_offers = Offer.query.filter_by(author=user).order_by(Offer.date_created.desc()).paginate(per_page=5, page=page)
    return render_template("offers_by_author.html", offers=the_offers, author=user)


@app.route("/signup/", methods=["GET", "POST"])
def signup():

    form = SignupForm()

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        password2 = form.password2.data
        my_contact = form.my_contact.data

        encrypted_password = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(username=username, email=email, password=encrypted_password, contact_username=my_contact)
        db.session.add(user)
        db.session.commit()

        flash(f"Ο λογαριασμός για τον χρήστη <b>{username}</b> δημιουργήθηκε με επιτυχία", "success")
        return redirect(url_for('login'))
    return render_template("signup.html", form=form)


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("root"))

    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            flash(f"Η είσοδος του χρήστη με email: {email} στη σελίδα μας έγινε με επιτυχία.", "success")
            login_user(user, remember=form.remember_me.data)
            next_link = request.args.get("next")
            return redirect(next_link) if next_link else redirect(url_for("root"))
        else:
            flash("Η είσοδος του χρήστη ήταν ανεπιτυχής, παρακαλούμε δοκιμάστε ξανά με τα σωστά email/password.", "warning")
    return render_template("login.html", form=form)


@app.route("/logout/")
def logout():
    logout_user()
    flash("Έγινε αποσύνδεση του χρήστη.", "success")
    return redirect(url_for("root"))


@app.route("/new_article/", methods=["GET", "POST"])
@login_required
def new_article():
    form = NewArticleForm()

    if request.method == 'POST' and form.validate_on_submit():
        article_title = form.article_title.data
        article_body = form.article_body.data

        if form.article_image.data:
            try:
                image_file = image_save(form.article_image.data, 'articles_images', (640, 360))
            except:
                abort(415)

            article = Article(article_title=article_title,
                              article_body=article_body,
                              author=current_user,
                              article_image=image_file)
        else:
            article = Article(article_title=article_title, article_body=article_body, author=current_user)

        db.session.add(article)
        db.session.commit()

        flash(f"Το άρθρο με τίτλο {article.article_title} δημιουργήθηκε με επιτυχία", "success")

        return redirect(url_for("root"))

    return render_template("new_article.html", form=form, page_title="Εισαγωγή Νέου Άρθρου")


@app.route("/new_offer/", methods=["GET", "POST"])
@login_required
def new_offer():
    form = NewOfferForm()

    if request.method == 'POST' and form.validate_on_submit():
        offer_title = form.offer_title.data
        offer_body = form.offer_body.data
        offer = Offer(offer_title=offer_title,
                      offer_body=offer_body,
                      author=current_user,
                      )
        db.session.add(offer)
        db.session.commit()
        flash(f"H αγγελία με θέμα {offer.offer_title} καταχωρήθηκε.", "success")
        return redirect(url_for("root"))
    return render_template("new_offer.html", form=form, page_title="Καταχώριση Νέας Αγγελίας")


@app.route("/full_article/<int:article_id>", methods=["GET"])
def full_article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template("full_article.html", article=article)


@app.route("/full_offer/<int:offer_id>", methods=["GET"])
def full_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template("full_offer.html", offer=offer)


@app.route("/delete_article/<int:article_id>", methods=["GET", "POST"])
@login_required
def delete_article(article_id):
    article = Article.query.filter_by(id=article_id, author=current_user).first_or_404()

    if article:
        db.session.delete(article)
        db.session.commit()
        flash("Το άρθρο διεγράφη με επιτυχία.", "success")
        return redirect(url_for("root"))
    flash("Το άρθρο δε βρέθηκε.", "warning")
    return redirect(url_for("root"))


@app.route("/delete_offer/<int:offer_id>", methods=["GET", "POST"])
@login_required
def delete_offer(offer_id):
    offer = Offer.query.filter_by(id=offer_id, author=current_user).first_or_404()

    if offer:
        db.session.delete(offer)
        db.session.commit()
        flash("H αγγελία διαγράφηκε.", "success")
        return redirect(url_for("root"))
    flash("Η αγγελία δεν βρέθηκε.", "warning")
    return redirect(url_for("root"))


@app.route("/account/", methods=['GET', 'POST'])
@login_required
def account():
    form = AccountUpdateForm(username=current_user.username, email=current_user.email)

    if request.method == 'POST' and form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        # image_save(image, where, size)
        if form.profile_image.data:
            try:
                image_file = image_save(form.profile_image.data, 'profiles_images', (150, 150))
            except:
                abort(415)
            current_user.profile_image = image_file
        db.session.commit()
        flash(f"Ο λογαριασμός του χρήστη <b>{current_user.username}</b> ενημερώθηκε με επιτυχία", "success")
        return redirect(url_for('root'))
    return render_template("account_update.html", form=form)


@app.route("/edit_article/<int:article_id>", methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.filter_by(id=article_id, author=current_user).first_or_404()
    form = NewArticleForm(article_title=article.article_title, article_body=article.article_body)

    if request.method == 'POST' and form.validate_on_submit():
        article.article_title = form.article_title.data
        article.article_body = form.article_body.data

        if form.article_image.data:
            try:
                image_file = image_save(form.article_image.data, 'articles_images', (640, 360))
            except:
                abort(415)
            article.article_image = image_file

        db.session.commit()
        flash(f"Το άρθρο με τίτλο <b>{article.article_title}</b> ενημερώθηκε με επιτυχία.", "success")
        return redirect(url_for('root'))
    return render_template("new_article.html", form=form, page_title="Επεξεργασία Άρθρου")


@app.route("/edit_offer/<int:offer_id>", methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):

    offer = Offer.query.filter_by(id=offer_id, author=current_user).first_or_404()

    form = NewOfferForm(offer_title=offer.article_title, offer_body=offer.offer_body)

    if request.method == 'POST' and form.validate_on_submit():
        offer.offer_title = form.offer_title.data
        offer.offer_body = form.offer_body.data

        db.session.commit()
        flash(f"Η αγγελία με τίτλο <b>{offer.offer_title}</b> ενημερώθηκε με επιτυχία.", "success")
        return redirect(url_for('root'))
    return render_template("new_offer.html", form=form, page_title="Επεξεργασία Άγγελίας")
