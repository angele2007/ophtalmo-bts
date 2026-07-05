"""Module Patients : liste avec boutons action, couleurs alternées, gestion statuts."""
import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection
from utils.styles import *

# Couleurs des lignes alternées
ROW_ODD  = "#EAF3FB"   # bleu clair
ROW_EVEN = "#D4E9F7"   # bleu un peu plus soutenu
ROW_SEL  = "#B0D4F1"   # sélection


class PatientsPage:
    def __init__(self, parent, medecin):
        self.parent  = parent
        self.medecin = medecin
        self._build()
        self._load()

    def _build(self):
        # ── Toolbar ────────────────────────────────────────────────
        toolbar = tk.Frame(self.parent, bg=BG_CARD, pady=10, padx=16,
                           highlightthickness=1, highlightbackground=BORDER)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="➕  Nouveau patient", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, activebackground=PRIMARY_DARK,
                  command=self._new_patient).pack(side="left")

        # Boutons d'action (actifs quand une ligne est sélectionnée)
        sep = tk.Frame(toolbar, bg=BORDER, width=1)
        sep.pack(side="left", fill="y", padx=14, pady=2)

        self.btn_edit = tk.Button(toolbar, text="✏  Modifier", font=FONT_NORMAL,
                  bg="#E6F1FB", fg=PRIMARY, relief="flat", cursor="hand2",
                  padx=10, pady=5, activebackground=PRIMARY, activeforeground="white",
                  state="disabled", command=self._edit_patient)
        self.btn_edit.pack(side="left", padx=(0,6))

        self.btn_del = tk.Button(toolbar, text="🗑  Supprimer", font=FONT_NORMAL,
                  bg=DANGER_LIGHT, fg=DANGER, relief="flat", cursor="hand2",
                  padx=10, pady=5, activebackground=DANGER, activeforeground="white",
                  state="disabled", command=self._delete_patient)
        self.btn_del.pack(side="left", padx=(0,6))

        self.btn_cons = tk.Button(toolbar, text="🩺  Consultations", font=FONT_NORMAL,
                  bg=ACCENT_LIGHT, fg=ACCENT, relief="flat", cursor="hand2",
                  padx=10, pady=5, activebackground=ACCENT, activeforeground="white",
                  state="disabled", command=self._view_consultations)
        self.btn_cons.pack(side="left")

        # Recherche (côté droit)
        tk.Label(toolbar, text="🔍", font=FONT_NORMAL, bg=BG_CARD).pack(side="right", padx=(0,4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        tk.Entry(toolbar, textvariable=self.search_var, font=FONT_NORMAL,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER,
                 width=28).pack(side="right", ipady=5)
        tk.Label(toolbar, text="Recherche :", font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side="right", padx=(0,6))

        # ── Style du Treeview ──────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Patient.Treeview",
                        background=ROW_ODD,
                        fieldbackground=ROW_ODD,
                        foreground=TEXT_MAIN,
                        rowheight=34,
                        font=FONT_NORMAL,
                        borderwidth=0)
        style.configure("Patient.Treeview.Heading",
                        background=PRIMARY,
                        foreground="white",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat", padding=6)
        style.map("Patient.Treeview",
                  background=[("selected", ROW_SEL)],
                  foreground=[("selected", PRIMARY_DARK)])
        style.map("Patient.Treeview.Heading",
                  background=[("active", PRIMARY_DARK)])

        # ── Tableau ────────────────────────────────────────────────
        table_f = tk.Frame(self.parent, bg=PRIMARY, padx=1, pady=1)  # bordure bleue
        table_f.pack(fill="both", expand=True, padx=16, pady=(8,0))

        cols = ("ID", "Nom", "Prénom", "Âge", "Sexe", "Téléphone", "Date naiss.", "Adresse")
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings",
                                 style="Patient.Treeview", selectmode="browse")
        widths  = [50, 140, 140, 55, 60, 120, 100, 220]
        anchors = ["center","w","w","center","center","w","center","w"]
        for col, w, anc in zip(cols, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc, minwidth=w)

        # Tags couleurs alternées
        self.tree.tag_configure("odd",  background=ROW_ODD,  foreground=TEXT_MAIN)
        self.tree.tag_configure("even", background=ROW_EVEN, foreground=TEXT_MAIN)
        self.tree.tag_configure("male",   foreground="#185FA5")
        self.tree.tag_configure("female", foreground="#8B1A6B")

        sb_y = ttk.Scrollbar(table_f, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Événements
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda e: self._edit_patient())
        self.tree.bind("<Delete>",           lambda e: self._delete_patient())

        # ── Barre de statut + boutons inline ──────────────────────
        status_bar = tk.Frame(self.parent, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        status_bar.pack(fill="x", padx=16, pady=(0,10))

        self.info_lbl = tk.Label(status_bar, text="", font=FONT_SMALL,
                                 bg=BG_CARD, fg=TEXT_MUTED, padx=12, pady=6)
        self.info_lbl.pack(side="left")

        # Mini-boutons dans la barre de statut
        self.sel_lbl = tk.Label(status_bar, text="", font=FONT_SMALL,
                                bg=BG_CARD, fg=PRIMARY)
        self.sel_lbl.pack(side="right", padx=12)

        # ── Menu contextuel ────────────────────────────────────────
        self.ctx = tk.Menu(self.parent, tearoff=0)
        self.ctx.add_command(label="✏  Modifier le patient",   command=self._edit_patient)
        self.ctx.add_command(label="🗑  Supprimer le patient",  command=self._delete_patient)
        self.ctx.add_separator()
        self.ctx.add_command(label="🩺  Voir les consultations", command=self._view_consultations)
        self.ctx.add_command(label="📋  Fiche patient",          command=self._fiche_patient)
        self.tree.bind("<Button-3>", self._show_ctx)

    # ── Chargement données ─────────────────────────────────────────
    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        q = self.search_var.get().strip()
        conn = get_connection()
        if q:
            rows = conn.execute("""
                SELECT idpat,nompat,prenompat,agepat,sexe,telpat,dateNaissance,adresse
                FROM patients
                WHERE nompat LIKE ? OR prenompat LIKE ? OR telpat LIKE ?
                ORDER BY nompat
            """, (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
        else:
            rows = conn.execute("""
                SELECT idpat,nompat,prenompat,agepat,sexe,telpat,dateNaissance,adresse
                FROM patients ORDER BY nompat
            """).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", iid=str(r[0]), tags=(tag,), values=(
                r[0],
                r[1].upper(),
                r[2].capitalize(),
                r[3],
                "♂ M" if r[4] == "M" else "♀ F",
                r[5],
                r[6] or "—",
                r[7] or "—"
            ))
        n = len(rows)
        self.info_lbl.config(text=f"  {n} patient{'s' if n>1 else ''} enregistré{'s' if n>1 else ''}")
        self._update_buttons(False)

    # ── Sélection ──────────────────────────────────────────────────
    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])["values"]
            sexe_raw = vals[4]
            nom_affich = f"{vals[2]} {vals[1]}"
            self.sel_lbl.config(text=f"Sélectionné : {nom_affich}  |  {'♂' if 'M' in sexe_raw else '♀'}  |  {vals[3]} ans")
            self._update_buttons(True)
        else:
            self.sel_lbl.config(text="")
            self._update_buttons(False)

    def _update_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in (self.btn_edit, self.btn_del, self.btn_cons):
            btn.config(state=state)

    # ── Actions ────────────────────────────────────────────────────
    def _show_ctx(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.ctx.post(event.x_root, event.y_root)

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Veuillez sélectionner un patient d'abord.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def _new_patient(self):
        PatientForm(self.parent, None, self._load)

    def _edit_patient(self):
        pid = self._get_selected_id()
        if pid:
            conn = get_connection()
            p = dict(conn.execute("SELECT * FROM patients WHERE idpat=?", (pid,)).fetchone())
            conn.close()
            PatientForm(self.parent, p, self._load)

    def _delete_patient(self):
        pid = self._get_selected_id()
        if not pid:
            return
        vals = self.tree.item(str(pid))["values"]
        nom  = f"{vals[2]} {vals[1]}"
        if messagebox.askyesno("Confirmer la suppression",
                               f"Supprimer définitivement le patient\n« {nom } » ?\n\n"
                               "Toutes ses consultations, analyses et ordonnances\n"
                               "seront également supprimées.", icon="warning"):
            try:
                conn = get_connection()
                conn.execute("DELETE FROM patients WHERE idpat=?", (pid,))
                conn.commit(); conn.close()
                self._load()
                messagebox.showinfo("Succès", f"Patient « {nom} » supprimé.")
            except Exception as ex:
                messagebox.showerror("Erreur", str(ex))

    def _view_consultations(self):
        pid = self._get_selected_id()
        if not pid:
            return
        vals = self.tree.item(str(pid))["values"]
        nom  = f"{vals[2]} {vals[1]}"
        ConsultationsPatient(self.parent, pid, nom)

    def _fiche_patient(self):
        pid = self._get_selected_id()
        if not pid:
            return
        conn = get_connection()
        p = dict(conn.execute("SELECT * FROM patients WHERE idpat=?", (pid,)).fetchone())
        stats = {
            "consultations": conn.execute("SELECT COUNT(*) FROM consultations WHERE idpat=?", (pid,)).fetchone()[0],
            "rdv":           conn.execute("SELECT COUNT(*) FROM rendezvous WHERE idpat=?", (pid,)).fetchone()[0],
        }
        conn.close()
        FichePatient(self.parent, p, stats)


# ── Fiche patient (vue détail) ─────────────────────────────────────
class FichePatient(tk.Toplevel):
    def __init__(self, parent, p, stats):
        super().__init__(parent)
        self.title(f"Fiche — {p['prenompat']} {p['nompat']}")
        w, h = 420, 380
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        # En-tête
        hdr = tk.Frame(self, bg=PRIMARY, padx=20, pady=16)
        hdr.pack(fill="x")
        icon = "♂" if p["sexe"] == "M" else "♀"
        tk.Label(hdr, text=f"{icon}  {p['prenompat'].capitalize()} {p['nompat'].upper()}",
                 font=("Segoe UI",14,"bold"), bg=PRIMARY, fg="white").pack(anchor="w")
        tk.Label(hdr, text=f"{p['agepat']} ans  ·  Patient #{p['idpat']}",
                 font=FONT_NORMAL, bg=PRIMARY, fg="#85B7EB").pack(anchor="w")

        body = tk.Frame(self, bg=BG, padx=20, pady=14)
        body.pack(fill="both", expand=True)

        rows = [
            ("📞 Téléphone",      p["telpat"]),
            ("📅 Date naissance", p["dateNaissance"] or "—"),
            ("🏠 Adresse",        p["adresse"] or "—"),
            ("🩺 Consultations",  str(stats["consultations"])),
            ("📅 Rendez-vous",    str(stats["rdv"])),
        ]
        for lbl, val in rows:
            rf = tk.Frame(body, bg=BG)
            rf.pack(fill="x", pady=5)
            tk.Label(rf, text=lbl, font=FONT_LABEL, bg=BG, fg=TEXT_MUTED, width=18, anchor="w").pack(side="left")
            tk.Label(rf, text=val, font=FONT_NORMAL, bg=BG, fg=TEXT_MAIN).pack(side="left")
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x")

        tk.Button(self, text="Fermer", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=20, pady=7, cursor="hand2",
                  command=self.destroy).pack(pady=10)


# ── Consultations d'un patient ────────────────────────────────────
class ConsultationsPatient(tk.Toplevel):
    def __init__(self, parent, pid, nom):
        super().__init__(parent)
        self.title(f"Consultations — {nom}")
        w, h = 700, 400
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.configure(bg=BG)
        self.grab_set()

        tk.Label(self, text=f"🩺  Consultations de {nom}", font=FONT_SECTION,
                 bg=BG, fg=PRIMARY, padx=16, pady=12).pack(anchor="w")

        f = tk.Frame(self, bg=BG, padx=16)
        f.pack(fill="both", expand=True)

        cols = ("Date","Motif","Type","Statut")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=14)
        for col, w in zip(cols, [100, 300, 120, 100]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w")

        conn = get_connection()
        rows = conn.execute("""
            SELECT datecons, motifcons, type_cons, statut
            FROM consultations WHERE idpat=? ORDER BY datecons DESC
        """, (pid,)).fetchall()
        conn.close()

        status_colors = {
            "En cours": "#854F0B", "Terminée": "#3B6D11", "Annulée": "#A32D2D"
        }
        for row in rows:
            tree.insert("", "end", values=tuple(row))

        sb = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        if not rows:
            tk.Label(self, text="Aucune consultation enregistrée pour ce patient.",
                     font=FONT_NORMAL, bg=BG, fg=TEXT_MUTED).pack(pady=10)

        tk.Button(self, text="Fermer", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=20, pady=7, cursor="hand2",
                  command=self.destroy).pack(pady=10)


# ── Formulaire ajout / modification ───────────────────────────────
class PatientForm(tk.Toplevel):
    def __init__(self, parent, patient, callback):
        super().__init__(parent)
        self.patient  = patient
        self.callback = callback
        self.title("Nouveau patient" if not patient else "Modifier le patient")
        self.resizable(False, False)
        w, h = 500, 540
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.configure(bg=BG)
        self.grab_set()
        self._build()

    def _field(self, frame, label, row, value="", readonly=False):
        tk.Label(frame, text=label, font=FONT_LABEL, bg=BG, fg=TEXT_MUTED).grid(
            row=row, column=0, sticky="w", pady=5)
        var = tk.StringVar(value=value)
        state = "readonly" if readonly else "normal"
        e = tk.Entry(frame, textvariable=var, font=FONT_NORMAL, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER, width=32,
                     state=state, readonlybackground="#F0F0F0")
        e.grid(row=row, column=1, sticky="ew", padx=(10,0), pady=5, ipady=7)
        return var

    def _build(self):
        p = self.patient or {}
        is_edit = bool(self.patient)

        # En-tête coloré
        hdr = tk.Frame(self, bg=PRIMARY if not is_edit else ACCENT, padx=20, pady=12)
        hdr.pack(fill="x")
        icon = "✏" if is_edit else "➕"
        title = "Modifier le patient" if is_edit else "Nouveau patient"
        tk.Label(hdr, text=f"{icon}  {title}", font=("Segoe UI",13,"bold"),
                 bg=hdr["bg"], fg="white").pack(anchor="w")
        if is_edit:
            tk.Label(hdr, text=f"ID #{p['idpat']}  ·  {p['prenompat']} {p['nompat']}",
                     font=FONT_SMALL, bg=hdr["bg"], fg="white").pack(anchor="w")

        f = tk.Frame(self, bg=BG, padx=22, pady=12)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        self.nom     = self._field(f, "Nom *",            0, p.get("nompat",""))
        self.prenom  = self._field(f, "Prénom *",         1, p.get("prenompat",""))
        self.age     = self._field(f, "Âge *",            2, str(p.get("agepat","")))
        self.dob     = self._field(f, "Date naissance",   3, p.get("dateNaissance","") or "",
                                   )
        tk.Label(f, text="(YYYY-MM-DD)", font=("Segoe UI",8), bg=BG,
                 fg=TEXT_LIGHT).grid(row=3, column=1, sticky="e", padx=(0,4))
        self.tel     = self._field(f, "Téléphone *",      4, p.get("telpat",""))
        self.adresse = self._field(f, "Adresse",          5, p.get("adresse","") or "")

        # Sexe avec boutons radio stylisés
        tk.Label(f, text="Sexe *", font=FONT_LABEL, bg=BG, fg=TEXT_MUTED).grid(
            row=6, column=0, sticky="w", pady=5)
        self.sexe_var = tk.StringVar(value=p.get("sexe","M"))
        sf = tk.Frame(f, bg=BG)
        sf.grid(row=6, column=1, sticky="w", padx=(10,0))
        for val, lbl, color in [("M","♂  Masculin","#185FA5"), ("F","♀  Féminin","#8B1A6B")]:
            tk.Radiobutton(sf, text=lbl, variable=self.sexe_var, value=val,
                           font=FONT_NORMAL, bg=BG, fg=color,
                           selectcolor=BG, activebackground=BG).pack(side="left", padx=(0,16))

        # Boutons
        btn_f = tk.Frame(self, bg=BG_CARD, padx=20, pady=12,
                         highlightthickness=1, highlightbackground=BORDER)
        btn_f.pack(fill="x", side="bottom")
        tk.Button(btn_f, text="✖  Annuler", font=FONT_NORMAL, bg=BG_CARD,
                  relief="flat", highlightthickness=1, highlightbackground=BORDER,
                  padx=16, pady=6, cursor="hand2", command=self.destroy).pack(side="right", padx=6)
        lbl_save = "💾  Enregistrer les modifications" if is_edit else "💾  Ajouter le patient"
        tk.Button(btn_f, text=lbl_save, font=FONT_NORMAL,
                  bg=ACCENT if is_edit else PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=16, pady=6,
                  activebackground=PRIMARY_DARK,
                  command=self._save).pack(side="right", padx=6)

    def _save(self):
        nom    = self.nom.get().strip()
        prenom = self.prenom.get().strip()
        age_s  = self.age.get().strip()
        tel    = self.tel.get().strip()
        if not nom or not prenom or not age_s or not tel:
            messagebox.showerror("Erreur", "Les champs marqués * sont obligatoires.", parent=self)
            return
        try:
            age = int(age_s)
            if age < 0 or age > 130:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "L'âge doit être un nombre entier valide (0-130).", parent=self)
            return
        conn = get_connection()
        try:
            if self.patient:
                conn.execute("""
                    UPDATE patients
                    SET nompat=?,prenompat=?,agepat=?,dateNaissance=?,sexe=?,adresse=?,telpat=?
                    WHERE idpat=?
                """, (nom, prenom, age, self.dob.get() or None,
                      self.sexe_var.get(), self.adresse.get() or None,
                      tel, self.patient["idpat"]))
                msg = f"Patient « {prenom} {nom} » mis à jour avec succès."
            else:
                conn.execute("""
                    INSERT INTO patients (nompat,prenompat,agepat,dateNaissance,sexe,adresse,telpat)
                    VALUES (?,?,?,?,?,?,?)
                """, (nom, prenom, age, self.dob.get() or None,
                      self.sexe_var.get(), self.adresse.get() or None, tel))
                msg = f"Patient « {prenom} {nom} » ajouté avec succès."
            conn.commit()
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex), parent=self)
            return
        finally:
            conn.close()
        self.callback()
        self.destroy()
        messagebox.showinfo("Succès", msg)
