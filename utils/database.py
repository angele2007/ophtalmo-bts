"""Gestion de la base de données SQLite — avec colonne prix_cons."""
import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ophtalmo.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS medecins (
            id_medecin INTEGER PRIMARY KEY AUTOINCREMENT,
            nom        TEXT NOT NULL,
            prenom     TEXT NOT NULL,
            specialite TEXT NOT NULL,
            telephone  TEXT NOT NULL,
            login      TEXT NOT NULL UNIQUE,
            motdepasse TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS patients (
            idpat         INTEGER PRIMARY KEY AUTOINCREMENT,
            nompat        TEXT NOT NULL,
            prenompat     TEXT NOT NULL,
            agepat        INTEGER NOT NULL,
            dateNaissance TEXT,
            sexe          TEXT NOT NULL CHECK(sexe IN ('M','F')),
            adresse       TEXT,
            telpat        TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consultations (
            idcons      INTEGER PRIMARY KEY AUTOINCREMENT,
            datecons    TEXT NOT NULL,
            motifcons   TEXT NOT NULL,
            type_cons   TEXT DEFAULT 'Standard',
            statut      TEXT NOT NULL DEFAULT 'En cours'
                            CHECK(statut IN ('En cours','Terminée','Annulée')),
            prix_cons   REAL DEFAULT 0,
            idpat       INTEGER NOT NULL,
            id_medecin  INTEGER NOT NULL,
            FOREIGN KEY (idpat)      REFERENCES patients(idpat)      ON DELETE RESTRICT,
            FOREIGN KEY (id_medecin) REFERENCES medecins(id_medecin) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS analyses (
            idanal      INTEGER PRIMARY KEY AUTOINCREMENT,
            av_od       TEXT NOT NULL,
            av_og       TEXT NOT NULL,
            tension_od  INTEGER NOT NULL,
            tension_og  INTEGER NOT NULL,
            sphere_od   REAL,
            cylindre_od REAL,
            axe_od      INTEGER,
            sphere_og   REAL,
            cylindre_og REAL,
            axe_og      INTEGER,
            addition    REAL,
            observation TEXT NOT NULL,
            idcons      INTEGER NOT NULL,
            FOREIGN KEY (idcons) REFERENCES consultations(idcons) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ordonnances (
            idord       INTEGER PRIMARY KEY AUTOINCREMENT,
            medicaments TEXT NOT NULL,
            posologie   TEXT NOT NULL,
            idcons      INTEGER NOT NULL,
            FOREIGN KEY (idcons) REFERENCES consultations(idcons) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS rendezvous (
            idrdv       INTEGER PRIMARY KEY AUTOINCREMENT,
            date_rdv    TEXT NOT NULL,
            idpat       INTEGER NOT NULL,
            id_medecin  INTEGER NOT NULL,
            statut      TEXT NOT NULL DEFAULT 'Planifié'
                            CHECK(statut IN ('Planifié','Confirmé','Annulé','Honoré')),
            motif       TEXT,
            FOREIGN KEY (idpat)      REFERENCES patients(idpat)      ON DELETE RESTRICT,
            FOREIGN KEY (id_medecin) REFERENCES medecins(id_medecin) ON DELETE RESTRICT
        );
    """)

    # Migration : ajouter prix_cons si colonne absente (base existante)
    cols = [r[1] for r in c.execute("PRAGMA table_info(consultations)").fetchall()]
    if "prix_cons" not in cols:
        c.execute("ALTER TABLE consultations ADD COLUMN prix_cons REAL DEFAULT 0")

    # Médecin par défaut
    c.execute("SELECT COUNT(*) FROM medecins")
    if c.fetchone()[0] == 0:
        pwd = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"
        c.execute("""
            INSERT INTO medecins (nom,prenom,specialite,telephone,login,motdepasse,email)
            VALUES (?,?,?,?,?,?,?)
        """, ("Ayiya","Edem","Cataracte et Chirurgie","99550066","edemo",pwd,"ayiyaedem@gmail.com"))

    conn.commit()
    conn.close()
