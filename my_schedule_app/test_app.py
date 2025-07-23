import json
import os
import calendar
from datetime import datetime, timedelta
import uuid # ユニークID生成のためにuuidモジュールをインポート

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.jinja_env.globals.update(enumerate=enumerate)

DATE_SCHEDULE_FILE = 'date_schedule.json'
TIMETABLE_FILE = 'timetable.json'

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
DEFAULT_CATEGORIES = {
    "仕事": "#ff9999",
    "勉強": "#99ccff",
    "プライベート": "#99ff99",
    "その他": "#cccccc"
}

# JSON読み込み/保存ヘルパー関数
def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# データアクセス関数を導入
# これにより、テストでこれらの関数をモックできるようになる
def get_date_schedule_data():
    return load_json(DATE_SCHEDULE_FILE, [])

def set_date_schedule_data(data):
    save_json(DATE_SCHEDULE_FILE, data)

def get_timetable_data():
    return load_json(TIMETABLE_FILE, {day: [""] * 6 for day in WEEKDAYS})

def set_timetable_data(data):
    save_json(TIMETABLE_FILE, data)

# ---------------- カレンダー（TOPページ） ----------------
@app.route('/')
def index():
    return redirect(url_for('date_schedule_view'))

@app.route('/calendar')
def calendar_view():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    # データを取得する際にヘルパー関数を使用
    date_schedule = get_date_schedule_data()

    schedules_by_day = {}
    for item in date_schedule:
        date_obj = datetime.strptime(item['date'], "%Y-%m-%d")
        if date_obj.year == year and date_obj.month == month:
            day = date_obj.day
            # カレンダー表示では完了した予定も表示したい場合、ここはフィルタリングしない
            schedules_by_day.setdefault(day, []).append(item)

    return render_template("calendar.html", year=year, month=month,
                           month_days=month_days, schedules_by_day=schedules_by_day,
                           calendar_month_name=calendar.month_name[month],
                           categories=DEFAULT_CATEGORIES)

# ---------------- 日付スケジュール登録 ----------------
@app.route('/date_schedule')
def date_schedule_view():
    year = datetime.now().year
    month = datetime.now().month
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    # データを取得する際にヘルパー関数を使用
    date_schedule = get_date_schedule_data()

    schedules_by_day = {}
    for item in date_schedule:
        date_obj = datetime.strptime(item['date'], "%Y-%m-%d")
        if date_obj.year == year and date_obj.month == month:
            day = date_obj.day
            schedules_by_day.setdefault(day, []).append(item)

    current_date = datetime.now()
    today_date = current_date.strftime("%Y-%m-%d")
    today_weekday_index = current_date.weekday()
    today_weekday_name = WEEKDAYS[today_weekday_index]
    
    today_schedules = [s for s in date_schedule if s['date'] == today_date and s.get('completed', False) == False]
    
    # 時間割データを取得する際にヘルパー関数を使用
    timetable = get_timetable_data()
    today_timetable = timetable.get(today_weekday_name, [""] * 6)

    current_time = current_date.strftime("%H:%M")
    today_plus_one_year = (current_date + timedelta(days=365)).strftime("%Y-%m-%d")

    uncompleted_schedules = [s for s in date_schedule if s.get('completed', False) == False]

    return render_template('date_schedule.html',
                           schedules=uncompleted_schedules,
                           categories=DEFAULT_CATEGORIES,
                           year=year,
                           month=month,
                           month_days=month_days,
                           calendar_month_name=calendar.month_name[month],
                           schedules_by_day=schedules_by_day,
                           today=today_date,
                           weekday=today_weekday_name,
                           today_schedules=today_schedules,
                           today_timetable=today_timetable,
                           current_time=current_time,
                           today_plus_one_year=today_plus_one_year)


@app.route('/date_schedule/add', methods=['POST'])
def add_date_schedule():
    # データを取得
    date_schedule = get_date_schedule_data()
    new_item = {
        "id": str(uuid.uuid4()), # ユニークIDを追加
        "date": request.form['date'],
        "start": request.form['start'],
        "end": request.form['end'],
        "category": request.form['category'],
        "title": request.form['title'],
        "note": request.form.get('note', ''),
        "completed": False
    }
    date_schedule.append(new_item)
    # データを保存
    set_date_schedule_data(date_schedule)
    flash('予定を追加しました。')
    return redirect(url_for('date_schedule_view'))

# IDベースの削除に変更
@app.route('/date_schedule/delete/<string:item_id>')
def delete_date_schedule(item_id):
    date_schedule = get_date_schedule_data() # データを取得
    original_len = len(date_schedule)
    # IDが一致しないアイテムのみを残す
    date_schedule = [item for item in date_schedule if item.get('id') != item_id]
    if len(date_schedule) < original_len: # 実際に削除されたか確認
        set_date_schedule_data(date_schedule) # データを保存
        flash('予定を削除しました。')
    else:
        flash('指定された予定は見つかりませんでした。') # IDが見つからない場合
    return redirect(url_for('date_schedule_view'))

# IDベースの完了に変更
@app.route('/date_schedule/complete/<string:item_id>')
def complete_date_schedule(item_id):
    date_schedule = get_date_schedule_data() # データを取得
    found = False
    for item in date_schedule:
        if item.get('id') == item_id:
            item['completed'] = True
            found = True
            break
    if found:
        set_date_schedule_data(date_schedule) # データを保存
        flash('予定を完了しました。')
    else:
        flash('指定された予定は見つかりませんでした。') # IDが見つからない場合
    return redirect(url_for('date_schedule_view'))


# ---------------- 時間割管理 ----------------
@app.route("/timetable", methods=["GET", "POST"])
def timetable_view():
    if request.method == "POST":
        timetable = get_timetable_data() # データを取得
        for day in WEEKDAYS:
            for i in range(6):
                key = f"{day}_{i+1}"
                timetable[day][i] = request.form.get(key, "")
        set_timetable_data(timetable) # データを保存
        flash("時間割を保存しました")
        return redirect(url_for("timetable_view"))

    # GETリクエストは従来どおり全曜日の時間割を表示
    timetable = get_timetable_data() # データを取得
    return render_template("timetable.html", timetable=timetable, weekdays=WEEKDAYS)

# ---------------- 今日の予定表示 ----------------
@app.route('/today')
def today_view():
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_weekday_index = datetime.now().weekday()
    today_weekday_name = WEEKDAYS[today_weekday_index]

    date_schedule = get_date_schedule_data() # データを取得
    schedules_for_today = [s for s in date_schedule if s['date'] == today_date and s.get('completed', False) == False]
    
    timetable = get_timetable_data() # データを取得
    timetable_for_today = timetable.get(today_weekday_name, [""] * 6)

    return render_template('today.html',
                           today=today_date,
                           weekday=today_weekday_name,
                           schedules=schedules_for_today,
                           timetable=timetable_for_today,
                           categories=DEFAULT_CATEGORIES)

# ---------------- Flask実行 ----------------
if __name__ == '__main__':
    app.run(debug=True)
