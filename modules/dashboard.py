"""Tableau de bord — filtre date global par module avec onglets."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from utils.database import get_connection
from utils.styles import *


class DashboardPage:
    def __init__(self, parent, medecin, switch_page):
        self.parent      = parent
        self.medecin     = medecin
        self.switch_page = switch_page
        self._active_tab = "consultations"
        self._build()

    # ─────────────────────────────────────────────────────────────
    def _build(self):
        # ── Barre de filtre ────────────────────────────────────────
        filter_bar = tk.Frame(self.parent, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER,
                              padx=16, pady=10)
        filter_bar.pack(fill="x", side="top")

        tk.Label(filter_bar, text="📅  Période :", font=("Segoe UI",10,"bold"),
                 bg=BG_CARD, fg=PRIMARY).pack(side="left")
        tk.Label(filter_bar, text="Du", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left", padx=(10,4))
        self.date_debut = tk.StringVar(value=(date.today()-timedelta(days=30)).isoformat())
        tk.Entry(filter_bar, textvariable=self.date_debut, font=FONT_NORMAL, width=12,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER).pack(side="left", ipady=5)
        tk.Label(filter_bar, text="au", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left", padx=(8,4))
        self.date_fin = tk.StringVar(value=date.today().isoformat())
        tk.Entry(filter_bar, textvariable=self.date_fin, font=FONT_NORMAL, width=12,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER).pack(side="left", ipady=5)

        tk.Button(filter_bar, text="🔍  Filtrer", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, command=self._apply_filter).pack(side="left", padx=(10,4))

        for label, days in [("7 jours",7),("30 jours",30),("3 mois",90),("Tout",None)]:
            tk.Button(filter_bar, text=label, font=FONT_SMALL,
                      bg=PRIMARY_LIGHT, fg=PRIMARY, relief="flat", cursor="hand2", padx=8, pady=5,
                      command=lambda d=days: self._quick_filter(d)).pack(side="left", padx=2)

        tk.Button(filter_bar, text="🖨  Imprimer rapport", font=FONT_NORMAL,
                  bg="#FFF3E0", fg="#E65100", relief="flat", cursor="hand2",
                  padx=12, pady=5, command=self._print_rapport).pack(side="right", padx=(0,6))

        # ── Zone principale scrollable ─────────────────────────────
        self.canvas = tk.Canvas(self.parent, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG)
        self.win_id = self.canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win_id, width=e.width))
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120),"units"))

        self._apply_filter()

    def _quick_filter(self, days):
        self.date_debut.set(("2000-01-01" if days is None else (date.today()-timedelta(days=days)).isoformat()))
        self.date_fin.set(date.today().isoformat())
        self._apply_filter()

    def _apply_filter(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        d1 = self.date_debut.get().strip()
        d2 = self.date_fin.get().strip()
        if not d1 or not d2:
            messagebox.showerror("Erreur","Veuillez renseigner les deux dates."); return
        self._render(d1, d2)

    # ── Rendu complet ──────────────────────────────────────────────
    def _render(self, d1, d2):
        pad = tk.Frame(self.scroll_frame, bg=BG)
        pad.pack(fill="both", expand=True, padx=18, pady=14)

        # Salutation
        tk.Label(pad, text=f"Bonjour, Dr. {self.medecin['prenom']} 👋",
                 font=("Segoe UI",14,"bold"), bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(pad, text=f"Aujourd'hui : {date.today()}   |   Période : {d1}  →  {d2}",
                 font=FONT_SMALL, bg=BG, fg=TEXT_MUTED).pack(anchor="w", pady=(0,12))

        # ── Cartes résumé ──────────────────────────────────────────
        stats = self._get_stats(d1, d2)
        cards = [
            ("Patients",         stats["patients"],                     "👥", PRIMARY_LIGHT,  PRIMARY),
            ("Consultations",    stats["consultations"],                "🩺", ACCENT_LIGHT,   ACCENT),
            ("Rendez-vous",      stats["rdv"],                         "📅", WARNING_LIGHT,  WARNING),
            ("Recettes (FCFA)",  f"{stats['recettes']:,.0f}",          "💰", "#E8F5E9",       "#1B5E20"),
            ("Ordonnances",      stats["ordonnances"],                 "💊", "#F3E5F5",       "#4A148C"),
            ("Analyses",         stats["analyses"],                    "🔬", "#E3F2FD",       "#0D47A1"),
        ]
        grid = tk.Frame(pad, bg=BG)
        grid.pack(fill="x", pady=(0,14))
        for i in range(6): grid.columnconfigure(i, weight=1, uniform="stat")
        for idx,(lbl,val,ico,bg,fg) in enumerate(cards):
            c = tk.Frame(grid, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER)
            c.grid(row=0, column=idx, padx=4, pady=4, sticky="nsew")
            tk.Label(c, text=ico, font=("Segoe UI",18), bg=BG_CARD).pack(pady=(10,0))
            tk.Label(c, text=str(val), font=("Segoe UI",16,"bold"), bg=BG_CARD, fg=fg).pack()
            tk.Label(c, text=lbl, font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED,
                     wraplength=120).pack(pady=(0,10))

        # ── Onglets de filtre par module ───────────────────────────
        TABS = [
            ("🩺  Consultations", "consultations"),
            ("👥  Patients",      "patients"),
            ("📅  Rendez-vous",   "rendezvous"),
            ("💊  Ordonnances",   "ordonnances"),
            ("🔬  Analyses",      "analyses"),
        ]
        tab_bar = tk.Frame(pad, bg=BG_CARD,
                           highlightthickness=1, highlightbackground=BORDER)
        tab_bar.pack(fill="x", pady=(0,0))

        self.tab_btns = {}
        for lbl, key in TABS:
            btn = tk.Button(tab_bar, text=lbl, font=("Segoe UI",10,"bold"),
                            relief="flat", cursor="hand2", padx=16, pady=9,
                            command=lambda k=key, d1=d1, d2=d2: self._show_tab(k, d1, d2, pad))
            btn.pack(side="left")
            self.tab_btns[key] = btn

        # Zone de contenu des onglets
        self.tab_content = tk.Frame(pad, bg=BG_CARD,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.tab_content.pack(fill="both", expand=True, pady=(0,14))

        # Afficher l'onglet actif
        self._show_tab(self._active_tab, d1, d2, pad)

        # ── Accès rapides ──────────────────────────────────────────
        qc = tk.LabelFrame(pad, text="  🚀  Accès rapides", font=FONT_SECTION,
                           bg=BG_CARD, fg=PRIMARY, bd=0,
                           highlightthickness=1, highlightbackground=BORDER,
                           padx=14, pady=10)
        qc.pack(fill="x")
        for i in range(4): qc.columnconfigure(i, weight=1)
        quick = [("➕ Nouveau patient","patients"),("📅 Nouveau RDV","rendezvous"),
                 ("🩺 Nouvelle consultation","consultations"),("💊 Nouvelle ordonnance","ordonnances")]
        for i,(lbl,key) in enumerate(quick):
            tk.Button(qc, text=lbl, font=FONT_NORMAL, bg=PRIMARY_LIGHT, fg=PRIMARY,
                      relief="flat", cursor="hand2", pady=8, padx=8, anchor="w",
                      activebackground=PRIMARY, activeforeground="white",
                      command=lambda k=key: self.switch_page(k)).grid(row=0,column=i,padx=5,sticky="ew")

    # ── Affichage d'un onglet ──────────────────────────────────────
    def _show_tab(self, key, d1, d2, pad):
        self._active_tab = key
        # Style boutons onglets
        for k, btn in self.tab_btns.items():
            if k == key:
                btn.config(bg=PRIMARY, fg="white")
            else:
                btn.config(bg=BG_CARD, fg=TEXT_MUTED)

        for w in self.tab_content.winfo_children():
            w.destroy()

        if key == "consultations":
            self._tab_consultations(d1, d2)
        elif key == "patients":
            self._tab_patients(d1, d2)
        elif key == "rendezvous":
            self._tab_rendezvous(d1, d2)
        elif key == "ordonnances":
            self._tab_ordonnances(d1, d2)
        elif key == "analyses":
            self._tab_analyses(d1, d2)

    # ── Onglet Consultations ───────────────────────────────────────
    def _tab_consultations(self, d1, d2):
        f = self.tab_content
        info_f = tk.Frame(f, bg=BG_CARD, padx=14, pady=8)
        info_f.pack(fill="x")

        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        rows = conn.execute("""
            SELECT c.idcons,c.datecons,p.nompat||' '||p.prenompat,
                   c.motifcons,c.type_cons,c.prix_cons,c.statut
            FROM consultations c JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ?
            ORDER BY c.datecons DESC
        """, (mid,d1,d2)).fetchall()
        total = conn.execute("""
            SELECT COALESCE(SUM(prix_cons),0) FROM consultations
            WHERE id_medecin=? AND datecons BETWEEN ? AND ?
        """, (mid,d1,d2)).fetchone()[0]
        conn.close()

        # Résumé
        st_count = {}
        for r in rows: st_count[r[6]] = st_count.get(r[6],0)+1
        summary = tk.Frame(info_f, bg=BG_CARD)
        summary.pack(fill="x", pady=(0,8))
        tk.Label(summary, text=f"  {len(rows)} consultation(s)   |",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
        for st, cnt in st_count.items():
            colors_st = {"Terminée":("#EAF3DE","#2A5C0E"),"En cours":("#FFF8E1","#7A5000"),"Annulée":("#FCEBEB","#7A0000")}
            bg_s,fg_s = colors_st.get(st,(PRIMARY_LIGHT,PRIMARY))
            tk.Label(summary, text=f"  {st}: {cnt}",
                     font=FONT_SMALL, bg=bg_s, fg=fg_s, padx=6, pady=2).pack(side="left", padx=4)
        tk.Label(summary, text=f"   💰 Total : {total:,.0f} FCFA",
                 font=("Segoe UI",10,"bold"), bg=BG_CARD, fg="#1B5E20").pack(side="right")

        # Tableau
        self._make_tree(f,
            cols=[("ID",50,"center"),("Date",100,"center"),("Patient",170,"w"),
                  ("Motif",200,"w"),("Type",110,"center"),("Prix (FCFA)",95,"center"),("Statut",95,"center")],
            rows=[(r[0],r[1],r[2],r[3][:45]+"…" if len(r[3])>45 else r[3],
                   r[4],f"{r[5]:,.0f}" if r[5] else "—",r[6]) for r in rows],
            height=10,
            tag_col=6,
            tag_colors={"Terminée":"#E8F5E9","En cours":"#FFF8E1","Annulée":"#FFEBEE"}
        )

    # ── Onglet Patients ────────────────────────────────────────────
    def _tab_patients(self, d1, d2):
        f = self.tab_content
        info_f = tk.Frame(f, bg=BG_CARD, padx=14, pady=8)
        info_f.pack(fill="x")

        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        # Patients ayant eu une consultation dans la période
        rows = conn.execute("""
            SELECT DISTINCT p.idpat,p.nompat,p.prenompat,p.agepat,p.sexe,p.telpat,
                   COUNT(c.idcons) AS nb_cons,
                   COALESCE(SUM(c.prix_cons),0) AS total_paye
            FROM patients p
            LEFT JOIN consultations c ON c.idpat=p.idpat
                AND c.id_medecin=? AND c.datecons BETWEEN ? AND ?
            WHERE c.idcons IS NOT NULL
            GROUP BY p.idpat ORDER BY p.nompat
        """, (mid,d1,d2)).fetchall()
        conn.close()

        tk.Label(info_f, text=f"  {len(rows)} patient(s) consulté(s) sur la période",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0,6))

        self._make_tree(f,
            cols=[("ID",50,"center"),("Nom",130,"w"),("Prénom",130,"w"),
                  ("Âge",60,"center"),("Sexe",60,"center"),("Téléphone",120,"w"),
                  ("Nb consultations",120,"center"),("Total payé (FCFA)",130,"center")],
            rows=[(r[0],r[1],r[2],r[3],r[4],r[5],r[6],f"{r[7]:,.0f}") for r in rows],
            height=10
        )

    # ── Onglet Rendez-vous ─────────────────────────────────────────
    def _tab_rendezvous(self, d1, d2):
        f = self.tab_content
        info_f = tk.Frame(f, bg=BG_CARD, padx=14, pady=8)
        info_f.pack(fill="x")

        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        rows = conn.execute("""
            SELECT r.idrdv,r.date_rdv,p.nompat||' '||p.prenompat,r.motif,r.statut
            FROM rendezvous r JOIN patients p ON p.idpat=r.idpat
            WHERE r.id_medecin=? AND r.date_rdv BETWEEN ? AND ?
            ORDER BY r.date_rdv DESC
        """, (mid,d1+"%",d2+"%")).fetchall()
        conn.close()

        st_count = {}
        for r in rows: st_count[r[4]] = st_count.get(r[4],0)+1
        summary = tk.Frame(info_f, bg=BG_CARD); summary.pack(fill="x",pady=(0,6))
        tk.Label(summary, text=f"  {len(rows)} rendez-vous   |",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
        RDV_COLORS = {"Planifié":("#E6F1FB","#185FA5"),"Confirmé":("#EAF3DE","#2A5C0E"),
                      "Annulé":("#FCEBEB","#7A0000"),"Honoré":(ACCENT_LIGHT,ACCENT)}
        for st,cnt in st_count.items():
            bg_s,fg_s = RDV_COLORS.get(st,(PRIMARY_LIGHT,PRIMARY))
            tk.Label(summary, text=f"  {st}: {cnt}",
                     font=FONT_SMALL, bg=bg_s, fg=fg_s, padx=6, pady=2).pack(side="left",padx=4)

        self._make_tree(f,
            cols=[("ID",55,"center"),("Date & heure",155,"center"),("Patient",180,"w"),
                  ("Motif",220,"w"),("Statut",100,"center")],
            rows=[(r[0],r[1],r[2],(r[3] or "—")[:50],r[4]) for r in rows],
            height=10,
            tag_col=4,
            tag_colors={"Planifié":"#E6F1FB","Confirmé":"#EAF3DE","Annulé":"#FFEBEE","Honoré":"#E1F5EE"}
        )

    # ── Onglet Ordonnances ─────────────────────────────────────────
    def _tab_ordonnances(self, d1, d2):
        f = self.tab_content
        info_f = tk.Frame(f, bg=BG_CARD, padx=14, pady=8)
        info_f.pack(fill="x")

        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        rows = conn.execute("""
            SELECT o.idord,c.datecons,p.nompat||' '||p.prenompat,
                   o.medicaments,o.posologie
            FROM ordonnances o
            JOIN consultations c ON c.idcons=o.idcons
            JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ?
            ORDER BY c.datecons DESC
        """, (mid,d1,d2)).fetchall()
        conn.close()

        tk.Label(info_f, text=f"  {len(rows)} ordonnance(s) émise(s) sur la période",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0,6))

        self._make_tree(f,
            cols=[("ID",55,"center"),("Date",100,"center"),("Patient",180,"w"),
                  ("Médicaments",260,"w"),("Posologie",240,"w")],
            rows=[(r[0],r[1],r[2],
                   r[3][:55]+"…" if len(r[3])>55 else r[3],
                   r[4][:60]+"…" if len(r[4])>60 else r[4]) for r in rows],
            height=10
        )

    # ── Onglet Analyses ────────────────────────────────────────────
    def _tab_analyses(self, d1, d2):
        f = self.tab_content
        info_f = tk.Frame(f, bg=BG_CARD, padx=14, pady=8)
        info_f.pack(fill="x")

        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        rows = conn.execute("""
            SELECT a.idanal,c.datecons,p.nompat||' '||p.prenompat,
                   a.av_od,a.av_og,a.tension_od,a.tension_og,
                   a.sphere_od,a.sphere_og,a.addition
            FROM analyses a
            JOIN consultations c ON c.idcons=a.idcons
            JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ?
            ORDER BY c.datecons DESC
        """, (mid,d1,d2)).fetchall()
        conn.close()

        tk.Label(info_f, text=f"  {len(rows)} analyse(s) sur la période",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0,6))

        def fmt(v): return str(v) if v is not None else "—"

        self._make_tree(f,
            cols=[("ID",50,"center"),("Date",100,"center"),("Patient",160,"w"),
                  ("AV OD",65,"center"),("AV OG",65,"center"),
                  ("T. OD",65,"center"),("T. OG",65,"center"),
                  ("Sph OD",70,"center"),("Sph OG",70,"center"),("Addition",75,"center")],
            rows=[(r[0],r[1],r[2],r[3],r[4],r[5],r[6],
                   fmt(r[7]),fmt(r[8]),fmt(r[9])) for r in rows],
            height=10
        )

    # ── Helper : créer un Treeview stylisé ────────────────────────
    def _make_tree(self, parent, cols, rows, height=10, tag_col=None, tag_colors=None):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dash.Treeview", rowheight=30, font=FONT_NORMAL,
                        background="#F8FBFF", fieldbackground="#F8FBFF",
                        foreground=TEXT_MAIN, borderwidth=0)
        style.configure("Dash.Treeview.Heading", background=PRIMARY, foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat", padding=6)
        style.map("Dash.Treeview",
                  background=[("selected","#B0D4F1")],
                  foreground=[("selected",PRIMARY_DARK)])
        style.map("Dash.Treeview.Heading",
                  background=[("active",PRIMARY_DARK)])

        wrap = tk.Frame(parent, bg=PRIMARY, padx=1, pady=1)
        wrap.pack(fill="both", expand=True, padx=12, pady=(0,10))

        col_names = [c[0] for c in cols]
        tree = ttk.Treeview(wrap, columns=col_names, show="headings",
                            style="Dash.Treeview", height=height)
        for col_name, w, anc in cols:
            tree.heading(col_name, text=col_name, anchor="center")
            tree.column(col_name, width=w, anchor=anc, minwidth=w, stretch=True)

        # Tags couleurs
        if tag_colors:
            for tag, bg_color in tag_colors.items():
                tree.tag_configure(tag, background=bg_color)
        tree.tag_configure("odd",  background="#EEF5FF")
        tree.tag_configure("even", background="#F8FBFF")

        sb_y = ttk.Scrollbar(wrap, orient="vertical",   command=tree.yview)
        sb_x = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        for i, row in enumerate(rows):
            if tag_col is not None and tag_colors:
                tag_val = str(row[tag_col])
                tag = tag_val if tag_val in tag_colors else ("odd" if i%2==0 else "even")
            else:
                tag = "odd" if i%2==0 else "even"
            tree.insert("", "end", values=row, tags=(tag,))

        if not rows:
            tree.insert("", "end", values=("—","Aucune donnée sur cette période") + ("",)*(len(cols)-2))

        return tree

    # ── Statistiques ──────────────────────────────────────────────
    def _get_stats(self, d1, d2):
        conn = get_connection()
        mid  = self.medecin["id_medecin"]
        r = {
            "patients":      conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "consultations": conn.execute("SELECT COUNT(*) FROM consultations WHERE id_medecin=? AND datecons BETWEEN ? AND ?",(mid,d1,d2)).fetchone()[0],
            "recettes":      conn.execute("SELECT COALESCE(SUM(prix_cons),0) FROM consultations WHERE id_medecin=? AND datecons BETWEEN ? AND ?",(mid,d1,d2)).fetchone()[0],
            "rdv":           conn.execute("SELECT COUNT(*) FROM rendezvous WHERE id_medecin=? AND date_rdv BETWEEN ? AND ?",(mid,d1+"%",d2+"%")).fetchone()[0],
            "ordonnances":   conn.execute("SELECT COUNT(*) FROM ordonnances o JOIN consultations c ON c.idcons=o.idcons WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ?",(mid,d1,d2)).fetchone()[0],
            "analyses":      conn.execute("SELECT COUNT(*) FROM analyses a JOIN consultations c ON c.idcons=a.idcons WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ?",(mid,d1,d2)).fetchone()[0],
        }
        conn.close()
        return r

    # ── Impression rapport PDF ─────────────────────────────────────
    def _print_rapport(self):
        d1 = self.date_debut.get().strip()
        d2 = self.date_fin.get().strip()
        if not d1 or not d2: return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,HRFlowable
        except ImportError:
            messagebox.showerror("Erreur","Installez reportlab : pip install reportlab"); return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"rapport_{d1}_{d2}.pdf")
        if not path: return

        stats = self._get_stats(d1, d2)
        mid   = self.medecin["id_medecin"]
        conn  = get_connection()
        cons_rows = conn.execute("""
            SELECT c.datecons,p.nompat||' '||p.prenompat,c.type_cons,c.prix_cons,c.statut
            FROM consultations c JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ? ORDER BY c.datecons
        """, (mid,d1,d2)).fetchall()
        rdv_rows = conn.execute("""
            SELECT r.date_rdv,p.nompat||' '||p.prenompat,r.motif,r.statut
            FROM rendezvous r JOIN patients p ON p.idpat=r.idpat
            WHERE r.id_medecin=? AND r.date_rdv BETWEEN ? AND ? ORDER BY r.date_rdv
        """, (mid,d1+"%",d2+"%")).fetchall()
        ord_rows = conn.execute("""
            SELECT c.datecons,p.nompat||' '||p.prenompat,o.medicaments
            FROM ordonnances o JOIN consultations c ON c.idcons=o.idcons
            JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ? ORDER BY c.datecons
        """, (mid,d1,d2)).fetchall()
        ana_rows = conn.execute("""
            SELECT c.datecons,p.nompat||' '||p.prenompat,a.av_od,a.av_og,a.tension_od,a.tension_og
            FROM analyses a JOIN consultations c ON c.idcons=a.idcons
            JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=? AND c.datecons BETWEEN ? AND ? ORDER BY c.datecons
        """, (mid,d1,d2)).fetchall()
        conn.close()

        pc = colors.HexColor("#0C447C"); ac = colors.HexColor("#1D9E75")
        bd = colors.HexColor("#E0DDD5")
        doc_pdf = SimpleDocTemplate(path,pagesize=A4,rightMargin=1.8*cm,leftMargin=1.8*cm,
                                    topMargin=1.5*cm,bottomMargin=2*cm)

        def sty(n,**k): return ParagraphStyle(n,**k)
        s_w  = sty("sw",fontName="Helvetica-Bold",fontSize=13,textColor=colors.white)
        s_ws = sty("sws",fontName="Helvetica",fontSize=9,textColor=colors.HexColor("#85B7EB"))
        s_h  = sty("sh",fontName="Helvetica-Bold",fontSize=11,textColor=pc)
        s_n  = sty("sn",fontName="Helvetica",fontSize=9)
        s_b  = sty("sb",fontName="Helvetica-Bold",fontSize=9)
        s_sm = sty("ssm",fontName="Helvetica",fontSize=8,textColor=colors.HexColor("#9A9994"))

        def make_table(rows_data, headers, col_widths, row_colors=None):
            data = [[Paragraph(h,s_b) for h in headers]]
            for r in rows_data:
                data.append([Paragraph(str(v) if v else "—",s_n) for v in r])
            t = Table(data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),pc),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),row_colors or [colors.HexColor("#EAF4FF"),colors.white]),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",(0,0),(-1,-1),6),("BOX",(0,0),(-1,-1),0.5,bd),
                ("GRID",(0,0),(-1,-1),0.3,bd)]))
            return t

        story = []

        # En-tête
        ht = Table([[Paragraph(f"Dr. {self.medecin['prenom']} {self.medecin['nom']}",s_w),""],
                    [Paragraph(self.medecin["specialite"],s_ws),""],
                    [Paragraph(f"Tél : {self.medecin['telephone']}",s_ws),""]], colWidths=["75%","25%"])
        ht.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),pc),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),14)]))
        story += [ht, Spacer(1,10),
                  Paragraph("RAPPORT D'ACTIVITÉ", sty("rt",fontName="Helvetica-Bold",fontSize=13,textColor=pc)),
                  Paragraph(f"Période : {d1}  →  {d2}", sty("rp",fontName="Helvetica",fontSize=10,textColor=colors.HexColor("#6B6A65"))),
                  HRFlowable(width="100%",thickness=1,color=bd), Spacer(1,8)]

        # Stats
        stat_data = [
            ["Consultations",str(stats["consultations"])],
            ["Recettes (FCFA)",f"{stats['recettes']:,.0f}"],
            ["Rendez-vous",str(stats["rdv"])],
            ["Ordonnances",str(stats["ordonnances"])],
            ["Analyses",str(stats["analyses"])],
            ["Patients (total)",str(stats["patients"])],
        ]
        st_t = Table([[Paragraph(h,s_b) for h in ["Indicateur","Valeur"]]]+
                     [[Paragraph(r[0],s_n),Paragraph(r[1],s_b)] for r in stat_data],
                     colWidths=["70%","30%"])
        st_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),pc),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F5F5F5"),colors.white]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8),("BOX",(0,0),(-1,-1),0.5,bd),("GRID",(0,0),(-1,-1),0.3,bd)]))
        story += [Paragraph("📊  Résumé statistique",s_h),Spacer(1,4),st_t,Spacer(1,12)]

        # Consultations
        if cons_rows:
            prix_rows = [(r[0],r[1],r[2],f"{r[3]:,.0f}" if r[3] else "—",r[4]) for r in cons_rows]
            story += [Paragraph("🩺  Consultations",s_h), Spacer(1,4),
                      make_table(prix_rows,["Date","Patient","Type","Prix (FCFA)","Statut"],
                                 ["18%","30%","17%","17%","18%"],
                                 [colors.HexColor("#EAF4FF"),colors.white]),
                      Spacer(1,10)]

        # RDV
        if rdv_rows:
            story += [Paragraph("📅  Rendez-vous",s_h), Spacer(1,4),
                      make_table(rdv_rows,["Date & heure","Patient","Motif","Statut"],
                                 ["25%","28%","27%","20%"],
                                 [colors.HexColor("#E1F5EE"),colors.white]),
                      Spacer(1,10)]

        # Ordonnances
        if ord_rows:
            ord_data = [(r[0],r[1],r[2][:80]+"…" if len(r[2])>80 else r[2]) for r in ord_rows]
            story += [Paragraph("💊  Ordonnances",s_h), Spacer(1,4),
                      make_table(ord_data,["Date","Patient","Médicaments"],
                                 ["18%","28%","54%"],
                                 [colors.HexColor("#F3E5F5"),colors.white]),
                      Spacer(1,10)]

        # Analyses
        if ana_rows:
            story += [Paragraph("🔬  Analyses",s_h), Spacer(1,4),
                      make_table(ana_rows,["Date","Patient","AV OD","AV OG","T. OD","T. OG"],
                                 ["18%","34%","12%","12%","12%","12%"],
                                 [colors.HexColor("#E3F2FD"),colors.white]),
                      Spacer(1,10)]

        story += [HRFlowable(width="100%",thickness=0.5,color=bd),Spacer(1,4),
                  Paragraph(f"Rapport généré le {date.today()}  —  OphtalmoPro v1.0",s_sm)]

        try:
            doc_pdf.build(story)
            messagebox.showinfo("PDF créé",f"Rapport exporté :\n{path}")
            import os,subprocess,sys
            if sys.platform.startswith("win"): os.startfile(path)
            elif sys.platform=="darwin": subprocess.call(["open",path])
            else: subprocess.call(["xdg-open",path])
        except Exception as ex:
            messagebox.showerror("Erreur PDF",str(ex))
