# docs/conf.py

import os
import sys

project_root = os.path.abspath('../..')

sys.path.insert(0, os.path.join(project_root, 'src'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc.typehints' 
]

autodoc_typehints = "description"
autoclass_content = "both"