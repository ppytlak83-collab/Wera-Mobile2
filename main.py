from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
import math
import random
import json
import time

# --- MODUŁ KOMUNIKACJI (BRIDGE) ---
class WeraBridge:
    def __init__(self):
        self.is_connected = False
        self.packet_id = 0

    def connect(self):
        self.is_connected = True
        return {"status": "OK", "msg": "CONNECTED"}

    def disconnect(self):
        self.is_connected = False
        return {"status": "OK", "msg": "DISCONNECTED"}

    def sync_data(self, telemetry_data):
        if not self.is_connected:
            return None
        self.packet_id += 1
        
        # Symulacja odpowiedzi z serwera
        response = {
            "ack": self.packet_id,
            "directive": "SYSTEM_OK"
        }
        
        # Logika dyrektyw
        temp = telemetry_data.get("temp", 0)
        if temp > 80:
            response["directive"] = "CRITICAL: REDUCE POWER"
        elif temp > 60:
            response["directive"] = "WARN: HIGH TEMP"
        elif telemetry_data.get("mode") == "AUTO":
             response["directive"] = "AUTO_OPTIMIZING"
            
        return response

class WeraInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, **kwargs)
        
        self.bridge = WeraBridge()
        self.current_temp_val = 40.0
        self.time_counter = 0.0
        
        # 1. NAGŁÓWEK
        self.add_widget(Label(
            text="[ WERA 3.0 - MOBILE ]", 
            size_hint_y=None, height=40, 
            color=(0, 1, 0.5, 1), bold=True
        ))
        
        # 2. TELEMETRIA
        self.tele_box = BoxLayout(orientation='vertical', size_hint_y=None, height=140, spacing=5)
        self.live_load = Label(text="OBCIAZENIE: 0%", font_size='18sp', color=(1, 0.4, 0.4, 1))
        self.live_temp = Label(text="TEMP: 40.0 C", font_size='18sp', color=(1, 0.9, 0, 1))
        self.net_status = Label(text="SIEC: OFFLINE", font_size='14sp', color=(0.5, 0.5, 0.5, 1))
        self.directive_log = Label(text="DYREKTYWA: BRAK", font_size='12sp')
        
        self.tele_box.add_widget(self.live_load)
        self.tele_box.add_widget(self.live_temp)
        self.tele_box.add_widget(self.net_status)
        self.tele_box.add_widget(self.directive_log)
        self.add_widget(self.tele_box)

        self.power_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        self.add_widget(self.power_bar)

        # 3. PRZYCISKI STEROWANIA
        self.box_buttons = BoxLayout(size_hint_y=None, height=60, spacing=10)
        
        self.btn_auto = ToggleButton(
            text="AUTOPILOT", 
            background_color=(0, 0.4, 0.8, 1), bold=True
        )
        self.btn_net = ToggleButton(
            text="LACZE DANYCH", 
            background_color=(0, 0.8, 0.4, 1), bold=True
        )
        
        self.box_buttons.add_widget(self.btn_auto)
        self.box_buttons.add_widget(self.btn_net)
        self.add_widget(self.box_buttons)

        # 4. SUWAKI
        scroll = ScrollView(size_hint=(1, 1))
        self.ctrl_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=30, padding=[10, 20])
        self.ctrl_layout.bind(minimum_height=self.ctrl_layout.setter('height'))

        self.sliders = {}
        # Parametry w pętli
        params = [("Moc", 50, "%"), ("Chlodzenie", 50, "%"), ("Freq", 200, "Hz")]

        for p_name, p_start, p_unit in params:
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=5)
            lbl = Label(text=f"{p_name}: {p_start}{p_unit}", bold=True)
            sld = Slider(min=0, max=100 if p_name != "Freq" else 500, value=p_start, size_hint_y=None, height=50)
            
            # Bezpieczne bindowanie (bez lambda w jednej linii)
            sld.bind(value=lambda instance, val, l=lbl, n=p_name, u=p_unit: setattr(l, 'text', f"{n}: {int(val)}{u}"))
            
            self.sliders[p_name] = sld
            box.add_widget(lbl)
            box.add_widget(sld)
            self.ctrl_layout.add_widget(box)

        scroll.add_widget(self.ctrl_layout)
        self.add_widget(scroll)

        # 5. PRZYCISK WYJSCIA (Poprawiony)
        self.btn_exit = Button(
            text="ZAMKNIJ SYSTEM", 
            size_hint_y=None, height=50, 
            background_color=(0.8, 0, 0, 1), bold=True
        )
        # Bindowanie do metody, a nie do lambda
        self.btn_exit.bind(on_press=self.zamknij_aplikacje)
        self.add_widget(self.btn_exit)

        Clock.schedule_interval(self.update_system, 0.2)

    # Nowa metoda zamiast lambda (bezpieczna dla Pydroid)
    def zamknij_aplikacje(self, instance):
        App.get_running_app().stop()

    def update_system(self, dt):
        self.time_counter += dt
        
        # AUTOPILOT
        if self.btn_auto.state == 'down':
            val_moc = 70 + (10 * math.sin(self.time_counter * 0.5))
            val_freq = 300 + (20 * math.cos(self.time_counter * 0.3))
            self.sliders["Moc"].value = val_moc
            self.sliders["Freq"].value = val_freq

        # BRIDGE (SIEC)
        if self.btn_net.state == 'down':
            if not self.bridge.is_connected:
                self.bridge.connect()
                self.net_status.text = "SIEC: POLACZONO"
                self.net_status.color = (0, 1, 0, 1)
            
            data = {
                "temp": self.current_temp_val,
                "power": self.sliders["Moc"].value,
                "mode": "AUTO" if self.btn_auto.state == 'down' else "MAN"
            }
            
            resp = self.bridge.sync_data(data)
            if resp:
                cmd = resp["directive"]
                self.directive_log.text = f"CMD: {cmd}"
                if "CRITICAL" in cmd:
                    self.directive_log.color = (1, 0, 0, 1)
                else:
                    self.directive_log.color = (0, 1, 1, 1)
        else:
            if self.bridge.is_connected:
                self.bridge.disconnect()
                self.net_status.text = "SIEC: ROZLACZONO"
                self.net_status.color = (1, 0.5, 0, 1)
                self.directive_log.text = "CMD: ---"

        # FIZYKA
        p = self.sliders["Moc"].value
        c = self.sliders["Chlodzenie"].value
        f = self.sliders["Freq"].value
        self.power_bar.value = p
        
        tgt = 35 + (p * 0.45) + (max(0, f-300)*0.1) - (c * 0.35)
        self.current_temp_val += (tgt - self.current_temp_val) * 0.15
        
        self.live_temp.text = f"TEMP: {self.current_temp_val:.1f} C"
        
        if self.current_temp_val > 85: self.live_temp.color = (1, 0, 0, 1)
        else: self.live_temp.color = (0, 1, 0, 1)

        load = min(100, max(0, p + random.uniform(-1, 1)))
        self.live_load.text = f"OBCIAZENIE: {int(load)}%"

class WeraApp(App):
    def build(self): return WeraInterface()

if __name__ == "__main__":
    WeraApp().run()
