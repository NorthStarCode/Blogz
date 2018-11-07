from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import configs  #imports password for database, use in config of SQLALCHEMY_DATABASE_URI



app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:{}@localhost:8889/blogz'.format(configs.db_password)
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = configs.key_password

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(10000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dateblog = db.Column(db.DateTime)

    def __init__(self, title, body, owner,  dateblog=None):
        self.title = title
        self.body = body
        self.owner = owner
        self.dateblog = datetime.utcnow()   #sets time to current

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


def is_blank(entry):
    return bool(entry and entry.strip())

def is_space(entry):
    if " " in entry:
        return True
    else:
        return False

def len_ok(entry):
    if 2 < len(entry) < 21:
        return False
    else:
        return True


@app.before_request     #runs first to ensure user is logged in, if nor, redirects to login page
def require_login():
    allowed_routes = ['login', 'signup', 'static', 'homepage', 'blog_post']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route("/") 
def homepage():
    users = User.query.all()
    return render_template('/index.html',
    users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()  #grabs user info from database

        if user and user.password == password:
            session['username'] = username    #remembers user in this session
            return redirect('/newpost')
        elif not is_blank(password) or not is_blank(username):
            flash('Username or Password field was left blank!', 'error')
            return redirect ('/login')
        elif not user:
            flash('Username not in system!', 'error')
            return redirect ('/login')
        else:
            flash('User password is incorrect!', 'error')
            return redirect ('/login')
       
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verifypass = request.form['verifypass']

        username_error = ''
        password_error = ''
        verifypass_error = ''
        exist_user_error = ''

        existing_user = User.query.filter_by(username=username).first()

        if not is_blank(username):
            username_error = 'Username field was left blank'
            username = ''
        elif existing_user:
            username_error =  "Duplicate User! Please Enter Another User Name!"
            username = ''
        else:
            if is_space(username) or len_ok(username):
                username_error = 'Username not valid! Please make sure there are no spaces and it is between 3-20 characters.'
                username = username

        if not is_blank(password):
            password_error = 'Password field was left blank'
            password = ''
        else:
            if is_space(password) or len_ok(password):
                password_error = 'Password not valid! Please make sure there are no spaces and it is between 3-20 characters.'
                password = ''

        if not is_blank(verifypass):
            verifypass_error = 'Verify Password field was left blank'
            varifypass = ''
        else:
            if password != verifypass:
                verifypass_error = 'Passwords do not match! Please re-enter both.'
                verifypass = ''
                password = ''

        
        if not existing_user and not username_error and not password_error and not verifypass_error:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/')

    
        return render_template('signup.html',
            username_error=username_error,
            password_error=password_error,
            verifypass_error=verifypass_error,
            password=password,
            username=username,
            title="User Signup")    #renders signup page with approriate signup erros

    return render_template('signup.html')  


@app.route("/newpost")  #renders page for submitting new blog post
def index():
    return render_template('newpost.html',
    ptitle="New Blog Post")

@app.route('/newpost', methods=['POST'])
def new_post():

    blog_title = request.form['title']
    blog_body = request.form['body']
    title_error = ''
    body_error = ''

    owner = User.query.filter_by(username=session['username']).first()

    if not is_blank(blog_title):
        title_error = 'Please enter a title for your blog'

    if not is_blank(blog_body):
        body_error = 'Please enter the body for your blog'

    if request.method == 'POST' and not title_error and not body_error:
        new_blog = Blog(blog_title, blog_body, owner)
        db.session.add(new_blog)
        db.session.commit()
        blogid = Blog.query.order_by(Blog.id.desc()).first()  #sorts query by desc order and grabs last user id
        blog_id=blogid.id
        return redirect('/blog?id={}'.format(blog_id)) #retunrs user to new post entry page

    else:
        return render_template('newpost.html',
            title_error=title_error,
            body_error=body_error,
            blog_title=blog_title,
            blog_body=blog_body,
            ptitle="New Blog Post") #renders newpost page with appropriate errors in blog entry

@app.route("/blog", methods=['POST', 'GET'])
def blog_post():

    blogs = Blog.query.order_by(Blog.dateblog.desc())   #orders post by date time submitted
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')

    if request.method == 'GET' and is_blank(blog_id):
        blog_id = int(blog_id)
        blog = Blog.query.filter_by(id = {blog_id}).all()
        return render_template('blogpost.html',
        ptitle="Blog Post",
        blog=blog)      #renders page with single specific blogpost only

    if request.method == 'GET' and is_blank(user_id):
        user_id = int(user_id)
        blog = Blog.query.filter_by(owner_id=user_id).order_by(Blog.dateblog.desc()).all()  #orders blogs by specified user by desc date
        return render_template('userposts.html',
        ptitle="Blog Posts",
        blog=blog)  #renders page with all blogs from specified user id

    return render_template('blog.html',
    ptitle="Blog",
    blogs=blogs)    #renders page with all blog entries


@app.route('/logout', methods=['GET'])
def logout():
    del session['username'] #logs user out by deleting session identifier
    return redirect('/')


if __name__ == '__main__':
    app.run()
