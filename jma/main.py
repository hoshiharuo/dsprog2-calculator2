import flet as ft
import requests

# 地域データを取得する関数
def get_region_data():
    URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    data_json = requests.get(URL).json()  # リクエストしてJSONデータを取得
    return data_json

# 天気データを取得する関数
def get_weather_data(region_code):
    URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    data_json = requests.get(URL).json()  # リクエストしてJSONデータを取得
    return data_json

# メイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.padding = 20

    # 天気予報カードを作成する関数
    def create_weather_card(date, weather, min_temp, max_temp):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(date, weight="bold", size=16),
                        ft.Icon(ft.Icons.WB_SUNNY, size=40, color="orange"),  # 天気アイコン
                        ft.Text(weather, size=14),
                        ft.Text(f"{min_temp} / {max_temp}", size=12, color="gray"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                width=150,
                height=200,
                bgcolor="white",
                border_radius=8,
                alignment=ft.alignment.center,
            ),
        )

    # メイン画面に天気予報を表示する関数
    def show_weather(region_code):
        weather_data = get_weather_data(region_code)
        if not weather_data:
            weather_grid.controls = [ft.Text("天気データの取得に失敗しました")]
            page.update()
            return

        # 天気データを解析して1週間分を取得
        forecasts = weather_data[0]["timeSeries"][0]["areas"]
        dates = weather_data[0]["timeSeries"][0]["timeDefines"]

        # 指定された地域コードに対応するエリアデータを取得
        area = next((area for area in forecasts if area["area"]["code"] == region_code), None)
        if not area:
            weather_grid.controls = [ft.Text("該当する天気データがありません")]
            page.update()
            return

        # 1週間分の天気データをカードに追加
        cards = [
            create_weather_card(
                date=dates[i],
                weather=area["weathers"][i],
                min_temp=area["temps"][0][i] if area["temps"][0] else "N/A",
                max_temp=area["temps"][1][i] if area["temps"][1] else "N/A",
            )
            for i in range(len(dates))
        ]
        weather_grid.controls = cards
        page.update()

    # 地域リストを取得
    region_data = get_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました"))
        return

    # トップレベルの地域リストを構築
    top_regions = [
        details for code, details in region_data["offices"].items() if details.get("parent") is None
    ]

    # 地域と対応するエリアを含むナビゲーションパネルを作成
    navigation_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.ExpansionTile(
                    title=ft.Text(region["name"]),
                    controls=[
                        ft.ListTile(
                            title=ft.Text(region_data["offices"][county]["name"]),
                            on_click=lambda e, code=county: show_weather(code),
                        )
                        for county in region["children"]
                    ],
                )
                for region in top_regions
            ],
            spacing=10,
        ),
        width=250,
        bgcolor="#607D8B",
        border_radius=10,
        padding=10,
    )

    # 天気予報を表示するメイン画面
    weather_grid = ft.GridView(
        expand=True,
        runs_count=3,  # 1行に表示するカード数
        spacing=10,
        run_spacing=10,
    )

    # 全体レイアウト
    page.add(
        ft.Row(
            [
                navigation_panel,
                ft.VerticalDivider(width=1),
                weather_grid,
            ],
            expand=True,
        )
    )

ft.app(target=main)