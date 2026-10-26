import sys

class DevNull:
    def write(self, msg): pass
    def flush(self): pass

sys.stdout = DevNull()
sys.stderr = DevNull()

import flet as ft

def main(page: ft.Page):
    page.title = "Справочник домов"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    def button_click(e):
        tf.value = "Кнопка нажата! Приложение работает!"
        page.update()

    tf = ft.Text("Приложение успешно запущено!", size=18, color=ft.colors.GREEN, weight=ft.FontWeight.BOLD)
    btn = ft.ElevatedButton("Нажми меня", on_click=button_click)

    page.add(
        ft.Column([
            ft.Icon(ft.icons.CHECK_CIRCLE, size=60, color=ft.colors.GREEN),
            tf,
            ft.Container(height=20),
            btn
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
