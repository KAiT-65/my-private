import csv
import json
import random
import urllib.request
import io
import sys
import _thread

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
from kivy.animation import Animation

if sys.platform not in ('android', 'ios'):
    Window.size = (450, 800)

Window.clearcolor = (0.95, 0.96, 0.98, 1)


class StyledCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SpinnerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        
        with self.canvas:
            PushMatrix()
            self.rot = Rotate(angle=0, axis=(0, 0, 1))
            Color(0.22, 0.55, 0.95, 1)
            self.rect = RoundedRectangle(size=(dp(40), dp(8)), radius=[dp(4)])
            PopMatrix()

        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.anim = Animation(angle=-360, duration=1.0)
        self.anim.repeat = True
        self.anim.start(self.rot)

    def update_canvas(self, *args):
        self.rot.origin = self.center
        self.rect.pos = (self.center_x - dp(20), self.center_y - dp(4))


class LoadingPopup(Popup):
    def __init__(self, message="Pobieranie danych...", **kwargs):
        super().__init__(**kwargs)
        self.title = ""
        self.separator_height = 0
        self.size_hint = (0.8, 0.25)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        spinner = SpinnerWidget()
        spinner.pos_hint = {'center_x': 0.5}
        content.add_widget(spinner)

        lbl = Label(
            text=message,
            font_size=sp(16),
            color=(0.2, 0.3, 0.4, 1),
            halign='center',
            valign='middle'
        )
        lbl.bind(size=lbl.setter('text_size'))
        content.add_widget(lbl)

        card = StyledCard()
        card.add_widget(content)
        self.content = card


class InstalingApp(App):
    GITHUB_USER = "KAiT-65"
    GITHUB_REPO = "my-private"
    GITHUB_BRANCH = "main"
    GITHUB_FOLDER = "dlsylwka"

    def build(self):
        self.title = ""
        self.dostepne_pliki = {}
        self.zaznaczone_pliki = set()
        
        # Logika sesji
        self.kolejka_slowek = []       # Słówka pozostałe w sesji
        self.bledne_mialy = set()       # Słówka, w których popełniono błąd przynajmniej raz
        self.aktualne_slowo = None
        self.poczatek_sesji_ilosc = 0
        self.bezbledne_za_pierwszym = 0
        self.loading_popup = None

        self.root_layout = FloatLayout()

        self.main_wrapper = BoxLayout(
            orientation='vertical',
            padding=[dp(18), dp(45), dp(18), dp(18)],
            spacing=dp(12),
            size_hint=(1, 1)
        )

        # Sekcja statusu na samej górze
        self.status_card = StyledCard(size_hint_y=0.1, padding=[dp(10), dp(5)])
        self.label_info = Label(
            text="Łączenie z serwerem...",
            font_size=sp(16),
            bold=True,
            color=(0.2, 0.3, 0.4, 1),
            halign='center',
            valign='middle'
        )
        self.label_info.bind(size=self.label_info.setter('text_size'))
        self.status_card.add_widget(self.label_info)
        self.main_wrapper.add_widget(self.status_card)

        # Kontener główny
        self.main_container = BoxLayout(orientation='vertical', size_hint_y=0.9)
        self.main_wrapper.add_widget(self.main_container)

        self.root_layout.add_widget(self.main_wrapper)

        # Krzyżyk wyjścia
        self.btn_close = Button(
            text="✕",
            font_size=sp(18),
            bold=True,
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            pos_hint={'right': 0.96, 'top': 0.98},
            background_normal='',
            background_color=(0.85, 0.35, 0.35, 1)
        )
        self.btn_close.bind(on_press=lambda x: self.pokaz_ekran_wyboru_zestawow())
        self.root_layout.add_widget(self.btn_close)

        self.pokaz_ekran_wyboru_zestawow()
        return self.root_layout

    def pokaz_loading(self, msg="Pobieranie..."):
        if not self.loading_popup:
            self.loading_popup = LoadingPopup(message=msg)
            self.loading_popup.open()

    def ukryj_loading(self):
        if self.loading_popup:
            self.loading_popup.dismiss()
            self.loading_popup = None

    # -------------------------------------------------------------------
    # EKRAN 1: Wybór zestawów + Długość sesji
    # -------------------------------------------------------------------
    def pokaz_ekran_wyboru_zestawow(self):
        self.main_container.clear_widgets()
        self.btn_close.opacity = 0
        self.btn_close.disabled = True
        self.wyczysc_pamiec()

        # Lista zestawów (ScrollView)
        list_card = StyledCard(size_hint=(1, 0.68), padding=dp(10))
        scroll = ScrollView(size_hint=(1, 1))
        self.grid_checkboxow = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.grid_checkboxow.bind(minimum_height=self.grid_checkboxow.setter('height'))
        
        scroll.add_widget(self.grid_checkboxow)
        list_card.add_widget(scroll)
        self.main_container.add_widget(list_card)

        # Panel wyboru liczby słówek
        limit_card = StyledCard(size_hint=(1, 0.12), padding=[dp(10), dp(5)], spacing=dp(10))
        lbl_limit = Label(
            text="Liczba słówek w sesji:",
            font_size=sp(15),
            color=(0.2, 0.3, 0.4, 1),
            size_hint_x=0.6,
            halign='left',
            valign='middle'
        )
        lbl_limit.bind(size=lbl_limit.setter('text_size'))
        
        self.input_limit = TextInput(
            text='10',
            font_size=sp(18),
            multiline=False,
            input_filter='int',
            size_hint_x=0.4,
            padding=[dp(8), dp(8), dp(8), dp(8)],
            halign='center',
            background_normal='',
            background_color=(0.94, 0.96, 0.98, 1)
        )
        limit_card.add_widget(lbl_limit)
        limit_card.add_widget(self.input_limit)
        self.main_container.add_widget(limit_card)

        # Przyciski
        btn_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.2,
            spacing=dp(10),
            padding=[0, dp(10), 0, 0]
        )

        btn_odswiez = Button(
            text="Odśwież",
            font_size=sp(16),
            background_normal='',
            background_color=(0.5, 0.55, 0.65, 1)
        )
        btn_odswiez.bind(on_press=lambda x: self.pobierz_liste_plikow_github())
        btn_layout.add_widget(btn_odswiez)

        btn_start = Button(
            text="Rozpocznij",
            font_size=sp(18),
            bold=True,
            background_normal='',
            background_color=(0.18, 0.72, 0.42, 1)
        )
        btn_start.bind(on_press=self.rozpocznij_nauke)
        btn_layout.add_widget(btn_start)

        self.main_container.add_widget(btn_layout)
        self.pobierz_liste_plikow_github()

    def pobierz_liste_plikow_github(self):
        self.pokaz_loading("Pobieranie zestawów...")
        _thread.start_new_thread(self._pobierz_liste_worker, ())

    def _pobierz_liste_worker(self):
        path_str = f"/{self.GITHUB_FOLDER}" if self.GITHUB_FOLDER else ""
        api_url = f"https://api.github.com/repos/{self.GITHUB_USER}/{self.GITHUB_REPO}/contents{path_str}?ref={self.GITHUB_BRANCH}"

        dostepne = {}
        error_msg = None

        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))

            for item in data:
                if item.get('type') == 'file' and item.get('name', '').endswith('.csv'):
                    dostepne[item['name']] = item['download_url']
        except Exception as e:
            error_msg = str(e)

        Clock.schedule_once(lambda dt: self._pobierz_liste_finish(dostepne, error_msg))

    def _pobierz_liste_finish(self, dostepne, error_msg):
        self.ukryj_loading()
        self.dostepne_pliki = dostepne
        self.grid_checkboxow.clear_widgets()

        if error_msg:
            self.label_info.text = f"Błąd połączenia: {error_msg}"
            return

        for nazwa in self.dostepne_pliki:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48))
            cb = CheckBox(size_hint_x=0.15, color=(0.18, 0.72, 0.42, 1))
            cb.bind(active=self.on_checkbox_active(nazwa))

            lbl = Label(
                text=nazwa,
                font_size=sp(16),
                color=(0.2, 0.25, 0.3, 1),
                size_hint_x=0.85,
                halign='left',
                valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))

            row.add_widget(cb)
            row.add_widget(lbl)
            self.grid_checkboxow.add_widget(row)

        if self.dostepne_pliki:
            self.label_info.text = "Zaznacz zestawy do nauki:"
        else:
            self.label_info.text = "Brak dostępnych zestawów."

    def on_checkbox_active(self, nazwa_pliku):
        def callback(checkbox, value):
            if value:
                self.zaznaczone_pliki.add(nazwa_pliku)
            else:
                self.zaznaczone_pliki.discard(nazwa_pliku)
        return callback

    # -------------------------------------------------------------------
    # EKRAN 2: Pytanie (Sesja)
    # -------------------------------------------------------------------
    def rozpocznij_nauke(self, instance):
        if not self.zaznaczone_pliki:
            self.label_info.text = "Wybierz przynajmniej jeden zestaw!"
            return

        self.pokaz_loading("Pobieranie słówek...")
        _thread.start_new_thread(self._rozpocznij_nauke_worker, ())

    def _rozpocznij_nauke_worker(self):
        pobrane_slowka = []
        error_msg = None

        try:
            for nazwa_pliku in self.zaznaczone_pliki:
                url = self.dostepne_pliki[nazwa_pliku]
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    csv_text = response.read().decode('utf-8')
                    f = io.StringIO(csv_text)
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2 and row[0].strip():
                            pobrane_slowka.append((row[0].strip(), row[1].strip()))
        except Exception as e:
            error_msg = str(e)

        Clock.schedule_once(lambda dt: self._rozpocznij_nauke_finish(pobrane_slowka, error_msg))

    def _rozpocznij_nauke_finish(self, pobrane_slowka, error_msg):
        self.ukryj_loading()

        if error_msg:
            self.label_info.text = f"Błąd pobierania danych: {error_msg}"
            return

        if not pobrane_slowka:
            self.label_info.text = "Wybrane zestawy są puste!"
            return

        # Odczyt ilości z TextInput
        try:
            target_limit = int(self.input_limit.text.strip())
            if target_limit <= 0:
                target_limit = 10
        except ValueError:
            target_limit = 10

        # Losowanie zestawu słówek na sesję
        random.shuffle(pobrane_slowka)
        if len(pobrane_slowka) > target_limit:
            self.kolejka_slowek = pobrane_slowka[:target_limit]
        else:
            self.kolejka_slowek = pobrane_slowka

        self.poczatek_sesji_ilosc = len(self.kolejka_slowek)
        self.bezbledne_za_pierwszym = 0
        self.bledne_mialy.clear()

        self.btn_close.opacity = 1
        self.btn_close.disabled = False
        self.nastepne_slowo()

    def pokaz_ekran_pytania(self):
        self.main_container.clear_widgets()
        self.label_info.text = f"Pozostało słówek w sesji: {len(self.kolejka_slowek)}"

        quiz_card = StyledCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=dp(20),
            spacing=dp(15)
        )

        self.label_pytanie = Label(
            text=self.aktualne_slowo[0],
            font_size=sp(32),
            bold=True,
            color=(0.1, 0.15, 0.25, 1),
            size_hint_y=0.45,
            halign='center',
            valign='middle'
        )
        self.label_pytanie.bind(size=self.label_pytanie.setter('text_size'))
        quiz_card.add_widget(self.label_pytanie)

        self.input_odpowiedz = TextInput(
            hint_text='Wpisz odpowiedź...',
            font_size=sp(20),
            multiline=False,
            size_hint_y=0.25,
            padding=[dp(12), dp(12), dp(12), dp(12)],
            background_normal='',
            background_color=(0.94, 0.96, 0.98, 1),
            foreground_color=(0.1, 0.1, 0.1, 1),
            halign='center'
        )
        self.input_odpowiedz.bind(on_text_validate=self.sprawdz_odpowiedz)
        quiz_card.add_widget(self.input_odpowiedz)

        btn_sprawdz = Button(
            text='Sprawdź',
            font_size=sp(20),
            bold=True,
            size_hint_y=0.3,
            background_normal='',
            background_color=(0.22, 0.55, 0.95, 1)
        )
        btn_sprawdz.bind(on_press=self.sprawdz_odpowiedz)
        quiz_card.add_widget(btn_sprawdz)

        self.main_container.add_widget(quiz_card)

    def sprawdz_odpowiedz(self, instance):
        if not self.aktualne_slowo:
            return

        wpisane = self.input_odpowiedz.text.strip().lower()
        poprawne = self.aktualne_slowo[1].strip().lower()
        czy_poprawne = (wpisane == poprawne)

        if czy_poprawne:
            # Usuwamy z kolejki bieżące słówko
            if self.aktualne_slowo in self.kolejka_slowek:
                self.kolejka_slowek.remove(self.aktualne_slowo)
            
            # Zliczamy, czy była to odpowiedź bezbłędna za pierwszym razem
            if self.aktualne_slowo[0] not in self.bledne_mialy:
                self.bezbledne_za_pierwszym += 1
        else:
            # Oznaczamy słówko jako z błędną odpowiedzią
            self.bledne_mialy.add(self.aktualne_slowo[0])
            
            # Przesuwamy słówko na koniec kolejki (powtórka później)
            if self.aktualne_slowo in self.kolejka_slowek:
                self.kolejka_slowek.remove(self.aktualne_slowo)
            self.kolejka_slowek.append(self.aktualne_slowo)

        self.pokaz_ekran_wyniku(czy_poprawne, wpisane, poprawne)

    # -------------------------------------------------------------------
    # EKRAN 3: Wynik odpowiedzi
    # -------------------------------------------------------------------
    def pokaz_ekran_wyniku(self, czy_poprawne, wpisane, poprawne):
        self.main_container.clear_widgets()

        result_card = StyledCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=dp(20),
            spacing=dp(12)
        )

        if czy_poprawne:
            lbl_status = Label(
                text="Super!",
                font_size=sp(36),
                bold=True,
                color=(0.18, 0.72, 0.42, 1),
                size_hint_y=0.3
            )
            lbl_details = Label(
                text=f"Słówko: {self.aktualne_slowo[0]}\nTwoja odpowiedź: {wpisane}",
                font_size=sp(20),
                color=(0.2, 0.3, 0.4, 1),
                size_hint_y=0.4,
                halign='center',
                valign='middle'
            )
        else:
            lbl_status = Label(
                text="Niestety, błąd!",
                font_size=sp(34),
                bold=True,
                color=(0.85, 0.3, 0.3, 1),
                size_hint_y=0.3
            )
            lbl_details = Label(
                text=f"Słówko: {self.aktualne_slowo[0]}\nTwoja odpowiedź: {wpisane if wpisane else '(brak)'}\nPoprawna odpowiedź: {poprawne}\n\n(Słówko powtórzy się w sesji)",
                font_size=sp(18),
                color=(0.2, 0.3, 0.4, 1),
                size_hint_y=0.4,
                halign='center',
                valign='middle'
            )

        lbl_details.bind(size=lbl_details.setter('text_size'))
        result_card.add_widget(lbl_status)
        result_card.add_widget(lbl_details)

        btn_nastepne = Button(
            text='Następne słówko ➔',
            font_size=sp(20),
            bold=True,
            size_hint_y=0.3,
            background_normal='',
            background_color=(0.18, 0.72, 0.42, 1) if czy_poprawne else (0.22, 0.55, 0.95, 1)
        )
        btn_nastepne.bind(on_press=lambda x: self.nastepne_slowo())
        result_card.add_widget(btn_nastepne)

        self.main_container.add_widget(result_card)

    def nastepne_slowo(self):
        if not self.kolejka_slowek:
            self.pokaz_ekran_podsumowania()
            return

        # Wybieramy pierwsze słówko z kolejki
        self.aktualne_slowo = self.kolejka_slowek[0]
        self.pokaz_ekran_pytania()

    # -------------------------------------------------------------------
    # EKRAN 4: Podsumowanie całej sesji
    # -------------------------------------------------------------------
    def pokaz_ekran_podsumowania(self):
        self.main_container.clear_widgets()
        self.label_info.text = "Sesja zakończona!"

        summary_card = StyledCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=dp(20),
            spacing=dp(15)
        )

        lbl_title = Label(
            text="Koniec lekcji!",
            font_size=sp(32),
            bold=True,
            color=(0.18, 0.72, 0.42, 1),
            size_hint_y=0.35
        )

        procent = int((self.bezbledne_za_pierwszym / self.poczatek_sesji_ilosc) * 100) if self.poczatek_sesji_ilosc > 0 else 0

        lbl_stats = Label(
            text=f"Bez błędów od razu:\n[b]{self.bezbledne_za_pierwszym} / {self.poczatek_sesji_ilosc}[/b] ({procent}%)",
            markup=True,
            font_size=sp(22),
            color=(0.2, 0.3, 0.4, 1),
            size_hint_y=0.4,
            halign='center',
            valign='middle'
        )
        lbl_stats.bind(size=lbl_stats.setter('text_size'))

        summary_card.add_widget(lbl_title)
        summary_card.add_widget(lbl_stats)

        btn_finish = Button(
            text='Wróć do wyboru zestawów',
            font_size=sp(18),
            bold=True,
            size_hint_y=0.25,
            background_normal='',
            background_color=(0.22, 0.55, 0.95, 1)
        )
        btn_finish.bind(on_press=lambda x: self.pokaz_ekran_wyboru_zestawow())
        summary_card.add_widget(btn_finish)

        self.main_container.add_widget(summary_card)

    def wyczysc_pamiec(self):
        self.kolejka_slowek.clear()
        self.bledne_mialy.clear()
        self.zaznaczone_pliki.clear()
        self.aktualne_slowo = None
        self.poczatek_sesji_ilosc = 0
        self.bezbledne_za_pierwszym = 0


if __name__ == '__main__':
    InstalingApp().run()