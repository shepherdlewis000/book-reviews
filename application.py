# coding=utf-8 
import os
import requests
from flask import Flask, flash, session, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


app = Flask(__name__)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    # disable caching of responses provided we're in debugging mode
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Goodreads API key not really needed! Works when unset.
#if not os.environ.get("GOODREADS_KEY"):
#	raise RuntimeError("GOODREADS_KEY not set")
	

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userid") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Borrowed from CS50 Finance (pset8)
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

# Index/Search: Once a user has logged in, they should be taken to a page where they can search for a book. 
# Users should be able to type in the ISBN number of a book, the title of a book, or the author of a book. 
# After performing the search, your website should display a list of possible matching results, or some sort of message if there were no matches. 
# If the user typed in only part of a title, ISBN, or author name, your search page should find matches for those as well!
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
	# If user is submitting the search form
	if request.method == "POST":
		query = "%" + request.form.get("input") + "%"
		rows = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :query OR title ILIKE :query OR author ILIKE :query", {"query": query})
		
		if rows.rowcount == 0:
			flash("No matching books found")
			return redirect("/")
			
		results = rows.fetchall()
		return render_template("results.html", results=results)
		
	else:
		return render_template("search.html")
    
# Registration: Users should be able to register for your website, providing (at minimum) a username and password.
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("You must provide a username", 400)
        
        # Make sure username is not in use
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).rowcount != 0:
        	return apology("Username is in use. Please choose another", 400)

        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Please enter password and confirmation", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password did not match confirmation value", 400)

        password = generate_password_hash(request.form.get("password"))
        
        result = db.execute("INSERT INTO users(username, password) VALUES (:username, :password)", 
        	{"username": request.form.get("username"), "password": password})
        db.commit()

        if not result:
            return apology("Something went wrong with your registration. Try another username", 400)
        
        # Log the user in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
        	{"username": request.form.get("username")}).fetchone()
        
        session["userid"] = rows.userid
        session['username'] = rows.username
        
        flash("Welcome " + session["username"])
        return redirect("/")

	# Just a GET request so render the registration form
    else:
        return render_template("register.html")

# API Access: If users make a GET request to your website’s /api/<isbn> route, where <isbn> is an ISBN number, 
# your website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score.
# If the requested ISBN number isn't in your database, your website should return a 404 error.
@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):
	bookinfo = db.execute("SELECT title, bookid, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn})
	bookinfo = bookinfo.fetchone()
	
	if bookinfo == None:
		return apology("No such book", 404)
		
	title = bookinfo[0]
	bookid = bookinfo[1]
	author = bookinfo[2]
	year = bookinfo[3]
	
	# Get the number of reviews on my site for this book
	num_ratings = db.execute("SELECT COUNT(*) FROM reviews WHERE bookid = :bookid", {"bookid": bookid})
	num_ratings = num_ratings.fetchone()[0]
	
	# Get an average of the star ratings for this book on my site. Format it to two decimal places for display
	avg = db.execute("SELECT AVG(stars) FROM reviews WHERE bookid = :bookid", {"bookid": bookid})
	avg = avg.fetchone()[0]
	avg = format(avg, '.2f')
	
	# Compose the JSON response and return it
	rv = {"title": title, "author": author, "year": year,"isbn": isbn,"review_count": num_ratings,"average_score": avg}
	return(rv)
	
# Book Page: When users click on a book from the results of the search page, they should be taken to a book page,
# with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website.
# Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component 
# to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.
# Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads.
@app.route("/book/<isbn>", methods=['GET','POST'])
@login_required
def book(isbn):
	if request.method == "POST":
		userid = session["userid"]
		bookid = db.execute("SELECT bookid FROM books WHERE isbn = :isbn", {"isbn": isbn})
		bookid = bookid.fetchall()[0][0]
		
		row = db.execute("SELECT * from reviews WHERE userid = :userid AND bookid = :bookid", {"userid": userid, "bookid": bookid})
		row = row.fetchall()
		
		# If user already left a review
		if(len(row) > 0):
			flash("Can't leave more than one review per book!", 'error')
			url = "/book/" + isbn
			return redirect(url) 	
            		
		# Otherwise go ahead an enter the review		
		else:
			stars = request.form['inlineRadioOptions']
			text = request.form['text']
			
			result = db.execute("INSERT INTO reviews(bookid, userid, stars, review) VALUES (:bookid, :userid, :stars, :text)",
				{"bookid": bookid, "userid": userid, "stars": stars, "text": text})
			db.commit()
			
			if not result:
				return apology("Something went wrong saving your review.", 400)
			flash("Thank you for the review!")
			url = "/book/" + isbn
			return redirect(url)
				
	else: # Method is GET so just display page and reviews
		row = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn})
		book = row.fetchall()
		if len(book) == 0:
			flash("Book not found")
			return redirect("/")
			
		bookid = db.execute("SELECT bookid FROM books WHERE isbn = :isbn", {"isbn": isbn})
		bookid = bookid.fetchall()[0][0]
		reviews = db.execute("SELECT reviews.stars, reviews.review, users.username FROM reviews, users WHERE users.userid = reviews.userid AND reviews.bookid = :bookid", {"bookid": bookid})
		reviews = reviews.fetchall()	
		
		# Read API key from env variable
		key = os.getenv("GOODREADS_KEY")
		goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
		goodreads = goodreads.json()

		return render_template("book.html", book=book, goodreads=goodreads, reviews=reviews)
		
# Logout: Logged in users should be able to log out of the site.
@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")
            
# Login: Users, once registered, should be able to log in to your website with their username and password.
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 401)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 401)

        # Query database for username
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).rowcount == 0:
        	return apology("invalid username and/or password", 401)        
        
        rows = db.execute("SELECT * FROM users WHERE username = :username", 
        	{"username": request.form.get("username")}).fetchone()
        
        # If no user by that username or if password is incorrect
        if rows is None or not check_password_hash(rows.password, request.form.get("password")):
        	return apology("invalid username and/or password", 401)
        
        # Remember which user has logged in
        session["userid"] = rows.userid
        session["username"] = rows.username
                
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        
