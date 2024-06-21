from flask import Flask, render_template, request, jsonify,send_file
import pickle
import numpy as np
import requests
from io import BytesIO

popular_df = pickle.load(open("DataSet/popular.pkl", "rb"))
books = pickle.load(open("DataSet/Books.pkl", "rb"))
similarity_scores = pickle.load(open("DataSet/similarity_scores.pkl", "rb"))
pt = pickle.load(open("DataSet/pt.pkl", "rb"))


app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        book_name=list(popular_df["Book-Title"].values),
        author=list(popular_df["Book-Author"].values),
        img=list(popular_df["Image-URL-M"].values),
        votes=list(popular_df["num_ratings"].values),
        rating=list(popular_df["avg_rating"].values),
    )


@app.route("/recommend")
def recommend_ui():
    return render_template(
        "recommend.html",
    )


@app.route("/recommend_books", methods=["POST"])
def recommend():
    user_input = request.form.get("user_input")
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(
        list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True
    )[1:10]
    data = []
    for i in similar_items:
        item = []
        temp_df = books[books["Book-Title"] == pt.index[i[0]]]
        item.append(list(temp_df.drop_duplicates("Book-Title")["Book-Title"].values))
        item.append(list(temp_df.drop_duplicates("Book-Title")["Book-Author"].values))
        item.append(list(temp_df.drop_duplicates("Book-Title")["Image-URL-M"].values))
        item.append(list(temp_df.drop_duplicates("Book-Title")["ISBN"].values))  
        data.append(item)
    print(data)

    return render_template("recommend.html", data=data)


# For The APIs :


# Api for Popular Books
@app.route("/api/popular")
def popular():
    popular_books = popular_df.to_dict(orient="records")
    return jsonify(popular_books)


# Api for Recommend Books
@app.route("/api/recommend", methods=["POST"])
def recommend_book():
    book = request.form.get("book")

    if not book:
        return jsonify({"error": "No book provided"}), 400

    if book not in pt.index:
        return jsonify({"error": "Book not found"}), 404

    index = np.where(pt.index == book)[0][0]
    similar_items = sorted(
        list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True
    )[1:10]

    recommendations = []
    for i in similar_items:
        temp_df = books[books["Book-Title"] == pt.index[i[0]]]
        recommendation = {
            "title": temp_df["Book-Title"].values[0],
            "author": temp_df["Book-Author"].values[0],
            "image_url": temp_df["Image-URL-M"].values[0],
            "isbn": temp_df["ISBN"].values[0],
        }
        recommendations.append(recommendation)

    return jsonify(recommendations)


# Api for all Books

with open("DataSet/books.pkl", "rb") as f:
    books = pickle.load(f)

# Convert to dictionary only once
books_dict = books.to_dict(orient="records")


@app.route("/api/books", methods=["POST"])
def all_books():
    # Get form data from the POST request
    page = request.form.get("page", 2, type=int)
    per_page = request.form.get("per_page", 10, type=int)

    # Calculate start and end indices
    start = (page - 1) * per_page
    end = start + per_page

    # Slice the list to get the requested page of results
    paginated_books = books_dict[start:end]

    # Return the paginated results as JSON
    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": len(books_dict),
            "total_pages": (len(books_dict) + per_page - 1) // per_page,
            "data": paginated_books,
        }
    )


@app.route("/proxy-image")
def proxy_image():
    image_url = request.args.get("url")
    if not image_url:
        return "No URL provided", 400

    response = requests.get(image_url)
    if response.status_code != 200:
        return (
            f"Failed to fetch image, status code: {response.status_code}",
            response.status_code,
        )

    return send_file(BytesIO(response.content), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
