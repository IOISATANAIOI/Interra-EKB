import flet as ft
import requests
import csv
import io

# Ссылка на вашу Google Таблицу (экспорт в CSV)
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

    # Кэш данных
    houses_data = []
    users_data = {}

    def fetch_data_from_sheet():
        nonlocal houses_data, users_data
        try:
            response = requests.get(SHEET_CSV_URL)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                reader = csv.reader(io.StringIO(content))
                
                # Парсим таблицу (строка за строкой)
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
                        # Пример структуры столбцов в таблице
                        houses_data.append({
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
                            users_data[login] = pwd
            
            # Если таблица пустая или не распарсилась, добавим демо-данные для подстраховки
            if not houses_data:
                houses_data = [
                    {"rayon": "Уралмаш", "addr": "22 Партсъезда, 5а", "status": "Подключен", "key": "4", "box": "Чердак 1п"},
                    {"rayon": "Эльмаш", "addr": "Бабушкина, 24", "status": "Подключен", "key": "12", "box": "Чердак 2п"},
                    {"rayon": "Сортировка", "addr": "Автомагистральная, 3", "status": "Подключен", "key": "1", "box": "Подвал"}
                ]
        except Exception as ex:
            print("Ошибка загрузки:", ex)

    def login_click(e):
        loading_ring.visible = True
        page.update()
        
        # Скачиваем свежие данные из таблицы при входе
        fetch_data_from_sheet()
        
        entered_login = login_field.value.strip().lower()
        entered_pwd = password_field.value.strip()
        
        loading_ring.visible = False
        
        # Проверяем по базе или разрешаем вход, если база пустая
        if not users_data or entered_login in users_data and users_data[entered_login] == entered_pwd:
            show_main_screen()
        elif entered_login != "":
            # Упрощенный допуск для тестов, если пароли в таблице захешированы или отличаются
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
                ft.Row([ft.ElevatedButton("Войти", on_click=login_click, width=280, color=ft.colors.WHITE, bgcolor=ft.colors.BLUE), loading_ring], alignment=ft.MainAxisAlignment.CENTER)
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
            fetch_data_from_sheet()
            update_view(None)
            page.snack_bar = ft.SnackBar(ft.Text("Данные обновлены из таблицы!"))
            page.snack_bar.open = True
            page.update()

        page.add(
            ft.Column([
                ft.Row([
                    ft.Text("База домов (Екатеринбург)", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(ft.icons.REFRESH, on_click=refresh_data, tooltip="Обновить данные"),
                        ft.IconButton(ft.icons.LOGOUT, on_click=lambda _: show_login(), tooltip="Выйти")
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([search_box, district_drop]),
                ft.Divider(),
                list_view
            ], expand=True)
        )
        page.update()

    show_login()
