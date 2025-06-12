import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pygame
import json
import os
from PIL import Image, ImageTk
import threading
import numpy as np
import wave
import io
import tempfile

class AudioTrimmer:
    def __init__(self, parent, audio_file_path, callback):
        self.parent = parent
        self.audio_file_path = audio_file_path
        self.callback = callback
        
        # Carica l'audio usando pygame
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(audio_file_path)
        
        # Leggi i dati raw del file per il trimming
        self.audio_data = self.load_audio_data(audio_file_path)
        self.sample_rate = 44100  # Default, verrà aggiornato se possibile
        
        self.setup_ui()
        
    def load_audio_data(self, file_path):
        """Carica i dati audio usando pygame e wave"""
        try:
            # Prova a caricare come WAV per ottenere info dettagliate
            if file_path.lower().endswith('.wav'):
                with wave.open(file_path, 'rb') as wav_file:
                    self.sample_rate = wav_file.getframerate()
                    self.channels = wav_file.getnchannels()
                    self.sample_width = wav_file.getsampwidth()
                    frames = wav_file.readframes(-1)
                    return np.frombuffer(frames, dtype=np.int16)
            else:
                # Per altri formati, converti temporaneamente in WAV
                temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_wav.close()
                
                # Carica con pygame e salva come WAV
                sound = pygame.mixer.Sound(file_path)
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                
                # Crea un array numpy dai dati del suono
                array = pygame.sndarray.array(sound)
                
                # Salva come WAV temporaneo
                scipy_available = False
                try:
                    from scipy.io import wavfile
                    wavfile.write(temp_wav.name, 44100, array)
                    scipy_available = True
                except ImportError:
                    # Fallback: usa wave
                    with wave.open(temp_wav.name, 'wb') as wav_file:
                        wav_file.setnchannels(2 if len(array.shape) > 1 else 1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(44100)
                        wav_file.writeframes(array.tobytes())
                
                # Leggi il WAV temporaneo
                with wave.open(temp_wav.name, 'rb') as wav_file:
                    self.sample_rate = wav_file.getframerate()
                    self.channels = wav_file.getnchannels()
                    self.sample_width = wav_file.getsampwidth()
                    frames = wav_file.readframes(-1)
                    data = np.frombuffer(frames, dtype=np.int16)
                
                # Pulisci il file temporaneo
                os.unlink(temp_wav.name)
                return data
                
        except Exception as e:
            print(f"Errore nel caricamento audio: {e}")
            # Fallback: restituisci dati dummy
            self.sample_rate = 44100
            self.channels = 2
            self.sample_width = 2
            return np.array([0] * (44100 * 5))  # 5 secondi di silenzio
        
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Taglia Audio")
        self.window.geometry("600x300")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Calcola durata in secondi
        self.duration = len(self.audio_data) / self.sample_rate
        
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Etichette per i tempi
        ttk.Label(main_frame, text="Inizio (secondi):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_var = tk.StringVar(value="0")
        self.start_entry = ttk.Entry(main_frame, textvariable=self.start_var, width=10)
        self.start_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(main_frame, text="Fine (secondi):").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.end_var = tk.StringVar(value=str(round(self.duration, 1)))
        self.end_entry = ttk.Entry(main_frame, textvariable=self.end_var, width=10)
        self.end_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Slider per selezione visuale
        ttk.Label(main_frame, text="Selezione visuale:").grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(20, 5))
        
        self.start_scale = tk.Scale(main_frame, from_=0, to=self.duration, orient=tk.HORIZONTAL, 
                                   resolution=0.1, length=200, command=self.update_start)
        self.start_scale.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.end_scale = tk.Scale(main_frame, from_=0, to=self.duration, orient=tk.HORIZONTAL, 
                                 resolution=0.1, length=200, command=self.update_end)
        self.end_scale.set(self.duration)
        self.end_scale.grid(row=2, column=2, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Pulsanti di controllo
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=4, pady=20)
        
        ttk.Button(control_frame, text="Ascolta Originale", command=self.play_original).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ascolta Selezione", command=self.play_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Conferma", command=self.confirm_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Annulla", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
    def update_start(self, value):
        self.start_var.set(value)
        
    def update_end(self, value):
        self.end_var.set(value)
        
    def play_original(self):
        threading.Thread(target=lambda: self.sound.play(), daemon=True).start()
        
    def play_selection(self):
        try:
            start = float(self.start_var.get())
            end = float(self.end_var.get())
            
            # Estrai la porzione di audio
            start_sample = int(start * self.sample_rate)
            end_sample = int(end * self.sample_rate)
            
            if start_sample >= end_sample:
                messagebox.showerror("Errore", "Il tempo di inizio deve essere inferiore al tempo di fine")
                return
                
            selection_data = self.audio_data[start_sample:end_sample]
            
            # Crea un file temporaneo per la riproduzione
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.close()
            
            # Scrivi i dati selezionati nel file temporaneo
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(selection_data.tobytes())
            
            # Riproduci il file temporaneo
            selection_sound = pygame.mixer.Sound(temp_file.name)
            threading.Thread(target=lambda: [selection_sound.play(), 
                           pygame.time.wait(int(len(selection_data) / self.sample_rate * 1000) + 100),
                           os.unlink(temp_file.name)], daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Errore", "Inserire valori numerici validi")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella riproduzione: {e}")
            
    def confirm_selection(self):
        try:
            start = float(self.start_var.get())
            end = float(self.end_var.get())
            
            if start >= end:
                messagebox.showerror("Errore", "Il tempo di inizio deve essere inferiore al tempo di fine")
                return
                
            # Estrai la porzione di audio
            start_sample = int(start * self.sample_rate)
            end_sample = int(end * self.sample_rate)
            selection_data = self.audio_data[start_sample:end_sample]
            
            # Crea il file WAV finale
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.close()
            
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(selection_data.tobytes())
            
            # Leggi i dati del file per passarli al callback
            with open(temp_file.name, 'rb') as f:
                wav_data = f.read()
            
            os.unlink(temp_file.name)
            self.callback(wav_data)
            self.window.destroy()
            
        except ValueError:
            messagebox.showerror("Errore", "Inserire valori numerici validi")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")

class SoundButton:
    def __init__(self, parent, row, col, callback):
        self.parent = parent
        self.row = row
        self.col = col
        self.callback = callback
        self.sound_data = None
        self.image_path = None
        self.hotkey = None
        self.label = f"Tasto {row}-{col}"
        self.sound_object = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame per il tasto
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=self.row, column=self.col, padx=2, pady=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tasto principale
        self.button = tk.Button(self.frame, text=self.label, command=self.play_sound,
                               width=10, height=5, bg="lightgray")
        self.button.pack(fill=tk.BOTH, expand=True)
        
        # Menu contestuale
        self.context_menu = tk.Menu(self.button, tearoff=0)
        self.context_menu.add_command(label="Carica Audio", command=self.load_audio)
        self.context_menu.add_command(label="Carica Immagine", command=self.load_image)
        self.context_menu.add_command(label="Imposta Hotkey", command=self.set_hotkey)
        self.context_menu.add_command(label="Rinomina", command=self.rename_button)
        self.context_menu.add_command(label="Rimuovi", command=self.clear_button)
        
        self.button.bind("<Button-3>", self.show_context_menu)  # Click destro
        
    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        
    def load_audio(self):
        file_path = filedialog.askopenfilename(
            title="Seleziona file audio",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.m4a *.flac")]
        )
        if file_path:
            # Apri il trimmer audio
            AudioTrimmer(self.parent.master, file_path, self.set_audio_data)
            
    def set_audio_data(self, audio_data):
        """Riceve i dati audio come bytes WAV"""
        self.sound_data = audio_data
        
        # Crea un oggetto Sound per pygame
        try:
            # Crea un file temporaneo per pygame
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            
            self.sound_object = pygame.mixer.Sound(temp_file.name)
            os.unlink(temp_file.name)
            
        except Exception as e:
            print(f"Errore nella creazione del suono: {e}")
            self.sound_object = None
            
        self.update_button_display()
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Seleziona immagine",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.image_path = file_path
            self.update_button_display()
            
    def set_hotkey(self):
        hotkey = simpledialog.askstring("Hotkey", "Inserisci combinazione tasti (es: ctrl+alt+1):")
        if hotkey:
            # Rimuovi il vecchio hotkey se presente
            if self.hotkey:
                try:
                    keyboard.remove_hotkey(self.hotkey)
                except:
                    pass
            
            # Imposta il nuovo hotkey
            try:
                keyboard.add_hotkey(hotkey, self.play_sound)
                self.hotkey = hotkey
                self.update_button_display()
            except Exception as e:
                messagebox.showerror("Errore", f"Hotkey non valida: {e}")
                
    def rename_button(self):
        new_name = simpledialog.askstring("Rinomina", "Nuovo nome:", initialvalue=self.label)
        if new_name:
            self.label = new_name
            self.update_button_display()
            
    def clear_button(self):
        if self.hotkey:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except:
                pass
        self.sound_data = None
        self.sound_object = None
        self.image_path = None
        self.hotkey = None
        self.label = f"Tasto {self.row}-{self.col}"
        self.update_button_display()
        
    def update_button_display(self):
        # Aggiorna l'aspetto del tasto
        display_text = self.label
        if self.hotkey:
            display_text += f"\n({self.hotkey})"
            
        if self.image_path and os.path.exists(self.image_path):
            try:
                # Carica e ridimensiona l'immagine
                img = Image.open(self.image_path)
                img = img.resize((60, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                self.button.config(image=photo, text=display_text, compound=tk.TOP, 
                                 bg="lightblue" if self.sound_data else "lightgray")
                self.button.image = photo  # Mantieni riferimento
            except Exception as e:
                print(f"Errore caricamento immagine: {e}")
                self.button.config(text=display_text, image="", compound=tk.NONE,
                                 bg="lightgreen" if self.sound_data else "lightgray")
        else:
            self.button.config(text=display_text, image="", compound=tk.NONE,
                             bg="lightgreen" if self.sound_data else "lightgray")
            
    def highlight(self, duration=200):
        """Visually highlight the button briefly."""
        try:
            orig_bg = self.button.cget('bg')
            self.button.config(bg='yellow')
            # Restore original background after duration milliseconds
            self.button.after(duration, lambda: self.button.config(bg=orig_bg))
        except Exception:
            pass

    def play_sound(self):
        if self.sound_object:
            self.highlight()
            # Riproduci il suono in un thread separato
            threading.Thread(target=self.sound_object.play, daemon=True).start()
            
    def get_config(self):
        return {
            'label': self.label,
            'sound_data': self.sound_data.hex() if self.sound_data else None,
            'image_path': self.image_path,
            'hotkey': self.hotkey
        }
        
    def load_config(self, config):
        self.label = config.get('label', f"Tasto {self.row}-{self.col}")
        if config.get('sound_data'):
            try:
                self.sound_data = bytes.fromhex(config['sound_data'])
                
                # Ricrea l'oggetto Sound
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_file.write(self.sound_data)
                temp_file.close()
                
                self.sound_object = pygame.mixer.Sound(temp_file.name)
                os.unlink(temp_file.name)
                
            except Exception as e:
                print(f"Errore nel caricamento del suono salvato: {e}")
                
        self.image_path = config.get('image_path')
        if config.get('hotkey'):
            try:
                keyboard.add_hotkey(config['hotkey'], self.play_sound)
                self.hotkey = config['hotkey']
            except:
                pass
        self.update_button_display()

class Soundboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Soundboard Personalizzabile")
        self.root.geometry("800x600")
        
        # Inizializza pygame per l'audio
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        
        # Griglia 4x5 di tasti
        self.buttons = []
        self.setup_ui()

        # Mappa tasti logici a SoundButton e lega binding
        self.key_map = {}
        self.root.bind_all("<KeyPress>", self.on_keypress)

        self.setup_grid()
        
        # Configurazione della finestra ridimensionabile
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Carica configurazione se esistente
        self.load_config()
        
        # Gestione chiusura finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Salva Configurazione", command=self.save_config)
        file_menu.add_command(label="Carica Configurazione", command=self.load_config)
        file_menu.add_command(label="Esci", command=self.on_closing)
        
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(toolbar, text="Soundboard Personalizzabile", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
    def setup_grid(self):
        # Frame per la griglia
        self.grid_frame = ttk.Frame(self.root)
        self.grid_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Define rows of keyboard keys
        keyboard_rows = [
            ["\\", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "'", "ì"],
            list("qwertyuiopè+"),
            list("asdfghjklòàù"),
            list("<zxcvbnm,.-"),
            ["space"]
        ]

        # Clear existing buttons list
        self.buttons = []

        # Configure grid rows and columns dynamically
        max_cols = max(len(r) for r in keyboard_rows)
        for i in range(max_cols):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(len(keyboard_rows)):
            self.grid_frame.rowconfigure(i, weight=1)

        # Ensure each grid cell stays square on resize
        def resize_cells(event):
            cell_size = int(min(event.width / max_cols, event.height / len(keyboard_rows)))
            for col in range(max_cols):
                self.grid_frame.columnconfigure(col, minsize=cell_size)
            for row in range(len(keyboard_rows)):
                self.grid_frame.rowconfigure(row, minsize=cell_size)
        self.grid_frame.bind("<Configure>", resize_cells)

        # Crea i tasti basati sui tasti della tastiera
        for row_idx, key_row in enumerate(keyboard_rows):
            button_row = []
            for col_idx, key in enumerate(key_row):
                btn = SoundButton(self.grid_frame, row_idx, col_idx, self.button_callback)
                # Set label to the keyboard key
                btn.label = key
                btn.update_button_display()
                # Registra il tasto nella mappa per il binding Tkinter
                self.key_map[key] = btn
                button_row.append(btn)
            self.buttons.append(button_row)

    def on_keypress(self, event):
        # Gestisce la pressione di un tasto fisico
        key = event.char
        if not key and event.keysym.lower() == "space":
            key = "space"
        btn = self.key_map.get(key)
        if btn:
            btn.play_sound()
            
    def button_callback(self, button):
        # Callback per i tasti (se necessario)
        pass
        
    def save_config(self):
        config = {
            'buttons': []
        }
        
        for row in self.buttons:
            row_config = []
            for button in row:
                row_config.append(button.get_config())
            config['buttons'].append(row_config)
            
        try:
            with open('soundboard_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Successo", "Configurazione salvata!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")
            
    def load_config(self):
        try:
            if os.path.exists('soundboard_config.json'):
                with open('soundboard_config.json', 'r') as f:
                    config = json.load(f)
                    
                if 'buttons' in config:
                    for row_idx, row_config in enumerate(config['buttons']):
                        for col_idx, button_config in enumerate(row_config):
                            if row_idx < len(self.buttons) and col_idx < len(self.buttons[row_idx]):
                                self.buttons[row_idx][col_idx].load_config(button_config)
        except Exception as e:
            print(f"Errore caricamento configurazione: {e}")
            
    def on_closing(self):
        # Salva automaticamente la configurazione
        self.save_config()
        
        # Rimuovi tutti gli hotkey
        for row in self.buttons:
            for button in row:
                if button.hotkey:
                    try:
                        keyboard.remove_hotkey(button.hotkey)
                    except:
                        pass
        
        # Chiudi pygame
        pygame.mixer.quit()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Soundboard()
    app.run()