from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import calendar
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.jinja_env.globals.update(enumerate=enumerate) # enumerate関数をJinja2テンプレートで利用可能にする

DATE_SCHEDULE_FILE = 'date_schedule.json'
TIMETABLE_FILE = 'timetable.json'

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
DEFAULT_CATEGORIES = {
    "仕事": "#ff9999",
    "勉強": "#99ccff",
    "プライベート": "#99ff99",
    "その他": "#cccccc"
}

# JSON読み込み/保存
def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# データ読み込み
date_schedule = load_json(DATE_SCHEDULE_FILE, [])
timetable = load_json(TIMETABLE_FILE, {day: [""] * 6 for day in WEEKDAYS})
categories = DEFAULT_CATEGORIES

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

    schedules_by_day = {}
    for item in date_schedule:
        date_obj = datetime.strptime(item['date'], "%Y-%m-%d")
        # ここで year と month が一致するかを確認し、一致する場合にのみ 'day' を定義して使用
        if date_obj.year == year and date_obj.month == month:
            day = date_obj.day # ✅ 'day' はここで定義されます
            schedules_by_day.setdefault(day, []).append(item)
            # カレンダー表示では完了した予定も表示したい場合、ここに item.get('completed', False) == False を追加しない

    return render_template("calendar.html", year=year, month=month,
                           month_days=month_days, schedules_by_day=schedules_by_day,
                           calendar_month_name=calendar.month_name[month],
                           categories=categories)

# ---------------- 日付スケジュール登録 ----------------
@app.route('/date_schedule')
def date_schedule_view():
    # カレンダー表示用のデータを用意
    year = datetime.now().year
    month = datetime.now().month
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    schedules_by_day = {}
    for item in date_schedule:
        date_obj = datetime.strptime(item['date'], "%Y-%m-%d")
        # ここで year と month が一致するかを確認し、一致する場合にのみ 'day' を定義して使用
        if date_obj.year == year and date_obj.month == month:
            day = date_obj.day # ✅ 'day' はここで定義されます
            schedules_by_day.setdefault(day, []).append(item)
            # カレンダーでは完了した予定も表示

    # Today's schedule and timetable for the bottom section
    current_date = datetime.now()
    today_date = current_date.strftime("%Y-%m-%d")
    today_weekday_index = current_date.weekday()
    today_weekday_name = WEEKDAYS[today_weekday_index]
    
    # 今日のスケジュールは未完了のものだけ表示
    today_schedules = [s for s in date_schedule if s['date'] == today_date and s.get('completed', False) == False]
    
    today_timetable = timetable.get(today_weekday_name, [""] * 6)

    # フォームのデフォルト値と最小値・最大値の設定
    current_time = current_date.strftime("%H:%M")
    today_plus_one_year = (current_date + timedelta(days=365)).strftime("%Y-%m-%d")

    # 「登録された予定」リストは未完了のものだけ表示
    uncompleted_schedules = [s for s in date_schedule if s.get('completed', False) == False]


    return render_template('date_schedule.html',
                           schedules=uncompleted_schedules,
                           categories=categories,
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
    new_item = {
        "date": request.form['date'],
        "start": request.form['start'],
        "end": request.form['end'],
        "category": request.form['category'],
        "title": request.form['title'],
        "note": request.form.get('note', ''),
        "completed": False
    }
    date_schedule.append(new_item)
    save_json(DATE_SCHEDULE_FILE, date_schedule)
    flash('予定を追加しました。')
    return redirect(url_for('date_schedule_view'))

@app.route('/date_schedule/delete/<int:idx>')
def delete_date_schedule(idx):
    if 0 <= idx < len(date_schedule):
        del date_schedule[idx]
        save_json(DATE_SCHEDULE_FILE, date_schedule)
        flash('予定を削除しました。')
    return redirect(url_for('date_schedule_view'))

# ---------------- 予定完了機能の追加 ----------------
@app.route('/date_schedule/complete/<int:idx>')
def complete_date_schedule(idx):
    if 0 <= idx < len(date_schedule):
        date_schedule[idx]['completed'] = True
        save_json(DATE_SCHEDULE_FILE, date_schedule)
        flash('予定を完了しました。')
    return redirect(url_for('date_schedule_view'))


# ---------------- 時間割管理 ----------------
@app.route("/timetable", methods=["GET", "POST"])
def timetable_view():
    if request.method == "POST":
        for day in WEEKDAYS:
            for i in range(6):
                key = f"{day}_{i+1}"
                timetable[day][i] = request.form.get(key, "")
        save_json(TIMETABLE_FILE, timetable)
        flash("時間割を保存しました")
        return redirect(url_for("timetable_view"))

    # GETリクエストは従来どおり全曜日の時間割を表示
    return render_template("timetable.html", timetable=timetable, weekdays=WEEKDAYS)

# ---------------- 今日の予定表示 ----------------
@app.route('/today')
def today_view():
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_weekday_index = datetime.now().weekday()
    today_weekday_name = WEEKDAYS[today_weekday_index]

    schedules_for_today = [s for s in date_schedule if s['date'] == today_date and s.get('completed', False) == False]
    timetable_for_today = timetable.get(today_weekday_name, [""] * 6)

    return render_template('today.html',
                           today=today_date,
                           weekday=today_weekday_name,
                           schedules=schedules_for_today,
                           timetable=timetable_for_today,
                           categories=categories)

# ---------------- Flask実行 ----------------
if __name__ == '__main__':
    app.run(debug=True)