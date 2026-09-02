# ============================================================
#  ТРЕКЕР с кнопкой Старт/Стоп
# ============================================================

import threading
import time
import json
import socket
import urllib.request
import urllib.parse
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

# ========== НАСТРОЙКИ ==========
TG_TOKEN   = "8919330635:AAGJfN_gRzwHoFsExnjA0VcbV98FtU8OLRk"
TG_CHAT_ID = "1074193014"
INTERVAL   = 60
# ================================

tracker_running = False
tracker_thread  = None


def internet_ok():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def get_location():
    try:
        url = "http://ip-api.com/json/?lang=ru"
        response = urllib.request.urlopen(url, timeout=8)
        data = json.loads(response.read().decode())
        if data.get("status") == "success":
            return data
        return None
    except:
        return None


def send_telegram(loc, ts):
    maps = f"https://maps.google.com/?q={loc['lat']},{loc['lon']}"
    text = (
        f"📍 Локация\n"
        f"🕐 {ts}\n"
        f"🏙 {loc.get('city','')}, {loc.get('regionName','')}\n"
        f"📌 {loc['lat']}, {loc['lon']}\n"
        f"🗺 {maps}"
    )
    url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TG_CHAT_ID,
        "text": text
    }).encode()
    try:
        urllib.request.urlopen(url, data, timeout=10)
        return True
    except:
        return False


class TrackerApp(App):

    def build(self):
        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)

        title = Label(text="📡 GPS ТРЕКЕР", font_size=28, bold=True, size_hint=(1, 0.15))

        self.status_label = Label(text="⛔ Трекер остановлен", font_size=18, size_hint=(1, 0.15))

        self.loc_label = Label(
            text="Последняя локация:\n—",
            font_size=15,
            size_hint=(1, 0.3),
            halign="center"
        )

        self.btn = Button(
            text="▶  СТАРТ",
            font_size=26,
            bold=True,
            background_color=(0.2, 0.8, 0.2, 1),
            size_hint=(1, 0.4)
        )
        self.btn.bind(on_press=self.toggle_tracker)

        layout.add_widget(title)
        layout.add_widget(self.status_label)
        layout.add_widget(self.loc_label)
        layout.add_widget(self.btn)

        return layout

    def toggle_tracker(self, instance):
        global tracker_running, tracker_thread

        if not tracker_running:
            tracker_running = True
            self.btn.text = "⏹  СТОП"
            self.btn.background_color = (0.9, 0.2, 0.2, 1)
            self.status_label.text = "✅ Трекер работает..."
            tracker_thread = threading.Thread(target=self.run_tracker, daemon=True)
            tracker_thread.start()
        else:
            tracker_running = False
            self.btn.text = "▶  СТАРТ"
            self.btn.background_color = (0.2, 0.8, 0.2, 1)
            self.status_label.text = "⛔ Трекер остановлен"

    def run_tracker(self):
        global tracker_running
        while tracker_running:
            ts = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            if internet_ok():
                loc = get_location()
                if loc:
                    sent = send_telegram(loc, ts)
                    city = loc.get("city", "")
                    lat  = loc.get("lat", "")
                    lon  = loc.get("lon", "")
                    status = "✅ Отправлено" if sent else "❌ Ошибка"
                    location_text = f"{city}\n{lat}, {lon}\n{ts}"
                    Clock.schedule_once(lambda dt, s=status, l=location_text: self.update_ui(s, l))
                else:
                    Clock.schedule_once(lambda dt: self.update_ui("⚠️ Локация не определена", self.loc_label.text))
            else:
                Clock.schedule_once(lambda dt: self.update_ui("📵 Нет интернета", self.loc_label.text))

            for _ in range(INTERVAL):
                if not tracker_running:
                    break
                time.sleep(1)

    def update_ui(self, status, location):
        self.status_label.text = status
        self.loc_label.text = f"Последняя локация:\n{location}"


if __name__ == "__main__":
    TrackerApp().run()
