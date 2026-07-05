"""Module Ordonnances — liste, formulaire, aperçu + impression PDF."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from utils.database import get_connection
from utils.styles import *


# ══════════════════════════════════════════════════════════════════
#  Page principale
# ══════════════════════════════════════════════════════════════════
class OrdonnancesPage:
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

        tk.Button(toolbar, text="➕  Nouvelle ordonnance", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, activebackground=PRIMARY_DARK,
                  command=self._new_ord).pack(side="left")

        tk.Frame(toolbar, bg=BORDER, width=1).pack(side="left", fill="y", padx=12, pady=2)

        self.btn_edit  = self._abtn(toolbar, "✏  Modifier",  "#E6F1FB", PRIMARY,    self._edit_ord)
        self.btn_print = self._abtn(toolbar, "🖨  Imprimer", ACCENT_LIGHT, ACCENT,   self._print_ord)
        self.btn_pdf   = self._abtn(toolbar, "📄  Exporter PDF", "#FFF3E0","#E65100", self._export_pdf)
        self.btn_del   = self._abtn(toolbar, "🗑  Supprimer", DANGER_LIGHT, DANGER,   self._delete_ord)
        self.action_btns = [self.btn_edit, self.btn_print, self.btn_pdf, self.btn_del]

        # Recherche
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        tk.Entry(toolbar, textvariable=self.search_var, font=FONT_NORMAL, width=26,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER).pack(
            side="right", ipady=5)
        tk.Label(toolbar, text="🔍 Recherche :", font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side="right", padx=(0,6))

        # ── Style Treeview ─────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Ord.Treeview", rowheight=34, font=FONT_NORMAL,
                        background="#F5F0FF", fieldbackground="#F5F0FF",
                        foreground=TEXT_MAIN, borderwidth=0)
        style.configure("Ord.Treeview.Heading",
                        background=PRIMARY, foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat", padding=8)
        style.map("Ord.Treeview",
                  background=[("selected","#C5B3F0")],
                  foreground=[("selected", "#2A005F")])
        style.map("Ord.Treeview.Heading",
                  background=[("active", PRIMARY_DARK)])

        # ── Tableau ────────────────────────────────────────────────
        table_f = tk.Frame(self.parent, bg=PRIMARY, padx=1, pady=1)
        table_f.pack(fill="both", expand=True, padx=16, pady=(8,0))

        cols = ("ID","Date","Patient","Médicaments","Posologie")
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings",
                                 style="Ord.Treeview", selectmode="browse")
        col_config = [
            ("ID",          55,  "center"),
            ("Date",       110,  "center"),
            ("Patient",    200,  "w"),
            ("Médicaments",240,  "w"),
            ("Posologie",  260,  "w"),
        ]
        for col, ww, anc in col_config:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=ww, anchor=anc, minwidth=ww, stretch=True)

        self.tree.tag_configure("odd",  background="#F5F0FF")
        self.tree.tag_configure("even", background="#EBE3FF")

        sb_y = ttk.Scrollbar(table_f, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda e: self._edit_ord())

        ctx = tk.Menu(self.parent, tearoff=0)
        ctx.add_command(label="✏  Modifier",       command=self._edit_ord)
        ctx.add_command(label="🖨  Aperçu / Imprimer", command=self._print_ord)
        ctx.add_command(label="📄  Exporter en PDF",   command=self._export_pdf)
        ctx.add_separator()
        ctx.add_command(label="🗑  Supprimer",      command=self._delete_ord)
        self.tree.bind("<Button-3>", lambda e: (
            self.tree.selection_set(self.tree.identify_row(e.y)),
            ctx.post(e.x_root, e.y_root)))

        # ── Barre de statut ────────────────────────────────────────
        sb2 = tk.Frame(self.parent, bg=BG_CARD,
                       highlightthickness=1, highlightbackground=BORDER)
        sb2.pack(fill="x", padx=16, pady=(0,10))
        self.info_lbl = tk.Label(sb2, text="", font=FONT_SMALL,
                                  bg=BG_CARD, fg=TEXT_MUTED, padx=12, pady=6)
        self.info_lbl.pack(side="left")
        self.sel_lbl = tk.Label(sb2, text="", font=FONT_SMALL, bg=BG_CARD, fg=PRIMARY)
        self.sel_lbl.pack(side="right", padx=12)

    def _abtn(self, parent, text, bg, fg, cmd):
        btn = tk.Button(parent, text=text, font=FONT_NORMAL, bg=bg, fg=fg,
                        relief="flat", cursor="hand2", padx=9, pady=5,
                        activebackground=fg, activeforeground="white",
                        state="disabled", command=cmd)
        btn.pack(side="left", padx=(0,5))
        return btn

    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0])["values"]
            self.sel_lbl.config(text=f"  Ordonnance #{v[0]}  —  {v[2]}  —  {v[1]}")
            for btn in self.action_btns:
                btn.config(state="normal")
        else:
            self.sel_lbl.config(text="")
            for btn in self.action_btns:
                btn.config(state="disabled")

    # ── Chargement ─────────────────────────────────────────────────
    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        q = self.search_var.get().strip()
        conn = get_connection()
        if q:
            rows = conn.execute("""
                SELECT o.idord, c.datecons, p.nompat||' '||p.prenompat,
                       o.medicaments, o.posologie
                FROM ordonnances o
                JOIN consultations c ON c.idcons=o.idcons
                JOIN patients p ON p.idpat=c.idpat
                WHERE c.id_medecin=? AND (p.nompat LIKE ? OR o.medicaments LIKE ?)
                ORDER BY c.datecons DESC
            """, (self.medecin["id_medecin"], f"%{q}%", f"%{q}%")).fetchall()
        else:
            rows = conn.execute("""
                SELECT o.idord, c.datecons, p.nompat||' '||p.prenompat,
                       o.medicaments, o.posologie
                FROM ordonnances o
                JOIN consultations c ON c.idcons=o.idcons
                JOIN patients p ON p.idpat=c.idpat
                WHERE c.id_medecin=?
                ORDER BY c.datecons DESC
            """, (self.medecin["id_medecin"],)).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            meds = r[3][:55]+"…" if len(r[3])>55 else r[3]
            pos  = r[4][:70]+"…" if len(r[4])>70 else r[4]
            self.tree.insert("", "end", iid=str(r[0]), tags=(tag,),
                             values=(r[0], r[1], r[2], meds, pos))
        n = len(rows)
        self.info_lbl.config(text=f"  {n} ordonnance{'s' if n>1 else ''}")
        for btn in self.action_btns:
            btn.config(state="disabled")
        self.sel_lbl.config(text="")

    def _get_sel_id(self):
        sel = self.tree.selection()
        return int(self.tree.item(sel[0])["values"][0]) if sel else None

    def _get_full_data(self, oid):
        conn = get_connection()
        row = conn.execute("""
            SELECT o.idord, o.medicaments, o.posologie, o.idcons,
                   c.datecons,
                   p.nompat, p.prenompat, p.agepat, p.sexe, p.telpat,
                   m.nom AS mnom, m.prenom AS mprenom, m.specialite,
                   m.telephone AS mtel, m.email
            FROM ordonnances o
            JOIN consultations c ON c.idcons=o.idcons
            JOIN patients p ON p.idpat=c.idpat
            JOIN medecins m ON m.id_medecin=c.id_medecin
            WHERE o.idord=?
        """, (oid,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def _new_ord(self):
        OrdonnanceForm(self.parent, None, None, self._load)

    def _edit_ord(self):
        oid = self._get_sel_id()
        if oid:
            conn = get_connection()
            o = dict(conn.execute("SELECT * FROM ordonnances WHERE idord=?", (oid,)).fetchone())
            conn.close()
            OrdonnanceForm(self.parent, o["idcons"], o, self._load)

    def _delete_ord(self):
        oid = self._get_sel_id()
        if not oid: return
        if messagebox.askyesno("Supprimer","Supprimer cette ordonnance ?", icon="warning"):
            conn = get_connection()
            conn.execute("DELETE FROM ordonnances WHERE idord=?", (oid,))
            conn.commit(); conn.close(); self._load()

    def _print_ord(self):
        oid = self._get_sel_id()
        if not oid: return
        data = self._get_full_data(oid)
        if data:
            PrintPreview(self.parent, data)

    def _export_pdf(self):
        oid = self._get_sel_id()
        if not oid: return
        data = self._get_full_data(oid)
        if data:
            generate_pdf(self.parent, data)


# ══════════════════════════════════════════════════════════════════
#  Formulaire ordonnance  (corrigé — pas de collision de variable)
# ══════════════════════════════════════════════════════════════════
class OrdonnanceForm(tk.Toplevel):
    def __init__(self, parent, idcons, ordonnance, callback):
        super().__init__(parent)
        self.idcons     = idcons
        self.ordonnance = ordonnance
        self.callback   = callback
        self.title("Nouvelle ordonnance" if not ordonnance else "Modifier ordonnance")
        self.resizable(True, True)
        self.minsize(560, 600)
        FORM_W, FORM_H = 600, 660
        self.geometry(f"{FORM_W}x{FORM_H}+"
                      f"{(self.winfo_screenwidth()-FORM_W)//2}+"
                      f"{(self.winfo_screenheight()-FORM_H)//2}")
        self.configure(bg=BG)
        self.grab_set()
        self._build()

    def _build(self):
        o       = self.ordonnance or {}
        is_edit = bool(self.ordonnance)
        hdr_c   = ACCENT if is_edit else PRIMARY

        # ── En-tête ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=hdr_c, padx=22, pady=14)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr,
                 text="✏  Modifier l'ordonnance" if is_edit else "💊  Nouvelle Ordonnance",
                 font=("Segoe UI",13,"bold"), bg=hdr_c, fg="white").pack(anchor="w")

        # ── Barre de boutons (packée AVANT le corps pour rester visible) ──
        btn_bar = tk.Frame(self, bg=BG_CARD, padx=22, pady=10,
                           highlightthickness=1, highlightbackground=BORDER)
        btn_bar.pack(fill="x", side="bottom")

        tk.Button(btn_bar, text="✖  Annuler", font=FONT_NORMAL,
                  bg="#F5F5F5", fg=TEXT_MAIN,
                  relief="flat", highlightthickness=1, highlightbackground=BORDER,
                  padx=16, pady=7, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=6)

        save_lbl = "💾  Enregistrer les modifications" if is_edit else "💾  Créer l'ordonnance"
        tk.Button(btn_bar, text=save_lbl, font=("Segoe UI",11,"bold"),
                  bg=ACCENT if is_edit else PRIMARY, fg="white",
                  relief="flat", padx=16, pady=7, cursor="hand2",
                  activebackground=PRIMARY_DARK,
                  command=self._save).pack(side="right", padx=6)

        if is_edit:
            tk.Button(btn_bar, text="🖨  Aperçu / Imprimer", font=FONT_NORMAL,
                      bg="#FFF3E0", fg="#E65100",
                      relief="flat", padx=14, pady=7, cursor="hand2",
                      command=self._preview).pack(side="left", padx=6)

        # ── Corps (scrollable) ─────────────────────────────────────
        body = tk.Frame(self, bg=BG, padx=22, pady=14)
        body.pack(fill="both", expand=True, side="top")

        # Sélection consultation
        tk.Label(body, text="Consultation liée *", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(body, text="Sélectionnez la consultation dans la liste ↓",
                 font=("Segoe UI",8), bg=BG, fg=TEXT_LIGHT).pack(anchor="w")

        conn = get_connection()
        cons_list = conn.execute("""
            SELECT c.idcons,
                   c.datecons||' — '||p.nompat||' '||p.prenompat AS label
            FROM consultations c JOIN patients p ON p.idpat=c.idpat
            ORDER BY c.datecons DESC LIMIT 150
        """).fetchall()
        conn.close()

        self.cons_map = {row["label"]: row["idcons"] for row in cons_list}
        self.cons_var = tk.StringVar()
        if self.idcons:
            for lbl, cid in self.cons_map.items():
                if cid == self.idcons:
                    self.cons_var.set(lbl); break

        cons_cb = ttk.Combobox(body, textvariable=self.cons_var,
                               values=list(self.cons_map.keys()),
                               font=FONT_NORMAL, state="readonly")
        cons_cb.pack(fill="x", pady=(6,16), ipady=7)

        # Séparateur
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0,12))

        # Médicaments
        tk.Label(body, text="💊  Médicaments *", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(body, text="Saisir un médicament par ligne",
                 font=("Segoe UI",8), bg=BG, fg=TEXT_LIGHT).pack(anchor="w")
        self.med_text = tk.Text(body, font=FONT_NORMAL, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 height=5, padx=8, pady=6)
        self.med_text.pack(fill="x", pady=(4,14))
        if o.get("medicaments"):
            self.med_text.insert("1.0", o["medicaments"])

        # Posologie
        tk.Label(body, text="📋  Posologie / Instructions *", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        self.pos_text = tk.Text(body, font=FONT_NORMAL, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 height=5, padx=8, pady=6)
        self.pos_text.pack(fill="x", pady=(4,0))
        if o.get("posologie"):
            self.pos_text.insert("1.0", o["posologie"])


    def _save(self):
        cons_lbl = self.cons_var.get().strip()
        meds     = self.med_text.get("1.0", "end").strip()
        pos      = self.pos_text.get("1.0", "end").strip()
        if not cons_lbl or not meds or not pos:
            messagebox.showerror("Erreur","Tous les champs sont obligatoires.", parent=self)
            return
        cid = self.cons_map.get(cons_lbl)
        if not cid:
            messagebox.showerror("Erreur","Consultation introuvable.", parent=self)
            return
        conn = get_connection()
        try:
            if self.ordonnance:
                conn.execute(
                    "UPDATE ordonnances SET medicaments=?,posologie=?,idcons=? WHERE idord=?",
                    (meds, pos, cid, self.ordonnance["idord"]))
                new_oid = self.ordonnance["idord"]
            else:
                cur = conn.execute(
                    "INSERT INTO ordonnances (medicaments,posologie,idcons) VALUES (?,?,?)",
                    (meds, pos, cid))
                new_oid = cur.lastrowid
            conn.commit()
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex), parent=self)
            return
        finally:
            conn.close()
        self.callback()
        # Proposer l'impression directement après la sauvegarde
        if messagebox.askyesno("Impression",
                               "Ordonnance enregistrée !\n\nVoulez-vous l'imprimer maintenant ?",
                               parent=self):
            conn2 = get_connection()
            row = conn2.execute("""
                SELECT o.idord, o.medicaments, o.posologie, o.idcons,
                       c.datecons,
                       p.nompat, p.prenompat, p.agepat, p.sexe, p.telpat,
                       m.nom AS mnom, m.prenom AS mprenom, m.specialite,
                       m.telephone AS mtel, m.email
                FROM ordonnances o
                JOIN consultations c ON c.idcons=o.idcons
                JOIN patients p ON p.idpat=c.idpat
                JOIN medecins m ON m.id_medecin=c.id_medecin
                WHERE o.idord=?
            """, (new_oid,)).fetchone()
            conn2.close()
            if row:
                PrintPreview(self.master, dict(row))
        self.destroy()

    def _preview(self):
        if not self.ordonnance: return
        conn = get_connection()
        row = conn.execute("""
            SELECT o.idord, o.medicaments, o.posologie, o.idcons,
                   c.datecons,
                   p.nompat, p.prenompat, p.agepat, p.sexe, p.telpat,
                   m.nom AS mnom, m.prenom AS mprenom, m.specialite,
                   m.telephone AS mtel, m.email
            FROM ordonnances o
            JOIN consultations c ON c.idcons=o.idcons
            JOIN patients p ON p.idpat=c.idpat
            JOIN medecins m ON m.id_medecin=c.id_medecin
            WHERE o.idord=?
        """, (self.ordonnance["idord"],)).fetchone()
        conn.close()
        if row:
            PrintPreview(self.master, dict(row))


# ══════════════════════════════════════════════════════════════════
#  Aperçu impression (fenêtre)
# ══════════════════════════════════════════════════════════════════
class PrintPreview(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        nom_pat = f"{data['prenompat']} {data['nompat']}"
        self.title(f"Aperçu ordonnance — {nom_pat}")
        WIN_W, WIN_H = 640, 740
        self.geometry(f"{WIN_W}x{WIN_H}+"
                      f"{(self.winfo_screenwidth()-WIN_W)//2}+"
                      f"{(self.winfo_screenheight()-WIN_H)//2}")
        self.configure(bg="#E8E8E8")
        self.grab_set()
        self._build()

    def _build(self):
        d = self.data

        # ── Barre d'outils ─────────────────────────────────────────
        action_bar = tk.Frame(self, bg="#333333", pady=8)
        action_bar.pack(fill="x")

        tk.Button(action_bar, text="📄  Exporter PDF",
                  font=FONT_NORMAL, bg="#E65100", fg="white",
                  relief="flat", padx=14, pady=5, cursor="hand2",
                  command=lambda: generate_pdf(self, d)).pack(side="left", padx=10)

        tk.Button(action_bar, text="💾  Sauvegarder .txt",
                  font=FONT_NORMAL, bg="#37474F", fg="white",
                  relief="flat", padx=14, pady=5, cursor="hand2",
                  command=self._save_txt).pack(side="left", padx=4)

        tk.Button(action_bar, text="✖  Fermer",
                  font=FONT_NORMAL, bg="#555555", fg="white",
                  relief="flat", padx=14, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=10)

        # ── Aperçu scrollable ──────────────────────────────────────
        canvas = tk.Canvas(self, bg="#E0E0E0", highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=20, pady=12)

        # Feuille blanche simulant A4
        paper = tk.Frame(canvas, bg="white",
                         highlightthickness=1, highlightbackground="#AAAAAA")
        canvas.create_window((0, 0), window=paper, anchor="nw")
        paper.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width-4))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        doc = tk.Frame(paper, bg="white", padx=40, pady=30)
        doc.pack(fill="both", expand=True)

        # ── En-tête cabinet ────────────────────────────────────────
        hdr = tk.Frame(doc, bg=PRIMARY, padx=18, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text=f"Dr. {d['mprenom']} {d['mnom']}",
                 font=("Segoe UI",14,"bold"), bg=PRIMARY, fg="white").pack(anchor="w")
        tk.Label(hdr, text=d["specialite"],
                 font=FONT_NORMAL, bg=PRIMARY, fg="#85B7EB").pack(anchor="w")
        tk.Label(hdr, text=f"📞 {d['mtel']}   ✉ {d.get('email','')}",
                 font=FONT_SMALL, bg=PRIMARY, fg="#B5D4F4").pack(anchor="w")

        self._sep(doc)

        # Titre
        tk.Label(doc, text="ORDONNANCE MÉDICALE",
                 font=("Segoe UI",14,"bold"), bg="white", fg=PRIMARY).pack(pady=(10,2))
        tk.Label(doc, text=f"Date : {d['datecons']}",
                 font=FONT_NORMAL, bg="white", fg=TEXT_MUTED).pack(pady=(0,12))

        # ── Bloc patient ───────────────────────────────────────────
        pat_f = tk.Frame(doc, bg=PRIMARY_LIGHT, padx=16, pady=10,
                         highlightthickness=1, highlightbackground="#B5D4F4")
        pat_f.pack(fill="x", pady=(0,14))
        sexe_lbl = "M." if d["sexe"] == "M" else "Mme"
        tk.Label(pat_f, text="PATIENT", font=("Segoe UI",8,"bold"),
                 bg=PRIMARY_LIGHT, fg=PRIMARY).pack(anchor="w")
        tk.Label(pat_f,
                 text=f"{sexe_lbl} {d['prenompat'].capitalize()} {d['nompat'].upper()}",
                 font=("Segoe UI",12,"bold"), bg=PRIMARY_LIGHT, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(pat_f, text=f"{d['agepat']} ans   ·   Tél : {d['telpat']}",
                 font=FONT_NORMAL, bg=PRIMARY_LIGHT, fg=TEXT_MUTED).pack(anchor="w")

        # ── Médicaments ────────────────────────────────────────────
        tk.Label(doc, text="💊  Médicaments prescrits",
                 font=("Segoe UI",11,"bold"), bg="white", fg=TEXT_MAIN).pack(anchor="w", pady=(4,6))

        for i, line in enumerate(d["medicaments"].splitlines()):
            if not line.strip(): continue
            row_f = tk.Frame(doc, bg="#F8F4FF" if i%2==0 else "white",
                             padx=10, pady=5,
                             highlightthickness=1, highlightbackground="#E8E0F8")
            row_f.pack(fill="x", pady=1)
            tk.Label(row_f, text=f"{i+1}.", font=("Segoe UI",10,"bold"),
                     bg=row_f["bg"], fg=PRIMARY, width=3).pack(side="left")
            tk.Label(row_f, text=line.strip(), font=FONT_NORMAL,
                     bg=row_f["bg"], fg=TEXT_MAIN,
                     wraplength=460, justify="left").pack(side="left", anchor="w")

        self._sep(doc, pady=14)

        # ── Posologie ──────────────────────────────────────────────
        tk.Label(doc, text="📋  Posologie / Instructions",
                 font=("Segoe UI",11,"bold"), bg="white", fg=TEXT_MAIN).pack(anchor="w", pady=(0,8))

        pos_f = tk.Frame(doc, bg="#F0FFF8", padx=14, pady=12,
                         highlightthickness=1, highlightbackground="#A8DFC9")
        pos_f.pack(fill="x")
        tk.Label(pos_f, text=d["posologie"], font=FONT_NORMAL,
                 bg="#F0FFF8", fg=TEXT_MAIN,
                 wraplength=490, justify="left").pack(anchor="w")

        self._sep(doc, pady=20)

        # ── Signature ──────────────────────────────────────────────
        sig_f = tk.Frame(doc, bg="white")
        sig_f.pack(fill="x")
        tk.Label(sig_f, text="Cachet et signature du médecin :",
                 font=FONT_LABEL, bg="white", fg=TEXT_MUTED).pack(anchor="e")
        tk.Frame(sig_f, bg=BORDER, height=1).pack(fill="x", pady=(40,4))
        tk.Label(sig_f,
                 text=f"Dr. {d['mprenom']} {d['mnom']}",
                 font=("Segoe UI",11,"bold"), bg="white", fg=TEXT_MAIN).pack(anchor="e")
        tk.Label(sig_f, text=d["specialite"],
                 font=FONT_SMALL, bg="white", fg=TEXT_MUTED).pack(anchor="e")

        tk.Label(doc, text=f"Ordonnance N° {d['idord']}  —  Imprimée le {date.today()}",
                 font=("Segoe UI",8), bg="white", fg=TEXT_LIGHT).pack(pady=(24,0))

    def _sep(self, parent, pady=8):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=pady)

    def _save_txt(self):
        d = self.data
        content = (
            f"{'='*55}\n"
            f"  ORDONNANCE MÉDICALE  N° {d['idord']}\n"
            f"{'='*55}\n\n"
            f"Cabinet : Dr. {d['mprenom']} {d['mnom']}\n"
            f"Spécialité : {d['specialite']}\n"
            f"Tél : {d['mtel']}   Email : {d.get('email','')}\n\n"
            f"Date : {d['datecons']}\n\n"
            f"Patient : {d['prenompat']} {d['nompat']}  —  {d['agepat']} ans\n"
            f"Téléphone : {d['telpat']}\n\n"
            f"{'─'*40}\n"
            f"MÉDICAMENTS :\n"
            f"{'─'*40}\n"
            + "\n".join(f"  {i+1}. {l}" for i,l in enumerate(d["medicaments"].splitlines()) if l.strip())
            + f"\n\n{'─'*40}\n"
            f"POSOLOGIE / INSTRUCTIONS :\n"
            f"{'─'*40}\n"
            f"{d['posologie']}\n\n"
            f"{'='*55}\n"
            f"Signature : Dr. {d['mprenom']} {d['mnom']}\n"
            f"{'='*55}\n"
        )
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte","*.txt")],
            initialfile=f"ordonnance_{d['datecons']}_{d['nompat']}.txt",
            parent=self)
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            messagebox.showinfo("Sauvegardé", f"Fichier enregistré :\n{path}", parent=self)


# ══════════════════════════════════════════════════════════════════
#  Génération PDF avec ReportLab
# ══════════════════════════════════════════════════════════════════
def generate_pdf(parent, d):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
    except ImportError:
        messagebox.showerror("ReportLab manquant",
                             "La bibliothèque ReportLab n'est pas installée.\n"
                             "Lancez : pip install reportlab",
                             parent=parent)
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF","*.pdf")],
        initialfile=f"ordonnance_{d['datecons']}_{d['nompat']}.pdf",
        parent=parent)
    if not path:
        return

    doc_pdf = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=1.5*cm, bottomMargin=2*cm)
    primary_color = colors.HexColor("#0C447C")
    accent_color  = colors.HexColor("#1D9E75")
    light_blue    = colors.HexColor("#E6F1FB")
    light_green   = colors.HexColor("#E1F5EE")
    border_color  = colors.HexColor("#E0DDD5")

    styles = getSampleStyleSheet()
    style_normal  = ParagraphStyle("N", fontName="Helvetica",      fontSize=10, leading=15)
    style_bold    = ParagraphStyle("B", fontName="Helvetica-Bold",  fontSize=10, leading=15)
    style_title   = ParagraphStyle("T", fontName="Helvetica-Bold",  fontSize=14, leading=18,
                                   textColor=primary_color, alignment=1)
    style_section = ParagraphStyle("S", fontName="Helvetica-Bold",  fontSize=11, leading=14,
                                   textColor=colors.HexColor("#1A1A18"))
    style_small   = ParagraphStyle("Sm", fontName="Helvetica",      fontSize=8, leading=11,
                                   textColor=colors.HexColor("#9A9994"))
    style_white   = ParagraphStyle("W", fontName="Helvetica-Bold",  fontSize=13, leading=16,
                                   textColor=colors.white)
    style_white_s = ParagraphStyle("Ws", fontName="Helvetica",      fontSize=10, leading=13,
                                   textColor=colors.HexColor("#85B7EB"))

    story = []

    # ── En-tête cabinet (tableau coloré) ─────────────────────────
    hdr_data = [[
        Paragraph(f"Dr. {d['mprenom']} {d['mnom']}", style_white),
        ""
    ], [
        Paragraph(d["specialite"], style_white_s),
        ""
    ], [
        Paragraph(f"Tél : {d['mtel']}   •   {d.get('email','')}", style_white_s),
        ""
    ]]
    hdr_table = Table(hdr_data, colWidths=["75%","25%"])
    hdr_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), primary_color),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 16),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 14))

    # Titre
    story.append(Paragraph("ORDONNANCE MÉDICALE", style_title))
    story.append(Paragraph(f"Date : {d['datecons']}", ParagraphStyle(
        "date", fontName="Helvetica", fontSize=10, alignment=1,
        textColor=colors.HexColor("#6B6A65"))))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color))
    story.append(Spacer(1, 10))

    # Patient
    sexe_lbl = "M." if d["sexe"] == "M" else "Mme"
    pat_data = [[
        Paragraph("PATIENT", ParagraphStyle(
            "plab", fontName="Helvetica-Bold", fontSize=8, textColor=primary_color))
    ], [
        Paragraph(f"{sexe_lbl} {d['prenompat'].capitalize()} {d['nompat'].upper()}",
                  ParagraphStyle("pname", fontName="Helvetica-Bold", fontSize=12,
                                 textColor=colors.HexColor("#1A1A18")))
    ], [
        Paragraph(f"{d['agepat']} ans   •   Tél : {d['telpat']}", style_normal)
    ]]
    pat_table = Table(pat_data, colWidths=["100%"])
    pat_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), light_blue),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#B5D4F4")),
    ]))
    story.append(pat_table)
    story.append(Spacer(1, 14))

    # Médicaments
    story.append(Paragraph("💊  Médicaments prescrits", style_section))
    story.append(Spacer(1, 6))
    meds = [l.strip() for l in d["medicaments"].splitlines() if l.strip()]
    med_rows = [[
        Paragraph(f"{i+1}.", ParagraphStyle("n",fontName="Helvetica-Bold",
                  fontSize=10, textColor=primary_color)),
        Paragraph(line, style_normal)
    ] for i, line in enumerate(meds)]
    if med_rows:
        med_table = Table(med_rows, colWidths=[0.6*cm, "95%"])
        med_table.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [colors.HexColor("#F8F4FF"),
                                              colors.white]),
            ("BOX",  (0,0),(-1,-1), 0.5, colors.HexColor("#E0D8F8")),
            ("GRID", (0,0),(-1,-1), 0.3, colors.HexColor("#EDE8FF")),
        ]))
        story.append(med_table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color))
    story.append(Spacer(1, 10))

    # Posologie
    story.append(Paragraph("📋  Posologie / Instructions", style_section))
    story.append(Spacer(1, 6))
    pos_data = [[Paragraph(d["posologie"], style_normal)]]
    pos_table = Table(pos_data, colWidths=["100%"])
    pos_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), light_green),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("BOX", (0,0),(-1,-1), 0.5, colors.HexColor("#A8DFC9")),
    ]))
    story.append(pos_table)
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color))
    story.append(Spacer(1, 8))

    # Signature
    sig_data = [[
        "",
        Paragraph(f"Dr. {d['mprenom']} {d['mnom']}<br/>"
                  f"<font size='9' color='#6B6A65'>{d['specialite']}</font>",
                  ParagraphStyle("sig", fontName="Helvetica-Bold",
                                 fontSize=11, alignment=2))
    ]]
    sig_table = Table(sig_data, colWidths=["50%","50%"])
    story.append(sig_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Ordonnance N° {d['idord']}  —  Générée le {date.today()}",
        style_small))

    try:
        doc_pdf.build(story)
        messagebox.showinfo("PDF créé",
                            f"Ordonnance exportée en PDF :\n{path}", parent=parent)
        # Ouvrir le PDF automatiquement
        import os, subprocess, sys
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as ex:
        messagebox.showerror("Erreur PDF", str(ex), parent=parent)
