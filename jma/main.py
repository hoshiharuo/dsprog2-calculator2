import flet as ft
import requests

# 天気コード対応表
WEATHER_CODES = {
    "100": {"name": "晴れ", "icon": ft.icons.WB_SUNNY},
    "200": {"name": "曇り", "icon": ft.icons.CLOUD},
    "300": {"name": "雨", "icon": ft.icons.UMBRELLA},
    "400": {"name": "雪", "icon": ft.icons.AC_UNIT},
}

# 天気コードから天気名とアイコンを取得
def get_weather_info(code):
    return WEATHER_CODES.get(code, {"name": "不明", "icon": ft.icons.HELP})

# 地域データを取得する関数
def get_region_data():
    URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"地域データ取得エラー: {e}")
        return None

# 天気データを取得する関数
def get_weather_data(region_code):
    URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"天気データ取得エラー: {e}")
        return None

# メイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.padding = 10

    # 地域データを取得
    region_data = get_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました"))
        return

    # サイドバーの内容を更新する関数
    def update_sidebar(region_code):
        sub_areas = region_data["offices"][region_code].get("children", [])
        sub_area_tiles = [
            ft.ListTile(
                title=ft.Text(region_data["offices"][sub_code]["name"]),
                on_click=lambda e, code=sub_code: show_weather(code),
            )
            for sub_code in sub_areas
        ]
        navigation_panel.controls = sub_area_tiles
        page.update()

    # 天気を表示する関数
    def show_weather(region_code):
        weather_data = get_weather_data(region_code)
        if not weather_data:
            weather_grid.controls = [ft.Text("天気データの取得に失敗しました")]
            page.update()
            return

        # 天気データの解析
        forecasts = weather_data[0]["timeSeries"][0]["areas"]
        dates = weather_data[0]["timeSeries"][0]["timeDefines"]

        # 該当地域のデータを取得
        area = next(
            (area for area in forecasts if area["area"]["code"] == region_code), None
        )
        if not area:
            weather_grid.controls = [ft.Text("該当する天気データがありません")]
            page.update()
            return

        # 天気カードの作成
        cards = [
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(dates[i].split("T")[0]),  # 日付（年月日部分）
                            ft.Icon(get_weather_info(area["weatherCodes"][i])["icon"]),
                            ft.Text(get_weather_info(area["weatherCodes"][i])["name"]),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=150,
                    height=200,
                    padding=10,
                    bgcolor="white",
                    border_radius=8,
                )
            )
            for i in range(len(dates))
        ]
        weather_grid.controls = cards
        page.update()

    # サイドバーの初期表示
    navigation_panel = ft.Column(
        controls=[
            ft.ExpansionTile(
                title=ft.Text(details["name"]),
                on_click=lambda e, code=code: update_sidebar(code),
            )
            for code, details in region_data["offices"].items() if details.get("parent") is None
        ],
        spacing=10,
    )

    # 天気表示エリア
    weather_grid = ft.Column(expand=True)

    # 全体レイアウト
    page.add(
        ft.Row(
            [
                ft.Container(
                    content=navigation_panel,
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
