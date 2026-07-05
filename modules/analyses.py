"""Module Analyses ophtalmologiques — boutons Modifier/Supprimer + couleurs."""
import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import get_connection
from utils.styles import *

ROW_ODD  = "#EAF4FF"
ROW_EVEN = "#D5EAFF"
ROW_SEL  = "#A8D4F5"


class AnalysesPage:
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

        tk.Button(toolbar, text="➕  Nouvelle analyse", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, activebackground=PRIMARY_DARK,
                  command=self._new_analyse).pack(side="left")

        tk.Frame(toolbar, bg=BORDER, width=1).pack(side="left", fill="y", padx=12, pady=2)

        self.btn_edit = self._abtn(toolbar, "✏  Modifier",   "#E6F1FB", PRIMARY, self._edit_analyse)
        self.btn_view = self._abtn(toolbar, "🔍  Détail",     "#EAF3DE", "#2A5C0E", self._view_detail)
        self.btn_del  = self._abtn(toolbar, "🗑  Supprimer",  DANGER_LIGHT, DANGER, self._delete_analyse)
        self.action_btns = [self.btn_edit, self.btn_view, self.btn_del]

        # ── Style Treeview ─────────────────────────────────────────
        style = ttk.Style()
        style.configure("Ana.Treeview", rowheight=34, font=FONT_NORMAL,
                        background=ROW_ODD, fieldbackground=ROW_ODD,
                        foreground=TEXT_MAIN, borderwidth=0)
        style.configure("Ana.Treeview.Heading", background=PRIMARY, foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat", padding=6)
        style.map("Ana.Treeview",
                  background=[("selected", ROW_SEL)],
                  foreground=[("selected", PRIMARY_DARK)])

        # ── Tableau ────────────────────────────────────────────────
        table_f = tk.Frame(self.parent, bg=PRIMARY, padx=1, pady=1)
        table_f.pack(fill="both", expand=True, padx=16, pady=(8,0))

        cols = ("ID","Date","Patient","AV OD","AV OG","T. OD","T. OG",
                "Sph OD","Cyl OD","Axe OD","Sph OG","Cyl OG","Axe OG","Addition")
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings",
                                 style="Ana.Treeview", selectmode="browse")
        widths = [45, 100, 160, 65, 65, 65, 65, 70, 70, 65, 70, 70, 65, 75]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center", minwidth=w)
        self.tree.column("Patient", anchor="w")

        self.tree.tag_configure("odd",  background=ROW_ODD)
        self.tree.tag_configure("even", background=ROW_EVEN)

        sb_y = ttk.Scrollbar(table_f, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda e: self._view_detail())

        ctx = tk.Menu(self.parent, tearoff=0)
        ctx.add_command(label="🔍  Voir le détail",  command=self._view_detail)
        ctx.add_command(label="✏  Modifier",         command=self._edit_analyse)
        ctx.add_separator()
        ctx.add_command(label="🗑  Supprimer",        command=self._delete_analyse)
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
            self.sel_lbl.config(text=f"  Analyse #{v[0]}  —  {v[2]}  —  {v[1]}")
            for btn in self.action_btns:
                btn.config(state="normal")
        else:
            self.sel_lbl.config(text="")
            for btn in self.action_btns:
                btn.config(state="disabled")

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("""
            SELECT a.idanal, c.datecons, p.nompat||' '||p.prenompat,
                   a.av_od, a.av_og, a.tension_od, a.tension_og,
                   a.sphere_od, a.cylindre_od, a.axe_od,
                   a.sphere_og, a.cylindre_og, a.axe_og, a.addition
            FROM analyses a
            JOIN consultations c ON c.idcons=a.idcons
            JOIN patients p ON p.idpat=c.idpat
            WHERE c.id_medecin=?
            ORDER BY c.datecons DESC
        """, (self.medecin["id_medecin"],)).fetchall()
        conn.close()

        def fmt(v): return str(v) if v is not None else "—"

        for i, r in enumerate(rows):
            tag = "odd" if i%2==0 else "even"
            self.tree.insert("", "end", iid=str(r[0]), tags=(tag,),
                             values=(r[0], r[1], r[2],
                                     r[3], r[4], r[5], r[6],
                                     fmt(r[7]), fmt(r[8]), fmt(r[9]),
                                     fmt(r[10]), fmt(r[11]), fmt(r[12]),
                                     fmt(r[13])))
        n = len(rows)
        self.info_lbl.config(text=f"  {n} analyse{'s' if n>1 else ''}")
        for btn in self.action_btns:
            btn.config(state="disabled")
        self.sel_lbl.config(text="")

    def _get_sel_id(self):
        sel = self.tree.selection()
        return int(self.tree.item(sel[0])["values"][0]) if sel else None

    def _new_analyse(self):
        AnalyseForm(self.parent, None, None, self._load)

    def _edit_analyse(self):
        aid = self._get_sel_id()
        if aid:
            conn = get_connection()
            a = dict(conn.execute("SELECT * FROM analyses WHERE idanal=?", (aid,)).fetchone())
            conn.close()
            AnalyseForm(self.parent, a["idcons"], a, self._load)

    def _view_detail(self):
        aid = self._get_sel_id()
        if aid:
            conn = get_connection()
            a = dict(conn.execute("""
                SELECT a.*, c.datecons, p.nompat, p.prenompat, p.agepat, p.sexe
                FROM analyses a
                JOIN consultations c ON c.idcons=a.idcons
                JOIN patients p ON p.idpat=c.idpat
                WHERE a.idanal=?
            """, (aid,)).fetchone())
            conn.close()
            AnalyseDetail(self.parent, a)

    def _delete_analyse(self):
        aid = self._get_sel_id()
        if not aid: return
        v = self.tree.item(str(aid))["values"]
        if messagebox.askyesno("Supprimer",
                               f"Supprimer l'analyse de {v[2]} ({v[1]}) ?",
                               icon="warning"):
            conn = get_connection()
            conn.execute("DELETE FROM analyses WHERE idanal=?", (aid,))
            conn.commit(); conn.close(); self._load()


# ── Fiche détail analyse ────────────────────────────────────────────
class AnalyseDetail(tk.Toplevel):
    def __init__(self, parent, a):
        super().__init__(parent)
        self.title(f"Analyse — {a['prenompat']} {a['nompat']} — {a['datecons']}")
        WIN_W, WIN_H = 560, 520
        self.geometry(f"{WIN_W}x{WIN_H}+"
                      f"{(self.winfo_screenwidth()-WIN_W)//2}+"
                      f"{(self.winfo_screenheight()-WIN_H)//2}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._build(a)

    def _build(self, a):
        hdr = tk.Frame(self, bg=PRIMARY, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🔬  Analyse ophtalmologique — #{a['idanal']}",
                 font=("Segoe UI",13,"bold"), bg=PRIMARY, fg="white").pack(anchor="w")
        tk.Label(hdr, text=f"{a['prenompat']} {a['nompat']}  ·  {a['agepat']} ans  ·  {a['datecons']}",
                 font=FONT_SMALL, bg=PRIMARY, fg="#85B7EB").pack(anchor="w")

        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure((0,1), weight=1, uniform="eye")

        def fmt(v): return str(v) if v is not None else "—"

        def eye_card(parent, title, color, fields):
            card = tk.LabelFrame(parent, text=f"  {title}", font=("Segoe UI",10,"bold"),
                                 bg=BG_CARD, fg=color, bd=0,
                                 highlightthickness=1, highlightbackground=color,
                                 padx=14, pady=10)
            for lbl, val in fields:
                rf = tk.Frame(card, bg=BG_CARD)
                rf.pack(fill="x", pady=3)
                tk.Label(rf, text=lbl, font=FONT_LABEL, bg=BG_CARD,
                         fg=TEXT_MUTED, width=14, anchor="w").pack(side="left")
                tk.Label(rf, text=val, font=("Segoe UI",11,"bold"),
                         bg=BG_CARD, fg=color).pack(side="left")
            return card

        od_fields = [
            ("Acuité visuelle", fmt(a["av_od"])),
            ("Tension (mmHg)",  fmt(a["tension_od"])),
            ("Sphère",          fmt(a["sphere_od"])),
            ("Cylindre",        fmt(a["cylindre_od"])),
            ("Axe (°)",         fmt(a["axe_od"])),
        ]
        og_fields = [
            ("Acuité visuelle", fmt(a["av_og"])),
            ("Tension (mmHg)",  fmt(a["tension_og"])),
            ("Sphère",          fmt(a["sphere_og"])),
            ("Cylindre",        fmt(a["cylindre_og"])),
            ("Axe (°)",         fmt(a["axe_og"])),
        ]
        eye_card(body, "Œil Droit (OD)", PRIMARY, od_fields).grid(
            row=0, column=0, padx=(0,8), sticky="nsew")
        eye_card(body, "Œil Gauche (OG)", ACCENT, og_fields).grid(
            row=0, column=1, padx=(8,0), sticky="nsew")

        # Addition + observation
        extra = tk.Frame(body, bg=BG)
        extra.pack(fill="x", pady=(12,0))
        add_f = tk.Frame(extra, bg=PRIMARY_LIGHT, padx=14, pady=8,
                         highlightthickness=1, highlightbackground=BORDER)
        add_f.pack(fill="x", pady=(0,10))
        tk.Label(add_f, text="Addition :", font=FONT_LABEL, bg=PRIMARY_LIGHT, fg=TEXT_MUTED).pack(side="left")
        tk.Label(add_f, text=fmt(a["addition"]), font=("Segoe UI",12,"bold"),
                 bg=PRIMARY_LIGHT, fg=PRIMARY).pack(side="left", padx=8)

        tk.Label(extra, text="Observations :", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        obs_f = tk.Frame(extra, bg="#FFFDE7", padx=12, pady=8,
                         highlightthickness=1, highlightbackground="#F9A825")
        obs_f.pack(fill="x")
        tk.Label(obs_f, text=a["observation"], font=FONT_NORMAL, bg="#FFFDE7",
                 fg=TEXT_MAIN, wraplength=480, justify="left").pack(anchor="w")

        tk.Button(self, text="Fermer", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=20, pady=7, cursor="hand2",
                  command=self.destroy).pack(pady=10)


# ── Formulaire analyse ─────────────────────────────────────────────
class AnalyseForm(tk.Toplevel):
    def __init__(self, parent, idcons, analyse, callback):
        super().__init__(parent)
        self.idcons   = idcons
        self.analyse  = analyse
        self.callback = callback
        is_edit = bool(analyse)
        self.title("Modifier l'analyse" if is_edit else "Nouvelle analyse")
        self.resizable(False, True)
        WIN_W, WIN_H = 640, 600
        self.geometry(f"{WIN_W}x{WIN_H}+"
                      f"{(self.winfo_screenwidth()-WIN_W)//2}+"
                      f"{(self.winfo_screenheight()-WIN_H)//2}")
        self.configure(bg=BG)
        self.grab_set()
        self._build()

    def _build(self):
        a       = self.analyse or {}
        is_edit = bool(self.analyse)
        hdr_c   = ACCENT if is_edit else PRIMARY

        hdr = tk.Frame(self, bg=hdr_c, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="✏  Modifier l'analyse" if is_edit else "🔬  Nouvelle Analyse",
                 font=("Segoe UI",13,"bold"), bg=hdr_c, fg="white").pack(anchor="w")

        # Zone scrollable
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG, padx=18, pady=12)
        canvas.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))

        # Consultation
        tk.Label(body, text="Consultation liée *", font=FONT_LABEL,
                 bg=BG, fg=TEXT_MUTED).pack(anchor="w")
        conn = get_connection()
        cons_list = conn.execute("""
            SELECT c.idcons,
                   c.datecons||' — '||p.nompat||' '||p.prenompat AS label
            FROM consultations c JOIN patients p ON p.idpat=c.idpat
            ORDER BY c.datecons DESC LIMIT 150
        """).fetchall()
        conn.close()
        self.cons_map = {r["label"]: r["idcons"] for r in cons_list}
        self.cons_var = tk.StringVar()
        if self.idcons:
            for lbl, cid in self.cons_map.items():
                if cid == self.idcons:
                    self.cons_var.set(lbl); break
        ttk.Combobox(body, textvariable=self.cons_var,
                     values=list(self.cons_map.keys()),
                     font=FONT_NORMAL, state="readonly").pack(fill="x", pady=(4,14), ipady=5)

        # Grille OD / OG
        eyes_f = tk.Frame(body, bg=BG)
        eyes_f.pack(fill="x", pady=4)
        eyes_f.columnconfigure((0,1), weight=1, uniform="eye")

        od_frame = tk.LabelFrame(eyes_f, text="  👁 Œil Droit (OD)", font=("Segoe UI",10,"bold"),
                                  bg=BG_CARD, fg=PRIMARY, bd=0,
                                  highlightthickness=1, highlightbackground=PRIMARY,
                                  padx=12, pady=8)
        od_frame.grid(row=0, column=0, padx=(0,6), sticky="nsew")

        og_frame = tk.LabelFrame(eyes_f, text="  👁 Œil Gauche (OG)", font=("Segoe UI",10,"bold"),
                                  bg=BG_CARD, fg=ACCENT, bd=0,
                                  highlightthickness=1, highlightbackground=ACCENT,
                                  padx=12, pady=8)
        og_frame.grid(row=0, column=1, padx=(6,0), sticky="nsew")

        self.od_vars = self._eye_fields(od_frame, "od", a)
        self.og_vars = self._eye_fields(og_frame, "og", a)

        # Addition + observation
        bot = tk.Frame(body, bg=BG)
        bot.pack(fill="x", pady=(12,0))

        add_row = tk.Frame(bot, bg=BG)
        add_row.pack(fill="x", pady=(0,10))
        tk.Label(add_row, text="Addition :", font=FONT_LABEL, bg=BG, fg=TEXT_MUTED).pack(side="left")
        self.addition_var = tk.StringVar(value=str(a["addition"]) if a.get("addition") is not None else "")
        tk.Entry(add_row, textvariable=self.addition_var, font=FONT_NORMAL, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER, width=10).pack(
            side="left", padx=(8,0), ipady=6)

        tk.Label(bot, text="Observations *", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        self.obs_text = tk.Text(bot, font=FONT_NORMAL, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 height=4, padx=8, pady=6)
        self.obs_text.pack(fill="x", pady=(4,0))
        if a.get("observation"):
            self.obs_text.insert("1.0", a["observation"])

        # Boutons
        btn_bar = tk.Frame(self, bg=BG_CARD, padx=20, pady=10,
                           highlightthickness=1, highlightbackground=BORDER)
        btn_bar.pack(fill="x", side="bottom")
        tk.Button(btn_bar, text="✖  Annuler", font=FONT_NORMAL, bg=BG_CARD,
                  relief="flat", highlightthickness=1, highlightbackground=BORDER,
                  padx=14, pady=6, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=6)
        lbl_save = "💾  Enregistrer les modifications" if is_edit else "💾  Enregistrer l'analyse"
        tk.Button(btn_bar, text=lbl_save, font=FONT_NORMAL,
                  bg=ACCENT if is_edit else PRIMARY, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  activebackground=PRIMARY_DARK,
                  command=self._save).pack(side="right", padx=6)

    def _eye_fields(self, parent, prefix, data):
        vars_ = {}
        fields = [
            ("Acuité visuelle *", f"av_{prefix}",       False),
            ("Tension (mmHg) *",  f"tension_{prefix}",   False),
            ("Sphère",            f"sphere_{prefix}",    True),
            ("Cylindre",          f"cylindre_{prefix}",  True),
            ("Axe (°)",           f"axe_{prefix}",       True),
        ]
        parent.columnconfigure(1, weight=1)
        for i, (lbl, key, optional) in enumerate(fields):
            tk.Label(parent, text=lbl, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).grid(
                row=i, column=0, sticky="w", pady=4)
            raw = data.get(key)
            val = str(raw) if raw is not None else ""
            var = tk.StringVar(value=val)
            tk.Entry(parent, textvariable=var, font=FONT_NORMAL, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER).grid(
                row=i, column=1, sticky="ew", padx=(8,0), pady=4, ipady=6)
            vars_[key] = var
        return vars_

    def _save(self):
        cons_lbl = self.cons_var.get().strip()
        obs      = self.obs_text.get("1.0", "end").strip()
        if not cons_lbl or not obs:
            messagebox.showerror("Erreur", "Consultation et observations obligatoires.", parent=self)
            return
        cid = self.cons_map.get(cons_lbl)
        if not cid:
            messagebox.showerror("Erreur", "Consultation introuvable.", parent=self)
            return

        av_od = self.od_vars["av_od"].get().strip()
        av_og = self.og_vars["av_og"].get().strip()
        t_od_s = self.od_vars["tension_od"].get().strip()
        t_og_s = self.og_vars["tension_og"].get().strip()

        if not av_od or not av_og or not t_od_s or not t_og_s:
            messagebox.showerror("Erreur", "Acuité visuelle et tension obligatoires (OD et OG).", parent=self)
            return
        try:
            t_od = int(t_od_s); t_og = int(t_og_s)
        except ValueError:
            messagebox.showerror("Erreur", "La tension doit être un entier (ex: 14).", parent=self)
            return

        def fv(var):
            s = var.get().strip()
            return float(s) if s else None
        def iv(var):
            s = var.get().strip()
            return int(s) if s else None

        add_s = self.addition_var.get().strip()
        addition = float(add_s) if add_s else None

        conn = get_connection()
        try:
            params = (av_od, av_og, t_od, t_og,
                      fv(self.od_vars["sphere_od"]),   fv(self.od_vars["cylindre_od"]),
                      iv(self.od_vars["axe_od"]),
                      fv(self.og_vars["sphere_og"]),   fv(self.og_vars["cylindre_og"]),
                      iv(self.og_vars["axe_og"]),
                      addition, obs, cid)
            if self.analyse:
                conn.execute("""
                    UPDATE analyses SET av_od=?,av_og=?,tension_od=?,tension_og=?,
                    sphere_od=?,cylindre_od=?,axe_od=?,sphere_og=?,cylindre_og=?,axe_og=?,
                    addition=?,observation=?,idcons=? WHERE idanal=?
                """, params + (self.analyse["idanal"],))
            else:
                conn.execute("""
                    INSERT INTO analyses (av_od,av_og,tension_od,tension_og,
                    sphere_od,cylindre_od,axe_od,sphere_og,cylindre_og,axe_og,
                    addition,observation,idcons) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, params)
            conn.commit()
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex), parent=self)
            return
        finally:
            conn.close()
        self.callback()
        self.destroy()
        messagebox.showinfo("Succès", "Analyse enregistrée avec succès.")
