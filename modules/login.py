"""Fenêtre de connexion."""
import tkinter as tk
from tkinter import messagebox
from utils.database import get_connection, hash_password
from utils.styles import *


class LoginWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("OphtalmoPro — Connexion")
        self.resizable(False, False)
        w, h = 420, 480
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _on_close(self):
        self.master.destroy()

    def _build(self):
        # Header bleu
        header = tk.Frame(self, bg=PRIMARY, height=130)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="👁", font=("Segoe UI", 32), bg=PRIMARY, fg="white").pack(pady=(22,2))
        tk.Label(header, text="OphtalmoPro", font=("Segoe UI",16,"bold"), bg=PRIMARY, fg="white").pack()
        tk.Label(header, text="Cabinet ophtalmologique", font=FONT_SMALL, bg=PRIMARY,
                 fg="#85B7EB").pack()

        form = tk.Frame(self, bg=BG_CARD, padx=36, pady=28)
        form.pack(fill="both", expand=True, padx=0, pady=0)

        tk.Label(form, text="Connexion", font=("Segoe UI",14,"bold"), bg=BG_CARD, fg=TEXT_MAIN).pack(anchor="w", pady=(0,6))
        tk.Label(form, text="Entrez vos identifiants pour accéder au système",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0,18))

        # Login
        tk.Label(form, text="Identifiant", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")
        self.login_var = tk.StringVar()
        e1 = tk.Entry(form, textvariable=self.login_var, font=FONT_NORMAL,
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=PRIMARY)
        e1.pack(fill="x", ipady=7, pady=(3,14))

        # Mot de passe
        tk.Label(form, text="Mot de passe", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")
        self.pwd_var = tk.StringVar()
        e2 = tk.Entry(form, textvariable=self.pwd_var, show="•", font=FONT_NORMAL,
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=PRIMARY)
        e2.pack(fill="x", ipady=7, pady=(3,6))

        tk.Label(form, text="Identifiant : edemo   |   Mot de passe : 1234",
                 font=("Segoe UI",9), bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(0,20))

        self.err_lbl = tk.Label(form, text="", font=FONT_SMALL, bg=BG_CARD, fg=DANGER)
        self.err_lbl.pack(anchor="w", pady=(0,4))

        btn = tk.Button(form, text="Se connecter", font=("Segoe UI",11,"bold"),
                        bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                        activebackground=PRIMARY_DARK, activeforeground="white",
                        command=self._login)
        btn.pack(fill="x", ipady=9)
        self.bind("<Return>", lambda e: self._login())
        e1.focus_set()

    def _login(self):
        login = self.login_var.get().strip()
        pwd   = self.pwd_var.get()
        if not login or not pwd:
            self.err_lbl.config(text="Veuillez remplir tous les champs.")
            return
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM medecins WHERE login=? AND motdepasse=?",
            (login, hash_password(pwd))
        ).fetchone()
        conn.close()
        if row:
            self.destroy()
            self._open_main(dict(row))
        else:
            self.err_lbl.config(text="Identifiant ou mot de passe incorrect.")

    def _open_main(self, medecin):
        from modules.main_window import MainWindow
        self.master.deiconify()
        MainWindow(self.master, medecin)
