import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pygame
import json
import os
from PIL import Image, ImageTk
import threading
import keyboard
import numpy as np
import wave
import io
import tempfile
import platform

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
        
        # Binding multipli per compatibilità cross-platform
        self.setup_context_menu_bindings()
        
    def setup_context_menu_bindings(self):
        """Configura i binding del menu contestuale per tutte le piattaforme"""
        # Rileva il sistema operativo
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Su Mac, usa Control+Click o Button-2
            self.button.bind("<Button-2>", self.show_context_menu)
            self.button.bind("<Control-Button-1>", self.show_context_menu)
        elif system == "Linux":
            # Su Linux, usa Button-3 (click destro)
            self.button.bind("<Button-3>", self.show_context_menu)
        else:  # Windows e altri
            # Su Windows, usa Button-3 (click destro)
            self.button.bind("<Button-3>", self.show_context_menu)
        
        # Aggiungi anche un doppio click come alternativa universale
        self.button.bind("<Double-Button-1>", self.show_context_menu_alt)
        
    def show_context_menu(self, event):
        """Mostra il menu contestuale"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_context_menu_alt(self, event):
        """Menu contestuale alternativo per doppio click"""
        # Mostra una finestra di dialogo con le opzioni principali
        choice = messagebox.askyesnocancel(
            "Configura Tasto", 
            f"Vuoi configurare il tasto '{self.label}'?\n\n"
            "Sì = Carica Audio\n"
            "No = Altre opzioni\n"
            "Annulla = Chiudi"
        )
        
        if choice is True:
            self.load_audio()
        elif choice is False:
            self.show_options_dialog()
    
    def show_options_dialog(self):
        """Mostra finestra di dialogo con tutte le opzioni"""
        dialog = tk.Toplevel(self.parent.master)
        dialog.title(f"Configura {self.label}")
        dialog.geometry("300x250")
        dialog.transient(self.parent.master)
        dialog.grab_set()
        
        # Centra la finestra
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"300x250+{x}+{y}")
        
        # Frame principale
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        ttk.Label(main_frame, text=f"Configura {self.label}", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 20))
        
        # Pulsanti delle opzioni
        btn_style = {'width': 20, 'pady': 5}
        
        ttk.Button(main_frame, text="🎵 Carica Audio", 
                  command=lambda: [self.load_audio(), dialog.destroy()], 
                  **btn_style).pack(pady=5)
        
        ttk.Button(main_frame, text="🖼️ Carica Immagine", 
                  command=lambda: [self.load_image(), dialog.destroy()], 
                  **btn_style).pack(pady=5)
        
        ttk.Button(main_frame, text="⌨️ Imposta Hotkey", 
                  command=lambda: [self.set_hotkey(), dialog.destroy()], 
                  **btn_style).pack(pady=5)
        
        ttk.Button(main_frame, text="✏️ Rinomina", 
                  command=lambda: [self.rename_button(), dialog.destroy()], 
                  **btn_style).pack(pady=5)
        
        ttk.Button(main_frame, text="🗑️ Rimuovi", 
                  command=lambda: [self.clear_button(), dialog.destroy()], 
                  **btn_style).pack(pady=5)
        
        # Pulsante chiudi
        ttk.Button(main_frame, text="❌ Chiudi", 
                  command=dialog.destroy, 
                  **btn_style).pack(pady=(20, 0))
        
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
            
    def play_sound(self):
        if self.sound_object:
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
        self.setup_grid()
        
        # Configurazione della finestra ridimensionabile
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Carica configurazione se esistente
        self.load_config()
        
        # Gestione chiusura finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Mostra istruzioni per Mac se necessario
        self.show_platform_instructions()
        
    def show_platform_instructions(self):
        """Mostra istruzioni specifiche per la piattaforma"""
        if platform.system() == "Darwin":  # macOS
            messagebox.showinfo(
                "Istruzioni per Mac", 
                "Per configurare i tasti:\n\n"
                "• Control + Click sui tasti\n"
                "• Oppure doppio-click\n"
                "• Oppure click con il tasto centrale del mouse\n\n"
                "Questo messaggio apparirà solo al primo avvio."
            )
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Salva Configurazione", command=self.save_config)
        file_menu.add_command(label="Carica Configurazione", command=self.load_config)
        file_menu.add_command(label="Mostra Istruzioni", command=self.show_help)
        file_menu.add_command(label="Esci", command=self.on_closing)
        
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(toolbar, text="Soundboard Personalizzabile", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Aggiungi etichetta con istruzioni per Mac
        if platform.system() == "Darwin":
            ttk.Label(toolbar, text="💡 Mac: Control+Click o doppio-click per configurare", 
                     foreground="blue", font=("Arial", 9)).pack(side=tk.RIGHT)
    
    def show_help(self):
        """Mostra finestra di aiuto"""
        help_text = """
ISTRUZIONI D'USO:

🎵 Per aggiungere suoni:
"""
        
        if platform.system() == "Darwin":  # macOS
            help_text += """• Control + Click sui tasti
• Oppure doppio-click sui tasti
• Oppure click con tasto centrale del mouse"""
        else:
            help_text += """• Click destro sui tasti"""
            
        help_text += """

🎮 Funzionalità:
• Carica file audio (MP3, WAV, OGG, etc.)
• Taglia audio prima di aggiungerlo
• Aggiungi immagini ai tasti
• Imposta hotkey (scorciatoie da tastiera)
• Rinomina i tasti
• Salvataggio automatico della configurazione

⌨️ Hotkey:
Usa combinazioni come: ctrl+1, alt+a, shift+space, etc.

🎛️ Audio Trimmer:
• Regola inizio e fine del suono
• Ascolta anteprima prima di confermare
• Usa i slider per selezione visuale
        """
        
        messagebox.showinfo("Istruzioni", help_text)
        
    def setup_grid(self):
        # Frame per la griglia
        self.grid_frame = ttk.Frame(self.root)
        self.grid_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Configura la griglia per essere ridimensionabile
        for i in range(4):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(5):
            self.grid_frame.rowconfigure(i, weight=1)
            
        # Crea i tasti
        for row in range(5):
            button_row = []
            for col in range(4):
                btn = SoundButton(self.grid_frame, row, col, self.button_callback)
                button_row.append(btn)
            self.buttons.append(button_row)
            
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