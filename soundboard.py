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
import socket
import pickle
import time

class NetworkManager:
    def __init__(self, soundboard_instance):
        self.soundboard = soundboard_instance
        self.server_port = 9999
        self.peers = set()  # Set di IP dei peer connessi
        self.server_socket = None
        self.is_party_mode = False
        self.server_running = False
        
    def get_local_ip(self):
        """Ottiene l'IP locale del dispositivo"""
        try:
            # Prova a ottenere l'IP dalla connessione di default
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_server(self):
        """Avvia il server per ricevere connessioni"""
        if self.server_running:
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.server_port))
            self.server_socket.listen(10)
            self.server_running = True
            
            # Thread per accettare connessioni
            threading.Thread(target=self.accept_connections, daemon=True).start()
            print(f"Server avviato su porta {self.server_port}")
            
        except Exception as e:
            print(f"Errore avvio server: {e}")
            messagebox.showerror("Errore", f"Impossibile avviare il server: {e}")
    
    def accept_connections(self):
        """Accetta connessioni in entrata"""
        while self.server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Connessione da {addr[0]}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except:
                break
    
    def handle_client(self, client_socket, addr):
        """Gestisce un client connesso"""
        try:
            while self.server_running:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                # Deserializza il messaggio
                message = pickle.loads(data)
                
                if message['type'] == 'sound_trigger':
                    # Riproduci il suono localmente
                    self.soundboard.play_sound_by_position(message['row'], message['col'])
                elif message['type'] == 'peer_discovery':
                    # Risposta alla discovery
                    response = {
                        'type': 'peer_response',
                        'ip': self.get_local_ip()
                    }
                    client_socket.send(pickle.dumps(response))
                    
        except Exception as e:
            print(f"Errore gestione client {addr[0]}: {e}")
        finally:
            client_socket.close()
    
    def connect_to_peer(self, peer_ip):
        """Connette a un peer specificato"""
        try:
            # Test di connessione
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(3)
            result = test_socket.connect_ex((peer_ip, self.server_port))
            test_socket.close()
            
            if result == 0:
                self.peers.add(peer_ip)
                print(f"Peer {peer_ip} aggiunto")
                return True
            else:
                return False
        except:
            return False
    
    def discover_peers(self):
        """Scopre automaticamente i peer sulla rete locale"""
        local_ip = self.get_local_ip()
        network = '.'.join(local_ip.split('.')[:-1]) + '.'
        
        def scan_ip(ip):
            if ip != local_ip:  # Non scansionare se stesso
                if self.connect_to_peer(ip):
                    return ip
            return None
        
        # Scansiona la rete locale (solo primi 20 IP per velocità)
        threads = []
        for i in range(1, 21):
            ip = network + str(i)
            thread = threading.Thread(target=scan_ip, args=(ip,))
            thread.start()
            threads.append(thread)
        
        # Aspetta che tutte le scansioni finiscano
        for thread in threads:
            thread.join()
    
    def broadcast_sound(self, row, col):
        """Invia il trigger del suono a tutti i peer"""
        if not self.is_party_mode or not self.peers:
            return
            
        message = {
            'type': 'sound_trigger',
            'row': row,
            'col': col,
            'timestamp': time.time()
        }
        
        data = pickle.dumps(message)
        
        # Invia a tutti i peer
        dead_peers = set()
        for peer_ip in self.peers.copy():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((peer_ip, self.server_port))
                sock.send(data)
                sock.close()
            except:
                print(f"Peer {peer_ip} non raggiungibile, rimozione...")
                dead_peers.add(peer_ip)
        
        # Rimuovi peer non raggiungibili
        self.peers -= dead_peers
    
    def stop_server(self):
        """Ferma il server"""
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        self.peers.clear()

class PartyModeDialog:
    def __init__(self, parent, network_manager):
        self.parent = parent
        self.network_manager = network_manager
        self.setup_ui()
    
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Modalità Party")
        self.window.geometry("500x400")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Stato attuale
        status_frame = ttk.LabelFrame(main_frame, text="Stato", padding="5")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Modalità Party: Disattivata")
        self.status_label.pack()
        
        local_ip = self.network_manager.get_local_ip()
        ttk.Label(status_frame, text=f"IP locale: {local_ip}").pack()
        
        # Controlli
        control_frame = ttk.LabelFrame(main_frame, text="Controlli", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.toggle_button = ttk.Button(control_frame, text="Attiva Modalità Party", 
                                       command=self.toggle_party_mode)
        self.toggle_button.pack(pady=5)
        
        ttk.Button(control_frame, text="Scopri Peer Automaticamente", 
                  command=self.discover_peers).pack(pady=2)
        
        # Connessione manuale
        manual_frame = ttk.LabelFrame(main_frame, text="Connessione Manuale", padding="5")
        manual_frame.pack(fill=tk.X, pady=(0, 10))
        
        connection_frame = ttk.Frame(manual_frame)
        connection_frame.pack(fill=tk.X)
        
        ttk.Label(connection_frame, text="IP Peer:").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(connection_frame, width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(connection_frame, text="Connetti", command=self.connect_manual).pack(side=tk.LEFT)
        
        # Lista peer
        peers_frame = ttk.LabelFrame(main_frame, text="Peer Connessi", padding="5")
        peers_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox con scrollbar
        list_frame = ttk.Frame(peers_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.peers_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.peers_listbox.yview)
        self.peers_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.peers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti gestione peer
        peer_buttons = ttk.Frame(peers_frame)
        peer_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(peer_buttons, text="Rimuovi Selezionato", 
                  command=self.remove_peer).pack(side=tk.LEFT, padx=2)
        ttk.Button(peer_buttons, text="Aggiorna Lista", 
                  command=self.update_peers_list).pack(side=tk.LEFT, padx=2)
        
        # Aggiorna la lista iniziale
        self.update_peers_list()
        self.update_status()
    
    def toggle_party_mode(self):
        if self.network_manager.is_party_mode:
            # Disattiva
            self.network_manager.is_party_mode = False
            self.network_manager.stop_server()
            self.toggle_button.config(text="Attiva Modalità Party")
        else:
            # Attiva
            self.network_manager.start_server()
            self.network_manager.is_party_mode = True
            self.toggle_button.config(text="Disattiva Modalità Party")
        
        self.update_status()
    
    def discover_peers(self):
        self.status_label.config(text="Ricerca peer in corso...")
        self.window.update()
        
        # Esegui discovery in thread separato
        def do_discovery():
            self.network_manager.discover_peers()
            self.window.after(0, lambda: [
                self.update_peers_list(),
                self.update_status()
            ])
        
        threading.Thread(target=do_discovery, daemon=True).start()
    
    def connect_manual(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Errore", "Inserire un IP valido")
            return
        
        if self.network_manager.connect_to_peer(ip):
            messagebox.showinfo("Successo", f"Connesso a {ip}")
            self.update_peers_list()
        else:
            messagebox.showerror("Errore", f"Impossibile connettersi a {ip}")
    
    def remove_peer(self):
        selection = self.peers_listbox.curselection()
        if selection:
            peer_ip = self.peers_listbox.get(selection[0])
            self.network_manager.peers.discard(peer_ip)
            self.update_peers_list()
    
    def update_peers_list(self):
        self.peers_listbox.delete(0, tk.END)
        for peer in sorted(self.network_manager.peers):
            self.peers_listbox.insert(tk.END, peer)
    
    def update_status(self):
        if self.network_manager.is_party_mode:
            peer_count = len(self.network_manager.peers)
            self.status_label.config(text=f"Modalità Party: Attiva ({peer_count} peer)")
        else:
            self.status_label.config(text="Modalità Party: Disattivata")

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
            
    def play_sound(self):
        if self.sound_object:
            # Riproduci il suono in un thread separato
            threading.Thread(target=self.sound_object.play, daemon=True).start()
            
            # Notifica la soundboard per il broadcast di rete
            self.callback(self.row, self.col)
            
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
        
        # Inizializza il network manager
        self.network_manager = NetworkManager(self)
        
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
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Salva Configurazione", command=self.save_config)
        file_menu.add_command(label="Carica Configurazione", command=self.load_config)
        file_menu.add_command(label="Esci", command=self.on_closing)
        
        # Menu per modalità party
        party_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Party Mode", menu=party_menu)
        party_menu.add_command(label="Configurazione Party", command=self.open_party_dialog)
        
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(toolbar, text="Soundboard Personalizzabile", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Indicatore stato party
        self.party_status_label = ttk.Label(toolbar, text="Party: OFF", foreground="red")
        self.party_status_label.pack(side=tk.RIGHT, padx=10)
        
        # Aggiorna stato party ogni secondo
        self.update_party_status()
        
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
    
    def button_callback(self, row, col):
        """Callback chiamato quando un tasto viene premuto"""
        # Invia il trigger ai peer se in modalità party
        if self.network_manager.is_party_mode:
            self.network_manager.broadcast_sound(row, col)
    
    def play_sound_by_position(self, row, col):
        """Riproduci suono in base alla posizione (chiamato dalla rete)"""
        if 0 <= row < len(self.buttons) and 0 <= col < len(self.buttons[row]):
            button = self.buttons[row][col]
            if button.sound_object:
                threading.Thread(target=button.sound_object.play, daemon=True).start()
    
    def open_party_dialog(self):
        """Apre la finestra di configurazione party"""
        PartyModeDialog(self.root, self.network_manager)
    
    def update_party_status(self):
        """Aggiorna l'indicatore di stato party"""
        if self.network_manager.is_party_mode:
            peer_count = len(self.network_manager.peers)
            self.party_status_label.config(text=f"Party: ON ({peer_count})", foreground="green")
        else:
            self.party_status_label.config(text="Party: OFF", foreground="red")
        
        # Richiama ogni secondo
        self.root.after(1000, self.update_party_status)
        
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
        
        # Ferma il network manager
        self.network_manager.stop_server()
        
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