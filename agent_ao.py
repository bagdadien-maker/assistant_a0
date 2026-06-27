import os
from pypdf import PdfReader
from google import genai
from google.genai import types
from docx import Document

# 1. Configuration de la clé API (remets bien ta clé ici)
API_KEY = "AQ.Ab8RN6IiyPrT8fOYMvM8PBTDmy1l1rZRE8f-VGIpjkn7uFbUCQ"
client = genai.Client(api_key=API_KEY)

def extraire_texte_pdf(chemin_pdf):
    """Fonction pour lire le texte d'un fichier PDF"""
    if not os.path.exists(chemin_pdf):
        print(f"⚠️ Fichier introuvable : {chemin_pdf}")
        return ""
    
    reader = PdfReader(chemin_pdf)
    texte = ""
    for page in reader.pages:
        texte += page.extract_text() + "\n"
    return texte

print("📖 Lecture des fichiers PDF en cours...")
texte_rc = extraire_texte_pdf("RC.pdf")
texte_ccap = extraire_texte_pdf("CCAP.pdf")
texte_cctp = extraire_texte_pdf("CCTP.pdf")

instructions_agent = """
Tu es un expert en marchés publics et privés. Ton rôle est d'analyser les documents d'un DCE et de rédiger un rapport structuré.
"""

model_name = "gemini-2.5-flash" 

print("🤖 Analyse en cours par l'Agent IA (Génération du rapport complet)...")

prompt_analyse = f"""
Voici les textes extraits des documents du projet :

--- RC ---
{texte_rc[:100000]} 
--- CCAP ---
{texte_ccap[:100000]}
--- CCTP ---
{texte_cctp[:100000]}

Effectue le travail suivant dans l'ordre :

1. FILTRAGE STRICT :
Vérifie si le montant estimé dépasse 200 000 euros et s'il y a une visite obligatoire. Affiche CLAIREMENT : ÉLIGIBLE ou REJETÉ.

2. ESTIMATION DES CRITÈRES DE JUGEMENT :
Détaille la pondération (Prix, Technique, Rapidité...) et explique comment le jury va noter le projet.

3. CAHIER DES CHARGES DÉTAILLÉ PAR LOT / ÉLÉMENT :
En te basant sur le CCTP, identifie tous les lots ou équipements principaux. Pour CHAQUE lot/équipement, rédige un cahier des charges technique ultra-complet reprenant toutes les contraintes fonctionnelles et technologiques écrites dans le texte.
"""

try:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt_analyse,
        config=types.GenerateContentConfig(
            system_instruction=instructions_agent,
            temperature=0.2,
        )
    )
    
    texte_rapport = response.text
    
    # MODIFICATION : On affiche TOUT le rapport directement sur l'écran (le terminal / cmd)
    print("\n================ RÉSULTAT DE L'AGENT IA ================\n")
    print(texte_rapport)
    print("\n========================================================\n")

    # --- SAUVEGARDE TEXTE ---
    with open("Rapport_Analyse_AO.txt", "w", encoding="utf-8") as f:
        f.write(texte_rapport)
        
    # --- SAUVEGARDE WORD (.docx) ---
    doc = Document()
    doc.add_heading("Rapport d'Analyse et Cahier des Charges - Appel d'Offres", level=0)
    
    for ligne in texte_rapport.split('\n'):
        if ligne.startswith('**1.') or ligne.startswith('**2.') or ligne.startswith('**3.'):
            doc.add_heading(ligne.replace('**', ''), level=1)
        elif ligne.startswith('**Élément') or ligne.startswith('**Lot'):
            doc.add_heading(ligne.replace('**', ''), level=2)
        elif ligne.startswith('* '):
            doc.add_paragraph(ligne.replace('* ', ''), style='List Bullet')
        else:
            doc.add_paragraph(ligne.replace('**', ''))
            
    doc.save("Cahier_des_Charges_Lots.docx")
    
    print("📝 Fichier Word créé avec succès : 'Cahier_des_Charges_Lots.docx'")

except Exception as e:
    print(f"\n❌ Une erreur est survenue : {e}")