import sys
sys.path.append('src/base')
sys.path.append('src/core')
from gui.app import App
import threading

if __name__ == '__main__':
    App().show()