"""
OphtalmoPro - Application de gestion de cabinet ophtalmologique
Projet BTS Informatique
"""
import tkinter as tk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_db
from modules.login import LoginWindow


def main():
    init_db()
    root = tk.Tk()
    root.withdraw()
    login = LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
