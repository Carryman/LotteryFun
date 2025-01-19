import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

app = Flask(__name__)

# 讀取 Render PostgreSQL `DATABASE_URL`
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lottery.db")  # 預設為 SQLite（本地測試用）
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")  # 修正 SQLAlchemy 格式問題

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 設置速率限制（每個 IP 限制 10 次 / 分鐘）
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# 設定 API 金鑰（應該從環境變數讀取，但這裡示範用）
VALID_API_KEY = os.getenv("API_KEY", "Bearer " + secrets.token_urlsafe(32))

def verify_api_key():
    """ 驗證請求中的 API 金鑰 """
    api_key = request.headers.get('Authorization')
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/')
@limiter.limit("5 per minute")  # 限制每分鐘最多 5 次請求
def welcome():
    """ 顯示 API 健康狀態和資料庫內容 """
    try:
        # 取得所有資料表名稱
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
    auth_response = verify_api_key()
    if auth_response:
        return auth_response

    results = LotteryResult.query.all()
    return jsonify([{"game_type": r.game_type, "draw_numbers": r.draw_numbers} for r in results])

@app.route('/api/check_numbers', methods=['POST'])
@limiter.limit("5 per minute")  # 限制對獎請求
def check_numbers():
    """ 使用者對獎 API """
    auth_response = verify_api_key()
    if auth_response:
        return auth_response

    data = request.get_json()
    user_numbers = data.get('numbers')
    result = LotteryResult.query.filter_by(draw_numbers=user_numbers).first()
    if result:
        return jsonify({'status': 'win', 'game_type': result.game_type})
    return jsonify({'status': 'lose'}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
