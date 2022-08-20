import ctypes  # An included library with Python install.
import sys
def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def Deb(msg = None):
  return (f"Debug {sys._getframe().f_back.f_lineno} {msg if msg is not None else ''}")

Mbox('Your title', 'Your text' + Deb(), 1)

##  Styles:
##  0 : OK
##  1 : OK | Cancel
##  2 : Abort | Retry | Ignore
##  3 : Yes | No | Cancel
##  4 : Yes | No
##  5 : Retry | Cancel 
##  6 : Cancel | Try Again | Continue