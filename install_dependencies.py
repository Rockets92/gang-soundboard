import subprocess
import sys

def install_packages():
    packages = [
        'pygame>=2.1.0',
        'Pillow>=9.0.0',
        'keyboard>=0.13.5',
        'numpy>=1.21.0',
        'PyQt6>=6.5.0',
        'qt-material>=2.14',
        'qdarkstyle>=3.0.3'
    ]
    
    print("Installazione dipendenze per UI stile glass + Material 3...")
    
    for package in packages:
        try:
            print(f"Installando {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} installato con successo")
        except subprocess.CalledProcessError:
            print(f"✗ Errore nell'installazione di {package}")
    
    print("\nInstalazione completata!")
    print("Ora puoi eseguire: python soundboard_fixed.py")

if __name__ == "__main__":
    install_packages()