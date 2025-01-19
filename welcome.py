
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
db = SQLAlchemy(app)

@app.route('/')
def welcome():
    try:
        # Get database table names
        table_names = db.engine.table_names()

        # Count number of records in each table
        table_counts = {table: db.session.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in table_names}

        return jsonify({
            "message": "Welcome to the Lottery API!",
            "status": "Service is running",
            "database_tables": table_names,
            "record_counts": table_counts
        })
    except Exception as e:
        return jsonify({
            "message": "Error accessing database",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
