
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# Generate API key (replace this with a securely stored key in production)
VALID_API_KEY = "Bearer " + secrets.token_urlsafe(32)

class LotteryResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.String(50), nullable=False)
    draw_numbers = db.Column(db.String(50), nullable=False)

@app.route('/api/lottery_results', methods=['GET'])
@limiter.limit("10 per minute")
def get_lottery_results():
    api_key = request.headers.get('Authorization')
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    results = LotteryResult.query.all()
    return jsonify([{"game_type": r.game_type, "draw_numbers": r.draw_numbers} for r in results])

@app.route('/api/check_numbers', methods=['POST'])
@limiter.limit("5 per minute")
def check_numbers():
    api_key = request.headers.get('Authorization')
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_numbers = data.get('numbers')
    result = LotteryResult.query.filter_by(draw_numbers=user_numbers).first()
    if result:
        return jsonify({'status': 'win', 'game_type': result.game_type})
    return jsonify({'status': 'lose'}), 404

if __name__ == '__main__':
    app.run(debug=True)
