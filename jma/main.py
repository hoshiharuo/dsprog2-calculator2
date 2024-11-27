import flet as ft
import requests

# 地域データを取得する関数
def get_weather_list():
    areas_json = "/Users/osechigakudanstar/Lecture/DS2/jma/areas.json"
    response = requests.get(areas_json)
    data = response.json()
    return data

# メイン関数
def main(page: ft.Page):
    page.title = "気象庁 地域リスト"
    page.padding = 20

    # 地域リストを取得
    area_data = get_weather_list()

    # 地域リストのUI表示
    areas = [
        ft.ListTile(
            title=ft.Text(value["name"]),  # 地域名を表示
        ) 
        for key, value in area_data["offices"].items()
    ]

    page.add(
        ft.ListView(
            controls=areas,  # 地域名をリスト表示
            expand=True
        )
    )

ft.app(main)
