import os
import json
import glob
import sys
from pypdf import PdfReader
from google import genai
from google.genai import types

# Forcer l'encodage de la sortie console en UTF-8 pour éviter les crashs d'affichage sur Mac
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# CONFIGURATION GEMINI
# ============================================================
GEMINI_API_KEY = "AQ.Ab8RN6KQTI9JPuyMy-AI6RED-2n2xSVOlMjpf1hMHMWQ7lMPfA"
client = genai.Client(api_key=GEMINI_API_KEY)
MODELE_GEMINI = "gemini-2.5-flash"

# ============================================================
# DÉTECTION AUTOMATIQUE DU DOSSIER DE RECHERCHE
# ============================================================
print("\n🔍 Recherche d'un dossier (répertoire) se terminant par '_recherche'...")

tous_les_elements = os.listdir(".")
dossiers_trouves = [e for e in tous_les_elements if os.path.isdir(e) and e.endswith("_recherche")]

if not dossiers_trouves:
    print("❌ Aucun dossier se terminant par '_recherche' n'a été trouvé.")
    exit()

nom_du_dossier = dossiers_trouves[0]
print(f"🎯 Dossier détecté : [{nom_du_dossier}]")

fichiers_pdf = glob.glob(os.path.join(nom_du_dossier, "*.pdf"))

if not fichiers_pdf:
    print(f"⚠️  Le dossier [{nom_du_dossier}] ne contient aucun fichier PDF.")
    exit()

# ============================================================
# FILTRAGE ET LECTURE EXCLUSIVE DU RC ET DU CCAP
# ============================================================
def nettoyer_texte(texte):
    remplacements = {'à': 'a', 'â': 'a', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'î': 'i', 'ï': 'i', 'ô': 'o', 'ù': 'u', 'û': 'u'}
    texte_nettoie = texte.lower()
    for accent, sans_accent in remplacements.items():
        texte_nettoie = texte_nettoie.replace(accent, sans_accent)
    return texte_nettoie

texte_fusion_rc_ccap = ""
fichiers_retenus = []

print(f"\n📋 Analyse et filtrage des fichiers pour trouver le RC et le CCAP...")

for chemin_pdf in fichiers_pdf:
    nom_fichier = os.path.basename(chemin_pdf)
    nom_nettoie = nettoyer_texte(nom_fichier)
    
    if "question" in nom_nettoie or "reponse" in nom_nettoie:
        continue
        
    est_interessant = False
    
    if any(k in nom_nettoie for k in ["rc", "reglement", "consultation", "ccap", "administratif", "clause"]):
        est_interessant = True
    else:
        try:
            reader = PdfReader(chemin_pdf)
            texte_entete = ""
            for i in range(min(2, len(reader.pages))):
                texte_entete += reader.pages[i].extract_text() or ""
            texte_entete_nettoie = nettoyer_texte(texte_entete)
            
            if any(k in texte_entete_nettoie for k in ["reglement de consultation", "reglement de la consultation", "cahier des clauses administratives", "ccap"]):
                est_interessant = True
        except Exception:
            pass

    if est_interessant:
        try:
            print(f"  ✅ Fichier retenu : {nom_fichier}")
            fichiers_retenus.append(nom_fichier)
            reader = PdfReader(chemin_pdf)
            texte_fusion_rc_ccap += f"\n--- DEBUT DU FICHIER : {nom_fichier} ---\n"
            for page in reader.pages:
                texte_fusion_rc_ccap += (page.extract_text() or "") + "\n"
            texte_fusion_rc_ccap += f"--- FIN DU FICHIER : {nom_fichier} ---\n"
        except Exception as e:
            print(f"  🔺 Impossible de lire {nom_fichier} : {str(e)}")

if not fichiers_retenus:
    print("❌ Aucun fichier correspondant à un RC ou un CCAP n'a été identifié.")
    exit()

# ============================================================
# EXTRACTION DES 14 CRITÈRES PAR GEMINI
# ============================================================
print(f"\n⚡ Extraction des 14 critères en cours par Gemini sur la base de : {fichiers_retenus}...")

# Construction du prompt de manière sécurisée en forçant l'encodage des chaînes de caractères
consignes = """
**Mission :** Extraire les informations spécifiques listées ci-dessous à partir du document de consultation (appel d'offres) fourni.
Restituez les résultats en français, dans un format JSON structuré. Si absent, écrivez "Non spécifié".

Éléments à extraire :
1. date_limite_reception (Date et heure exactes de clôture)
2. delai_validite_offres
3. contenu_dossier
4. deroulement_procedure_et_documents_offre (contenant mode_transmission, pieces_administratives, pieces_techniques, pieces_financieres, formulaires_annexes_obligatoires)
5. criteres_attribution
6. acheteur
7. date_limite_remise
8. numero_lot
9. montant_maximum_lot
10. delai_execution
11. lieu_execution
12. duree_garantie
13. penalites_retard
14. visite_obligatoire_site

--- TEXTES DES DOCUMENTS SOURCE (RC / CCAP) ---
"""

# Pour éviter l'erreur de codec f-string, on fait une concaténation classique et sécurisée
prompt_extraction = consignes + texte_fusion_rc_ccap[:45000]

system_instruction = "Tu es un assistant juridique expert. Renvoie STRICTEMENT un objet JSON valide conforme au schéma."

try:
    response = client.models.generate_content(
        model=MODELE_GEMINI,
        contents=prompt_extraction,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "date_limite_reception": {"type": "STRING"},
                    "delai_validite_offres": {"type": "STRING"},
                    "contenu_dossier": {"type": "STRING"},
                    "deroulement_procedure_et_documents_offre": {
                        "type": "OBJECT",
                        "properties": {
                            "mode_transmission": {"type": "STRING"},
                            "pieces_administratives": {"type": "STRING"},
                            "pieces_techniques": {"type": "STRING"},
                            "pieces_financieres": {"type": "STRING"},
                            "formulaires_annexes_obligatoires": {"type": "STRING"}
                        }
                    },
                    "criteres_attribution": {"type": "STRING"},
                    "acheteur": {"type": "STRING"},
                    "date_limite_remise": {"type": "STRING"},
                    "numero_lot": {"type": "STRING"},
                    "montant_maximum_lot": {"type": "STRING"},
                    "delai_execution": {"type": "STRING"},
                    "lieu_execution": {"type": "STRING"},
                    "duree_garantie": {"type": "STRING"},
                    "penalites_retard": {"type": "STRING"},
                    "visite_obligatoire_site": {"type": "STRING"}
                }
            }
        )
    )

    nom_sortie_json = f"{nom_du_dossier}_Analyse_RC_CCAP.json"
    
    # Écriture forcée et explicite en UTF-8 du fichier JSON final
    with open(nom_sortie_json, "w", encoding="utf-8") as f:
        f.write(response.text)

    print("\n✅ EXTRACTION ET SYNTHÈSE JSON AVEC SUCCÈS !\n")
    print(response.text)
    print(f"\n💾 Fichier sauvegardé sous : '{nom_sortie_json}'")

except Exception as e:
    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        print("\n🛑 L'API GEMINI A ATTEINT SA LIMITE DE QUOTA GÉNÉRALE (20 requêtes gratuites par jour).")
        print("👉 Attends que Google réinitialise ton quota gratuit ou bascule vers le plan Pay-as-you-go.")
    else:
        print(f"❌ Erreur lors de l'appel à l'API : {str(e)}")