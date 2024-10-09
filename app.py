from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
DATABASE = 'ranking.db'

# SQLite接続設定
def create_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row  # データを辞書形式で取得する
    return connection

# 初期化時にテーブル作成
def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    
    # campaignsテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT NOT NULL,
            name TEXT NOT NULL,
            total_pages INTEGER NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL
        )
    ''')

    # processed_dataテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT NOT NULL,
            rank INTEGER,
            name TEXT,
            item TEXT,
            datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
        )
    ''')
    
    connection.commit()
    connection.close()

# キャンペーンの表示
@app.route('/')
def index():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM campaigns")
    campaigns = cursor.fetchall()
    connection.close()
    return render_template('campaigns.html', campaigns=campaigns)

# キャンペーンの追加
@app.route('/add_campaign', methods=['POST'])
def add_campaign():
    campaign_id = request.form['campaign_id']  # campaign_idを取得
    name = request.form['name']
    total_pages = request.form['total_pages']
    start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%dT%H:%M")

    connection = create_connection()
    cursor = connection.cursor()
    query = '''
        INSERT INTO campaigns (campaign_id, name, total_pages, start_time, end_time)
        VALUES (?, ?, ?, ?, ?)
    '''
    cursor.execute(query, (campaign_id, name, total_pages, start_time, end_time))
    connection.commit()
    connection.close()

    return redirect(url_for('index'))
# キャンペーンの削除
@app.route('/delete_campaign/<int:id>')
def delete_campaign(id):
    connection = create_connection()
    cursor = connection.cursor()
    query = "DELETE FROM campaigns WHERE id = ?"
    cursor.execute(query, (id,))
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

# キャンペーン自動実行のチェック
@app.route('/run_campaigns')
def run_campaigns():
    now = datetime.now()
    connection = create_connection()
    cursor = connection.cursor()
    query = '''
        SELECT * FROM campaigns
        WHERE start_time <= ? AND end_time >= ?
    '''
    cursor.execute(query, (now, now))
    active_campaigns = cursor.fetchall()
    connection.close()

    # ここで各キャンペーンのデータを取得・処理
    for campaign in active_campaigns:
        get_all_pages_and_save(campaign)
    
    return "Campaigns executed successfully"

# データ取得処理 (例)
def save_processed_data(campaign_id, rank, name, item):
    connection = create_connection()
    cursor = connection.cursor()
    query = '''
        INSERT INTO processed_data (campaign_id, rank, name, item, datetime)
        VALUES (?, ?, ?, ?, ?)
    '''
    current_time = datetime.now()  # 現在の時刻を取得
    try:
        cursor.execute(query, (campaign_id, rank, name, item, current_time))
        connection.commit()
        print(f"Data saved: Campaign ID: {campaign_id}, Rank: {rank}, Name: {name}, Item: {item}, Time: {current_time}")
    except sqlite3.Error as e:
        print(f"Error saving data: {e}")
    finally:
        connection.close()

def get_all_pages_and_save(campaign_id, total_pages):
    uid = "acd5795fa3a75066ff8b5f04ff36b708"  # 固定のUID
    for page in range(1, total_pages + 1):
        url = f"https://tapi.puyoquest.jp/html/guild_ranking_sp_boss_rush/?campaign_id={campaign_id}&page={page}&uid={uid}"
        print(f"Fetching data from: {url}")
        
        # リクエストを送信してHTMLを取得
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            ranking_areas = soup.select('div.ranking_area')  # ランキングエリアを取得
            
            # デバッグ用に取得された要素を表示
            print(f"Found {len(ranking_areas)} ranking areas")
            
            for ranking_area in ranking_areas:
                rank_element = ranking_area.select_one('p.rank')
                name_element = ranking_area.select_one('p.rank_user')
                item_element = ranking_area.select_one('p.progress_icon_b')
                
                # 要素が存在するか確認
                if rank_element and name_element and item_element:
                    rank = rank_element.text.strip()
                    name = name_element.text.strip()
                    item = item_element.text.strip()
                    
                    # デバッグ出力
                    print(f"Rank: {rank}, Name: {name}, Item: {item}")
                    
                    # データを保存
                    save_processed_data(campaign_id, rank, name, item)
                else:
                    print("Some elements were not found. Skipping this entry.")
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")


# キャンペーン編集画面の表示
@app.route('/edit_campaign/<int:id>', methods=['GET'])
def edit_campaign(id):
    connection = create_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM campaigns WHERE id = ?"
    cursor.execute(query, (id,))
    campaign = cursor.fetchone()
    connection.close()

    return render_template('edit_campaign.html', campaign=campaign)

# キャンペーンの更新処理
@app.route('/update_campaign/<int:id>', methods=['POST'])
def update_campaign(id):
    campaign_id = request.form['campaign_id']
    name = request.form['name']
    total_pages = request.form['total_pages']
    start_time = request.form['start_time']
    end_time = request.form['end_time']

    connection = create_connection()
    cursor = connection.cursor()
    query = '''
        UPDATE campaigns
        SET campaign_id = ?, name = ?, total_pages = ?, start_time = ?, end_time = ?
        WHERE id = ?
    '''
    cursor.execute(query, (campaign_id, name, total_pages, start_time, end_time, id))
    connection.commit()
    connection.close()

    return redirect(url_for('index'))

    if campaign:
        # データ取得処理を呼び出す
        get_all_pages_and_save(campaign)
        return f"Data for campaign {campaign_id} fetched successfully."
    else:
        return f"Campaign with ID {campaign_id} not found."

# データ表示画面
@app.route('/view_data')
def view_data():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT c.name,pd.name, pd.rank, pd.name as guild_name, pd.item, pd.datetime
        FROM processed_data pd
        JOIN campaigns c ON pd.campaign_id = c.campaign_id
        ORDER BY pd.datetime ASC
    ''')
    data = cursor.fetchall()
    connection.close()

    return render_template('view_data.html', data=data)

# 一時的に追加
@app.route('/test_campaign')
def test_campaign():
    campaign_id = "6067"  # 取得したいキャンペーンID
    total_pages = 20  # ページ数を手動で指定（キャンペーンデータがない場合）

    # データ取得処理を呼び出す
    get_all_pages_and_save(campaign_id, total_pages)

    return f"Data for campaign {campaign_id} fetched successfully and saved."

if __name__ == '__main__':
    create_table()  # アプリ起動時にテーブル作成
    app.run(debug=True)
