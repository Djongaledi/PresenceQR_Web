import sqlite3
from datetime import date, datetime

def init_db():
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS eleves (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        matricule TEXT UNIQUE,
                        nom TEXT,
                        prenom TEXT,
                        sexe TEXT,
                        classe TEXT,
                        option TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS presences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        matricule TEXT,
                        date TEXT,
                        heure TEXT)''')
    conn.commit()
    conn.close()

def ajouter_eleve(matricule, nom, prenom, sexe, classe, option):
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM eleves WHERE matricule = ?", (matricule.strip(),))
        existe_mat = cursor.fetchone()
        
        cursor.execute("SELECT id FROM eleves WHERE LOWER(nom) = ? AND LOWER(prenom) = ?", (nom.strip().lower(), prenom.strip().lower()))
        existe_nom = cursor.fetchone()
        
        if existe_mat:
            conn.close()
            return False, "❌ Ce matricule est déjà attribué à un autre élève."
        elif existe_nom:
            conn.close()
            return False, "❌ Un élève avec le même nom et prénom existe déjà dans le système."
        else:
            cursor.execute("INSERT INTO eleves (matricule, nom, prenom, sexe, classe, option) VALUES (?, ?, ?, ?, ?, ?)",
                         (matricule.strip(), nom.strip(), prenom.strip(), sexe, classe, option))
            conn.commit()
            conn.close()
            return True, f"✅ Élève {prenom} {nom} enregistré avec succès !"
    except Exception as e:
        conn.close()
        return False, f"❌ Erreur : {str(e)}"

def recuperer_eleve(matricule):
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom, prenom, classe, option FROM eleves WHERE matricule = ?", (matricule.strip(),))
    eleve = cursor.fetchone()
    conn.close()
    return eleve

def enregistrer_presence(scanned_code):
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom, prenom, classe FROM eleves WHERE matricule = ?", (scanned_code.strip(),))
    eleve = cursor.fetchone()
    
    if not eleve:
        conn.close()
        return False, f"❌ Matricule inconnu ou non enregistré : {scanned_code.strip()}"
    
    nom, prenom, classe = eleve
    date_actuelle = date.today().strftime("%Y-%m-%d")
    heure_actuelle = datetime.now().strftime("%H:%M:%S")
    
    cursor.execute("SELECT * FROM presences WHERE matricule = ? AND date = ?", (scanned_code.strip(), date_actuelle))
    deja_pointe = cursor.fetchone()
    
    if deja_pointe:
        conn.close()
        return False, f"⚠️ {prenom} {nom} a déjà pointé aujourd'hui à {deja_pointe[3]}."
    
    cursor.execute("INSERT INTO presences (matricule, date, heure) VALUES (?, ?, ?)",
                   (scanned_code.strip(), date_actuelle, heure_actuelle))
    conn.commit()
    conn.close()
    return True, f"✅ Présence validée pour **{prenom} {nom}** ({classe}) à {heure_actuelle}"

def supprimer_eleve(mat_supp):
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presences WHERE matricule = ?", (mat_supp,))
    cursor.execute("DELETE FROM eleves WHERE matricule = ?", (mat_supp,))
    conn.commit()
    conn.close()
