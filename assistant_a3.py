import os
import glob
from pypdf import PdfReader

# ============================================================
# CONFIGURATION DE L'AGENT ASSISTANT_A3 (SANS IA)
# ============================================================
NOM_AGENT = "assistant_a3"

print(f"\n🚀 DÉMARRAGE DE L'AGENT : {NOM_AGENT} (100% Algorithmique)")
print("🔍 Recherche d'un dossier (répertoire) se terminant par '_recherche'...")

# 1. Détection automatique du dossier complet
tous_les_elements = os.listdir(".")
dossiers_trouves = [e for e in tous_les_elements if os.path.isdir(e) and e.endswith("_recherche")]

if not dossiers_trouves:
    print("❌ Aucun dossier se terminant par '_recherche' n'a été trouvé.")
    print("👉 Crée un dossier (ex: 'Dossier_Affaire_recherche') et mets tes PDF dedans.")
    exit()

nom_du_dossier = dossiers_trouves[0]
print(f"🎯 Dossier détecté : [{nom_du_dossier}]")

# 2. Liste des fichiers PDF à analyser
fichiers_pdf = glob.glob(os.path.join(nom_du_dossier, "*.pdf"))

if not fichiers_pdf:
    print(f"⚠️ Le dossier [{nom_du_dossier}] ne contient aucun fichier PDF.")
    exit()

# Dictionnaire pour stocker le classement final
documents_identifies = {
    "RC (Règlement de Consultation)": [],
    "CCTP (Cahier des Charges Techniques)": [],
    "CCAP (Cahier des Clauses Administratives)": [],
    "Autres documents non classés": []
}

# Fonction utilitaire pour nettoyer le texte (retire les accents et passe en minuscule)
def nettoyer_texte(texte):
    remplacements = {'à': 'a', 'â': 'a', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'î': 'i', 'ï': 'i', 'ô': 'o', 'ù': 'u', 'û': 'u'}
    texte_nettoie = texte.lower()
    for accent, sans_accent in remplacements.items():
        texte_nettoie = texte_nettoie.replace(accent, sans_accent)
    return texte_nettoie

# ============================================================
# TRAVAIL DE RECHERCHE ET DE CLASSIFICATION
# ============================================================
print(f"📋 Analyse de {len(fichiers_pdf)} fichier(s)...")

for chemin_pdf in fichiers_pdf:
    nom_fichier = os.path.basename(chemin_pdf)
    nom_nettoie = nettoyer_texte(nom_fichier)
    classifie = False

    # 🛑 SÉCURITÉ / FILTRE : Ignorer si le nom contient "question" ou "reponse"
    if "question" in nom_nettoie or "reponse" in nom_nettoie:
        print(f"  ⏩ {nom_fichier} -> Ignoré (contient 'question' ou 'reponse')")
        continue

    # --- ÉTAPE 1 : Test rapide par le NOM du fichier ---
    if "rc" in nom_nettoie or "reglement" in nom_nettoie or "consultation" in nom_nettoie:
        documents_identifies["RC (Règlement de Consultation)"].append(nom_fichier)
        print(f"  ✅ {nom_fichier} -> Classé par son nom (RC)")
        continue
    if "cctp" in nom_nettoie or "technique" in nom_nettoie or "charge" in nom_nettoie:
        documents_identifies["CCTP (Cahier des Charges Techniques)"].append(nom_fichier)
        print(f"  ✅ {nom_fichier} -> Classé par son nom (CCTP)")
        continue
    if "ccap" in nom_nettoie or "administratif" in nom_nettoie or "clause" in nom_nettoie:
        documents_identifies["CCAP (Cahier des Clauses Administratives)"].append(nom_fichier)
        print(f"  ✅ {nom_fichier} -> Classé par son nom (CCAP)")
        continue

    # --- ÉTAPE 2 : Test approfondi par le CONTENU du fichier ---
    # Si le nom n'a rien donné, on ouvre le PDF pour fouiller les 3 premières pages
    try:
        reader = PdfReader(chemin_pdf)
        texte_interne = ""
        
        # On lit les 3 premières pages (souvent suffisant pour la page de garde ou l'intro)
        for i in range(min(3, len(reader.pages))):
            texte_interne += reader.pages[i].extract_text() or ""
            
        texte_interne_nettoie = nettoyer_texte(texte_interne)

        # Recherche des expressions du RC
        if "reglement de consultation" in texte_interne_nettoie or "reglement de la consultation" in texte_interne_nettoie:
            documents_identifies["RC (Règlement de Consultation)"].append(nom_fichier)
            print(f"  ✅ {nom_fichier} -> Classé par son contenu (RC)")
            classifie = True
        
        # Recherche des expressions du CCTP
        elif "cahier des clauses techniques" in texte_interne_nettoie or "cctp" in texte_interne_nettoie or "specifications techniques" in texte_interne_nettoie:
            documents_identifies["CCTP (Cahier des Charges Techniques)"].append(nom_fichier)
            print(f"  ✅ {nom_fichier} -> Classé par son contenu (CCTP)")
            classifie = True
            
        # Recherche des expressions du CCAP
        elif "cahier des clauses administratives" in texte_interne_nettoie or "ccap" in texte_interne_nettoie:
            documents_identifies["CCAP (Cahier des Clauses Administratives)"].append(nom_fichier)
            print(f"  ✅ {nom_fichier} -> Classé par son contenu (CCAP)")
            classifie = True

    except Exception as e:
        print(f"  🔺 Erreur lors de l'ouverture ou lecture de {nom_fichier} : {str(e)}")

    # Si ni le nom ni le contenu n'ont fonctionné
    if not classifie:
        documents_identifies["Autres documents non classés"].append(nom_fichier)
        print(f"  ❓ {nom_fichier} -> Impossible à classer")

# ============================================================
# AFFICHAGE DU RAPPORT FINAL
# ============================================================
print("\n" + "="*60)
print("📌 RAPPORT DE TRI DU DOSSIER (SANS IA)")
print("="*60)

for categorie, liste_fichiers in documents_identifies.items():
    print(f"\n📂 {categorie} :")
    if liste_fichiers:
        for f in sorted(list(set(liste_fichiers))):
            print(f"  🔹 {f}")
    else:
        print("  ❌ Aucun document trouvé.")

print("\n" + "="*60)
print(f"🎉 Analyse terminée avec succès par {NOM_AGENT} !")