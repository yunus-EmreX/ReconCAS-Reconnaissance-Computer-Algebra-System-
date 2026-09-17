"""
ReconCAS GUI Facade (BUG-017)
Tum GUI pencerelerini ve bilesenlerini alt modullerden re-export eder.
Geriye donuk tam uyumluluk saglar.
"""

from gui.theme import THEME
from gui.widgets import AnimatedToggle
from gui.auth_window import AuthGUI
from gui.terminal_window import TerminalGUI
from gui.lab_window import LabWindow
from gui.sandbox_window import SandboxWindow
from gui.document_window import DocumentWindow
from gui.admin_window import AdminPuppetWindow

__all__ = [
    "THEME",
    "AnimatedToggle",
    "AuthGUI",
    "TerminalGUI",
    "LabWindow",
    "SandboxWindow",
    "DocumentWindow",
    "AdminPuppetWindow"
]
