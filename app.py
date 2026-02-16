from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from config import Config
from datetime import date, datetime

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"],
    )

@app.route("/")
def home():
    return redirect(url_for("books_list"))

# -------------------- AUTHORS --------------------
@app.route("/authors")
def authors_list():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM authors ORDER BY id DESC")
    authors = cur.fetchall()
    cur.close(); db.close()
    return render_template("authors.html", authors=authors)

@app.route("/authors/new", methods=["GET", "POST"])
def author_new():
    if request.method == "POST":
        name = request.form["name"].strip()
        country = request.form.get("country", "").strip() or None
        if not name:
            flash("Numele autorului este obligatoriu.", "error")
            return redirect(url_for("author_new"))

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO authors(name, country) VALUES (%s,%s)", (name, country))
            db.commit()
            flash("Autor adăugat.", "success")
        except mysql.connector.Error as e:
            db.rollback()
            flash(f"Eroare DB: {e}", "error")
        finally:
            cur.close(); db.close()

        return redirect(url_for("authors_list"))

    return render_template("author_form.html", author=None)

@app.route("/authors/<int:aid>/edit", methods=["GET", "POST"])
def author_edit(aid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM authors WHERE id=%s", (aid,))
    author = cur.fetchone()
    if not author:
        cur.close(); db.close()
        flash("Autor inexistent.", "error")
        return redirect(url_for("authors_list"))

    if request.method == "POST":
        name = request.form["name"].strip()
        country = request.form.get("country", "").strip() or None
        if not name:
            flash("Numele autorului este obligatoriu.", "error")
            return redirect(url_for("author_edit", aid=aid))

        cur2 = db.cursor()
        try:
            cur2.execute("UPDATE authors SET name=%s, country=%s WHERE id=%s", (name, country, aid))
            db.commit()
            flash("Autor actualizat.", "success")
        except mysql.connector.Error as e:
            db.rollback()
            flash(f"Eroare DB: {e}", "error")
        finally:
            cur2.close(); cur.close(); db.close()

        return redirect(url_for("authors_list"))

    cur.close(); db.close()
    return render_template("author_form.html", author=author)

@app.route("/authors/<int:aid>/delete", methods=["POST"])
def author_delete(aid):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM authors WHERE id=%s", (aid,))
        db.commit()
        flash("Autor șters.", "success")
    except mysql.connector.Error as e:
        db.rollback()
        # Cel mai des: autorul are cărți (ON DELETE RESTRICT)
        flash(f"Nu pot șterge autorul: {e}", "error")
    finally:
        cur.close(); db.close()
    return redirect(url_for("authors_list"))

# -------------------- BOOKS --------------------
@app.route("/books")
def books_list():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT b.*, a.name AS author_name
        FROM books b
        JOIN authors a ON a.id = b.author_id
        ORDER BY b.id DESC
    """)
    books = cur.fetchall()

    cur.close(); db.close()
    return render_template("books.html", books=books)

@app.route("/books/new", methods=["GET", "POST"])
def book_new():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name FROM authors ORDER BY name")
    authors = cur.fetchall()

    if request.method == "POST":
        title = request.form["title"].strip()
        author_id = int(request.form["author_id"])
        isbn = request.form.get("isbn", "").strip() or None
        year = request.form.get("year", "").strip()
        year = int(year) if year else None
        genre = request.form.get("genre", "").strip() or None

        if not title:
            flash("Titlul este obligatoriu.", "error")
            cur.close(); db.close()
            return redirect(url_for("book_new"))

        cur2 = db.cursor()
        try:
            cur2.execute(
                "INSERT INTO books(title, author_id, isbn, year, genre) VALUES (%s,%s,%s,%s,%s)",
                (title, author_id, isbn, year, genre),
            )
            db.commit()
            flash("Carte adăugată.", "success")
        except mysql.connector.Error as e:
            db.rollback()
            flash(f"Eroare DB: {e}", "error")
        finally:
            cur2.close(); cur.close(); db.close()

        return redirect(url_for("books_list"))

    cur.close(); db.close()
    return render_template("book_form.html", book=None, authors=authors)

@app.route("/books/<int:bid>/edit", methods=["GET", "POST"])
def book_edit(bid):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM books WHERE id=%s", (bid,))
    book = cur.fetchone()
    if not book:
        cur.close(); db.close()
        flash("Carte inexistentă.", "error")
        return redirect(url_for("books_list"))

    cur.execute("SELECT id, name FROM authors ORDER BY name")
    authors = cur.fetchall()

    if request.method == "POST":
        title = request.form["title"].strip()
        author_id = int(request.form["author_id"])
        isbn = request.form.get("isbn", "").strip() or None
        year = request.form.get("year", "").strip()
        year = int(year) if year else None
        genre = request.form.get("genre", "").strip() or None

        if not title:
            flash("Titlul este obligatoriu.", "error")
            cur.close(); db.close()
            return redirect(url_for("book_edit", bid=bid))

        cur2 = db.cursor()
        try:
            cur2.execute("""
                UPDATE books
                SET title=%s, author_id=%s, isbn=%s, year=%s, genre=%s
                WHERE id=%s
            """, (title, author_id, isbn, year, genre, bid))
            db.commit()
            flash("Carte actualizată.", "success")
        except mysql.connector.Error as e:
            db.rollback()
            flash(f"Eroare DB: {e}", "error")
        finally:
            cur2.close(); cur.close(); db.close()

        return redirect(url_for("books_list"))

    cur.close(); db.close()
    return render_template("book_form.html", book=book, authors=authors)

@app.route("/books/<int:bid>/delete", methods=["POST"])
def book_delete(bid):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM books WHERE id=%s", (bid,))
        db.commit()
        flash("Carte ștearsă.", "success")
    except mysql.connector.Error as e:
        db.rollback()
        flash(f"Eroare DB: {e}", "error")
    finally:
        cur.close(); db.close()
    return redirect(url_for("books_list"))

# -------------------- LOANS --------------------
@app.route("/loans")
def loans_list():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT l.*, b.title
        FROM loans l
        JOIN books b ON b.id = l.book_id
        ORDER BY l.id DESC
    """)
    loans = cur.fetchall()
    cur.close(); db.close()
    return render_template("loans.html", loans=loans)

@app.route("/loans/new", methods=["GET", "POST"])
def loan_new():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, title FROM books WHERE available=1 ORDER BY title")
    available_books = cur.fetchall()

    if request.method == "POST":
        book_id = int(request.form["book_id"])
        borrower_name = request.form["borrower_name"].strip()
        loan_date = request.form.get("loan_date") or str(date.today())
        due_date = request.form.get("due_date", "").strip() or None

        if not borrower_name:
            flash("Numele cititorului este obligatoriu.", "error")
            cur.close(); db.close()
            return redirect(url_for("loan_new"))

        cur2 = db.cursor()
        try:
            # creează împrumut
            cur2.execute("""
                INSERT INTO loans(book_id, borrower_name, loan_date, due_date)
                VALUES (%s,%s,%s,%s)
            """, (book_id, borrower_name, loan_date, due_date))

            # marchează cartea ca indisponibilă
            cur2.execute("UPDATE books SET available=0 WHERE id=%s", (book_id,))
            db.commit()
            flash("Împrumut înregistrat.", "success")
        except mysql.connector.Error as e:
            db.rollback()
            flash(f"Eroare DB: {e}", "error")
        finally:
            cur2.close(); cur.close(); db.close()

        return redirect(url_for("loans_list"))

    cur.close(); db.close()
    return render_template("loan_form.html", books=available_books)

@app.route("/loans/<int:lid>/return", methods=["POST"])
def loan_return(lid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM loans WHERE id=%s", (lid,))
    loan = cur.fetchone()
    if not loan:
        cur.close(); db.close()
        flash("Împrumut inexistent.", "error")
        return redirect(url_for("loans_list"))

    if loan["returned_date"] is not None:
        cur.close(); db.close()
        flash("Cartea este deja returnată.", "error")
        return redirect(url_for("loans_list"))

    cur2 = db.cursor()
    try:
        today = str(date.today())
        cur2.execute("UPDATE loans SET returned_date=%s WHERE id=%s", (today, lid))
        cur2.execute("UPDATE books SET available=1 WHERE id=%s", (loan["book_id"],))
        db.commit()
        flash("Returnare făcută.", "success")
    except mysql.connector.Error as e:
        db.rollback()
        flash(f"Eroare DB: {e}", "error")
    finally:
        cur2.close(); cur.close(); db.close()

    return redirect(url_for("loans_list"))

if __name__ == "__main__":
    app.run(debug=True)
