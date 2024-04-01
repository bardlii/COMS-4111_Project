
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, Blueprint, flash, session, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
#bp = Blueprint('auth', __name__, url_prefix='/auth')


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "jtj2127"
DATABASE_PASSWRD = "jtj2127"
DATABASE_HOST = "35.212.75.104" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	# conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	return redirect('/login')
#	"""
#	request is a special object that Flask provides to access web request information:
#
#	request.method:   "GET" or "POST"
#	request.form:     if the browser submitted a form, this contains the data in the form
#	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2
#
#	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
#	"""
#
#	# DEBUG: this is debugging code to see what request looks like
#	print(request.args)
#
#
	#
	# example of a database query
	#
#	select_query = "SELECT name from test"
#	cursor = g.conn.execute(text(select_query))
#	names = []
#	for result in cursor:
#		names.append(result[0])
#	cursor.close()

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#
	#     # creates a <div> tag for each element in data
	#     # will print:
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
#	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
#	return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
	return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']

	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')


#@app.route('/login', methods=['POST'])
#def login():
	#based on user_id
	#user_id = request.form['user_id']

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        #password = request.form['password']
        #db = get_db()
        error = None
        user = g.conn.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        #elif not check_password_hash(user['password'], password):
            #error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            return redirect(url_for('feed'))

        flash(error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/feed', methods=['GET', 'POST'])
def feed():
	user_id = session.get('user_id')
	if request.method == 'POST':
		reaction = request.form['reaction']
		comment = request.form['comment']
		g.conn.execute("""
            INSERT INTO post_interaction (reaction, comment, post_owner_id, post_number, reacting_user_id)
            VALUES (:reaction, :comment, :post_owner_id, :post_number, :reacting_user_id)
        """, {"reaction": reaction, "comment": comment, "post_owner_id": request.form['post_owner_id'], "post_number": request.form['post_id'], "reacting_user_id": user_id}
		).fetchall()
	posts = text("""
        SELECT P.User_id AS Post_owner_id, P.Post_number, P.Creation_date AS Post_creation_date, P.Image_URL AS Post_image_url, P.Text AS Post_text, PI.Reaction, PI.Comment, PI.Reacting_user_id
        FROM Connect AS C
        JOIN POST AS P ON C.User_id2 = P.User_id
        LEFT JOIN POST_INTERACTION AS PI ON P.User_id = PI.Post_owner_id AND P.Post_number = PI.Post_number
        WHERE C.User_id1 = :user_id
    """)
	post_out = g.conn.execute(posts, {"person_user_id": user_id}).fetchall()
	return render_template('feed.html', user_feed=post_out)

@app.route('/for_you', methods=['GET','POST'])
def for_you():
    user_id = session.get('user_id')
    if request.method == 'POST':
        reaction = request.form['reaction']
        comment = request.form['comment']
        g.conn.execute("""
            INSERT INTO post_interaction (reaction, comment, post_owner_id, post_number, reacting_user_id)
            VALUES (:reaction, :comment, :post_owner_id, :post_number, :reacting_user_id)
        """, {"reaction": reaction, "comment": comment, "post_owner_id": request.form['post_owner_id'], "post_number": request.form['post_id'], "reacting_user_id": user_id}
        )
    page = text("""
        SELECT P.User_id AS Post_owner_id, P.Post_number, P.Creation_date AS Post_creation_date, P.Image_URL AS Post_image_url, P.Text AS Post_text, PI.Reaction, PI.Comment, PI.Reacting_user_id
        FROM POST AS P
        LEFT JOIN POST_INTERACTION AS PI ON P.User_id = PI.Post_owner_id AND P.Post_number = PI.Post_number
        WHERE P.User_id IN (
            SELECT U.User_id
            FROM USERS AS U
            JOIN PERSONAL_PROFILE AS PP ON U.User_id = PP.User_id
            WHERE PP.Location = (
                SELECT Location
                FROM PERSONAL_PROFILE
                WHERE User_id = :user_id
            )
            OR PP.Position = (
                SELECT Position
                FROM PERSONAL_PROFILE
                WHERE User_id = :user_id
            )
            OR U.User_id IN (
                SELECT User_id
                FROM COMPANY
                WHERE Field = (
                    SELECT Field
                    FROM COMPANY
                    WHERE User_id = :user_id
                )
            )
        )
        ORDER BY P.Creation_date DESC;
    """)
    page_out = g.conn.execute(page, {"user_id": user_id}).fetchall()
    return render_template('for_you.html', page_out=page_out)

		


if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
