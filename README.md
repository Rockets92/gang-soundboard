# Gang Soundboard - Soundboard Personalizzabile

Una soundboard avanzata per Windows, Linux e macOS scritta in Python con interfaccia grafica.

## Caratteristiche

- **Griglia 4x5 personalizzabile**: 20 tasti configurabili
- **Caricamento e taglio audio**: Carica file audio e seleziona porzioni specifiche
- **Immagini personalizzate**: Associa immagini ai tasti
- **Hotkey globali**: Combinazioni di tasti che funzionano anche quando l'app non ha il focus
- **Interfaccia ridimensionabile**: Si adatta automaticamente alle dimensioni della finestra
- **Salvataggio automatico**: La configurazione viene salvata automaticamente

## Installazione

1. Installa Python 3.7 o superiore
2. Installa le dipendenze:
```bash
pip install pygame Pillow pydub keyboard numpy
```

Oppure esegui:
```bash
python install_dependencies.py
```

## Formati Audio Supportati

- MP3
- WAV
- OGG
- M4A
- FLAC

## Come Usare

1. **Avvia l'applicazione**:
```bash
python soundboard.py
```

2. **Configura un tasto**:
   - Click destro su un tasto della griglia
   - Seleziona "Carica Audio"
   - Scegli il file audio
   - Usa il trimmer per selezionare la porzione desiderata
   - Opzionalmente aggiungi un'immagine e un hotkey

3. **Usa i tasti**:
   - Click sinistro per riprodurre il suono
   - Usa la combinazione di tasti impostata per riprodurre da qualsiasi applicazione

## Caratteristiche Avanzate

### Trimmer Audio
- Interfaccia visuale per selezionare porzioni di audio
- Anteprima dell'audio originale e della selezione
- Controlli precisi con slider e input numerici

### Hotkey Globali
- Funzionano anche quando l'app è in background
- Formato: `ctrl+alt+1`, `shift+f1`, `ctrl+shift+a`, etc.
- Gestione automatica dei conflitti

### Personalizzazione Visuale
- Immagini sui tasti (ridimensionate automaticamente)
- Colori diversi per tasti configurati/non configurati
- Etichette personalizzabili

## Risoluzione Problemi

### Linux
Se hai problemi con gli hotkey globali, potresti dover installare:
```bash
sudo apt-get install python3-tk python3-dev
```

### macOS
Per i permessi di accessibilità:
1. Vai in Preferenze di Sistema > Sicurezza e Privacy > Privacy
2. Seleziona "Accessibilità" 
3. Aggiungi Terminal o l'app Python

### Windows
Esegui come amministratore se gli hotkey globali non funzionano.

## File di Configurazione

La configurazione viene salvata in `soundboard_config.json` nella cartella dell'applicazione.

## Licenza

Progetto open source - sentiti libero di modificare e distribuire.
