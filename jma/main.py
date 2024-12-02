import flet as ft
import requests

# 天気コード対応表
WEATHER_CODES = {
    "100": {"name": "晴れ", "icon": ft.icons.WB_SUNNY},
    "101": {"name": "晴れ 時々 くもり", "icon": ft.icons.CLOUD_QUEUE},
    "103": {"name": "晴れ 時々 雨", "icon": ft.icons.UMBRELLA},
    "105": {"name": "晴れ 時々 雪", "icon": ft.icons.AC_UNIT},
    "200": {"name": "くもり", "icon": ft.icons.CLOUD},
    "201": {"name": "くもり 時々 晴れ", "icon": ft.icons.WB_SUNNY},
    "203": {"name": "くもり 時々 雨", "icon": ft.icons.UMBRELLA},
    "205": {"name": "くもり 時々 雪", "icon": ft.icons.AC_UNIT},
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

# 天気情報を取得
def get_weather_info(code):
    return WEATHER_CODES.get(code, {"name": "不明", "icon": ft.icons.HELP})

# 地域データを取得する関数
def get_region_data():
    URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        region_json = requests.get(URL).json()
        return region_json
    except Exception as e:
        print(f"地域データの取得エラー: {e}")
        return None

# 天気データを取得する関数
def get_weather_data(region_code):
    URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    try:
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

# 天気カードを作成
def create_weather_card(date, weather_code, max_temp, min_temp):
    weather_info = get_weather_info(weather_code)
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(date, weight="bold", size=16),  # 日付
                    ft.Icon(weather_info["icon"], size=40),  # 天気アイコン
                    ft.Text(weather_info["name"], size=14),  # 天気名
                    ft.Text(f"最高: {max_temp or '不明'}°C / 最低: {min_temp or '不明'}°C", size=12),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
            width=150,
            height=200,
            bgcolor="white",
            border_radius=8,
        )
    )

# メイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.padding = 10

    # 地域データを取得
    region_data = get_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました"))
        return

    # 天気表示エリア
    weather_grid = ft.GridView(
        expand=True,
        runs_count=3,  # 1行のカード数
        spacing=10,
        run_spacing=10,
    )

    # サイドバー作成
    def create_sidebar():
        sidebar = ft.Column(spacing=10)
        for region_code, region_info in region_data["centers"].items():
            region_tile = ft.ExpansionTile(
                title=ft.Text(region_info["name"]),
                controls=[
                    ft.ListTile(
                        title=ft.Text(sub_region),  # サブ地域のコードを表示
                        on_click=lambda e, code=sub_region: show_weather(code)
                    )
                    for sub_region in region_info["children"]
                ]
            )
            sidebar.controls.append(region_tile)
        return sidebar

    # 天気を表示
    def show_weather(region_code):
        weather_data = get_weather_data(region_code)
        if not weather_data or len(weather_data) < 2:  # 2つ目のデータセットを使用
            weather_grid.controls = [ft.Text("天気データの取得に失敗しました")]
            page.update()
            return

        # 週間予報のデータを使用
        forecasts = weather_data[1]["timeSeries"][0]
        dates = forecasts["timeDefines"]
        areas = forecasts["areas"]
    
        # 最初のエリアを使用
        area = areas[0]
    
        # 気温データの取得（2つ目のtimeSeriesから）
        temp_data = weather_data[1]["timeSeries"][1]
        temp_area = temp_data["areas"][0]

        cards = []
        for i in range(len(dates)):
            max_temp = temp_area.get("tempsMax", [None])[i] if "tempsMax" in temp_area else None
            min_temp = temp_area.get("tempsMin", [None])[i] if "tempsMin" in temp_area else None
        
            cards.append(
                create_weather_card(
                    date=dates[i].split("T")[0],
                    weather_code=area["weatherCodes"][i],
                    max_temp=max_temp,
                    min_temp=min_temp
                )
            )

        weather_grid.controls = cards
        page.update()

    # 全体レイアウト
    sidebar = create_sidebar()
    page.add(
        ft.Row(
            [
                ft.Container(
                    content=sidebar,
                    width=250,
                    bgcolor="#607D8B",
                    padding=10,
                    border_radius=10,
                ),
                ft.VerticalDivider(width=1),
                weather_grid,
            ],
            expand=True,
        )
    )

ft.app(target=main)
