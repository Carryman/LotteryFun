from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 設置速率限制，每個 IP 每分鐘最多 10 次請求
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# 生成 API 金鑰（實際應該存到環境變數）
VALID_API_KEY = "Bearer " + secrets.token_urlsafe(32)

@app.route('/')
@limiter.limit("5 per minute")  # 限制每分鐘最多 5 次請求
def welcome():
    """ 提供 API 健康檢查，顯示目前資料庫狀態 """
    try:
        # 取得資料庫中的所有表格名稱
        table_names = db.engine.table_names()

        # 取得每個表的資料數量
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

@app.route('/api/lottery_results', methods=['GET'])
@limiter.limit("10 per minute")  # 限制請求速率
def get_lottery_results():
    """ 取得開獎號碼，需要 API 金鑰 """
    api_key = request.headers.get('Authorization')
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    results = LotteryResult.query.all()
    return jsonify([{"game_type": r.game_type, "draw_numbers": r.draw_numbers} for r in results])

@app.route('/api/check_numbers', methods=['POST'])
@limiter.limit("5 per minute")  # 限制對獎請求
def check_numbers():
    """ 使用者對獎 API """
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
    app.run(host="0.0.0.0", port=5000, ssl_context=('cert.pem', 'key.pem'))
