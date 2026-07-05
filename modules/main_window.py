"""Fenêtre principale avec barre latérale et zone de contenu."""
import tkinter as tk
from utils.styles import *


class MainWindow:
    PAGES = [
        ("Tableau de bord", "dashboard",    "🏠"),
        ("Patients",         "patients",     "👥"),
        ("Rendez-vous",      "rendezvous",   "📅"),
        ("Consultations",    "consultations","🩺"),
        ("Analyses",         "analyses",     "🔬"),
        ("Ordonnances",      "ordonnances",  "💊"),
        ("Paramètres",       "parametres",   "⚙"),
    ]

    def __init__(self, root, medecin):
        self.root = root
        self.medecin = medecin
        self.root.title("OphtalmoPro")
        w, h = WIN_W, WIN_H
        self.root.geometry(f"{w}x{h}+{(self.root.winfo_screenwidth()-w)//2}+{(self.root.winfo_screenheight()-h)//2}")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self._build()
        self._switch_page("dashboard")

    # ── Layout principal ────────────────────────────────────────────
    def _build(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=PRIMARY, width=SIDEBAR_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_f = tk.Frame(self.sidebar, bg=PRIMARY, pady=16)
        logo_f.pack(fill="x")
        tk.Label(logo_f, text="👁", font=("Segoe UI",22), bg=PRIMARY, fg="white").pack()
        tk.Label(logo_f, text="OphtalmoPro", font=("Segoe UI",12,"bold"), bg=PRIMARY, fg="white").pack()
        tk.Label(logo_f, text="Cabinet ophtalmologique", font=FONT_SMALL, bg=PRIMARY, fg="#85B7EB").pack()
        tk.Frame(self.sidebar, bg="white", height=1, bd=0).pack(fill="x", padx=16)

        # Navigation
        nav_f = tk.Frame(self.sidebar, bg=PRIMARY, pady=10)
        nav_f.pack(fill="x")
        self.nav_btns = {}
        for label, key, icon in self.PAGES:
            btn = tk.Button(nav_f, text=f"  {icon}  {label}",
                            font=FONT_NORMAL, bg=PRIMARY, fg="#B5D4F4",
                            relief="flat", anchor="w", cursor="hand2",
                            activebackground="#185FA5", activeforeground="white",
                            padx=8, pady=7,
                            command=lambda k=key: self._switch_page(k))
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_btns[key] = btn

        # Profil médecin en bas
        tk.Frame(self.sidebar, bg="white", height=1, bd=0).pack(fill="x", padx=16, side="bottom")
        prof_f = tk.Frame(self.sidebar, bg=PRIMARY, pady=12)
        prof_f.pack(side="bottom", fill="x")
        initials = (self.medecin["prenom"][0] + self.medecin["nom"][0]).upper()
        tk.Label(prof_f, text=initials, font=("Segoe UI",12,"bold"),
                 bg="#185FA5", fg="white", width=3, pady=4).pack()
        tk.Label(prof_f, text=f"Dr. {self.medecin['prenom']} {self.medecin['nom']}",
                 font=FONT_SMALL, bg=PRIMARY, fg="white").pack()
        tk.Label(prof_f, text=self.medecin["specialite"], font=("Segoe UI",9),
                 bg=PRIMARY, fg="#85B7EB").pack()
        tk.Button(prof_f, text="Déconnexion", font=("Segoe UI",9), bg=PRIMARY,
                  fg="#85B7EB", relief="flat", cursor="hand2",
                  command=self._logout).pack(pady=(4,0))

        # Zone de contenu
        right = tk.Frame(self.root, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Topbar
        self.topbar = tk.Frame(right, bg=BG_CARD, height=TOPBAR_H,
                               highlightthickness=1, highlightbackground=BORDER)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        self.page_title_lbl = tk.Label(self.topbar, text="", font=FONT_TITLE,
                                       bg=BG_CARD, fg=TEXT_MAIN)
        self.page_title_lbl.pack(side="left", padx=20, pady=12)

        # Contenu scrollable
        self.content_frame = tk.Frame(right, bg=BG)
        self.content_frame.pack(fill="both", expand=True)

    # ── Navigation ──────────────────────────────────────────────────
    def _switch_page(self, key):
        # Réinitialiser les couleurs des boutons
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.config(bg="#185FA5", fg="white")
            else:
                btn.config(bg=PRIMARY, fg="#B5D4F4")

        # Détruire l'ancien contenu
        for w in self.content_frame.winfo_children():
            w.destroy()

        label = next(l for l, k, _ in self.PAGES if k == key)
        self.page_title_lbl.config(text=label)

        # Charger la page correspondante
        if key == "dashboard":
            from modules.dashboard import DashboardPage
            DashboardPage(self.content_frame, self.medecin, self._switch_page)
        elif key == "patients":
            from modules.patients import PatientsPage
            PatientsPage(self.content_frame, self.medecin)
        elif key == "rendezvous":
            from modules.rendezvous import RendezVousPage
            RendezVousPage(self.content_frame, self.medecin)
        elif key == "consultations":
            from modules.consultations import ConsultationsPage
            ConsultationsPage(self.content_frame, self.medecin)
        elif key == "analyses":
            from modules.analyses import AnalysesPage
            AnalysesPage(self.content_frame, self.medecin)
        elif key == "ordonnances":
            from modules.ordonnances import OrdonnancesPage
            OrdonnancesPage(self.content_frame, self.medecin)
        elif key == "parametres":
            from modules.parametres import ParametresPage
            ParametresPage(self.content_frame, self.medecin)

    def _logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Déconnexion", "Voulez-vous vous déconnecter ?"):
            self.root.withdraw()
            for w in self.root.winfo_children():
                w.destroy()
            from utils.database import init_db
            init_db()
            from modules.login import LoginWindow
            LoginWindow(self.root)
