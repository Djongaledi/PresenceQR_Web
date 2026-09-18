import streamlit as st
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import sqlite3

# Importation des fonctions de la base de données
from database import (
    init_db, 
    ajouter_eleve, 
    recuperer_eleve, 
    enregistrer_presence, 
    supprimer_eleve
)

# Initialisation de la base de données
init_db()

# Tentative d'importation sécurisée du scanner
try:
    from streamlit_qrcode_scanner import qrcode_scanner
    HAS_SCANNER = True
except ImportError:
    HAS_SCANNER = False

# Importations pour la génération PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuration de la page Web
st.set_page_config(
    page_title="Gestion Présence QR - École",
    page_icon="🎓",
    layout="wide"
)

# Style CSS personnalisé
st.markdown("""
    <style>
        .main { background-color: #f4f6f9; }
        .stButton>button, div[data-testid="stFormSubmitButton"]>button {
            background-color: #ffc107 !important;
            color: #000000 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            border: none !important;
        }
        .hero-box {
            background: linear-gradient(135deg, #0d6efd 0%, #0099ff 100%);
            padding: 25px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .tip-card {
            background-color: #ffffff;
            padding: 18px;
            border-radius: 10px;
            border-left: 5px solid #0d6efd;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# Gestion de l'état de session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "dernier_matricule" not in st.session_state:
    st.session_state.dernier_matricule = ""

if "admin_pwd_val" not in st.session_state:
    st.session_state.admin_pwd_val = ""

st.sidebar.title("🎓 Navigation École")
st.sidebar.markdown("---")

# Zone de connexion administrateur sécurisée
st.sidebar.subheader("🔒 Espace Administrateur")
admin_pwd = st.sidebar.text_input("Mot de passe admin", type="password", value=st.session_state.admin_pwd_val, key="pwd_admin_input")

if admin_pwd == "DjongaSime2026":
    st.session_state.authenticated = True
elif admin_pwd and admin_pwd != "DjongaSime2026":
    st.sidebar.error("❌ Mot de passe incorrect")

if st.session_state.authenticated:
    st.sidebar.success("🔒 Connecté en tant qu'Admin : **DJONGALEDI MUDIBU SIMEON**")
    if st.sidebar.button("Se déconnecter de l'Admin"):
        st.session_state.authenticated = False
        st.session_state.admin_pwd_val = ""
        st.rerun()

# Menu dynamique selon l'état de connexion
if st.session_state.authenticated:
    choix = st.sidebar.radio("Aller vers :", [
        "1. Inscription & Badges", 
        "2. Scanner de Présence", 
        "3. Espace Élève/Parents", 
        "4. Administration & Global"
    ], key="menu_admin")
else:
    choix = st.sidebar.radio("Aller vers :", [
        "1. Inscription & Badges", 
        "2. Espace Élève/Parents"
    ], key="menu_public")

# Fonction de génération du PDF
def generer_pdf(df, titre_filtre):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#0d6efd"),
        spaceAfter=10
    )
    
    elements.append(Paragraph(f"Rapport de Présence - {titre_filtre}", title_style))
    elements.append(Paragraph(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    if not df.empty:
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0d6efd")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8f9fa")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Aucune donnée disponible pour ce filtre.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MENU 1 : INSCRIPTION & BADGES ---
if choix == "1. Inscription & Badges":
    st.markdown("""
        <div class="hero-box">
            <h2>🎓 Portail d'Inscription & Badges QR</h2>
            <p>Enregistrez les nouveaux élèves de l'établissement et générez instantanément leur badge de pointage unique.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("#### 📝 Formulaire Nouvel Élève")
        matricule_input = st.text_input("Matricule Unique", placeholder="ex: MAT-001")
        nom = st.text_input("Nom de famille")
        prenom = st.text_input("Prénom")
        sexe = st.selectbox("Sexe", ["Homme", "Femme"])
        
        liste_classes = ["7ème", "8ème", "1ère", "2ème", "3ème","4ème"]
        classe = st.selectbox("Niveau / Classe", liste_classes)
        
        option = "Aucune"
        if classe in ["1ère", "2ème", "3ème","4ème"]:
            liste_options = [
                "Littéraire", "Scientifique", "Commerciale et gestion", 
                "Pédagogie", "Coupe couture", "Électricité", "Électronique", "Mécanique"
            ]
            option = st.selectbox("Option / Filière", liste_options)
        else:
            st.info("ℹ️ Les classes de 7ème et 8ème suivent le tronc commun (pas d'option spécifique).")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_enregistrer = st.button("Enregistrer l'élève")
        
        if btn_enregistrer:
            if matricule_input and nom and prenom:
                succes, message = ajouter_eleve(matricule_input, nom, prenom, sexe, classe, option)
                if succes:
                    st.session_state.dernier_matricule = matricule_input.strip()
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("⚠️ Veuillez remplir tous les champs obligatoires.")

    with col2:
        st.markdown("#### 🖨️ Génération de votre Badge QR")
        saisie_matricule = st.text_input("Entrez votre Matricule", value=st.session_state.dernier_matricule, placeholder="ex: MAT-001", key="input_recherche_badge")
        btn_recherche_badge = st.button("🔍 Afficher mon Badge QR")
        
        if btn_recherche_badge or saisie_matricule:
            mat_cherche = saisie_matricule.strip()
            if mat_cherche:
                eleve_trouve = recuperer_eleve(mat_cherche)
                if eleve_trouve:
                    nom_el, prenom_el, classe_el, option_el = eleve_trouve
                    st.success(f"Élève reconnu : **{prenom_el} {nom_el}** ({classe_el} - {option_el})")
                    
                    qr = qrcode.QRCode(version=1, box_size=10, border=2)
                    qr.add_data(mat_cherche)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    buf = BytesIO()
                    img.save(buf)
                    byte_im = buf.getvalue()
                    
                    st.image(byte_im, caption=f"Badge QR - {mat_cherche}", width=200)
                    st.download_button("📥 Télécharger mon Badge QR", data=byte_im, file_name=f"badge_{mat_cherche}.png", mime="image/png")
                else:
                    st.warning(f"🔍 Aucun élève trouvé avec le matricule '{mat_cherche}'.")

# --- MENU 2 : SCANNER DE PRÉSENCE ---
elif choix == "2. Scanner de Présence":
    st.markdown("""
        <div class="hero-box">
            <h2>📷 Caméra de Pointage en Direct</h2>
            <p>Pointez rapidement les présences à l'entrée de l'école en scannant le QR code de la carte d'étudiant.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_sc1, col_sc2 = st.columns([2, 1], gap="large")
    with col_sc1:
        st.write("Orientez la caméra vers le QR code de l'élève pour enregistrer sa présence instantanément.")
        
        scanned_code = None
        if HAS_SCANNER:
            try:
                scanned_code = qrcode_scanner(key="scanner_presence")
            except Exception:
                st.warning("⚠️ La caméra en direct ne peut pas démarrer sur cet appareil. Utilisez le champ de secours ci-dessous.")
        
        if not scanned_code:
            st.markdown("---")
            st.write("*(Option de secours si la caméra ne s'ouvre pas)*")
            scanned_code = st.text_input("Ou tapez/scannez le matricule directement ici :", placeholder="ex: MAT-001", key="secours_scan_input")
        
        if scanned_code:
            succes_p, message_p = enregistrer_presence(scanned_code)
            if succes_p:
                st.success(message_p)
            else:
                st.warning(message_p) if "déjà pointé" in message_p else st.error(message_ p)
            
    with col_sc2:
        st.markdown("""
            <div class="tip-card">
                <strong>💡 Astuce Scanner :</strong><br>
                - Assurez-vous d'avoir un bon éclairage.<br>
                - Maintenez le badge stable à environ 15-20 cm de la caméra.<br>
                - Un seul pointage par jour et par élève.
            </div>
        """, unsafe_allow_html=True)

# --- MENU 3 : ESPACE ÉLÈVE / PARENTS ---
elif choix == "2. Espace Élève/Parents":
    st.markdown("""
        <div class="hero-box">
            <h2>🔍 Espace de Consultation - Élèves & Parents</h2>
            <p>Vérifiez l'historique complet des présences et visualisez votre code QR personnel.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns([1, 1], gap="large")
    with col_p1:
        matricule_recherche = st.text_input("Entrez votre Matricule", placeholder="ex: MAT-001", key="input_espace_parent")
        btn_recherche_parent = st.button("🔍 Rechercher mon dossier")
        
        if btn_recherche_parent or matricule_recherche:
            mat_p = matricule_recherche.strip()
            if mat_p:
                eleve_infos = recuperer_eleve(mat_p)
                if eleve_infos:
                    nom, prenom, classe, option = eleve_infos
                    st.success(f"Élève trouvé : **{prenom} {nom}** - {classe} ({option})")
                    
                    qr = qrcode.QRCode(version=1, box_size=10, border=2)
                    qr.add_data(mat_p)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    buf = BytesIO()
                    img.save(buf)
                    byte_im = buf.getvalue()
                    
                    st.markdown("#### 📱 Votre Code QR Personnel")
                    st.image(byte_im, caption=f"Badge QR - {mat_p}", width=180)
                    st.download_button("📥 Télécharger mon Code QR", data=byte_im, file_name=f"badge_{mat_p}.png", mime="image/png")
                    st.divider()
                    
                    conn = sqlite3.connect("ecole.db")
                    df_pres = pd.read_sql_query("SELECT date, heure FROM presences WHERE matricule = ? ORDER BY date DESC, heure DESC", conn, params=(mat_p,))
                    conn.close()
                    
                    if not df_pres.empty:
                        st.markdown("#### 📅 Historique des pointages")
                        donnees_tableau = [{"Date": h[0], "Heure de Pointage": h[1]} for h in df_pres.values]
                        st.table(donnees_tableau)
                    else:
                        st.info("Aucune donnée de présence enregistrée pour le moment.")
                else:
                    st.error(f"❌ Matricule '{mat_p}' introuvable.")

# --- MENU 4 : ADMINISTRATION & GLOBAL ---
elif choix == "4. Administration & Global":
    st.markdown("""
        <div class="hero-box">
            <h2>⚙️ Tableau de Bord Administratif & Global</h2>
            <p>Gérez le répertoire, filtrez les présences et extrayez vos rapports officiels.</p>
        </div>
    """, unsafe_allow_html=True)
    
    conn = sqlite3.connect("ecole.db")
    tab_repertoire, tab_filtrage = st.tabs(["📁 Répertoire Général des Élèves", "🔍 Filtrage & Historique des Présences"])
    
    with tab_repertoire:
        df_eleves = pd.read_sql_query("SELECT id, matricule AS Matricule, nom AS Nom, prenom AS Prénom, sexe AS Sexe, classe AS Classe, option AS Option FROM eleves", conn)
        aujourdhui = date.today().strftime("%Y-%m-%d")
        df_presences_jour = pd.read_sql_query("SELECT COUNT(DISTINCT matricule) AS total FROM presences WHERE date = ?", conn, params=(aujourdhui,)).iloc[0]['total']
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Élèves Inscrits", len(df_eleves))
        m2.metric("Présents Aujourd'hui", df_presences_jour)
        m3.metric("Date Du Jour", aujourdhui)
        
        st.divider()
        st.markdown("#### 📋 Liste complète des Élèves Inscrits")
        if not df_eleves.empty:
            st.dataframe(df_eleves, use_container_width=True)
            
            st.markdown("#### 🗑️ Zone de Suppression")
            st.warning("⚠️ Attention : La suppression d'un élève effacera également son historique.")
            
            liste_suppression = ["-- Sélectionner un élève à supprimer --"] + (df_eleves['Matricule'] + " - " + df_eleves['Nom'] + " " + df_eleves['Prénom']).tolist()
            eleve_a_supprimer = st.selectbox("Choisir un élève à supprimer", liste_suppression)
            
            if eleve_a_supprimer and eleve_a_supprimer != "-- Sélectionner un élève à supprimer --":
                mat_supp = eleve_a_supprimer.split(" - ")[0]
                if st.button("❌ Supprimer Définitivement Cet Élève"):
                    supprimer_eleve(mat_supp)
                    st.success(f"L'élève {mat_supp} a été supprimé avec succès.")
                    st.rerun()
        else:
            st.info("Aucun élève enregistré pour le moment.")
            
        st.divider()
        if st.button("📥 Télécharger le Rapport Global des Élèves (PDF)"):
            pdf_buffer = generer_pdf(df_eleves, "Liste complète des élèves")
            st.download_button("Cliquer pour enregistrer le PDF", data=pdf_buffer, file_name="rapport_eleves.pdf", mime="application/pdf")

    with tab_filtrage:
        st.markdown("#### 🔍 Filtrer les Présences")
        
        options_filiere = ["Tous"] + pd.read_sql_query("SELECT DISTINCT option FROM eleves", conn)['option'].dropna().tolist()
        niveaux_classe = ["Tous"] + pd.read_sql_query("SELECT DISTINCT classe FROM eleves", conn)['classe'].dropna().tolist()
        liste_sexes = ["Tous", "Homme", "Femme"]
        
        c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
        with c_f1:
            filtre_opt = st.selectbox("Option / Filière", options_filiere)
        with c_f2:
            filtre_cls = st.selectbox("Niveau / Classe", niveaux_classe)
        with c_f3:
            filtre_sexe = st.selectbox("Sexe", liste_sexes)
        with c_f4:
            mois_selection = st.text_input("Par Mois", placeholder="ex: 2026-09")
        with c_f5:
            date_selection = st.text_input("Par Date exacte", placeholder="ex: 2026-09-12")
            
        query = """
            SELECT p.matricule AS Matricule, e.nom AS Nom, e.prenom AS Prénom, e.sexe AS Sexe, e.classe AS Classe, e.option AS Option, p.date AS Date, p.heure AS Heure, 'Present' AS Statut
            FROM presences p
            JOIN eleves e ON p.matricule = e.matricule
            WHERE 1=1
        """
        params = []
        
        if filtre_opt != "Tous":
            query += " AND e.option = ?"
            params.append(filtre_opt)
        if filtre_cls != "Tous":
            query += " AND e.classe = ?"
            params.append(filtre_cls)
        if filtre_sexe != "Tous":
            query += " AND e.sexe = ?"
            params.append(filtre_sexe)
        if mois_selection:
            query += " AND p.date LIKE ?"
            params.append(f"{mois_selection}%")
        if date_selection:
            query += " AND p.date = ?"
            params.append(date_selection)
            
        df_filtre = pd.read_sql_query(query, conn, params=params)
        
        st.markdown(f"**Résultats trouvés : {len(df_filtre)} présence(s)**")
        if not df_filtre.empty:
            st.dataframe(df_filtre, use_container_width=True)
            
            if st.button("📥 EXPORTER LE REGISTRE SÉLECTIONNÉ EN PDF"):
                pdf_buffer_filtre = generer_pdf(df_filtre, "Registre filtré des présences")
                st.download_button("Télécharger le PDF filtré", data=pdf_buffer_filtre, file_name="registre_presences_filtre.pdf", mime="application/pdf")
        else:
            st.info("Aucune présence ne correspond aux critères sélectionnés.")

    conn.close()
