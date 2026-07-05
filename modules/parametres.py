"""Module Paramètres : profil médecin, stats, à propos."""
import tkinter as tk
from tkinter import messagebox
from utils.database import get_connection, hash_password
from utils.styles import *


class ParametresPage:
    def __init__(self, parent, medecin):
        self.parent  = parent
        self.medecin = medecin
        self._build()

    def _build(self):
        canvas = tk.Canvas(self.parent, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        frame = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0,0), window=frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        pad = tk.Frame(frame, bg=BG, padx=24, pady=20)
        pad.pack(fill="both", expand=True)

        # ── Profil ─────────────────────────────────────────────────
        sec1 = tk.LabelFrame(pad, text="  👤  Profil du médecin", font=FONT_SECTION,
                              bg=BG_CARD, fg=PRIMARY, bd=0,
                              highlightthickness=1, highlightbackground=BORDER,
                              padx=20, pady=16)
        sec1.pack(fill="x", pady=(0,16))
        sec1.columnconfigure(1, weight=1)

        m = self.medecin
        fields_def = [
            ("Nom",        "nom",       m["nom"]),
            ("Prénom",     "prenom",    m["prenom"]),
            ("Spécialité", "specialite",m["specialite"]),
            ("Téléphone",  "telephone", m["telephone"]),
            ("Login",      "login",     m["login"]),
            ("Email",      "email",     m["email"]),
        ]
        self.prof_vars = {}
        for i, (lbl, key, val) in enumerate(fields_def):
            tk.Label(sec1, text=lbl, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).grid(
                row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=val)
            tk.Entry(sec1, textvariable=var, font=FONT_NORMAL, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER, width=36).grid(
                row=i, column=1, sticky="ew", padx=(12,0), pady=5, ipady=6)
            self.prof_vars[key] = var

        tk.Button(sec1, text="💾  Sauvegarder le profil", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", activebackground=PRIMARY_DARK,
                  command=self._save_profile).grid(row=len(fields_def), column=1, sticky="e", pady=(10,0))

        # ── Mot de passe ───────────────────────────────────────────
        sec2 = tk.LabelFrame(pad, text="  🔒  Changer le mot de passe", font=FONT_SECTION,
                              bg=BG_CARD, fg=PRIMARY, bd=0,
                              highlightthickness=1, highlightbackground=BORDER,
                              padx=20, pady=16)
        sec2.pack(fill="x", pady=(0,16))
        sec2.columnconfigure(1, weight=1)

        pwd_fields = [("Mot de passe actuel","old_pwd"),
                      ("Nouveau mot de passe","new_pwd"),
                      ("Confirmer","conf_pwd")]
        self.pwd_vars = {}
        for i, (lbl, key) in enumerate(pwd_fields):
            tk.Label(sec2, text=lbl, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).grid(
                row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            tk.Entry(sec2, textvariable=var, show="•", font=FONT_NORMAL, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER, width=30).grid(
                row=i, column=1, sticky="w", padx=(12,0), pady=5, ipady=6)
            self.pwd_vars[key] = var

        tk.Button(sec2, text="🔑  Changer le mot de passe", font=FONT_NORMAL,
                  bg=ACCENT, fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._change_password).grid(
            row=3, column=1, sticky="e", pady=(10,0))

        # ── Statistiques ───────────────────────────────────────────
        sec3 = tk.LabelFrame(pad, text="  📊  Statistiques du cabinet", font=FONT_SECTION,
                              bg=BG_CARD, fg=PRIMARY, bd=0,
                              highlightthickness=1, highlightbackground=BORDER,
                              padx=20, pady=16)
        sec3.pack(fill="x", pady=(0,16))

        conn = get_connection()
        mid = self.medecin["id_medecin"]
        stats = {
            "Total patients":        conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "Total consultations":   conn.execute("SELECT COUNT(*) FROM consultations WHERE id_medecin=?", (mid,)).fetchone()[0],
            "Consultations terminées":conn.execute("SELECT COUNT(*) FROM consultations WHERE id_medecin=? AND statut='Terminée'", (mid,)).fetchone()[0],
            "Total analyses":        conn.execute("SELECT COUNT(*) FROM analyses a JOIN consultations c ON c.idcons=a.idcons WHERE c.id_medecin=?", (mid,)).fetchone()[0],
            "Total ordonnances":     conn.execute("SELECT COUNT(*) FROM ordonnances o JOIN consultations c ON c.idcons=o.idcons WHERE c.id_medecin=?", (mid,)).fetchone()[0],
            "RDV planifiés":         conn.execute("SELECT COUNT(*) FROM rendezvous WHERE id_medecin=? AND statut='Planifié'", (mid,)).fetchone()[0],
        }
        conn.close()

        grid = tk.Frame(sec3, bg=BG_CARD)
        grid.pack(fill="x")
        for col in range(3): grid.columnconfigure(col, weight=1)
        items = list(stats.items())
        for i, (lbl, val) in enumerate(items):
            row, col = divmod(i, 3)
            c = tk.Frame(grid, bg=PRIMARY_LIGHT, padx=14, pady=10)
            c.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            tk.Label(c, text=str(val), font=("Segoe UI",22,"bold"), bg=PRIMARY_LIGHT, fg=PRIMARY).pack()
            tk.Label(c, text=lbl, font=FONT_SMALL, bg=PRIMARY_LIGHT, fg=TEXT_MUTED).pack()

        # ── À propos ───────────────────────────────────────────────
        sec4 = tk.LabelFrame(pad, text="  ℹ  À propos", font=FONT_SECTION,
                              bg=BG_CARD, fg=PRIMARY, bd=0,
                              highlightthickness=1, highlightbackground=BORDER,
                              padx=20, pady=16)
        sec4.pack(fill="x")

        about_lines = [
            ("Application","OphtalmoPro v1.0"),
            ("Type","Gestion cabinet ophtalmologique"),
            ("Projet","BTS Informatique"),
            ("Technologie","Python 3 · Tkinter · SQLite"),
            ("Base de données","ophtalmo.db (SQLite local)"),
        ]
        for lbl, val in about_lines:
            row = tk.Frame(sec4, bg=BG_CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl + " :", width=18, font=FONT_LABEL, bg=BG_CARD,
                     fg=TEXT_MUTED, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_NORMAL, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left")

    def _save_profile(self):
        nom   = self.prof_vars["nom"].get().strip()
        prenom= self.prof_vars["prenom"].get().strip()
        spec  = self.prof_vars["specialite"].get().strip()
        tel   = self.prof_vars["telephone"].get().strip()
        login = self.prof_vars["login"].get().strip()
        email = self.prof_vars["email"].get().strip()
        if not all([nom, prenom, spec, tel, login, email]):
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
            return
        conn = get_connection()
        try:
            conn.execute("""
                UPDATE medecins SET nom=?,prenom=?,specialite=?,telephone=?,login=?,email=?
                WHERE id_medecin=?
            """, (nom, prenom, spec, tel, login, email, self.medecin["id_medecin"]))
            conn.commit()
            # Mettre à jour le dict local
            for key in ["nom","prenom","specialite","telephone","login","email"]:
                self.medecin[key] = self.prof_vars[key].get().strip()
            messagebox.showinfo("Succès", "Profil mis à jour avec succès.")
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex))
        finally:
            conn.close()

    def _change_password(self):
        old  = self.pwd_vars["old_pwd"].get()
        new  = self.pwd_vars["new_pwd"].get()
        conf = self.pwd_vars["conf_pwd"].get()
        if not old or not new or not conf:
            messagebox.showerror("Erreur", "Remplissez tous les champs.")
            return
        conn = get_connection()
        row = conn.execute(
            "SELECT id_medecin FROM medecins WHERE id_medecin=? AND motdepasse=?",
            (self.medecin["id_medecin"], hash_password(old))
        ).fetchone()
        if not row:
            conn.close()
            messagebox.showerror("Erreur", "Mot de passe actuel incorrect.")
            return
        if new != conf:
            conn.close()
            messagebox.showerror("Erreur", "La confirmation ne correspond pas.")
            return
        if len(new) < 4:
            conn.close()
            messagebox.showerror("Erreur", "Le mot de passe doit faire au moins 4 caractères.")
            return
        conn.execute("UPDATE medecins SET motdepasse=? WHERE id_medecin=?",
                     (hash_password(new), self.medecin["id_medecin"]))
        conn.commit(); conn.close()
        for v in self.pwd_vars.values():
            v.set("")
        messagebox.showinfo("Succès", "Mot de passe modifié avec succès.")
