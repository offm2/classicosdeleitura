import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import os
import pickle
import xml.etree.ElementTree as ET

# Configuration
if Window.width > 1000:
    Window.size = (400, 700)

THEMES = {
    'light': {
        'bg': (0.95, 0.95, 0.95, 1),
        'text': (0.1, 0.1, 0.1, 1),
        'menu_bg': (0.9, 0.9, 0.9, 1),
        'button': (0.2, 0.6, 0.8, 1),
        'bar_color': (0.2, 0.6, 0.8, 1)
    },
    'dark': {
        'bg': (0.1, 0.1, 0.1, 1),
        'text': (0.9, 0.9, 0.9, 1),
        'menu_bg': (0.15, 0.15, 0.15, 1),
        'button': (0.3, 0.3, 0.3, 1),
        'bar_color': (0.4, 0.7, 1, 1)
    }
}

# Book data using your provided main.py structure
BOOKS = {
    "Livro-1": {"path": "xml/A-Morgadinha-dos-canaviais.xml", "save_file": "files/1.sav", "name": "Morgadinha"},
    "Livro-2": {"path": "xml/Os_Maias.xml", "save_file": "files/2.sav", "name": "Os Maias"},
    "Livro-3": {"path": "xml/Amor_de.xml", "save_file": "files/3.sav", "name": "Amor de Perdição"},
    "Livro-4": {"path": "xml/A-Moreninha.xml", "save_file": "files/4.sav", "name": "A Moreninha"},
    "Book-1": {"path": "xml/holmes.xml", "save_file": "files/5.sav", "name": "Sherlock Holmes"},
    "Book-2": {"path": "xml/The_secret_adversary.xml", "save_file": "files/6.sav", "name": "The Secret Adversary"}
}

class SplashScreen(Screen):
    def on_enter(self):
        layout = BoxLayout(orientation='vertical', padding=dp(20))
        # Displays the logo image requested
        logo = Image(source='1.png', allow_stretch=True, keep_ratio=True)
        layout.add_widget(logo)
        self.add_widget(layout)
        Clock.schedule_once(self.switch_to_main, 3)

    def switch_to_main(self, dt):
        self.manager.current = 'reading_screen'

class ReadingScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.menu_open = False
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        theme = THEMES[self.app.theme]
        
        self.root_container = BoxLayout(orientation='horizontal')
        
        # --- SIDE MENU ---
        self.menu_layout = BoxLayout(orientation='vertical', size_hint_x=None, width=0, spacing=dp(10), padding=dp(10))
        with self.menu_layout.canvas.before:
            Color(*theme['menu_bg'])
            self.menu_bg_rect = Rectangle(size=self.menu_layout.size, pos=self.menu_layout.pos)
        self.menu_layout.bind(size=self._update_menu_rect, pos=self._update_menu_rect)

        menu_label = Label(text="BIBLIOTECA", color=theme['text'], bold=True, size_hint_y=None, height=dp(50))
        self.menu_layout.add_widget(menu_label)

        for key, info in BOOKS.items():
            btn = Button(text=info['name'], size_hint_y=None, height=dp(45), background_color=theme['button'])
            btn.bind(on_release=lambda x, k=key: self.app.change_book_by_key(k))
            self.menu_layout.add_widget(btn)

        # --- READING AREA ---
        reading_area = BoxLayout(orientation='vertical')
        with reading_area.canvas.before:
            Color(*theme['bg'])
            self.bg_rect = Rectangle(size=Window.size, pos=reading_area.pos)
        reading_area.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # Header & Readability
        top_bar = BoxLayout(size_hint_y=0.1, padding=dp(5), spacing=dp(5))
        menu_btn = Button(text="Menu", size_hint_x=0.2, background_color=theme['button'])
        menu_btn.bind(on_release=self.toggle_menu)
        self.title_label = Label(text="Classicos", color=theme['text'], bold=True)
        top_bar.add_widget(menu_btn)
        top_bar.add_widget(self.title_label)

        controls = BoxLayout(size_hint_y=0.08, padding=dp(5), spacing=dp(5))
        btn_dec = Button(text="A-", on_release=self.app.shrink_font)
        btn_inc = Button(text="A+", on_release=self.app.grow_font)
        btn_theme = Button(text="Mode", on_release=self.app.toggle_theme)
        controls.add_widget(btn_dec)
        controls.add_widget(btn_inc)
        controls.add_widget(btn_theme)

        # Main Text Scroll
        scroll = ScrollView(size_hint_y=0.65)
        self.app.content_label = Label(
            text="Selecione um livro...",
            font_size=dp(self.app.font_size),
            color=theme['text'],
            size_hint_y=None,
            text_size=(Window.width - dp(40), None),
            valign='top', halign='left', padding=(dp(20), dp(20))
        )
        self.app.content_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        scroll.add_widget(self.app.content_label)

        # PROGRESS SECTION
        progress_box = BoxLayout(orientation='vertical', size_hint_y=0.07, padding=(dp(20), 0))
        self.app.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        self.app.progress_label = Label(text="0%", color=theme['text'], font_size=dp(12))
        progress_box.add_widget(self.app.progress_bar)
        progress_box.add_widget(self.app.progress_label)

        # Bottom Nav
        nav = BoxLayout(size_hint_y=0.1, padding=dp(5), spacing=dp(10))
        btn_prev = Button(text="Anterior", on_release=self.app.on_previous)
        btn_next = Button(text="Próximo", on_release=self.app.on_next)
        nav.add_widget(btn_prev)
        nav.add_widget(btn_next)

        reading_area.add_widget(top_bar)
        reading_area.add_widget(controls)
        reading_area.add_widget(scroll)
        reading_area.add_widget(progress_box)
        reading_area.add_widget(nav)

        self.root_container.add_widget(self.menu_layout)
        self.root_container.add_widget(reading_area)
        self.add_widget(self.root_container)

    def toggle_menu(self, *args):
        if not self.menu_open:
            self.menu_layout.size_hint_x = 0.6
            self.menu_layout.width = Window.width * 0.6
            self.menu_open = True
        else:
            self.menu_layout.size_hint_x = None
            self.menu_layout.width = 0
            self.menu_open = False

    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_menu_rect(self, instance, value):
        self.menu_bg_rect.pos = instance.pos
        self.menu_bg_rect.size = instance.size

class ReadingApp(App):
    def build(self):
        self.theme = 'light'
        self.font_size = 18
        self.current_book_key = "Livro-1"
        self.current_page = 0
        self.total_pages = 1
        self.root_xml = None
        
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(SplashScreen(name='splash'))
        self.reading_screen = ReadingScreen(app_ref=self, name='reading_screen')
        self.sm.add_widget(self.reading_screen)
        
        self.load_book_data(self.current_book_key)
        return self.sm

    def change_book_by_key(self, key):
        self.current_book_key = key
        self.load_book_data(key)
        self.reading_screen.toggle_menu()

    def toggle_theme(self, instance):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.reading_screen.build_ui()
        self.update_content()

    def grow_font(self, instance):
        self.font_size = min(self.font_size + 2, 40)
        self.content_label.font_size = dp(self.font_size)

    def shrink_font(self, instance):
        self.font_size = max(self.font_size - 2, 12)
        self.content_label.font_size = dp(self.font_size)

    def load_book_data(self, key):
        book = BOOKS[key]
        self.reading_screen.title_label.text = book['name']
        try:
            if os.path.exists(book['path']):
                tree = ET.parse(book['path'])
                self.root_xml = tree.getroot()
                # Determine total pages based on p{n} tags
                self.total_pages = len([n for n in self.root_xml.iter() if n.tag.startswith('p')])
                
                if os.path.exists(book['save_file']):
                    with open(book['save_file'], 'rb') as f:
                        self.current_page = pickle.load(f)
                else:
                    self.current_page = 0
            self.update_content()
        except:
            self.content_label.text = "Erro ao carregar livro."

    def update_content(self):
        if self.root_xml is not None:
            page = self.root_xml.find(f"p{self.current_page}")
            self.content_label.text = page.text if page is not None else "Fim do capítulo."
            
            # Update Progress Bar
            progress_pct = (self.current_page / max(1, self.total_pages - 3)) * 100
            self.progress_bar.value = progress_pct
            self.progress_label.text = f"{int(progress_pct)}%"
            
            # Auto-save
            with open(BOOKS[self.current_book_key]['save_file'], 'wb') as f:
                pickle.dump(self.current_page, f)

    def on_next(self, instance):
        if self.current_page < self.total_pages - 3:
            self.current_page += 1
            self.update_content()

    def on_previous(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_content()

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs("files", exist_ok=True)
    os.makedirs("xml", exist_ok=True)
    ReadingApp().run()
