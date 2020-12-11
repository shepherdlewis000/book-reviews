Book Review Site

This project is a book review website. Users are able to register for the site and then log in using their username and password. Once they log in, they are able to search for books, leave reviews for individual books, and see the reviews made by other people. Using a third-party API by Goodreads, it also pulls in ratings from a broader audience. Finally, users are able to query for book details and book reviews programmatically via this website’s API.

DEMO: https://ls-book-reviews.herokuapp.com/

Registration: Users are able to register for the website, providing a username and password.

Login: Users once registered are able to log in to the website with their username and password.

Logout: Logged in users are able to log out of the site.

Import: Initial PostgreSQL database population was done from books.csv, a sample spreadsheet of 5000 different books. Each one has an ISBN number, a title, an author, and a publication year. In import.py a Python script takes the books and imports them into PostgreSQL database.

Search: Once a user has logged in, they are taken to a page where they can search for a book. Users are able to type in the ISBN number of a book, the title of a book, or the author of a book. After performing the search, the site displays a list of possible matching results, or a message if there were no matches. If the user typed in only part of a title, ISBN, or author name, the search page finds matches for those as well.

Book Page: When users click on a book from the results of the search page, they are taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on the website.
    
Review Submission: On the book page, users are able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users are not able to submit multiple reviews for the same book.

Goodreads Review Data: On the book page is displayed (if available) the average rating and number of ratings the work has received from Goodreads.

API Access: If users make a GET request to the site's /api/<isbn> route, where <isbn> is an ISBN number, the site returns a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON follows the format:

{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}

If the requested ISBN number isn’t in the database, the site returns a 404 error.

Raw SQL commands via SQLAlchemy’s execute method are used in order to make database queries. The SQLAlchemy ORM is not used.
    
requirements.txt contains the few Python packages necessary to run the project.
