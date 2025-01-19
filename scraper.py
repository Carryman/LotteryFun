
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Database setup
from app import db, LotteryResult

def fetch_lottery_results():
    url = "https://www.taiwanlottery.com.tw/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Example: Extract Power Lottery numbers
    draw_date = datetime.now().strftime("%Y-%m-%d")
    numbers = [num.text for num in soup.select(".ball_blue")[:6]]
    draw_numbers = ','.join(numbers)

    if numbers:
        result = LotteryResult.query.filter_by(game_type="Power Lottery", draw_date=draw_date).first()
        if not result:
            new_result = LotteryResult(game_type="Power Lottery", draw_date=draw_date, draw_numbers=draw_numbers)
            db.session.add(new_result)
            db.session.commit()
            print(f"Updated Power Lottery numbers: {draw_numbers}")
        else:
            print("Numbers already exist in the database.")
    else:
        print("Failed to fetch numbers.")
