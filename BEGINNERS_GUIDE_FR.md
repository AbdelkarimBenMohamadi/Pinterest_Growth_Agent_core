# Guide du débutant pour Pinterest Growth Agent

> **Bienvenue !** Ce guide vous accompagne pas à pas, depuis le téléchargement du projet jusqu'à votre première publication réussie sur Pinterest. Aucune connaissance technique n'est requise.

---

## Qu'est-ce que cet outil ?

**Pinterest Growth Agent (PGA)** est un robot alimenté par l'IA qui effectue automatiquement les tâches suivantes :
- Recherche ce que les gens recherchent sur Pinterest (mots-clés à forte demande).
- Crée de superbes images d'épingles à l'aide de l'IA.
- Rédige des titres et descriptions optimisés pour le SEO.
- Publie des épingles sur votre compte Pinterest selon un planning.
- Apprend quels mots-clés sont les plus performants et se concentre sur ce qui fonctionne.

Considérez-le comme un assistant Pinterest disponible 24h/24 et 7j/7 qui ne dort jamais.

---

## Avant de commencer

### Ce dont vous aurez besoin

| Exigence | Ce que c'est | Où l'obtenir |
|---|---|---|
| Python 3.11+ | Le langage de programmation utilisé par l'outil | [python.org](https://www.python.org/downloads/) |
| Un compte Pinterest | Votre profil Pinterest | [pinterest.com](https://www.pinterest.com) |
| Une clé API Groq | Clé d'IA gratuite pour générer du texte | [console.groq.com](https://console.groq.com) (Gratuit, sans carte bancaire) |

### Systèmes d'exploitation pris en charge

- **Windows 10/11** — Support complet, tous les fichiers de script (Batch) fonctionnent directement.
- **macOS / Linux** — Utilisez les commandes manuelles du fichier README au lieu des fichiers de script.

---

## Installation étape par étape

### Étape 1 : Télécharger le projet

Téléchargez le dossier du projet sur votre ordinateur et extrayez-le s'il est au format ZIP. Gardez le dossier dans un endroit facile d'accès (comme votre Bureau).

### Étape 2 : Exécuter l'assistant de configuration

Double-cliquez sur **`01-install.bat`**

Cela va automatiquement :
- Créer un environnement virtuel Python (garde les fichiers organisés).
- Installer tous les packages Python requis.
- Installer le navigateur Chromium (utilisé pour l'automatisation de Pinterest).
- Créer un fichier `.env` et l'ouvrir dans le Bloc-notes pour vous permettre de le remplir.

La fenêtre de configuration vous indiquera quand l'installation est terminée. Cela prend environ 3 à 5 minutes selon votre connexion.

### Étape 3 : Obtenir votre clé API Groq gratuite

1. Ouvrez [console.groq.com](https://console.groq.com) dans votre navigateur.
2. Créez un compte gratuit (ou connectez-vous).
3. Cliquez sur **"API Keys"** dans la barre latérale.
4. Cliquez sur **"Create API Key"**.
5. Donnez-lui un nom (par exemple, "Pinterest Agent").
6. Copiez la clé — elle ressemble à `gsk_xxxxxxxxxxxxxxxxxxxxxx`.

### Étape 4 : Remplir votre fichier `.env`

L'assistant de configuration a ouvert le Bloc-notes avec votre fichier `.env`. Il devrait ressembler à ceci :

```env
# Pinterest Login Credentials (required if session state doesn't exist)
PINTEREST_EMAIL=votre_email_pinterest@example.com
PINTEREST_PASSWORD=votre_mot_de_passe_pinterest

# Groq API (free at console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxx

# Image generation fallback (optional — leave blank for now)
TOGETHER_API_KEY=
HF_API_KEY=
```

Remplissez :
- `PINTEREST_EMAIL` — l'adresse e-mail que vous utilisez pour vous connecter à Pinterest.
- `PINTEREST_PASSWORD` — votre mot de passe Pinterest.
- `GROQ_API_KEY` — collez votre clé obtenue à l'étape 3.

**Important :** Vous pouvez laisser `TOGETHER_API_KEY` et `HF_API_KEY` vides. Ce sont des fournisseurs d'images de secours qui ne sont pas nécessaires pour commencer.

Enregistrez le fichier et fermez le Bloc-notes.

### Étape 5 : Configurer votre thématique (Niche)

Ouvrez `config.yaml` dans n'importe quel éditeur de texte (double-cliquez dessus). Cela indique à l'agent les sujets sur lesquels publier.

Trouvez la section `niche` et remplacez les mots-clés d'exemple par les vôtres :

```yaml
# Exemple pour le contenu islamique :
niche:
  seed_keywords:
    - "Islamic Reminders"
    - "Morning Azkar"
    - "Tawheed Allah"
    - "Istighfar Benefits"
  categories:
    - "Islam"
    - "Islamic Reminders"

# Exemple pour la décoration intérieure :
niche:
  seed_keywords:
    - "Modern living room ideas"
    - "Minimalist home decor"
    - "Cozy bedroom design"
  categories:
    - "Home Decor"
    - "Interior Design"
```

**Choisissez des sujets sur lesquels vous souhaitez vraiment publier.** L'agent recherchera automatiquement des termes associés.

### Étape 6 : Tout valider

Double-cliquez sur **`02-validate.bat`**

Cela vérifie :
- Que Python est installé correctement.
- Que tous les packages sont installés.
- Que votre navigateur Chromium est prêt.
- Que votre fichier `.env` contient toutes les clés requises.

Si un test échoue, l'outil vous indiquera exactement ce qui ne va pas et comment le corriger.

### Étape 7 : Lancer votre premier cycle

Double-cliquez sur **`03-test-mode.bat`**

> **Note :** Utilisez ce fichier au lieu de `04-run-once.bat` pour votre premier test — il contourne les limites de sécurité pour vous permettre de voir tout le processus de publication immédiatement.

Cela lance un cycle complet immédiatement pour que vous puissiez voir ce qui se passe :
1. **Recherche** — Analyse Pinterest à la recherche de mots-clés et de tendances.
2. **Génération** — Crée des images via l'IA et génère les métadonnées.
3. **Publication** — Publie les épingles sur votre compte Pinterest.
4. **Analyse** — Analyse les performances de vos épingles.

Vous verrez des messages colorés dans la fenêtre au fur et à mesure que chaque étape se termine. Un rapport détaillé apparaîtra à la fin montrant :
- Combien de mots-clés ont été trouvés.
- Combien d'épingles ont été publiées.
- Les erreurs ou avertissements éventuels.

Cette première exécution peut prendre entre 5 et 10 minutes car elle doit générer des images et se connecter à Pinterest pour la première fois.

**Après votre premier test**, utilisez `04-run-once.bat` pour une utilisation quotidienne normale — il respecte les limites de sécurité.

---

## Comprendre les fichiers de script (Batch)

| Fichier | Quand l'utiliser |
|---|---|
| **`01-install.bat`** | À lancer une seule fois lors du premier téléchargement du projet. |
| **`02-validate.bat`** | À lancer avant chaque session pour s'assurer que tout fonctionne. |
| **`04-run-once.bat`** | Cycle normal à la demande — respecte les limites de sécurité. |
| **`03-test-mode.bat`** | **Mode de test complet** — contourne les limites pour tester et déboguer. |
| **`06-start-scheduler.bat`** | Démarrer le planificateur quotidien (tourne en arrière-plan). |
| **`05-status.bat`** | Vérifier vos statistiques — mots-clés, épingles publiées, engagement. |

---

## Fonctionnement du planificateur quotidien

Lorsque vous lancez `06-start-scheduler.bat`, l'agent démarre un planificateur en arrière-plan qui s'exécute une fois par jour à l'heure spécifiée dans `config.yaml`.

**Planning par défaut** (dans `config.yaml`) :
```yaml
schedule:
  start_hour: 8        # S'exécute à 8h00 (heure locale)
  peak_hours: [10, 14, 18, 20]  # Épingles publiées à ces heures-là
  timezone: "US/Eastern"
```

**Limites de sécurité du compte** — L'agent limite le nombre d'épingles publiées en fonction de l'ancienneté du compte pour éviter les suspensions :

| Âge du compte | Max Épingles/Jour | Max Actions Totales |
|---|---|---|
| Jours 1 à 7 | 1 épingle | 10 |
| Jours 8 à 14 | 2 épingles | 20 |
| Jours 15 à 30 | 5 épingles | 40 |
| 31+ jours | 8 épingles | 60 |

Ces limites s'appliquent automatiquement en fonction de la date `account.created_date` que vous définissez dans `config.yaml`.

---

## Comprendre l'affichage

### Que signifient les couleurs ?

- **Vert** — Succès
- **Jaune / Orange** — Avertissement (quelque chose d'inattendu s'est produit mais l'agent a géré la situation)
- **Rouge** — Erreur (l'agent va tenter de récupérer ou de passer à l'étape suivante)
- **Cyan / Magenta** — Informations / données de recherche

### Termes clés

| Terme | Signification |
|---|---|
| **Keyword** | Un mot-clé trouvé par l'agent sur Pinterest. |
| **Content Brief** | Un plan pour une épingle (mot-clé + type de contenu). |
| **Board** | Un tableau Pinterest (comme un dossier) où les épingles sont enregistrées. |
| **Engagement** | Comment les gens interagissent avec vos épingles (enregistrements, clics). |
| **CTR** | Taux de clic — % de personnes ayant cliqué sur votre épingle. |
| **Save Rate** | Taux d'enregistrement — % de personnes ayant enregistré l'épingle. |
| **Cooldown** | Mode de pause — l'agent s'arrête temporairement de publier par sécurité. |
| **Shadowban** | Suspension masquée — lorsque Pinterest masque vos épingles des recherches. |

---

## Dépannage

### "Python not found" lors de la configuration
- Installez Python 3.11+ depuis [python.org](https://www.python.org/downloads/)
- Assurez-vous de cocher "Add Python to PATH" lors de l'installation.
- Redémarrez votre ordinateur après l'installation.

### Erreur "GROQ_API_KEY not set"
- Ouvrez `.env` dans le Bloc-notes.
- Assurez-vous d'avoir collé votre clé correctement (sans espace supplémentaire).
- La clé doit commencer par `gsk_`.

### Épingle publiée mais invisible sur Pinterest
- Attendez 5 minutes — Pinterest peut être lent à se mettre à jour.
- Essayez d'actualiser votre profil Pinterest.
- Vérifiez si l'épingle a été enregistrée dans un tableau différent de celui prévu.
- Lancez `05-status.bat` pour voir l'URL enregistrée.

### L'agent s'est arrêté ou a planté
- Vérifiez le message d'erreur en bas de la fenêtre.
- La plupart des erreurs sont temporaires (problème d'Internet, serveurs Pinterest occupés).
- Lancez simplement `04-run-once.bat` à nouveau pour continuer.

### Trop d'échecs dans validate.bat
- Assurez-vous d'avoir bien exécuté `01-install.bat` avec succès.
- Essayez de relancer `01-install.bat`.
- Vérifiez que votre connexion Internet fonctionne.

---

## Foire Aux Questions

**Q : Mon compte Pinterest va-t-il être banni ?**
R : L'agent est conçu avec des limites de sécurité et utilise une automatisation du navigateur qui imite le comportement humain. Il ne publiera jamais plus d'épingles que l'ancienneté de votre compte ne le permet. De plus, il détecte automatiquement les shadowbans et se met en pause.

**Q : Combien d'épingles publiera-t-il par jour ?**
R : En fonction du planning d'échauffement du compte, entre 1 et 8 épingles par jour selon l'ancienneté. Les comptes plus anciens peuvent publier davantage.

**Q : Dois-je laisser mon ordinateur allumé ?**
R : Oui — l'agent s'exécute sur votre ordinateur. Si vous fermez la fenêtre, le planificateur s'arrête. Pour un fonctionnement 24h/24 et 7j/7, envisagez d'utiliser un VPS ou un ordinateur toujours allumé.

**Q : Puis-je modifier le planning de publication ?**
R : Oui — modifiez `config.yaml`. Changez `peak_hours` par les heures auxquelles vous souhaitez que vos épingles soient publiées, et `timezone` par votre fuseau horaire local.

---

## Fichiers et dossiers

```
pinterest-growth-agent/
├── 01-install.bat           ← À lancer en PREMIER
├── 02-validate.bat         ← Vérifier la configuration avant de lancer
├── 03-test-mode.bat         ← Premier test (contourne les limites)
├── 04-run-once.bat         ← Cycle normal à la demande
├── 05-status.bat           ← Voir les statistiques
├── 06-start-scheduler.bat  ← Démarrer le planificateur quotidien
├── config.yaml             ← Vos paramètres (modifiez-le !)
├── .env                    ← Vos clés d'API (créé automatiquement)
├── .env.example            ← Modèle pour le fichier .env
├── data/                   ← Base de données et fichiers de session
├── assets/                 ← Images générées par l'IA
├── src/                    ← Le code de l'agent (ne pas modifier)
├── BEGINNERS_GUIDE_EN.md   ← Guide du débutant en anglais
├── BEGINNERS_GUIDE_AR.md   ← Guide du débutant en arabe
└── BEGINNERS_GUIDE_FR.md   ← Vous êtes ici !
```

---

*Bonne publication !*
