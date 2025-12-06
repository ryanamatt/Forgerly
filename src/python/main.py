import sys
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow

def main() -> None:
    """
    The entry point of the Narrative Forge application. 
    
    It initializes the :py:class:`~PyQt6.QtWidgets.QApplication`, creates and 
    shows the :py:class:`~app.main_window.MainWindow`, and starts the Qt event loop.
    
    :rtype: None
    """
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()