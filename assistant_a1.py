import os
import json
import glob
from pypdf import PdfReader
from google import genai
from google.genai import types

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

# Liste tous les éléments du dossier courant
tous_les_elements = os.listdir(".")
dossiers_trouves = [e for e in tous_les_elements if os.path.isdir(e) and e.endswith("_recherche")]

if not dossiers_trouves:
    print("❌ Aucun dossier se terminant par '_recherche' n'a été trouvé.")
    print("👉 Crée un dossier (ex: 'Appel_Offre_recherche') et mets tes PDF dedans.")
    exit()

# On prend le premier dossier détecté
nom_du_dossier = dossiers_trouves[0]
print(f"🎯 Dossier détecté : [{nom_du_dossier}]")

# ============================================================
# LECTURE DE TOUS LES PDF À L'INTÉRIEUR DU DOSSIER
# ============================================================
# Recherche tous les .pdf présents dans ce dossier spécifique
fichiers_pdf = glob.glob(os.path.join(nom_du_dossier, "*.pdf"))

if not fichiers_pdf:
    print(f"⚠️  Le dossier [{nom_du_dossier}] est vide ou ne contient aucun fichier PDF.")
    exit()

print(f"📚 {len(fichiers_pdf)} fichier(s) PDF trouvé(s) à l'intérieur. Lecture en cours...")

texte_global_dossier = ""

for chemin_pdf in fichiers_pdf:
    try:
        reader = PdfReader(chemin_pdf)
        nom_fichier_court = os.path.basename(chemin_pdf)
        print(f"   🔹 Lecture de : {nom_fichier_court} ({len(reader.pages)} pages)")
        
        texte_global_dossier += f"\n--- DEBUT DU FICHIER : {nom_fichier_court} ---\n"
        for page in reader.pages:
            texte_global_dossier += page.extract_text() + "\n"
        texte_global_dossier += f"--- FIN DU FICHIER : {nom_fichier_court} ---\n"
        
    except Exception as e:
        print(f"   🔺 Impossible de lire le fichier {chemin_pdf} : {str(e)}")

# ============================================================
# ENVOI À L'API GEMINI
# ============================================================
print("\n⚡ Analyse globale et croisée de tous les documents par Gemini...")

prompt_extraction = f"""
Analyse l'ensemble des documents textuels extraits du dossier et trouve précisément les 14 éléments clés demandés.
Certaines informations peuvent être dans un fichier (ex: le RC) et d'autres dans un autre (ex: le CCAP). Fais une synthèse.
Si une information n'est pas mentionnée du tout, écris obligatoirement "Non mentionné".

--- TEXTES DU DOSSIER COMPLET ---
{texte_global_dossier[:40000]} 
"""

system_instruction = """
Tu es un agent de filtrage et d'extraction de données de marchés publics et privés.
Tu dois renvoyer STRICTEMENT un objet JSON valide contenant l'analyse des 14 points, sans aucun texte explicatif avant ou après.
"""

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

    # Sauvegarde du JSON final à côté du script
    nom_sortie_json = f"{nom_du_dossier}_Resultat.json"
    
    with open(nom_sortie_json, "w", encoding="utf-8") as f:
        f.write(response.text)

    print("\n✅ EXTRACTION REUSSIE FUSIONNÉE !\n")
    print(response.text)
    print(f"\n💾 Le fichier JSON global a été sauvegardé sous : '{nom_sortie_json}'")

except Exception as e:
    print(f"❌ Erreur lors de l'appel à l'API : {str(e)}")