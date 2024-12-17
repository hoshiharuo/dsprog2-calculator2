import flet as ft
import requests
import sqlite3

WEATHER_CODES = {
    "100": {"name": "晴れ", "icon": ft.icons.WB_SUNNY},
    "101": {"name": "晴れ 時々 くもり", "icon": ft.icons.CLOUD_QUEUE},
    "103": {"name": "晴れ 時々 雨", "icon": ft.icons.UMBRELLA},
    "105": {"name": "晴れ 時々 雪", "icon": ft.icons.AC_UNIT},
    "111": {"name": "晴れ のち くもり", "icon": ft.icons.CLOUD_QUEUE},
    "200": {"name": "くもり", "icon": ft.icons.CLOUD},
    "201": {"name": "くもり 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "203": {"name": "くもり 時々 雨", "icon": ft.icons.UMBRELLA},
    "205": {"name": "くもり 時々 雪", "icon": ft.icons.AC_UNIT},
    "206": {"name": "くもり のち 雨", "icon": ft.icons.UMBRELLA},
    "260": {"name": "くもり のち 時々 雨", "icon": ft.icons.UMBRELLA},
    "300": {"name": "雨", "icon": ft.icons.UMBRELLA},
    "301": {"name": "雨 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "303": {"name": "雨 時々 雪", "icon": ft.icons.AC_UNIT},
    "306": {"name": "大雨", "icon": ft.icons.WATER_DROP},
    "400": {"name": "雪", "icon": ft.icons.AC_UNIT},
    "401": {"name": "雪 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "402": {"name": "雪 時々止む", "icon": ft.icons.STOP},
    "403": {"name": "雪 時々 雨", "icon": ft.icons.UMBRELLA},
    "405": {"name": "大雪", "icon": ft.icons.AC_UNIT},
}

def get_weather_info(code):
    return WEATHER_CODES.get(code, {"name": "不明", "icon": ft.icons.HELP})

def get_region_data():
    URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        region_json = requests.get(URL).json()
        return region_json
    except Exception as e:
        print(f"地域データの取得エラー: {e}")
        return None

def get_weather_data(region_code):
    URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        weather_json = requests.get(URL).json()
        return weather_json
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"天気データの取得エラー (コード: {region_code}): 404 Not Found")
        else:
            print(f"天気データの取得エラー (コード: {region_code}): {e}")
        return None
    except Exception as e:
        print(f"その他のエラー (コード: {region_code}): {e}")
        return None

def create_weather_card(date, weather_code, max_temp, min_temp):
    weather_info = get_weather_info(weather_code)
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        date.split("-")[0] + "-" + date.split("-")[1] + "-" + date.split("-")[2],
                        weight="bold",
                        size=14,
                        color="#2B2B2B"
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    weather_info["icon"],
                                    size=32,
                                    color="#FF9800"  
                                ),
                                ft.Container(width=8),  
                                ft.Icon(
                                    ft.icons.CLOUD,
                                    size=28,
                                    color="#78909C"  
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        margin=ft.margin.symmetric(vertical=10),
                    ),
                    ft.Text(
                        weather_info["name"],
                        size=14,
                        color="#2B2B2B",
                        weight="w500"
                    ),
                    ft.Container(height=8),  
                    ft.Row(
                        [
                            ft.Text(
                                f"{min_temp}°C",
                                size=14,
                                color="#1976D2",  
                                weight="bold"
                            ),
                            ft.Text(
                                " / ",
                                size=14,
                                color="#757575",
                            ),
                            ft.Text(
                                f"{max_temp}°C",
                                size=14,
                                color="#D32F2F",  
                                weight="bold"
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.padding.all(16),
            width=140,
            height=160,
            bgcolor=ft.colors.WHITE,
            border_radius=16,
        ),
        elevation=0,  
    )

def init_db():
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()

    # 地域テーブル
    c.execute('''
    CREATE TABLE IF NOT EXISTS regions (
        region_code TEXT PRIMARY KEY,
        region_name TEXT
    )
    ''')

    # 天気テーブル
    c.execute('''
    CREATE TABLE IF NOT EXISTS forecasts (
        region_code TEXT,
        forecast_date TEXT,
        weather_code TEXT,
        min_temp REAL,
        max_temp REAL,
        PRIMARY KEY (region_code, forecast_date),
        FOREIGN KEY (region_code) REFERENCES regions(region_code)
    )
    ''')

    conn.commit()
    conn.close()

def store_region_data_in_db(region_data):
    if not region_data:
        return

    conn = sqlite3.connect("weather.db")
    c = conn.cursor()

    for office_code, office_info in region_data["offices"].items():
        region_code = office_code
        region_name = office_info.get("name", "不明")
        c.execute('''
            INSERT OR IGNORE INTO regions (region_code, region_name)
            VALUES (?, ?)
        ''', (region_code, region_name))
    conn.commit()
    conn.close()

def store_weather_data_in_db(region_code, weather_data):
    if not weather_data or len(weather_data) < 2:
        return
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()

    forecasts = weather_data[1]["timeSeries"][0]
    dates = forecasts["timeDefines"]
    areas = forecasts["areas"]
    area = areas[0]

    temp_data = weather_data[1]["timeSeries"][1]
    temp_area = temp_data["areas"][0]

    for i in range(len(dates)):
        date = dates[i].split("T")[0]
        weather_code = area["weatherCodes"][i]
        min_temp = temp_area.get("tempsMin", [None])[i] if "tempsMin" in temp_area else None
        max_temp = temp_area.get("tempsMax", [None])[i] if "tempsMax" in temp_area else None

        c.execute('''
            INSERT OR REPLACE INTO forecasts (region_code, forecast_date, weather_code, min_temp, max_temp)
            VALUES (?, ?, ?, ?, ?)
        ''', (region_code, date, weather_code, min_temp, max_temp))

    conn.commit()
    conn.close()

def get_forecasts_from_db(region_code):
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()

    c.execute('SELECT region_name FROM regions WHERE region_code = ?', (region_code,))
    row = c.fetchone()
    region_name = row[0] if row else "不明"

    c.execute('SELECT forecast_date, weather_code, min_temp, max_temp FROM forecasts WHERE region_code = ? ORDER BY forecast_date', (region_code,))
    forecasts = c.fetchall()
    conn.close()

    return region_name, forecasts

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT

    init_db()
    region_data = get_region_data()
    store_region_data_in_db(region_data)


    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました"))
        return
    
    region_title = ft.Text("", size=20, weight="bold")

    weather_grid = ft.GridView(
        expand=True,
        runs_count=3,
        spacing=10,
        run_spacing=10,
    )

    def create_sidebar():
        sidebar = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        for region_code, region_info in region_data["centers"].items():
            region_tile = ft.ExpansionTile(
                title=ft.Text(region_info["name"], color="white"),
                controls=[
                    ft.ListTile(
                        title=ft.Column([
                            ft.Text(
                                region_data["offices"].get(sub_region, {}).get("name", "不明"),
                                color="white",
                                size=16
                            ),
                            ft.Text(
                                sub_region,
                                color="white70",
                                size=12
                            )
                        ], spacing=2),
                        on_click=lambda e, code=sub_region: show_weather_from_db(code)
                    )
                    for sub_region in region_info["children"]
                ],
            )
            sidebar.controls.append(region_tile)
        return sidebar

    def show_weather_from_db(region_code):
        region_name, forecasts = get_forecasts_from_db(region_code)
        if not forecasts:
            weather_data = get_weather_data(region_code)
            if weather_data:
                store_weather_data_in_db(region_code, weather_data)
                region_name, forecasts = get_forecasts_from_db(region_code)

        if not forecasts:
            weather_grid.controls = [ft.Text("天気データの取得に失敗しました")]
            region_title.value = ""
            page.update()
            return

        region_title.value = region_name

        cards = []
        for (forecast_date, weather_code, min_temp, max_temp) in forecasts:
            cards.append(
                create_weather_card(
                    date=forecast_date,
                    weather_code=weather_code,
                    max_temp=max_temp,
                    min_temp=min_temp
                )
            )

        weather_grid.controls = cards
        page.update()


    sidebar_container = ft.Container(
        content=create_sidebar(),
        width=250,
        bgcolor="#455A64",
        padding=10,
        border_radius=10,
    )

    right_area = ft.Column(
        [
            region_title,   
            weather_grid,   
        ],
        spacing=10,
        expand=True
    )

    page.add(
        ft.Row(
            [
                sidebar_container,
                ft.VerticalDivider(width=1),
                right_area,
            ],
            expand=True,
        )
    )

ft.app(target=main)
