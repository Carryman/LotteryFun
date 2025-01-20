import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect
from sqlalchemy import text
import secrets


app = Flask(__name__)

# 設定 PostgreSQL 連接字串
DATABASE_URL = "postgresql://lottery_db_6opa_user:KBZVV9elK76ija0FUeQJ1ewwoAVNrfF2@dpg-cu6k97tds78s73ak6hp0-a/lottery_db_6opa"

# 修正 `postgres://` 為 `postgresql://`
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # ✅ 加入 Flask-Migrate

# 設置速率限制
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# 設定 API 金鑰
VALID_API_KEY = os.getenv("API_KEY", "Bearer " + secrets.token_urlsafe(32))

def verify_api_key():
    """ 驗證請求中的 API 金鑰 """
    api_key = request.headers.get('Authorization')
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

class LotteryResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.String(50), nullable=False)
    draw_numbers = db.Column(db.String(50), nullable=False)

# ✅ **應用啟動時，檢查是否有資料表，沒有則自動建立**
with app.app_context():
    inspector = inspect(db.engine)
    if 'lottery_results' not in inspector.get_table_names():
        print("⚠️ 沒有找到 `lottery_results` 資料表，正在建立...")
        db.create_all()
        print("✅ `lottery_results` 資料表建立完成！")

@app.route('/')
@limiter.limit("5 per minute")  # 限制每分鐘最多 5 次請求
def welcome():
    """ 顯示 API 健康狀態和資料庫內容 """
    try:
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()

        # ✅ 修正方式：使用 `text()` 來包裝 SQL 查詢
        table_counts = {table: db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in table_names}

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
