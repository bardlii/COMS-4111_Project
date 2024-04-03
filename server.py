
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
from datetime import date

from sqlalchemy.sql import text

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key=b'my_secret_key'
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
        import traceback
        traceback.print_exc()
        g.conn = None

    # Load the logged-in user's ID
    load_logged_in_user()

def load_logged_in_user():
    user_id = session.get('user_id')
    g.user_id = user_id
    print(g.user_id)


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

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        #password = request.form['password']
        #db = get_db()
        error = None
        user = text("SELECT * FROM users WHERE user_id = :user_id")
        user_out = g.conn.execute(user, {"user_id": user_id}).fetchone()

        if user is None:
            error = 'Incorrect username.'
        #elif not check_password_hash(user['password'], password):
            #error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user_out[0]
            return redirect(url_for('feed'))

        flash(error)

    return render_template('login.html')

@app.route('/viewprofile', methods=['GET'])
def user_profile():
    # Retrieve the username from the query parameters
    username = request.args.get('username')
    user_info = g.conn.execute(text("""
        SELECT name, bio, image_url
        FROM users
        WHERE user_id = :username
        """), {"username": username}
    ).fetchone()


    # Check if the user is a personal profile
    personal_profile = g.conn.execute(
       text("SELECT * FROM personal_profile WHERE user_id = :username"), {"username": username}
    ).fetchone()

    # If personal profile exists, render personal_profile.html
    if personal_profile:
        posts = g.conn.execute(
            text("SELECT * FROM post WHERE user_id = :username"), {"username": username}
        ).fetchall()
        return render_template('personal_profile.html', u=user_info, pp=personal_profile, posts=posts)

    # Check if the user is a company profile
    company_profile = g.conn.execute(
        text("SELECT * FROM company WHERE user_id = :username"), {"username": username}
    ).fetchone()

    # If company profile exists, render company_profile.html
    if company_profile:
        posts = g.conn.execute(
            text("SELECT * FROM post WHERE user_id = :username"), {"username": username}
        ).fetchall()
        # Retrieve additional data for company profile
        job_listings = g.conn.execute(
            text("SELECT * FROM job_listing WHERE user_id = :username"), {"username": username}
        ).fetchall()
        locations = g.conn.execute(
            text("SELECT location FROM company_locations WHERE user_id = :username"), {"username": username}
        ).fetchall()

        return render_template('company_profile.html', u=user_info, cp=company_profile, posts=posts, jl=job_listings, cl=locations)


@app.route('/groups', methods=['GET', 'POST'])
def groups():
    if request.method == 'GET':
        # Fetch all groups
        groups = g.conn.execute(text("SELECT * FROM GROUPS")).fetchall()
        return render_template('groups.html', groups=groups)
    
    elif request.method == 'POST':
        action = request.form.get('action')
        group_id = request.form.get('group_id')
        user_id = session.get('user_id')

        if action == 'join':
            # Insert into GROUP_MEMBERS table
            g.conn.execute(text("INSERT INTO GROUP_MEMBERS (Group_id, User_id) VALUES (:group_id, :user_id)"), {"group_id": group_id, "user_id": user_id})

            # Update Number_of_members in GROUPS table
            g.conn.execute(text("UPDATE GROUPS SET Number_of_members = Number_of_members + 1 WHERE Group_id = :group_id"), {"group_id": group_id})
            
        elif action == 'leave':
            # Remove from GROUP_MEMBERS table
            g.conn.execute(text("DELETE FROM GROUP_MEMBERS WHERE Group_id = :group_id AND User_id = :user_id"), {"group_id": group_id, "user_id": user_id})

            # Update Number_of_members in GROUPS table
            g.conn.execute(text("UPDATE GROUPS SET Number_of_members = Number_of_members - 1 WHERE Group_id = :group_id"), {"group_id": group_id})
        
        return redirect(url_for('groups'))


@app.route('/create_event', methods=['GET','POST'])
def create_event():
    if request.method == 'POST':
        user_id = session.get('user_id')
        event_description = request.form['event_description']
        image_url = request.form['image_url']
        associated_date = request.form['associated_date']
        creation_date = date.today()
        
        error = None
        get_max_num = g.conn.execute(text("SELECT MAX(post_number) FROM post")).fetchone()
        max_post_number = get_max_num[0] if get_max_num[0] is not None else 0
        post_num = str(max_post_number + 1)

        try:
            g.conn.execute(
                text('INSERT INTO POST (User_id, Post_number, Creation_date, Image_URL, Text) VALUES (:user_id, :post_number, :creation_date, :image_url, :event_description)'),
                {"user_id": user_id, "post_number": post_num, "creation_date": creation_date, "image_url": image_url, "event_description": event_description}
            )
            g.conn.execute(
                text('INSERT INTO EVENT (User_id, Post_number, Associated_date) VALUES (:user_id, (SELECT MAX(Post_number) FROM POST WHERE User_id = :user_id), :associated_date)'),
                {"user_id": user_id, "associated_date": associated_date}
            )
            #g.conn.commit()
            flash('Event created successfully!', 'success')
        except Exception as e:
            error = str(e)
            #g.conn.rollback()
            flash(f'An error occurred: {error}', 'error')
      
    return render_template('event.html')


@app.route('/announce', methods=['GET','POST'])
def announce():
    if request.method == 'POST':
        user_id = session.get('user_id')
        announcement_text = request.form['announcement_text']
        image_url = request.form['image_url']
        creation_date = date.today()

        error = None
        get_max_num = g.conn.execute(text("SELECT MAX(post_number) FROM post")).fetchone()
        max_post_number = get_max_num[0] if get_max_num[0] is not None else 0
        post_num = str(max_post_number + 1)

        try:
            g.conn.execute(
                text('INSERT INTO POST (User_id, Post_number, Creation_date, Image_URL, Text) VALUES (:user_id, :post_number, :creation_date, :image_url, :announcement_text)'),
                {"user_id": user_id, "post_number": post_num, "creation_date": creation_date, "image_url": image_url, "announcement_text": announcement_text}
            )
            g.conn.execute(
                text('INSERT INTO ANNOUNCEMENT (User_id, Post_number) VALUES (:user_id, (SELECT MAX(Post_number) FROM POST WHERE User_id = :user_id))'),
                {"user_id": user_id}
            )
            #g.conn.commit()
            flash('Announcement created successfully!', 'success')
        except Exception as e:
            error = str(e)
            flash(f'An error occurred: {error}', 'error')

    return render_template('announce.html')


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
        post_owner_id = request.form['post_owner_id']  # Extract post_owner_id from form data
        post_number = request.form['post_number']  # Extract post_number from form data

        # Insert reaction and comment into the database
        g.conn.execute(text("""
            INSERT INTO post_interaction (reaction, comment, post_owner_id, post_number, reacting_user_id)
            VALUES (:reaction, :comment, :post_owner_id, :post_number, :reacting_user_id)
        """), {
            "reaction": reaction,
            "comment": comment,
            "post_owner_id": post_owner_id,
            "post_number": post_number,
            "reacting_user_id": user_id
        })
    
    posts_query = text("""  
        SELECT P.User_id AS Post_owner_id, P.Post_number, P.Creation_date AS Post_creation_date, P.Image_URL AS Post_image_url, P.Text AS Post_text, PI.Reaction, PI.Comment, PI.Reacting_user_id
        FROM Connect AS C
        JOIN POST AS P ON ((C.User_id1 = P.User_id OR C.User_id2 = P.User_id) AND C.Connection_status = 'Connected')
        LEFT JOIN post_interaction AS PI ON (P.User_id = PI.Post_owner_id AND P.Post_number = PI.Post_number)
        WHERE :user_id IN (C.User_id1, C.User_id2)
        ORDER BY P.Creation_date DESC
    """)
    post_out = g.conn.execute(posts_query, {"user_id": user_id}).fetchall()
    #post_out = [dict(row) for row in post_out_raw]
    print(post_out)

    return render_template('feed.html', posts=post_out)


@app.route('/for_you', methods=['GET','POST'])
def for_you():
    user_id = session.get('user_id')
    if request.method == 'POST':
        reaction = request.form['reaction']
        comment = request.form['comment']
        post_owner_id = request.form['post_owner_id']
        post_number = request.form['post_number']
        g.conn.execute(text("""
            INSERT INTO post_interaction (reaction, comment, post_owner_id, post_number, reacting_user_id)
            VALUES (:reaction, :comment, :post_owner_id, :post_number, :reacting_user_id)
        	"""), {"reaction": reaction, "comment": comment, "post_owner_id": post_owner_id, "post_number": post_number, "reacting_user_id": user_id}
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
                SELECT gm.User_id
                FROM GROUP_MEMBERS gm
                WHERE gm.Group_id IN (
                    SELECT gm2.Group_id
                    FROM GROUP_MEMBERS gm2
                    WHERE gm2.User_id = :user_id
                )
            )
        )
        ORDER BY P.Creation_date DESC
    """)
    page_out = g.conn.execute(page, {"user_id": user_id}).fetchall()
    return render_template('for_you.html', page_out=page_out)


@app.route('/explore', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Get the search inputs from the form
        u_search = request.form.get('u_search')
        l_search = request.form.get('l_search')
        p_search = request.form.get('p_search')
        
        # Determine the search type based on the submitted form data
        if u_search:
            return redirect(url_for('search_results', search_type='users', query=u_search))
        elif l_search:
            return redirect(url_for('search_results', search_type='location', query=l_search))
        elif p_search:
            return redirect(url_for('search_results', search_type='position', query=p_search))
        else:
            return render_template('search.html', error_message='Please provide a search query.')

    return render_template('search.html', error_message=None)


@app.route('/search_results', methods=['GET'])
def search_results():
    search_type = request.args.get('search_type')
    query = request.args.get('query')

    if search_type == 'users':
        # Perform user search based on the query
        u_results = g.conn.execute(text("""
            SELECT user_id, name
            FROM users AS U
            WHERE name LIKE '%' || :keyword || '%' OR user_id LIKE '%' || :keyword || '%'
            """), {"keyword": query}
        ).fetchall()
        return render_template('search_results.html', results=u_results)

    elif search_type == 'location':
        # Perform location search based on the query
        l_results = g.conn.execute(text("""
            SELECT u.name, u.user_id
            FROM users u
            LEFT JOIN personal_profile pp ON u.user_id = pp.user_id
            LEFT JOIN company_locations cl ON u.user_id = cl.user_id
            WHERE u.name LIKE '%' || :keyword || '%' OR pp.location LIKE '%' || :keyword || '%' OR cl.location LIKE '%' || :keyword || '%'
            """), {"keyword": query}
        ).fetchall()
        return render_template('search_results.html', results=l_results)

    elif search_type == 'position':
        # Perform position search based on the query
        p_results = g.conn.execute(text("""
            SELECT DISTINCT COALESCE(PP.User_id, JL.User_id) AS User_id, U.Name
            FROM USERS U
            LEFT JOIN PERSONAL_PROFILE PP ON U.User_id = PP.User_id AND PP.Position LIKE '%' || :keyword || '%'
            LEFT JOIN COMPANY C ON U.User_id = C.User_id
            LEFT JOIN JOB_LISTING JL ON C.User_id = JL.User_id AND JL.Position LIKE '%' || :keyword || '%'
            WHERE COALESCE(PP.Position, JL.Position) IS NOT NULL;
            """), {"keyword": query}
        ).fetchall()
        return render_template('search_results.html', results=p_results)

    else:
        # If no search type is provided, redirect to the explore page
        return redirect(url_for('explore'))        


@app.route('/conversation_with', methods=['GET','POST'])
def conversation():
    username = request.args.get('username')
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))
    
    messages = g.conn.execute(text("""
        SELECT sender, receiver, text, text_date
        FROM message
        WHERE ((sender = :current_user AND receiver = :other_user)
            OR (sender = :other_user AND receiver = :current_user))
            AND EXISTS (
                SELECT 1
                FROM connect
                WHERE (user_id1 = :current_user AND user_id2 = :other_user)
                    OR (user_id1 = :other_user AND user_id2 = :current_user)
            )
        ORDER BY text_date;
    """), {'current_user': user_id, 'other_user': username}).fetchall()

    if request.method == 'POST':
        message = request.form['message']
        try:
            g.conn.execute(text("""
                INSERT INTO message (sender, receiver, text, text_date)
                VALUES (:user_id, :username, :message, :date)
            """), {"user_id": user_id, "username": username, "message": message, "date": date.today()})
            flash('Message sent successfully!', 'success')
        except Exception as e:
            print("Error executing SQL query:", e)


    return render_template('conversation_with.html', messages=messages, other_user=username)
				

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
		app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

run()
