import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow # ¡Importa nuestra ventana!

def load_stylesheet(app):
    """Carga la hoja de estilos QSS."""
    # Obtener la ruta absoluta al directorio del script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    style_file = os.path.join(base_dir, "style.qss")
    
    print("--- DIAGNÓSTICO DE ESTILOS ---")
    print(f"Buscando style.qss en: {style_file}")

    if os.path.exists(style_file):
        print("¡Éxito! El archivo 'style.qss' FUE ENCONTRADO.")
        try:
            with open(style_file, "r", encoding="utf-8") as f:
                style_content = f.read()
                
            # Verificamos si el contenido es válido
            if style_content.strip():
                print(f"Leyendo {len(style_content)} bytes de QSS...")
                app.setStyleSheet(style_content)
                print("¡ÉXITO! Hoja de estilos aplicada a la aplicación.")
            else:
                print("ERROR: 'style.qss' está vacío o corrupto.")
                
        except Exception as e:
            print(f"ERROR: No se pudo LEER el archivo 'style.qss'. Causa: {e}")
    else:
        print("ERROR: No se encontró 'style.qss' en la ruta.")
    
    print("--- FIN DEL DIAGNÓSTICO ---")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar un estilo básico (como fallback)
    app.setStyle("Fusion")
    
    # Cargar nuestra hoja de estilos personalizada
    load_stylesheet(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())