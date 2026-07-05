# OphtalmoPro — Application de gestion de cabinet ophtalmologique
**Projet BTS Informatique**

## Technologies utilisées
- Python 3.8+
- Tkinter (interface graphique, inclus dans Python)
- SQLite 3 (base de données locale, inclus dans Python)

## Structure du projet
```
ophtalmo/
├── main.py                  ← Point d'entrée
├── ophtalmo.db              ← Base de données (créée au 1er lancement)
├── utils/
│   ├── database.py          ← Connexion SQLite + initialisation
│   └── styles.py            ← Constantes visuelles (couleurs, polices)
└── modules/
    ├── login.py             ← Fenêtre de connexion
    ├── main_window.py       ← Fenêtre principale + sidebar
    ├── dashboard.py         ← Tableau de bord
    ├── patients.py          ← Gestion des patients
    ├── rendezvous.py        ← Gestion des rendez-vous
    ├── consultations.py     ← Gestion des consultations
    ├── analyses.py          ← Analyses ophtalmologiques
    ├── ordonnances.py       ← Ordonnances + aperçu
    └── parametres.py        ← Profil médecin + statistiques
```

## Installation et lancement

### Prérequis
Python 3.8 ou supérieur doit être installé.
Aucune bibliothèque externe requise (tout est inclus dans Python).

### Lancement
```bash
cd ophtalmo
python main.py
```

### Identifiants par défaut
| Champ           | Valeur          |
|-----------------|-----------------|
| Identifiant     | `edemo`         |
| Mot de passe    | `1234`          |
| Médecin         | Dr. Edem Ayiya  |

## Fonctionnalités

### 🏠 Tableau de bord
- Statistiques en temps réel (patients, consultations, RDV)
- Rendez-vous du jour avec statuts colorés
- Accès rapides vers tous les modules

### 👥 Patients
- Liste avec recherche en temps réel
- Ajout / Modification / Suppression
- Informations complètes (état civil, coordonnées)

### 📅 Rendez-vous
- Planification avec date, heure, motif
- Gestion des statuts : Planifié / Confirmé / Honoré / Annulé
- Filtre par date

### 🩺 Consultations
- Création liée à un patient
- Types : Standard, Urgence, Contrôle, Post-opératoire, Première visite
- Suivi des statuts : En cours / Terminée / Annulée
- Accès direct aux analyses et ordonnances associées

### 🔬 Analyses ophtalmologiques
- Acuité visuelle OD / OG
- Tension oculaire OD / OG
- Réfraction : sphère, cylindre, axe
- Addition (presbytie)
- Zone d'observations

### 💊 Ordonnances
- Prescription de médicaments
- Instructions de posologie
- **Aperçu imprimable** avec en-tête du cabinet
- Sauvegarde en fichier .txt

### ⚙ Paramètres
- Modification du profil médecin
- Changement de mot de passe sécurisé
- Statistiques globales du cabinet
- Informations sur l'application

## Sécurité
- Mots de passe hashés en SHA-256
- Authentification obligatoire au démarrage
- Contraintes d'intégrité référentielle (clés étrangères SQLite)

## Base de données
La base SQLite (`ophtalmo.db`) est créée automatiquement au premier lancement
dans le dossier du projet. Elle reproduit fidèlement le schéma MySQL fourni
(tables : `medecins`, `patients`, `consultations`, `analyses`, `ordonnances`, `rendezvous`).
