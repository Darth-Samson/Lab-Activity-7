from flask import Flask, jsonify, request, abort
import sqlite3

app = Flask(__name__)
app.config["DEBUG"] = True    # helpful during development

# -------------------------------
# In-memory data example (Books)
# -------------------------------
books = [
    {'id': 0, 'title': '1984', 'author': 'George Orwell'},
    {'id': 1, 'title': 'The Left Hand of Darkness', 'author': 'Ursula K. Le Guin'},
    {'id': 2, 'title': 'Dune', 'author': 'Frank Herbert'}
]

@app.route('/', methods=['GET'])
def home():
    return "<h1>My Flask API</h1><p>Endpoints:<br> /api/v1/resources/books/all<br> /api/v1/resources/albums</p>"

@app.route('/api/v1/resources/books/all', methods=['GET'])
def api_all():
    return jsonify(books)

@app.route('/api/v1/resources/books', methods=['GET'])
def api_filter():
    # Example: /api/v1/resources/books?id=1
    if 'id' in request.args:
        try:
            id_val = int(request.args['id'])
        except ValueError:
            abort(400, description="id must be an integer")
        results = [book for book in books if book['id'] == id_val]
        if len(results) == 0:
            abort(404)
        return jsonify(results)
    return jsonify(books)

# -------------------------------
# SQLite database example (Albums)
# -------------------------------
def query_db(query, args=(), one=False):
    conn = sqlite3.connect('chinook.db')  # Make sure chinook.db is in the same folder
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return rows if not one else (rows[0] if rows else None)

@app.route('/api/v1/resources/albums', methods=['GET'])
def api_albums():
    # Examples:
    # /api/v1/resources/albums?title=Jagged+Little+Pill
    # /api/v1/resources/albums?albumid=10
    if 'title' in request.args:
        title = request.args['title']
        rows = query_db("SELECT AlbumId, Title FROM albums WHERE Title LIKE ?", ('%'+title+'%',))
    elif 'albumid' in request.args:
        albumid = request.args['albumid']
        rows = query_db("SELECT AlbumId, Title FROM albums WHERE AlbumId = ?", (albumid,))
    else:
        rows = query_db("SELECT AlbumId, Title FROM albums LIMIT 100")

    albums = [{'AlbumId': r[0], 'Title': r[1]} for r in rows]
    return jsonify(albums)

# -------------------------------
# Error handling
# -------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="404: Resource not found"), 404

# -------------------------------
# Run the Flask app
# -------------------------------
if __name__ == '__main__':
    app.run()
