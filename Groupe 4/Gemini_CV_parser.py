import discord
from discord.ext import commands
import requests
from io import BytesIO
import google.generativeai as genai
from PyPDF2 import PdfReader  # Pour lire le fichier PDF

# Définir ton token Discord
DISCORD_TOKEN = 'METTRE INFO PERSONNELLE'

# Créer un objet bot avec les permissions nécessaires
intents = discord.Intents.default()
intents.message_content = True  # Nécessaire pour lire le contenu des messages
bot = commands.Bot(command_prefix='!', intents=intents)

# Définir l'API Gemini
GEMINI_API_KEY = "METTRE INFO PERSONNELLE"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Fonction pour extraire le texte d'un PDF
def extract_text_from_pdf(pdf_content):
    pdf_reader = PdfReader(BytesIO(pdf_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

@bot.command(name='parse_cv')
async def parse_cv(ctx):
    # Vérifier s'il y a des pièces jointes
    if len(ctx.message.attachments) == 0:
        await ctx.send("Aucune pièce jointe trouvée. Assure-toi de joindre un fichier PDF de CV !")
        return

    # Récupérer la première pièce jointe (supposons qu'il n'y en ait qu'une)
    attachment = ctx.message.attachments[0]
    
    # Vérifier si c'est un fichier PDF
    if not attachment.filename.endswith('.pdf'):
        await ctx.send("Le fichier joint n'est pas un PDF. Veuillez envoyer un fichier PDF.")
        return

    try:
        # Télécharger le fichier PDF
        pdf_content = await attachment.read()

        # Extraire le texte du fichier PDF
        pdf_text = extract_text_from_pdf(pdf_content)

        # Créer le prompt pour Gemini
        prompt = f"""
        Voici le texte complet d'un CV extrait d'un fichier PDF. Analyse-le et convertis-le directement en JSON avec la structure suivante:

        ```json
        {{
          "prenom_nom": "string",
          "email": "string",
          "telephone": "string",
          "linkedin": "string (seulement le nom d'utilisateur, pas l'URL complète, ou vide si non présent)",
          "github": "string (seulement le nom d'utilisateur, pas l'URL complète, ou vide si non présent)",
          "competences_techniques": [
            "compétence technique 1",
            "compétence technique 2"
          ],
          "soft_skills": [
            "soft skill 1",
            "soft skill 2"
          ],
          "langues": [
            "string (langue et niveau)"
          ],
          "certifications": [
            "string (certification 1)",
            "string (certification 2)"
          ],
          "formation": [
            {{
              "titre": "string (diplôme et spécialité)",
              "etablissement": "string (nom de l'école/université)",
              "periode": "string (dates de début et fin)",
              "details": [
                "string (enseignements, mentions, etc.)"
              ]
            }}
          ],
          "experience": [
            {{
              "titre": "string (intitulé du poste)",
              "entreprise": "string (nom de l'entreprise)",
              "lieu": "string (ville/pays ou télétravail)",
              "periode": "string (dates de début et fin)",
              "details": [
                "string (responsabilités, accomplissements)"
              ]
            }}
          ]
        }}
        ```

        Instructions spéciales:
        - Inclus TOUJOURS les champs "linkedin" et "github" dans le JSON, même s'ils sont vides ("").
        - Pour LinkedIn, si tu trouves une URL comme "linkedin.com/in/nom-utilisateur", n'inclus que "nom-utilisateur". Si tu trouves directement "/linkedin-innom-utilisateur", n'inclus que "nom-utilisateur".
        - Pour GitHub, si tu trouves une URL comme "github.com/nom-utilisateur", n'inclus que "nom-utilisateur". Si tu trouves directement "/githubnom-utilisateur", n'inclus que "nom-utilisateur".
        - Si aucun profil LinkedIn ou GitHub n'est mentionné dans le CV, laisse ces champs vides: "linkedin": "", "github": "".

        - IMPORTANT: Pour les compétences techniques, inclus UNIQUEMENT les langages de programmation, logiciels, et outils concrets.
          * Ne pas inclure dans cette section les domaines de connaissances théoriques comme l'économie, la finance, les mathématiques, etc.
          * Limite-toi aux compétences techniques concrètes et opérationnelles (langages, logiciels, frameworks, etc.)

        - Identifie et liste toutes les soft skills (compétences personnelles, interpersonnelles et transversales).

        - CERTIFICATIONS:
          * Recherche et inclus toutes les certifications mentionnées dans le CV.
          * Permis de conduire (B, BVA, etc.), certifications de langue (TOEIC, TOEFL, etc.), certifications informatiques (PIX, etc.)
          * Si aucune certification n'est mentionnée, laisse la liste vide: []

        - Tu dois ABSOLUMENT inclure les champs "competences_techniques", "soft_skills" et "certifications" dans le JSON final, même s'ils sont vides.

        Texte du CV:
        {pdf_text}

        Retourne UNIQUEMENT le JSON sans aucun autre commentaire. Assure-toi que le format est valide.
        """

        # Préparer la requête pour l'API Gemini
        response = gemini_model.generate_content(prompt)

        # Récupérer la réponse de Gemini
        result_json = response.text

        # Limite de Discord : 2000 caractères par message
        MAX_DISCORD_MESSAGE_LENGTH = 2000

        # Découpe le texte en morceaux de 2000 caractères maximum
        chunks = [result_json[i:i + MAX_DISCORD_MESSAGE_LENGTH] for i in range(0, len(result_json), MAX_DISCORD_MESSAGE_LENGTH)]

        # Envoie chaque morceau comme un message séparé
        for chunk in chunks:
            await ctx.send(chunk)

    except Exception as e:
        await ctx.send(f"Une erreur est survenue lors de l'analyse du CV : {str(e)}")

# Démarrer le bot Discord
bot.run(DISCORD_TOKEN)
