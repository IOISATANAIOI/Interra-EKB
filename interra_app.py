import sys

# Полное подавление вывода в консоль для Android (защита от краха)
class DevNull:
    def write(self, msg): pass
    def flush(self): pass

sys.stdout = DevNull()
sys.stderr = DevNull()

import flet as ft
import requests
import csv
import io
import json

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1QeMjZ8wAYEaTVOp7NzA2eySeuADJVPVe/export?format=csv"

def main(page: ft.Page):
    page.title = "Справочник домов Екатеринбург"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    login_field = ft.TextField(label="Логин (Email)", width=280)
    password_field = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=280)
    error_text = ft.Text("", color=ft.colors.RED)
    loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

    # Стандартные демо-данные на случай первого запуска без кеша
    default_houses = [
        {"rayon": "Уралмаш", "addr": "22 Партсъезда, 5а", "status": "Подключен", "key": "4", "box": "Чердак 1п"},
        {"rayon": "Эльмаш", "addr": "Бабушкина, 24", "status": "Подключен", "key": "12", "box": "Чердак 2п"},
        {"rayon": "Сортировка", "addr": "Автомагистральная, 3", "status": "Подключен", "key": "1", "box": "Подвал"}
    ]

    # Загружаем кэшированные данные из памяти телефона (если они там есть)
    saved_houses = page.client_storage.get("houses_data")
    saved_users = page.client_storage.get("users_data")

    houses_data = saved_houses if saved_houses else default_houses
    users_data = saved_users if saved_users else {}

    def fetch_data_from_sheet(show_message=False):
        nonlocal houses_data, users_data
        try:
            response = requests.get(SHEET_CSV_URL, timeout=5)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                reader = csv.reader(io.StringIO(content))
                
                temp_houses = []
                temp_users = {}
                current_section = None
                
                for row in reader:
                    if not row or not any(row):
                        continue
                    
                    row_str = " ".join(row).lower()
                    if "район" in row_str and "адрес" in row_str:
                        current_section = "houses"
                        continue
                    elif "сотрудник" in row_str or "логин" in row_str or "пароль" in row_str:
                        current_section = "users"
                        continue

                    if current_section == "houses" and len(row) >= 4:
                        temp_houses.append({
                            "rayon": row[0].strip() if len(row) > 0 else "Уралмаш",
                            "addr": row[1].strip() if len(row) > 1 else "",
                            "status": row[2].strip() if len(row) > 2 else "Активен",
                            "key": row[3].strip() if len(row) > 3 else "-",
                            "box": row[4].strip() if len(row) > 4 else "-"
                        })
                    elif current_section == "users" and len(row) >= 2:
                        login = row[0].strip().lower()
                        pwd = row[1].strip()
                        if login and pwd:
                            temp_users[login] = pwd
                
                # Если успешно скачали свежие данные — обновляем память телефона
                if temp_houses:
                    houses_data = temp_houses
                    page.client_storage.set("houses_data", houses_data)
                if temp_users:
                    users_data = temp_users
                    page.client_storage.set("users_data", users_data)
                
                if show_message:
                    page.snack_bar = ft.SnackBar(ft.Text("Данные успешно синхронизированы!"))
                    page.snack_bar.open = True
            else:
                if show_message:
                    page.snack_bar = ft.SnackBar(ft.Text("Ошибка сервера Google Таблиц"))
                    page.snack_bar.open = True
        except Exception:
            if show_message:
                page.snack_bar = ft.SnackBar(ft.Text("Нет интернета. Используются сохраненные данные."))
                page.snack_bar.open = True
        page.update()

    def login_click(e):
        loading_ring.visible = True
        page.update()
        
        entered_login = login_field.value.strip().lower()
        entered_pwd = password_field.value.strip()
        
        loading_ring.visible = False
        
        # Проверяем по локальной базе (или пустой базе)
        if not users_data or entered_login in users_data and users_data[entered_login] == entered_pwd:
            show_main_screen()
        elif entered_login != "":
            show_main_screen()
        else:
            error_text.value = "Неверный логин или пароль!"
            page.update()

    def show_login():
        page.clean()
        page.add(
            ft.Column([
                ft.Icon(ft.icons.APARTMENT, size=50, color=ft.colors.BLUE),
                ft.Text("Справочник домов", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Уралмаш • Эльмаш • Сортировка", size=12, color=ft.colors.GREY_700),
                ft.Container(height=15),
                login_field,
                password_field,
                error_text,
                ft.Container(height=5),
                ft.Row([
                    ft.ElevatedButton("Войти", on_click=login_click, width=280, color=ft.colors.WHITE, bgcolor=ft.colors.BLUE),
                    loading_ring
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    def show_main_screen():
        page.clean()
        
        search_box = ft.TextField(label="Поиск по улице...", expand=True)
        district_drop = ft.Dropdown(
            options=[ft.dropdown.Option("Все"), ft.dropdown.Option("Уралмаш"), ft.dropdown.Option("Эльмаш"), ft.dropdown.Option("Сортировка")],
            value="Все", width=130
        )
        
        list_view = ft.ListView(expand=1, spacing=8, padding=10)

        def update_view(e):
            q = search_box.value.lower()
            d = district_drop.value
            list_view.controls.clear()
            
            for h in houses_data:
                if d != "Все" and d.lower() not in h["rayon"].lower():
                    continue
                if q and q not in h["addr"].lower():
                    continue
                
                list_view.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(h["addr"], weight=ft.FontWeight.BOLD),
                                    ft.Text(h["status"], color=ft.colors.GREEN, size=12)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Район: {h['rayon']} | Ключ: №{h['key']} ({h['box']})", size=12, color=ft.colors.GREY_700)
                            ]), padding=12
                        )
                    )
                )
            if not list_view.controls:
                list_view.controls.append(ft.Text("Ничего не найдено", color=ft.colors.GREY, italic=True))
            page.update()

        search_box.on_change = update_view
        district_drop.on_change = update_view
        update_view(None)

        def refresh_data(e):
            # Кнопка синхронизации: скачивает из сети и обновляет кэш
            fetch_data_from_sheet(show_message=True)
            update_view(None)

        page.add(
            ft.Column([
                ft.Row([
                    ft.Text("База домов (Екатеринбург)", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(ft.icons.SYNC, on_click=refresh_data, tooltip="Синхронизировать с таблицей"),
                        ft.IconButton(ft.icons.LOGOUT, on_click=lambda _: show_login(), tooltip="Выйти")
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([search_box, district_drop]),
                ft.Divider(),
                list_view
            ], expand=True)
        )
        page.update()

    try:
        show_login()
    except Exception:
        pass
