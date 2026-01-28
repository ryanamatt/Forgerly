# src/python/utils/resource_path.py

import sys
import os

def get_resource_path(relative_path: str) -> str:
        """ 
        Get absolute path to resource, works for dev and for PyInstaller 
        
        :param relative_path: The relative path of the resource.
        :type relative_path: str
        :returns: The absolute path to the resource.
        :rtype: str
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)