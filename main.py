from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
conn_str = "mysql+pymysql://root:CSET115@localhost/boatdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


# render a file
@app.route('/')
def index():
    return render_template('index.html')


# remember how to take user inputs?
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# get all boats
# this is done to handle requests for two routes -
@app.route('/boats/')
@app.route('/boats/<page>')
def get_boats(page=1):
    page = int(page)  # request params always come as strings. So type conversion is necessary.
    per_page = 10  # records to show per page
    boats = conn.execute(text(f"SELECT * FROM boats LIMIT {per_page} OFFSET {(page - 1) * per_page}")).all()
    print(boats)
    return render_template('boats.html', boats=boats, page=page, per_page=per_page)


@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


@app.route('/create', methods=['POST'])
def create_boat():
    # you can access the values with request.from.name
    # this name is the value of the name attribute in HTML form's input element
    # ex: print(request.form['id'])
    try:
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"),
            request.form
        )
        conn.commit()
        return render_template('boats_create.html', error=None, success="Data inserted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)

@app.route('/search', methods=['GET','POST'])
def search():
    results = []
    query = ""

    if request.method == 'POST':
        query = request.form.get('query', '').strip()

    if query:
        try:
            results = conn.execute(
                text("select * from boats where name like :search_query"),
                {"search_query": f"%{query}%"}
            ).fetchall()
        except Exception as e:
            print(f"Error fetching search results: {e}")

        return render_template("search_results.html", results = results, query = query)
    return render_template('boats_search.html', results = results, query = query)

@app.route('/detail/<int:boat_id>', methods=['GET'])
def detail(boat_id):
    boat = conn.execute(text("select * from boats where id = :boat_id"),{"boat_id":boat_id}).fetchone()
    if not boat:
        return "Boat not found",404
    return render_template('details.html', boat=boat)

@app.route('/removed/<int:boat_id>',methods=['POST'])
def removed(boat_id):
    try:
        conn.execute(text("DELETE from boats where id = :boat_id"), {"boat_id": boat_id})
        conn.commit()
        return render_template('boat_removed.html', boat_id=boat_id)
    except Exception as e:
        return f"error removing boat: {e}", 500

@app.route('/update/<int:boat_id>', methods=['POST'])
def update_boat(boat_id):
    try:
        # Get new values from the form
        new_name = request.form.get('name')
        new_type = request.form.get('type')
        new_owner_id = request.form.get('owner_id')
        new_rental_price = request.form.get('rental_price')

        # Ensure owner_id and rental_price are integers
        new_owner_id = int(new_owner_id) if new_owner_id else None
        new_rental_price = float(new_rental_price) if new_rental_price else None

        # Update query
        conn.execute(
            text("UPDATE boats SET name = :name, type = :type, owner_id = :owner_id, rental_price = :rental_price WHERE id = :boat_id"),
            {"name": new_name, "type": new_type, "owner_id": new_owner_id, "rental_price": new_rental_price, "boat_id": boat_id}
        )
        conn.commit()

        # Fetch updated boat details
        updated_boat = conn.execute(
            text("SELECT * FROM boats WHERE id = :boat_id"), {"boat_id": boat_id}
        ).fetchone()

        return render_template('details.html', boat=updated_boat)
    except Exception as e:
        return f"Error updating boat: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
