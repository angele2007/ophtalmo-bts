"""Module Rendez-vous — formulaire corrigé + boutons statut + impression."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from utils.database import get_connection
from utils.styles import *

STATUTS = ("Planifié","Confirmé","Annulé","Honoré")

STATUT_STYLE = {
    "Planifié": ("#E6F1FB", "#B5D4F4", "#0C447C"),
    "Confirmé": ("#EAF3DE", "#B5DCA0", "#2A5C0E"),
    "Annulé":   ("#FCEBEB", "#F4B8B8", "#7A1A1A"),
    "Honoré":   ("#E1F5EE", "#A8DFC9", "#0F5A3A"),
}


class RendezVousPage:
    def __init__(self, parent, medecin):
        self.parent  = parent
        self.medecin = medecin
        self._build()
        self._load()

    # ── Toolbar ────────────────────────────────────────────────────
    def _build(self):
        toolbar = tk.Frame(self.parent, bg=BG_CARD, pady=10, padx=16,
                           highlightthickness=1, highlightbackground=BORDER)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="➕  Nouveau RDV", font=FONT_NORMAL,
                  bg=PRIMARY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, activebackground=PRIMARY_DARK,
                  command=self._new_rdv).pack(side="left")

        tk.Frame(toolbar, bg=BORDER, width=1).pack(side="left", fill="y", padx=12, pady=2)

        self.btn_edit   = self._abtn(toolbar, "✏  Modifier",  "#E6F1FB", PRIMARY,      self._edit_rdv)
        self.btn_conf   = self._abtn(toolbar, "✅ Confirmer",  "#EAF3DE", "#2A5C0E",    lambda: self._set_status("Confirmé"))
        self.btn_honore = self._abtn(toolbar, "🏁 Honoré",     "#E1F5EE", "#0F5A3A",    lambda: self._set_status("Honoré"))
        self.btn_annul  = self._abtn(toolbar, "❌ Annuler",    DANGER_LIGHT, DANGER,     lambda: self._set_status("Annulé"))
        self.btn_del    = self._abtn(toolbar, "🗑 Supprimer",  DANGER_LIGHT, DANGER,     self._delete_rdv)
        self.action_btns = [self.btn_edit, self.btn_conf, self.btn_honore, self.btn_annul, self.btn_del]

        # Filtre date (droite)
        tk.Button(toolbar, text="Tout afficher", font=FONT_SMALL, bg=BG_CARD, relief="flat",
                  fg=TEXT_MUTED, cursor="hand2",
                  command=lambda: [self.filter_var.set(""), self._load()]).pack(side="right", padx=4)
        tk.Button(toolbar, text="🔍", font=FONT_NORMAL, bg=BG_CARD, relief="flat",
                  cursor="hand2", command=self._load).pack(side="right", padx=(0,4))
        self.filter_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(toolbar, textvariable=self.filter_var, font=FONT_NORMAL, width=12,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER).pack(side="right", ipady=5)
        tk.Label(toolbar, text="📅 Date :", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(side="right", padx=(0,4))

        # ── Style Treeview ─────────────────────────────────────────
        style = ttk.Style()
        style.configure("RDV.Treeview", rowheight=34, font=FONT_NORMAL,
                        background="#F0F7FF", fieldbackground="#F0F7FF",
                        foreground=TEXT_MAIN, borderwidth=0)
        style.configure("RDV.Treeview.Heading", background=PRIMARY, foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat", padding=6)
        style.map("RDV.Treeview",
                  background=[("selected","#B0D4F1")],
                  foreground=[("selected", PRIMARY_DARK)])

        # ── Tableau ────────────────────────────────────────────────
        table_f = tk.Frame(self.parent, bg=PRIMARY, padx=1, pady=1)
        table_f.pack(fill="both", expand=True, padx=16, pady=(8,0))

        cols = ("ID","Date & Heure","Patient","Motif","Statut")
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings",
                                 style="RDV.Treeview", selectmode="browse")
        for col, w in zip(cols, [55, 160, 200, 280, 110]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w", minwidth=w)

        for st, (row_bg, _, _) in STATUT_STYLE.items():
            self.tree.tag_configure(st, background=row_bg)

        sb_y = ttk.Scrollbar(table_f, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda e: self._edit_rdv())

        ctx = tk.Menu(self.parent, tearoff=0)
        ctx.add_command(label="✏  Modifier",         command=self._edit_rdv)
        ctx.add_separator()
        ctx.add_command(label="✅  Marquer Confirmé", command=lambda: self._set_status("Confirmé"))
        ctx.add_command(label="🏁  Marquer Honoré",   command=lambda: self._set_status("Honoré"))
        ctx.add_command(label="❌  Marquer Annulé",   command=lambda: self._set_status("Annulé"))
        ctx.add_command(label="📋  Marquer Planifié", command=lambda: self._set_status("Planifié"))
        ctx.add_separator()
        ctx.add_command(label="🗑  Supprimer",        command=self._delete_rdv)
        self.tree.bind("<Button-3>", lambda e: (
            self.tree.selection_set(self.tree.identify_row(e.y)),
            ctx.post(e.x_root, e.y_root)))

        # ── Barre de statut ────────────────────────────────────────
        sb2 = tk.Frame(self.parent, bg=BG_CARD,
                       highlightthickness=1, highlightbackground=BORDER)
        sb2.pack(fill="x", padx=16, pady=(0,10))
        self.info_lbl = tk.Label(sb2, text="", font=FONT_SMALL, bg=BG_CARD,
                                  fg=TEXT_MUTED, padx=12, pady=6)
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
            self.sel_lbl.config(text=f"  {v[2]}  —  {v[1]}  —  {v[4]}")
            for btn in self.action_btns:
                btn.config(state="normal")
        else:
            self.sel_lbl.config(text="")
            for btn in self.action_btns:
                btn.config(state="disabled")

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        filt = self.filter_var.get().strip()
        conn = get_connection()
        if filt:
            rows = conn.execute("""
                SELECT r.idrdv, r.date_rdv, p.nompat||' '||p.prenompat, r.motif, r.statut
                FROM rendezvous r JOIN patients p ON p.idpat=r.idpat
                WHERE r.id_medecin=? AND r.date_rdv LIKE ?
                ORDER BY r.date_rdv
            """, (self.medecin["id_medecin"], filt+"%")).fetchall()
        else:
            rows = conn.execute("""
                SELECT r.idrdv, r.date_rdv, p.nompat||' '||p.prenompat, r.motif, r.statut
                FROM rendezvous r JOIN patients p ON p.idpat=r.idpat
                WHERE r.id_medecin=?
                ORDER BY r.date_rdv DESC
            """, (self.medecin["id_medecin"],)).fetchall()
        conn.close()
        counts = {s: 0 for s in STATUTS}
        for r in rows:
            st = r[4]
            counts[st] = counts.get(st, 0) + 1
            self.tree.insert("", "end", iid=str(r[0]), tags=(st,),
                             values=(r[0], r[1], r[2], (r[3] or "—")[:50], st))
        n = len(rows)
        summary = "  ".join(f"{s}: {counts[s]}" for s in STATUTS if counts[s] > 0)
        self.info_lbl.config(text=f"  {n} rendez-vous   [{summary}]")
        for btn in self.action_btns:
            btn.config(state="disabled")
        self.sel_lbl.config(text="")

    def _get_sel_id(self):
        sel = self.tree.selection()
        return int(self.tree.item(sel[0])["values"][0]) if sel else None

    def _set_status(self, status):
        rid = self._get_sel_id()
        if not rid: return
        conn = get_connection()
        conn.execute("UPDATE rendezvous SET statut=? WHERE idrdv=?", (status, rid))
        conn.commit(); conn.close(); self._load()

    def _new_rdv(self):
        RdvForm(self.parent, self.medecin, None, self._load)

    def _edit_rdv(self):
        rid = self._get_sel_id()
        if rid:
            conn = get_connection()
            r = dict(conn.execute("SELECT * FROM rendezvous WHERE idrdv=?", (rid,)).fetchone())
            conn.close()
            RdvForm(self.parent, self.medecin, r, self._load)

    def _delete_rdv(self):
        rid = self._get_sel_id()
        if not rid: return
        vals = self.tree.item(str(rid))["values"]
        if messagebox.askyesno("Supprimer", f"Supprimer le RDV de {vals[2]} ({vals[1]}) ?", icon="warning"):
            conn = get_connection()
            conn.execute("DELETE FROM rendezvous WHERE idrdv=?", (rid,))
            conn.commit(); conn.close(); self._load()


# ══════════════════════════════════════════════════════════════════
#  Formulaire RDV  (corrigé : plus de collision de variable 'w')
# ══════════════════════════════════════════════════════════════════
class RdvForm(tk.Toplevel):
    def __init__(self, parent, medecin, rdv, callback):
        super().__init__(parent)
        self.medecin  = medecin
        self.rdv      = rdv
        self.callback = callback
        self.title("Nouveau RDV" if not rdv else "Modifier RDV")
        self.resizable(False, False)
        WIN_W, WIN_H = 500, 460
        self.geometry(f"{WIN_W}x{WIN_H}+"
                      f"{(self.winfo_screenwidth()-WIN_W)//2}+"
                      f"{(self.winfo_screenheight()-WIN_H)//2}")
        self.configure(bg=BG)
        self.grab_set()
        self._build()

    def _build(self):
        r       = self.rdv or {}
        is_edit = bool(self.rdv)

        # En-tête coloré
        hdr_color = ACCENT if is_edit else PRIMARY
        hdr = tk.Frame(self, bg=hdr_color, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="✏  Modifier le rendez-vous" if is_edit else "➕  Nouveau Rendez-vous",
                 font=("Segoe UI", 13, "bold"), bg=hdr_color, fg="white").pack(anchor="w")
        if is_edit:
            tk.Label(hdr, text=f"ID #{r.get('idrdv','')}  —  {r.get('date_rdv','')}",
                     font=FONT_SMALL, bg=hdr_color, fg="white").pack(anchor="w")

        # Corps du formulaire
        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        # ── Ligne helper ──────────────────────────────────────────
        def lbl(text, row_num):
            tk.Label(body, text=text, font=FONT_LABEL, bg=BG, fg=TEXT_MUTED,
                     anchor="w").grid(row=row_num, column=0, sticky="w", pady=7)

        def entry(var, row_num):
            ent = tk.Entry(body, textvariable=var, font=FONT_NORMAL, relief="flat",
                           highlightthickness=1, highlightbackground=BORDER)
            ent.grid(row=row_num, column=1, sticky="ew", padx=(12,0), pady=7, ipady=8)
            return ent

        # ── Date & heure ──────────────────────────────────────────
        lbl("Date & heure *", 0)
        tk.Label(body, text="(YYYY-MM-DD HH:MM)", font=("Segoe UI",8),
                 bg=BG, fg=TEXT_LIGHT).grid(row=0, column=0, sticky="sw", padx=(0,4))
        dt_val = r.get("date_rdv", datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.dt_var = tk.StringVar(value=dt_val)
        entry(self.dt_var, 0)

        # ── Patient ───────────────────────────────────────────────
        lbl("Patient *", 1)
        conn = get_connection()
        pats = conn.execute(
            "SELECT idpat, nompat||' '||prenompat AS name FROM patients ORDER BY nompat"
        ).fetchall()
        conn.close()
        self.pat_map = {p["name"]: p["idpat"] for p in pats}

        self.pat_var = tk.StringVar()
        if r.get("idpat"):
            conn2 = get_connection()
            rp = conn2.execute(
                "SELECT nompat||' '||prenompat AS name FROM patients WHERE idpat=?",
                (r["idpat"],)
            ).fetchone()
            conn2.close()
            if rp:
                self.pat_var.set(rp["name"])

        pat_cb = ttk.Combobox(body, textvariable=self.pat_var,
                              values=list(self.pat_map.keys()),
                              font=FONT_NORMAL, state="normal")
        pat_cb.grid(row=1, column=1, sticky="ew", padx=(12,0), pady=7, ipady=6)

        # ── Motif ─────────────────────────────────────────────────
        lbl("Motif", 2)
        self.motif_var = tk.StringVar(value=r.get("motif", "") or "")
        entry(self.motif_var, 2)

        # ── Statut (boutons radio colorés) ────────────────────────
        lbl("Statut", 3)
        self.statut_var = tk.StringVar(value=r.get("statut", "Planifié"))
        sf = tk.Frame(body, bg=BG)
        sf.grid(row=3, column=1, sticky="w", padx=(12,0), pady=7)
        for st, (rbg, _, rfg) in STATUT_STYLE.items():
            tk.Radiobutton(
                sf, text=st, variable=self.statut_var, value=st,
                font=FONT_SMALL, bg=BG, fg=rfg,
                selectcolor=rbg, activebackground=BG
            ).pack(side="left", padx=(0,10))

        # ── Boutons bas de page ────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_CARD, padx=20, pady=12,
                           highlightthickness=1, highlightbackground=BORDER)
        btn_bar.pack(fill="x", side="bottom")

        tk.Button(btn_bar, text="✖  Annuler", font=FONT_NORMAL,
                  bg=BG_CARD, relief="flat",
                  highlightthickness=1, highlightbackground=BORDER,
                  padx=14, pady=6, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=6)

        save_label = "💾  Enregistrer les modifications" if is_edit else "💾  Créer le rendez-vous"
        tk.Button(btn_bar, text=save_label, font=FONT_NORMAL,
                  bg=ACCENT if is_edit else PRIMARY, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  activebackground=PRIMARY_DARK,
                  command=self._save).pack(side="right", padx=6)

    def _save(self):
        dt  = self.dt_var.get().strip()
        pat = self.pat_var.get().strip()
        if not dt or not pat:
            messagebox.showerror("Erreur", "Date & heure et patient sont obligatoires.", parent=self)
            return
        pid = self.pat_map.get(pat)
        if not pid:
            messagebox.showerror("Erreur", "Patient introuvable dans la liste.", parent=self)
            return
        conn = get_connection()
        try:
            if self.rdv:
                conn.execute("""
                    UPDATE rendezvous SET date_rdv=?,idpat=?,statut=?,motif=? WHERE idrdv=?
                """, (dt, pid, self.statut_var.get(), self.motif_var.get() or None,
                      self.rdv["idrdv"]))
            else:
                conn.execute("""
                    INSERT INTO rendezvous (date_rdv,idpat,id_medecin,statut,motif)
                    VALUES (?,?,?,?,?)
                """, (dt, pid, self.medecin["id_medecin"],
                      self.statut_var.get(), self.motif_var.get() or None))
            conn.commit()
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex), parent=self)
            return
        finally:
            conn.close()
        self.callback()
        self.destroy()
