import os
import requests
import datetime
import json
import yaml
import schedule
import time
import threading
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect, text, desc
import secrets

app = Flask(__name__)

# 讀取 YAML 設定檔
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

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
    game_code = db.Column(db.String(10), nullable=False)  # 遊戲代碼，例如 "A01"
    draw_numbers = db.Column(db.JSON, nullable=False)  # 遊戲獎號，存為 JSON 格式
    draw_date = db.Column(db.String(10), nullable=False)  # 日期，例如 "2025/01/22"
    update_method = db.Column(db.String(10), nullable=False)  # "手動" 或 "自動"

def get_latest_lottery_results():
    """ 取得每種遊戲的最新一期開獎號碼 """
    latest_results = {}
    try:
        game_codes = db.session.query(LotteryResult.game_code).distinct().all()
        for code in game_codes:
            latest_result = LotteryResult.query.filter_by(game_code=code[0]).order_by(desc(LotteryResult.draw_date)).first()
            if latest_result:
                latest_results[code[0]] = {
                    "draw_date": latest_result.draw_date,
                    "draw_numbers": json.loads(latest_result.draw_numbers)
                }
    except Exception as e:
        print(f"❌ 無法取得最新開獎號碼: {str(e)}")
    return latest_results

@app.route('/')
@limiter.limit("5 per minute")  # 限制每分鐘最多 5 次請求
def welcome():
    """ 顯示 API 健康狀態、資料庫內容及最新一期獎號 """
    try:
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        table_counts = {table: db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in table_names}
        
        latest_results = get_latest_lottery_results()

        return jsonify({
            "message": "Welcome to the Lottery API!",
            "status": "Service is running",
            "database_tables": table_names,
            "record_counts": table_counts,
            "latest_results": latest_results
        })
    except Exception as e:
        return jsonify({
            "message": "Error accessing database",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
