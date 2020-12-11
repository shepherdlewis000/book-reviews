import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
    
# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
   db.execute("CREATE TABLE IF NOT EXISTS users(userid SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
   db.execute("CREATE TABLE IF NOT EXISTS books(bookid SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, year VARCHAR NOT NULL, author VARCHAR NOT NULL)")
   db.execute("CREATE TABLE IF NOT EXISTS reviews(reviewid SERIAL PRIMARY KEY, bookid INTEGER REFERENCES books, userid INTEGER REFERENCES users, stars INTEGER NOT NULL, review TEXT)")
   db.commit()
   
   f = open("books.csv")
   reader = csv.reader(f)
   
   for isbn, title, author, year in reader:
   	db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
   db.commit()
   
if __name__ == "__main__":
    main()