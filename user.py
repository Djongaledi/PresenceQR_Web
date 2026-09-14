from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st

st.set_page_config(
    page_title="Espace Élève - Présence", page_icon="👤", layout="centered"
)

st.title("👤 Espace Consultation - Élève")
st.write(
    "Veuillez entrer votre numéro matricule pour accéder à vos informations"
    " personnelles et à votre taux de présence."
)


def get_connection():
  return sqlite3.connect("ecole.db")  # Gardez le même nom de base que dans app.py


conn = get_connection()

try:
  eleves_df = pd.read_sql_query("SELECT * FROM eleves", conn)
except Exception:
  eleves_df = pd.DataFrame()

if eleves_df.empty:
  st.warning(
      "Aucun élève n'a encore été enregistré par l'administrateur dans la"
      " base de données."
  )
else:
  # Normalisation des noms de colonnes en minuscules
  eleves_df.columns = [c.lower() for c in eleves_df.columns]

  # S'assurer que les colonnes nécessaires existent
  for col in ["matricule", "nom", "prenom", "classe"]:
    if col not in eleves_df.columns:
      eleves_df[col] = "Non défini"
  if "option" not in eleves_df.columns:
    eleves_df["option"] = "N/A"

  st.markdown("---")
  # Champ de saisie sécurisé par le numéro matricule
  matricule_saisi = st.text_input(
      "Entrez votre Numéro Matricule :", placeholder="ex: MAT-001"
  )

  if matricule_saisi:
    # Recherche de l'élève par son matricule exact
    resultat_eleve = eleves_df[
        eleves_df["matricule"].astype(str).str.strip().str.lower()
        == matricule_saisi.strip().lower()
    ]

    if not resultat_eleve.empty:
      infos_eleve = resultat_eleve.iloc[0]

      st.success("Matricule reconnu ! Voici vos informations :")

      st.markdown("---")
      st.subheader("📌 Vos Informations Personnelles")

      col1, col2 = st.columns(2)
      with col1:
        st.write(f"**Nom :** {infos_eleve['nom']}")
        st.write(f"**Prénom :** {infos_eleve['prenom']}")
      with col2:
        st.write(f"**Classe :** {infos_eleve['classe']}")
        st.write(f"**Option :** {infos_eleve['option']}")

      st.info(
          "🔑 Votre code unique (utilisé pour le QR code) :"
          f" **`{infos_eleve['matricule']}`**"
      )

      # Récupération des présences de cet élève
      try:
        query_presences = (
            "SELECT date, heure, statut FROM presences WHERE eleve_id = ?"
        )
        presences_user = pd.read_sql_query(
            query_presences, conn, params=(infos_eleve["matricule"],)
        )
      except Exception:
        presences_user = pd.DataFrame(columns=["date", "heure", "statut"])

      st.markdown("---")
      st.subheader("📈 Statistiques de Présence")

      total_seances = 10
      nb_presents = len(presences_user)
      taux = (
          min(float(nb_presents / total_seances) * 100, 100.0)
          if total_seances > 0
          else 0.0
      )

      st.metric(
          label="Taux de présence",
          value=f"{taux:.1f}%",
          delta=f"{nb_presents} présence(s) enregistrée(s)",
      )

      st.write("### 📋 Historique de vos pointages :")
      if not presences_user.empty:
        st.dataframe(presences_user, use_container_width=True)
      else:
        st.info("Aucune présence enregistrée à votre nom pour le moment.")

    else:
      st.error(
          "Matricule introuvable. Veuillez vérifier votre saisie ou contacter"
          " l'administrateur."
      )

conn.close()





