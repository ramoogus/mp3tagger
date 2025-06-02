
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, USLT, ID3NoHeaderError, APIC

class MP3Editor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=10, **kwargs)
        self.selected_files = []
        self.file_chooser = FileChooserIconView(filters=["*.mp3"], multiselect=True)
        self.file_chooser.bind(on_selection=self.load_metadata)
        self.add_widget(self.file_chooser)
        self.title_input = TextInput(hint_text="Title", multiline=False, size_hint_y=None, height=40)
        self.artist_input = TextInput(hint_text="Artist", multiline=False, size_hint_y=None, height=40)
        self.album_input = TextInput(hint_text="Album", multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.title_input)
        self.add_widget(self.artist_input)
        self.add_widget(self.album_input)
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=5)
        btn_box.add_widget(self.create_button("Save Metadata", self.save_metadata))
        btn_box.add_widget(self.create_button("Fetch Metadata", self.fetch_metadata))
        btn_box.add_widget(self.create_button("Fetch Lyrics", self.embed_lyrics))
        self.add_widget(btn_box)
        other_box = BoxLayout(size_hint_y=None, height=40, spacing=5)
        other_box.add_widget(self.create_button("Add Album Art", self.select_album_art))
        other_box.add_widget(self.create_button("Rename Files", self.rename_files))
        self.add_widget(other_box)

    def create_button(self, text, callback):
        btn = Button(text=text)
        btn.bind(on_press=callback)
        return btn

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close = Button(text="Close", size_hint_y=None, height=40)
        content.add_widget(close)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close.bind(on_press=popup.dismiss)
        popup.open()

    def load_metadata(self, *args):
        self.selected_files = self.file_chooser.selection
        if not self.selected_files:
            return
        try:
            audio = EasyID3(self.selected_files[0])
            self.title_input.text = audio.get("title", [""])[0]
            self.artist_input.text = audio.get("artist", [""])[0]
            self.album_input.text = audio.get("album", [""])[0]
        except Exception as e:
            self.show_popup("Error", "Failed to read metadata.")

    def save_metadata(self, instance):
        for file in self.selected_files:
            try:
                audio = EasyID3(file)
            except:
                audio = EasyID3()
            audio["title"] = self.title_input.text
            audio["artist"] = self.artist_input.text
            audio["album"] = self.album_input.text
            audio.save(file)
        self.show_popup("Success", "Metadata saved to selected files.")

    def fetch_metadata(self, instance):
        title = self.title_input.text
        artist = self.artist_input.text
        if not title or not artist:
            self.show_popup("Missing Info", "Title and Artist required.")
            return
        try:
            query = f"https://musicbrainz.org/ws/2/recording/?query=recording:{title}+artist:{artist}&fmt=json"
            res = requests.get(query)
            data = res.json()
            recordings = data.get("recordings", [])
            if recordings:
                rec = recordings[0]
                self.title_input.text = rec.get("title", title)
                self.artist_input.text = rec["artist-credit"][0]["artist"]["name"]
                self.album_input.text = rec.get("releases", [{}])[0].get("title", "")
                self.show_popup("Success", "Metadata fetched from MusicBrainz.")
            else:
                self.show_popup("Not Found", "No metadata found.")
        except Exception:
            self.show_popup("Error", "Failed to fetch from MusicBrainz.")

    def embed_lyrics(self, instance):
        title = self.title_input.text
        artist = self.artist_input.text
        if not title or not artist:
            self.show_popup("Missing Info", "Title and Artist required.")
            return
        try:
            res = requests.get(f"https://api.lyrics.ovh/v1/{artist}/{title}")
            data = res.json()
            lyrics = data.get("lyrics", "")
            if not lyrics:
                self.show_popup("No Lyrics", "Lyrics not found.")
                return
            self._save_lyrics_to_files(lyrics)
            self.show_popup("Success", "Lyrics embedded successfully.")
        except Exception:
            self.show_popup("Error", "Failed to fetch lyrics.")

    def _save_lyrics_to_files(self, lyrics):
        for file in self.selected_files:
            try:
                audio = ID3(file)
            except ID3NoHeaderError:
                audio = ID3()
            audio.delall("USLT")
            audio["USLT"] = USLT(encoding=3, lang="eng", desc="", text=lyrics)
            audio.save(file)

    def select_album_art(self, instance):
        chooser = FileChooserListView(filters=["*.jpg", "*.jpeg", "*.png"])
        popup = Popup(title="Choose Image", content=chooser, size_hint=(0.9, 0.9))
        chooser.bind(on_selection=lambda _, sel: self.embed_album_art(sel, popup))
        popup.open()

    def embed_album_art(self, selection, popup):
        if not selection:
            return
        img_path = selection[0]
        img_data = open(img_path, 'rb').read()
        mime = "image/jpeg" if img_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
        for file in self.selected_files:
            audio = ID3(file)
            audio.delall("APIC")
            audio.add(APIC(encoding=3, mime=mime, type=3, desc=u"Cover", data=img_data))
            audio.save(file)
        popup.dismiss()
        self.show_popup("Success", "Album art embedded.")

    def rename_files(self, instance):
        renamed = 0
        for file in self.selected_files:
            try:
                audio = EasyID3(file)
                artist = audio.get("artist", [""])[0]
                title = audio.get("title", [""])[0]
                if artist and title:
                    new_name = f"{artist} - {title}.mp3"
                    new_path = os.path.join(os.path.dirname(file), new_name)
                    if not os.path.exists(new_path):
                        os.rename(file, new_path)
                        renamed += 1
            except Exception:
                continue
        self.show_popup("Rename Files", f"Renamed {renamed} files.")

class MP3TaggerApp(App):
    def build(self):
        return MP3Editor()

if __name__ == '__main__':
    MP3TaggerApp().run()
