import sys
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow

if __name__ == '__main__':
    # Initialize the QApplication
    app = QApplication(sys.argv)

    # app_icon = QIcon(os.path.join('assets', 'logo.png'))
    # app.setWindowIcon(app_icon)
    
    # Create the main window instance
    window = MainWindow()
    
    # Show the window
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())