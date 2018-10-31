from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import configs  #imports password for database, use in config of SQLALCHEMY_DATABASE_URI



app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:{}@localhost:8889/build-a-blog'.format(configs.password)
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body= db.Column(db.String(10000))

    def __init__(self, title, body):
        self.title = title
        self.body = body


def is_blank(entry):
    return bool(entry and entry.strip())


@app.route("/newpost")
def index():
    return render_template('newpost.html',
    ptitle="New Blog Post")

@app.route('/newpost', methods=['POST'])
def new_post():

    blog_title = request.form['title']
    blog_body = request.form['body']
    title_error = ''
    body_error = ''

    if not is_blank(blog_title):
        title_error = 'Please enter a title for your blog'
        blog_title = ''

    if not is_blank(blog_body):
        body_error = 'Please enter the body for your blog'
        blog_body = ''

    if request.method == 'POST' and not title_error and not body_error:
        new_blog = Blog(blog_title, blog_body)
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
            ptitle="New Blog Post")

@app.route("/blog", methods=['POST', 'GET'])
def blog_post():

    blogs = Blog.query.order_by(Blog.id.desc()).all()  #order posts by desc order on main blog page
    blog_id = request.args.get('id')
    if request.method == 'GET' and is_blank(blog_id):
        blog_id = int(blog_id)
        blog = Blog.query.filter_by(id = {blog_id}).all()
        return render_template('blogpost.html',
        ptitle="Blog Post",
        blog=blog)

    return render_template('blog.html',
    ptitle="Blog",
    blogs=blogs)


if __name__ == '__main__':
    app.run()
