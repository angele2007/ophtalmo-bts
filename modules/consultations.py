"""Module Consultations — avec prix, reçu PDF, boutons d'action."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from utils.database import get_connection
from utils.styles import *

STATUTS = ("En cours","Terminée","Annulée")
TYPES   = ("Standard","Urgence","Contrôle","Post-opératoire","Première visite")
STATUT_STYLE = {
    "En cours": ("#FFF8E1","#F9A825","#7A5000"),
    "Terminée": ("#E8F5E9","#43A047","#1B5E20"),
    "Annulée":  ("#FFEBEE","#E53935","#7A0000"),
}
ROW_ODD  = "#EAF4FF"
ROW_EVEN = "#D5EAFF"
ROW_SEL  = "#A8D4F5"


class ConsultationsPage:
    def __init__(self, parent, medecin):
        self.parent  = parent
        self.medecin = medecin
        self._build()
        self._load()

    def _build(self):
        toolbar = tk.Frame(self.parent, bg=BG_CARD, pady=10, padx=16,
                           highlightthickness=1, highlightbackground=BORDER)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="➕  Nouvelle consultation", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, activebackground=PRIMARY_DARK,
                  command=self._new_cons).pack(side="left")

        tk.Frame(toolbar, bg=BORDER, width=1).pack(side="left", fill="y", padx=12, pady=2)

        self.btn_edit    = self._abtn(toolbar,"✏  Modifier",     "#E6F1FB",PRIMARY,       self._edit_cons)
        self.btn_termine = self._abtn(toolbar,"✅  Terminer",     "#E8F5E9","#1B5E20",     lambda: self._set_status("Terminée"))
        self.btn_annule  = self._abtn(toolbar,"❌  Annuler",      DANGER_LIGHT,DANGER,     lambda: self._set_status("Annulée"))
        self.btn_recu    = self._abtn(toolbar,"🧾  Reçu",         "#FFF8E1","#E65100",     self._print_recu)
        self.btn_analyse = self._abtn(toolbar,"🔬  Analyse",      "#E3F2FD","#0D47A1",     self._open_analyse)
        self.btn_ord     = self._abtn(toolbar,"💊  Ordonnance",   "#F3E5F5","#4A148C",     self._open_ordonnance)
        self.btn_del     = self._abtn(toolbar,"🗑  Supprimer",    DANGER_LIGHT,DANGER,     self._delete_cons)
        self.action_btns = [self.btn_edit, self.btn_termine, self.btn_annule,
                            self.btn_recu, self.btn_analyse, self.btn_ord, self.btn_del]

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        tk.Entry(toolbar, textvariable=self.search_var, font=FONT_NORMAL, width=24,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER).pack(side="right", ipady=5)
        tk.Label(toolbar, text="🔍", font=FONT_NORMAL, bg=BG_CARD).pack(side="right", padx=(0,4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cons.Treeview", rowheight=34, font=FONT_NORMAL,
                        background=ROW_ODD, fieldbackground=ROW_ODD,
                        foreground=TEXT_MAIN, borderwidth=0)
        style.configure("Cons.Treeview.Heading", background=PRIMARY, foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat", padding=6)
        style.map("Cons.Treeview",
                  background=[("selected",ROW_SEL)], foreground=[("selected",PRIMARY_DARK)])
        style.map("Cons.Treeview.Heading", background=[("active",PRIMARY_DARK)])

        table_f = tk.Frame(self.parent, bg=PRIMARY, padx=1, pady=1)
        table_f.pack(fill="both", expand=True, padx=16, pady=(8,0))

        cols = ("ID","Date","Patient","Motif","Type","Prix (FCFA)","Statut")
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings",
                                 style="Cons.Treeview", selectmode="browse")
        col_cfg = [("ID",50,"center"),("Date",100,"center"),("Patient",180,"w"),
                   ("Motif",230,"w"),("Type",110,"center"),("Prix (FCFA)",100,"center"),
                   ("Statut",100,"center")]
        for col, w, anc in col_cfg:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=w, anchor=anc, minwidth=w, stretch=True)

        for st,(bg_s,_,_) in STATUT_STYLE.items():
            self.tree.tag_configure(st, background=bg_s)

        sb_y = ttk.Scrollbar(table_f, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda e: self._edit_cons())

        ctx = tk.Menu(self.parent, tearoff=0)
        ctx.add_command(label="✏  Modifier",                 command=self._edit_cons)
        ctx.add_separator()
        ctx.add_command(label="✅  Marquer Terminée",         command=lambda: self._set_status("Terminée"))
        ctx.add_command(label="▶  Marquer En cours",         command=lambda: self._set_status("En cours"))
        ctx.add_command(label="❌  Marquer Annulée",          command=lambda: self._set_status("Annulée"))
        ctx.add_separator()
        ctx.add_command(label="🧾  Imprimer le reçu",         command=self._print_recu)
        ctx.add_command(label="🔬  Ouvrir / Créer Analyse",  command=self._open_analyse)
        ctx.add_command(label="💊  Ouvrir / Créer Ordonnance", command=self._open_ordonnance)
        ctx.add_separator()
        ctx.add_command(label="🗑  Supprimer",               command=self._delete_cons)
        self.tree.bind("<Button-3>", lambda e: (
            self.tree.selection_set(self.tree.identify_row(e.y)),
            ctx.post(e.x_root, e.y_root)))

        sb2 = tk.Frame(self.parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER)
        sb2.pack(fill="x", padx=16, pady=(0,10))
        self.info_lbl = tk.Label(sb2, text="", font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED, padx=12, pady=6)
        self.info_lbl.pack(side="left")
        self.total_lbl = tk.Label(sb2, text="", font=("Segoe UI",10,"bold"), bg=BG_CARD, fg=ACCENT)
        self.total_lbl.pack(side="left", padx=20)
        self.sel_lbl = tk.Label(sb2, text="", font=FONT_SMALL, bg=BG_CARD, fg=PRIMARY)
        self.sel_lbl.pack(side="right", padx=12)

    def _abtn(self, parent, text, bg, fg, cmd):
        btn = tk.Button(parent, text=text, font=FONT_NORMAL, bg=bg, fg=fg,
                        relief="flat", cursor="hand2", padx=8, pady=5,
                        activebackground=fg, activeforeground="white",
                        state="disabled", command=cmd)
        btn.pack(side="left", padx=(0,3))
        return btn

    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0])["values"]
            self.sel_lbl.config(text=f"  #{v[0]}  {v[2]}  —  {v[1]}  —  {v[6]}")
            for btn in self.action_btns: btn.config(state="normal")
        else:
            self.sel_lbl.config(text="")
            for btn in self.action_btns: btn.config(state="disabled")

    def _load(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        q = self.search_var.get().strip()
        conn = get_connection()
        if q:
            rows = conn.execute("""
                SELECT c.idcons,c.datecons,p.nompat||' '||p.prenompat,
                       c.motifcons,c.type_cons,c.prix_cons,c.statut
                FROM consultations c JOIN patients p ON p.idpat=c.idpat
                WHERE c.id_medecin=? AND (p.nompat LIKE ? OR c.motifcons LIKE ?)
                ORDER BY c.datecons DESC
            """, (self.medecin["id_medecin"],f"%{q}%",f"%{q}%")).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.idcons,c.datecons,p.nompat||' '||p.prenompat,
                       c.motifcons,c.type_cons,c.prix_cons,c.statut
                FROM consultations c JOIN patients p ON p.idpat=c.idpat
                WHERE c.id_medecin=? ORDER BY c.datecons DESC
            """, (self.medecin["id_medecin"],)).fetchall()
        conn.close()
        counts = {s:0 for s in STATUTS}
        total_prix = 0.0
        for i,r in enumerate(rows):
            st = r[6]; prix = r[5] or 0
            counts[st] = counts.get(st,0)+1
            total_prix += prix
            motif = r[3][:50]+"…" if len(r[3])>50 else r[3]
            prix_str = f"{prix:,.0f}" if prix else "—"
            self.tree.insert("", "end", iid=str(r[0]), tags=(st,),
                             values=(r[0],r[1],r[2],motif,r[4],prix_str,st))
        n = len(rows)
        summary = "  ".join(f"{s}: {counts[s]}" for s in STATUTS if counts[s]>0)
        self.info_lbl.config(text=f"  {n} consultation{'s' if n>1 else ''}   [{summary}]")
        self.total_lbl.config(text=f"  💰 Total : {total_prix:,.0f} FCFA")
        for btn in self.action_btns: btn.config(state="disabled")
        self.sel_lbl.config(text="")

    def _get_sel_id(self):
        sel = self.tree.selection()
        return int(self.tree.item(sel[0])["values"][0]) if sel else None

    def _set_status(self, status):
        cid = self._get_sel_id()
        if not cid: return
        conn = get_connection()
        conn.execute("UPDATE consultations SET statut=? WHERE idcons=?", (status,cid))
        conn.commit(); conn.close(); self._load()

    def _new_cons(self):  ConsultationForm(self.parent, self.medecin, None, self._load)

    def _edit_cons(self):
        cid = self._get_sel_id()
        if cid:
            conn = get_connection()
            c = dict(conn.execute("SELECT * FROM consultations WHERE idcons=?", (cid,)).fetchone())
            conn.close()
            ConsultationForm(self.parent, self.medecin, c, self._load)

    def _delete_cons(self):
        cid = self._get_sel_id()
        if not cid: return
        v = self.tree.item(str(cid))["values"]
        if messagebox.askyesno("Supprimer",
                f"Supprimer la consultation de {v[2]} ({v[1]}) ?\n\n"
                "Les analyses et ordonnances liées seront aussi supprimées.", icon="warning"):
            conn = get_connection()
            conn.execute("DELETE FROM consultations WHERE idcons=?",(cid,))
            conn.commit(); conn.close(); self._load()

    def _open_analyse(self):
        cid = self._get_sel_id()
        if not cid: return
        conn = get_connection()
        a = conn.execute("SELECT * FROM analyses WHERE idcons=?",(cid,)).fetchone()
        conn.close()
        from modules.analyses import AnalyseForm
        AnalyseForm(self.parent, cid, dict(a) if a else None, lambda: None)

    def _open_ordonnance(self):
        cid = self._get_sel_id()
        if not cid: return
        conn = get_connection()
        o = conn.execute("SELECT * FROM ordonnances WHERE idcons=?",(cid,)).fetchone()
        conn.close()
        from modules.ordonnances import OrdonnanceForm
        OrdonnanceForm(self.parent, cid, dict(o) if o else None, lambda: None)

    def _print_recu(self):
        cid = self._get_sel_id()
        if not cid: return
        conn = get_connection()
        data = conn.execute("""
            SELECT c.*,
                   p.nompat,p.prenompat,p.agepat,p.sexe,p.telpat,
                   m.nom AS mnom,m.prenom AS mprenom,m.specialite,m.telephone AS mtel,m.email,
                   o.medicaments,o.posologie
            FROM consultations c
            JOIN patients p ON p.idpat=c.idpat
            JOIN medecins m ON m.id_medecin=c.id_medecin
            LEFT JOIN ordonnances o ON o.idcons=c.idcons
            WHERE c.idcons=?
        """, (cid,)).fetchone()
        conn.close()
        if data: RecuWindow(self.parent, dict(data))


# ══════════════════════════════════════════════════════════════════
#  Formulaire consultation  (avec champ Prix)
# ══════════════════════════════════════════════════════════════════
class ConsultationForm(tk.Toplevel):
    def __init__(self, parent, medecin, cons, callback):
        super().__init__(parent)
        self.medecin=medecin; self.cons=cons; self.callback=callback
        is_edit = bool(cons)
        self.title("Modifier la consultation" if is_edit else "Nouvelle consultation")
        self.resizable(False, False)
        W,H = 540, 560
        self.geometry(f"{W}x{H}+{(self.winfo_screenwidth()-W)//2}+{(self.winfo_screenheight()-H)//2}")
        self.configure(bg=BG); self.grab_set(); self._build()

    def _build(self):
        c=self.cons or {}; is_edit=bool(self.cons); hdr_c=ACCENT if is_edit else PRIMARY

        # ── En-tête ────────────────────────────────────────────────
        hdr=tk.Frame(self,bg=hdr_c,padx=22,pady=14); hdr.pack(fill="x",side="top")
        tk.Label(hdr, text="✏  Modifier" if is_edit else "🩺  Nouvelle Consultation",
                 font=("Segoe UI",13,"bold"),bg=hdr_c,fg="white").pack(anchor="w")
        if is_edit:
            tk.Label(hdr,text=f"Consultation #{c['idcons']}  —  {c['datecons']}",
                     font=FONT_SMALL,bg=hdr_c,fg="white").pack(anchor="w")

        # ── Boutons (packés AVANT le corps) ────────────────────────
        btn_bar=tk.Frame(self,bg=BG_CARD,padx=22,pady=10,
                         highlightthickness=1,highlightbackground=BORDER)
        btn_bar.pack(fill="x",side="bottom")
        tk.Button(btn_bar,text="✖  Annuler",font=FONT_NORMAL,bg="#F5F5F5",fg=TEXT_MAIN,
                  relief="flat",highlightthickness=1,highlightbackground=BORDER,
                  padx=14,pady=7,cursor="hand2",command=self.destroy).pack(side="right",padx=6)
        lbl_save="💾  Enregistrer" if is_edit else "💾  Créer la consultation"
        tk.Button(btn_bar,text=lbl_save,font=("Segoe UI",11,"bold"),
                  bg=ACCENT if is_edit else PRIMARY,fg="white",relief="flat",
                  padx=14,pady=7,cursor="hand2",command=self._save).pack(side="right",padx=6)
        if is_edit:
            tk.Button(btn_bar,text="🧾  Reçu",font=FONT_NORMAL,
                      bg="#FFF8E1",fg="#E65100",relief="flat",padx=12,pady=7,cursor="hand2",
                      command=self._open_recu).pack(side="left",padx=6)
            tk.Button(btn_bar,text="🔬  Analyse",font=FONT_NORMAL,
                      bg="#E3F2FD",fg="#0D47A1",relief="flat",padx=12,pady=7,cursor="hand2",
                      command=self._open_analyse).pack(side="left",padx=6)
            tk.Button(btn_bar,text="💊  Ordonnance",font=FONT_NORMAL,
                      bg="#F3E5F5",fg="#4A148C",relief="flat",padx=12,pady=7,cursor="hand2",
                      command=self._open_ord).pack(side="left",padx=6)

        # ── Corps ──────────────────────────────────────────────────
        body=tk.Frame(self,bg=BG,padx=24,pady=14); body.pack(fill="both",expand=True,side="top")
        body.columnconfigure(1,weight=1)

        def lbl(text,row_num):
            tk.Label(body,text=text,font=FONT_LABEL,bg=BG,fg=TEXT_MUTED,anchor="w").grid(
                row=row_num,column=0,sticky="w",pady=6)

        def ent(var,row_num,**kw):
            e=tk.Entry(body,textvariable=var,font=FONT_NORMAL,relief="flat",
                       highlightthickness=1,highlightbackground=BORDER,**kw)
            e.grid(row=row_num,column=1,sticky="ew",padx=(12,0),pady=6,ipady=8); return e

        # Date
        lbl("Date *",0)
        self.date_var=tk.StringVar(value=c.get("datecons",date.today().isoformat()))
        ent(self.date_var,0)

        # Patient
        lbl("Patient *",1)
        conn=get_connection()
        pats=conn.execute("SELECT idpat,nompat||' '||prenompat AS name FROM patients ORDER BY nompat").fetchall()
        conn.close()
        self.pat_map={p["name"]:p["idpat"] for p in pats}
        self.pat_var=tk.StringVar()
        if c.get("idpat"):
            conn2=get_connection()
            rp=conn2.execute("SELECT nompat||' '||prenompat AS name FROM patients WHERE idpat=?",(c["idpat"],)).fetchone()
            conn2.close()
            if rp: self.pat_var.set(rp["name"])
        ttk.Combobox(body,textvariable=self.pat_var,values=list(self.pat_map.keys()),
                     font=FONT_NORMAL,state="readonly").grid(
            row=1,column=1,sticky="ew",padx=(12,0),pady=6,ipady=6)

        # Motif
        lbl("Motif *",2)
        self.motif_text=tk.Text(body,font=FONT_NORMAL,relief="flat",
                                highlightthickness=1,highlightbackground=BORDER,
                                height=3,padx=8,pady=6)
        self.motif_text.grid(row=2,column=1,sticky="ew",padx=(12,0),pady=6)
        if c.get("motifcons"): self.motif_text.insert("1.0",c["motifcons"])

        # Type
        lbl("Type",3)
        self.type_var=tk.StringVar(value=c.get("type_cons","Standard"))
        ttk.Combobox(body,textvariable=self.type_var,values=list(TYPES),
                     state="readonly",font=FONT_NORMAL).grid(row=3,column=1,sticky="w",padx=(12,0),pady=6)

        # Prix
        lbl("Prix (FCFA)",4)
        prix_frame=tk.Frame(body,bg=BG); prix_frame.grid(row=4,column=1,sticky="w",padx=(12,0),pady=6)
        self.prix_var=tk.StringVar(value=str(int(c.get("prix_cons",0) or 0)))
        prix_ent=tk.Entry(prix_frame,textvariable=self.prix_var,font=("Segoe UI",12,"bold"),
                          relief="flat",highlightthickness=1,highlightbackground=BORDER,
                          width=14,fg=ACCENT)
        prix_ent.pack(side="left",ipady=8)
        tk.Label(prix_frame,text="FCFA",font=FONT_NORMAL,bg=BG,fg=TEXT_MUTED).pack(side="left",padx=8)
        # Boutons montants rapides
        for montant in [5000,10000,15000,20000]:
            tk.Button(prix_frame,text=f"+{montant//1000}k",font=("Segoe UI",9),
                      bg=PRIMARY_LIGHT,fg=PRIMARY,relief="flat",cursor="hand2",
                      padx=6,pady=4,
                      command=lambda m=montant: self.prix_var.set(
                          str(int(self.prix_var.get() or 0)+m)
                      )).pack(side="left",padx=2)

        # Statut
        lbl("Statut",5)
        self.statut_var=tk.StringVar(value=c.get("statut","En cours"))
        sf=tk.Frame(body,bg=BG); sf.grid(row=5,column=1,sticky="w",padx=(12,0))
        for st,(_,_,rfg) in STATUT_STYLE.items():
            tk.Radiobutton(sf,text=st,variable=self.statut_var,value=st,
                           font=FONT_SMALL,bg=BG,fg=rfg,
                           selectcolor=BG,activebackground=BG).pack(side="left",padx=(0,12))

    def _save(self):
        d=self.date_var.get().strip(); pat=self.pat_var.get().strip()
        motif=self.motif_text.get("1.0","end").strip()
        if not d or not pat or not motif:
            messagebox.showerror("Erreur","Date, patient et motif obligatoires.",parent=self); return
        pid=self.pat_map.get(pat)
        if not pid:
            messagebox.showerror("Erreur","Patient introuvable.",parent=self); return
        try: prix=float(self.prix_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur","Le prix doit être un nombre.",parent=self); return
        conn=get_connection()
        try:
            if self.cons:
                conn.execute("""UPDATE consultations
                    SET datecons=?,motifcons=?,type_cons=?,statut=?,prix_cons=?,idpat=?
                    WHERE idcons=?""",
                    (d,motif,self.type_var.get(),self.statut_var.get(),prix,pid,self.cons["idcons"]))
            else:
                conn.execute("""INSERT INTO consultations
                    (datecons,motifcons,type_cons,statut,prix_cons,idpat,id_medecin)
                    VALUES (?,?,?,?,?,?,?)""",
                    (d,motif,self.type_var.get(),self.statut_var.get(),prix,pid,self.medecin["id_medecin"]))
            conn.commit()
        except Exception as ex:
            messagebox.showerror("Erreur",str(ex),parent=self); return
        finally: conn.close()
        self.callback(); self.destroy()

    def _open_recu(self):
        if not self.cons: return
        conn=get_connection()
        data=conn.execute("""
            SELECT c.*,p.nompat,p.prenompat,p.agepat,p.sexe,p.telpat,
                   m.nom AS mnom,m.prenom AS mprenom,m.specialite,m.telephone AS mtel,m.email,
                   o.medicaments,o.posologie
            FROM consultations c
            JOIN patients p ON p.idpat=c.idpat
            JOIN medecins m ON m.id_medecin=c.id_medecin
            LEFT JOIN ordonnances o ON o.idcons=c.idcons
            WHERE c.idcons=?""",(self.cons["idcons"],)).fetchone()
        conn.close()
        if data: RecuWindow(self.master,dict(data))

    def _open_analyse(self):
        if not self.cons: return
        conn=get_connection()
        a=conn.execute("SELECT * FROM analyses WHERE idcons=?",(self.cons["idcons"],)).fetchone()
        conn.close()
        from modules.analyses import AnalyseForm
        AnalyseForm(self.master,self.cons["idcons"],dict(a) if a else None,lambda: None)

    def _open_ord(self):
        if not self.cons: return
        conn=get_connection()
        o=conn.execute("SELECT * FROM ordonnances WHERE idcons=?",(self.cons["idcons"],)).fetchone()
        conn.close()
        from modules.ordonnances import OrdonnanceForm
        OrdonnanceForm(self.master,self.cons["idcons"],dict(o) if o else None,lambda: None)


# ══════════════════════════════════════════════════════════════════
#  Reçu — Consultation + Ordonnance
# ══════════════════════════════════════════════════════════════════
class RecuWindow(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data=data
        self.title(f"Reçu — {data['prenompat']} {data['nompat']} — {data['datecons']}")
        W,H=680,800
        self.geometry(f"{W}x{H}+{(self.winfo_screenwidth()-W)//2}+{(self.winfo_screenheight()-H)//2}")
        self.configure(bg="#E0E0E0"); self.grab_set()
        self._build()

    def _build(self):
        d=self.data
        # Barre d'outils
        bar=tk.Frame(self,bg="#333",pady=8); bar.pack(fill="x",side="top")
        tk.Button(bar,text="📄  Exporter PDF",font=FONT_NORMAL,bg="#E65100",fg="white",
                  relief="flat",padx=14,pady=5,cursor="hand2",
                  command=self._export_pdf).pack(side="left",padx=10)
        tk.Button(bar,text="💾  Sauvegarder .txt",font=FONT_NORMAL,bg="#37474F",fg="white",
                  relief="flat",padx=14,pady=5,cursor="hand2",
                  command=self._save_txt).pack(side="left",padx=4)
        tk.Button(bar,text="✖  Fermer",font=FONT_NORMAL,bg="#555",fg="white",
                  relief="flat",padx=14,pady=5,cursor="hand2",
                  command=self.destroy).pack(side="right",padx=10)

        canvas=tk.Canvas(self,bg="#D0D0D0",highlightthickness=0)
        vsb=ttk.Scrollbar(self,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y")
        canvas.pack(fill="both",expand=True,padx=16,pady=12)
        canvas.bind_all("<MouseWheel>",lambda e: canvas.yview_scroll(-1*(e.delta//120),"units"))

        paper=tk.Frame(canvas,bg="white",highlightthickness=1,highlightbackground="#AAAAAA")
        win=canvas.create_window((0,0),window=paper,anchor="nw")
        paper.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e: canvas.itemconfig(win,width=e.width-4))

        doc=tk.Frame(paper,bg="white",padx=40,pady=30); doc.pack(fill="both",expand=True)

        # ── En-tête cabinet ────────────────────────────────────────
        hdr=tk.Frame(doc,bg=PRIMARY,padx=18,pady=14); hdr.pack(fill="x")
        tk.Label(hdr,text=f"Dr. {d['mprenom']} {d['mnom']}",
                 font=("Segoe UI",14,"bold"),bg=PRIMARY,fg="white").pack(anchor="w")
        tk.Label(hdr,text=d["specialite"],font=FONT_NORMAL,bg=PRIMARY,fg="#85B7EB").pack(anchor="w")
        tk.Label(hdr,text=f"📞 {d['mtel']}   ✉ {d.get('email','')}",
                 font=FONT_SMALL,bg=PRIMARY,fg="#B5D4F4").pack(anchor="w")

        self._sep(doc)

        # Titre reçu
        tk.Label(doc,text="REÇU DE CONSULTATION",font=("Segoe UI",15,"bold"),
                 bg="white",fg=PRIMARY).pack(pady=(8,2))
        tk.Label(doc,text=f"N° {d['idcons']}  —  Date : {d['datecons']}",
                 font=FONT_NORMAL,bg="white",fg=TEXT_MUTED).pack(pady=(0,10))
        self._sep(doc)

        # ── Bloc patient ───────────────────────────────────────────
        pf=tk.Frame(doc,bg=PRIMARY_LIGHT,padx=16,pady=10,
                    highlightthickness=1,highlightbackground="#B5D4F4")
        pf.pack(fill="x",pady=(8,6))
        sexe_lbl="M." if d["sexe"]=="M" else "Mme"
        tk.Label(pf,text="PATIENT",font=("Segoe UI",8,"bold"),bg=PRIMARY_LIGHT,fg=PRIMARY).pack(anchor="w")
        tk.Label(pf,text=f"{sexe_lbl} {d['prenompat'].capitalize()} {d['nompat'].upper()}",
                 font=("Segoe UI",12,"bold"),bg=PRIMARY_LIGHT,fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(pf,text=f"{d['agepat']} ans   ·   Tél : {d['telpat']}",
                 font=FONT_NORMAL,bg=PRIMARY_LIGHT,fg=TEXT_MUTED).pack(anchor="w")

        # ── Détails consultation ───────────────────────────────────
        cf=tk.LabelFrame(doc,text="  🩺  Détails de la consultation",
                         font=("Segoe UI",10,"bold"),bg="white",fg=PRIMARY,
                         bd=0,highlightthickness=1,highlightbackground=BORDER,
                         padx=14,pady=10)
        cf.pack(fill="x",pady=8)
        rows=[("Type",d.get("type_cons","Standard")),
              ("Statut",d.get("statut","")),
              ("Motif",d.get("motifcons",""))]
        for lbl,val in rows:
            rf=tk.Frame(cf,bg="white"); rf.pack(fill="x",pady=3)
            tk.Label(rf,text=lbl+" :",font=FONT_LABEL,bg="white",fg=TEXT_MUTED,width=10,anchor="w").pack(side="left")
            tk.Label(rf,text=str(val),font=FONT_NORMAL,bg="white",fg=TEXT_MAIN,wraplength=430,justify="left").pack(side="left")

        # ── Ordonnance (si existante) ──────────────────────────────
        if d.get("medicaments"):
            of=tk.LabelFrame(doc,text="  💊  Ordonnance prescrite",
                             font=("Segoe UI",10,"bold"),bg="white",fg="#4A148C",
                             bd=0,highlightthickness=1,highlightbackground="#CE93D8",
                             padx=14,pady=10)
            of.pack(fill="x",pady=8)
            tk.Label(of,text="Médicaments :",font=("Segoe UI",9,"bold"),bg="white",fg=TEXT_MUTED).pack(anchor="w")
            for i,line in enumerate(d["medicaments"].splitlines()):
                if line.strip():
                    rf=tk.Frame(of,bg="#FAF5FF",padx=8,pady=4,
                                highlightthickness=1,highlightbackground="#EDE7F6")
                    rf.pack(fill="x",pady=1)
                    tk.Label(rf,text=f"{i+1}.",font=("Segoe UI",9,"bold"),bg=rf["bg"],fg="#4A148C",width=3).pack(side="left")
                    tk.Label(rf,text=line.strip(),font=FONT_NORMAL,bg=rf["bg"],fg=TEXT_MAIN).pack(side="left")
            tk.Label(of,text="Posologie :",font=("Segoe UI",9,"bold"),bg="white",fg=TEXT_MUTED).pack(anchor="w",pady=(8,2))
            pf2=tk.Frame(of,bg="#F3E5F5",padx=10,pady=8,
                         highlightthickness=1,highlightbackground="#CE93D8")
            pf2.pack(fill="x")
            tk.Label(pf2,text=d["posologie"],font=FONT_NORMAL,bg="#F3E5F5",
                     fg=TEXT_MAIN,wraplength=480,justify="left").pack(anchor="w")
        else:
            nof=tk.Frame(doc,bg="#F5F5F5",padx=14,pady=8,
                         highlightthickness=1,highlightbackground=BORDER)
            nof.pack(fill="x",pady=8)
            tk.Label(nof,text="💊  Aucune ordonnance liée à cette consultation.",
                     font=FONT_NORMAL,bg="#F5F5F5",fg=TEXT_MUTED).pack()

        self._sep(doc,pady=14)

        # ── Montant ────────────────────────────────────────────────
        prix=d.get("prix_cons",0) or 0
        mf=tk.Frame(doc,bg="#E8F5E9" if prix>0 else "#F5F5F5",padx=16,pady=14,
                    highlightthickness=2,highlightbackground=ACCENT if prix>0 else BORDER)
        mf.pack(fill="x",pady=(0,10))
        mf.columnconfigure(1,weight=1)
        tk.Label(mf,text="💰  MONTANT TOTAL",font=("Segoe UI",11,"bold"),
                 bg=mf["bg"],fg=TEXT_MAIN).grid(row=0,column=0,sticky="w")
        tk.Label(mf,text=f"{prix:,.0f} FCFA",font=("Segoe UI",18,"bold"),
                 bg=mf["bg"],fg=ACCENT if prix>0 else TEXT_MUTED).grid(row=0,column=1,sticky="e")
        tk.Label(mf,text="Consultation ophtalmologique",font=FONT_SMALL,
                 bg=mf["bg"],fg=TEXT_MUTED).grid(row=1,column=0,sticky="w")

        self._sep(doc)

        # Signature
        sf=tk.Frame(doc,bg="white"); sf.pack(fill="x",pady=(10,0))
        tk.Label(sf,text="Cachet et signature :",font=FONT_LABEL,bg="white",fg=TEXT_MUTED).pack(anchor="e")
        tk.Frame(sf,bg=BORDER,height=1).pack(fill="x",pady=(30,4))
        tk.Label(sf,text=f"Dr. {d['mprenom']} {d['mnom']}",
                 font=("Segoe UI",11,"bold"),bg="white",fg=TEXT_MAIN).pack(anchor="e")
        tk.Label(sf,text=d["specialite"],font=FONT_SMALL,bg="white",fg=TEXT_MUTED).pack(anchor="e")
        tk.Label(doc,text=f"Reçu N° {d['idcons']}  —  Émis le {date.today()}",
                 font=("Segoe UI",8),bg="white",fg=TEXT_LIGHT).pack(pady=(20,0))

    def _sep(self,parent,pady=8):
        tk.Frame(parent,bg=BORDER,height=1).pack(fill="x",pady=pady)

    def _save_txt(self):
        from tkinter import filedialog
        d=self.data; prix=d.get("prix_cons",0) or 0
        lines=[
            "="*55,
            f"  REÇU DE CONSULTATION  N° {d['idcons']}",
            "="*55,
            f"Cabinet : Dr. {d['mprenom']} {d['mnom']} — {d['specialite']}",
            f"Tél : {d['mtel']}",
            f"Date : {d['datecons']}",
            "",
            f"Patient : {d['prenompat']} {d['nompat']} — {d['agepat']} ans",
            f"Tél patient : {d['telpat']}",
            "",
            "─"*40,
            "CONSULTATION :",
            "─"*40,
            f"  Type   : {d.get('type_cons','')}",
            f"  Statut : {d.get('statut','')}",
            f"  Motif  : {d.get('motifcons','')}",
        ]
        if d.get("medicaments"):
            lines+=["","─"*40,"ORDONNANCE :","─"*40]
            for i,l in enumerate(d["medicaments"].splitlines()):
                if l.strip(): lines.append(f"  {i+1}. {l}")
            lines+=["","Posologie :",f"  {d['posologie']}"]
        lines+=["","="*55,f"  MONTANT : {prix:,.0f} FCFA","="*55,
                f"Signature : Dr. {d['mprenom']} {d['mnom']}"]
        path=filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Texte","*.txt")],
            initialfile=f"recu_{d['datecons']}_{d['nompat']}.txt",parent=self)
        if path:
            with open(path,"w",encoding="utf-8") as f: f.write("\n".join(lines))
            messagebox.showinfo("Sauvegardé",f"Reçu sauvegardé :\n{path}",parent=self)

    def _export_pdf(self):
        from tkinter import filedialog
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,HRFlowable
        except ImportError:
            messagebox.showerror("Erreur","Installez reportlab : pip install reportlab",parent=self); return

        d=self.data; prix=d.get("prix_cons",0) or 0
        path=filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"recu_{d['datecons']}_{d['nompat']}.pdf",parent=self)
        if not path: return

        doc_pdf=SimpleDocTemplate(path,pagesize=A4,
                                  rightMargin=2*cm,leftMargin=2*cm,
                                  topMargin=1.5*cm,bottomMargin=2*cm)
        pc=colors.HexColor("#0C447C"); ac=colors.HexColor("#1D9E75")
        lb=colors.HexColor("#E6F1FB"); bd=colors.HexColor("#E0DDD5")

        def sty(name,**kw):
            return ParagraphStyle(name,**kw)

        s_white=sty("w",fontName="Helvetica-Bold",fontSize=13,textColor=colors.white)
        s_ws=sty("ws",fontName="Helvetica",fontSize=10,textColor=colors.HexColor("#85B7EB"))
        s_title=sty("t",fontName="Helvetica-Bold",fontSize=15,textColor=pc,alignment=1)
        s_sub=sty("su",fontName="Helvetica",fontSize=10,textColor=colors.HexColor("#6B6A65"),alignment=1)
        s_label=sty("la",fontName="Helvetica-Bold",fontSize=9,textColor=colors.HexColor("#6B6A65"))
        s_val=sty("va",fontName="Helvetica",fontSize=10,textColor=colors.HexColor("#1A1A18"))
        s_bold=sty("bo",fontName="Helvetica-Bold",fontSize=10)
        s_med=sty("me",fontName="Helvetica",fontSize=10)
        s_prix=sty("pr",fontName="Helvetica-Bold",fontSize=18,textColor=ac,alignment=2)
        s_sm=sty("sm",fontName="Helvetica",fontSize=8,textColor=colors.HexColor("#9A9994"))

        story=[]

        # En-tête
        hdr_data=[[Paragraph(f"Dr. {d['mprenom']} {d['mnom']}",s_white),""],
                  [Paragraph(d["specialite"],s_ws),""],
                  [Paragraph(f"Tél : {d['mtel']}   •   {d.get('email','')}",s_ws),""]]
        ht=Table(hdr_data,colWidths=["75%","25%"])
        ht.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),pc),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),16)]))
        story+=[ht,Spacer(1,12),
                Paragraph("REÇU DE CONSULTATION",s_title),
                Paragraph(f"N° {d['idcons']}  —  Date : {d['datecons']}",s_sub),
                HRFlowable(width="100%",thickness=1,color=bd),Spacer(1,8)]

        # Patient
        sexe_lbl="M." if d["sexe"]=="M" else "Mme"
        pat_data=[[Paragraph("PATIENT",sty("pl",fontName="Helvetica-Bold",fontSize=8,textColor=pc))],
                  [Paragraph(f"{sexe_lbl} {d['prenompat']} {d['nompat'].upper()}",
                             sty("pn",fontName="Helvetica-Bold",fontSize=12))],
                  [Paragraph(f"{d['agepat']} ans   •   Tél : {d['telpat']}",s_val)]]
        pt=Table(pat_data,colWidths=["100%"])
        pt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),lb),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),12),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#B5D4F4"))]))
        story+=[pt,Spacer(1,10)]

        # Consultation
        cons_rows=[[Paragraph("Type :",s_label),Paragraph(d.get("type_cons",""),s_val)],
                   [Paragraph("Statut :",s_label),Paragraph(d.get("statut",""),s_val)],
                   [Paragraph("Motif :",s_label),Paragraph(d.get("motifcons",""),s_val)]]
        ct=Table(cons_rows,colWidths=["25%","75%"])
        ct.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#FAFAFA"),colors.white]),
            ("BOX",(0,0),(-1,-1),0.5,bd)]))
        story+=[Paragraph("🩺  Détails consultation",s_bold),Spacer(1,4),ct,Spacer(1,10)]

        # Ordonnance
        if d.get("medicaments"):
            meds=[l.strip() for l in d["medicaments"].splitlines() if l.strip()]
            med_rows=[[Paragraph(f"{i+1}.",sty("mn",fontName="Helvetica-Bold",fontSize=10,textColor=pc)),
                       Paragraph(line,s_med)] for i,line in enumerate(meds)]
            mt=Table(med_rows,colWidths=[0.6*cm,"95%"])
            mt.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",(0,0),(-1,-1),6),
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#FAF5FF"),colors.white]),
                ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#CE93D8"))]))
            pos_data=[[Paragraph(d["posologie"],s_val)]]
            pos_t=Table(pos_data,colWidths=["100%"])
            pos_t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F3E5F5")),
                ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
                ("LEFTPADDING",(0,0),(-1,-1),10),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#CE93D8"))]))
            story+=[Paragraph("💊  Ordonnance",s_bold),Spacer(1,4),mt,Spacer(1,6),
                    Paragraph("Posologie :",s_label),Spacer(1,2),pos_t,Spacer(1,10)]

        # Montant
        story.append(HRFlowable(width="100%",thickness=1.5,color=ac))
        prix_data=[[Paragraph("💰  MONTANT TOTAL",sty("ml",fontName="Helvetica-Bold",fontSize=12)),
                    Paragraph(f"{prix:,.0f} FCFA",s_prix)]]
        prit=Table(prix_data,colWidths=["60%","40%"])
        prit.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E8F5E9")),
            ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("BOX",(0,0),(-1,-1),1.5,ac)]))
        story+=[prit,Spacer(1,20),HRFlowable(width="100%",thickness=0.5,color=bd),Spacer(1,6),
                Paragraph(f"Reçu N° {d['idcons']}  —  Émis le {date.today()}",s_sm)]

        try:
            doc_pdf.build(story)
            messagebox.showinfo("PDF créé",f"Reçu exporté :\n{path}",parent=self)
            import os,subprocess,sys
            if sys.platform.startswith("win"): os.startfile(path)
            elif sys.platform=="darwin": subprocess.call(["open",path])
            else: subprocess.call(["xdg-open",path])
        except Exception as ex:
            messagebox.showerror("Erreur PDF",str(ex),parent=self)
