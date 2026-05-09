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
| Une clé API DeepSeek | Clé IA économique pour les titres, descriptions et contrôles qualité | [platform.deepseek.com](https://platform.deepseek.com) |
| Une clé API OpenAI | Clé pour le fournisseur d'images par défaut | [platform.openai.com](https://platform.openai.com) |

### Systèmes d'exploitation pris en charge

- **Windows 10/11** — Support complet, tous les fichiers de script (Batch) fonctionnent directement.
- **macOS / Linux** — Utilisez les fichiers `.sh` correspondants ou les commandes manuelles du README.

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

### Étape 3 : Obtenir vos clés API IA

La configuration par défaut actuelle utilise :

- **DeepSeek** pour les textes, les métadonnées, le contrôle qualité et l'auto-correction.
- **OpenAI Images** pour générer les images des épingles.

1. Ouvrez [platform.deepseek.com](https://platform.deepseek.com), créez une clé API et copiez-la.
2. Ouvrez [platform.openai.com](https://platform.openai.com), créez une clé API et copiez-la.
3. Gardez les deux clés pour les ajouter dans le fichier `.env`.

Groq reste pris en charge comme fournisseur texte optionnel, mais ce n'est plus le fournisseur par défaut dans `config.yaml`.

### Étape 4 : Remplir votre fichier `.env`

L'assistant de configuration a ouvert le Bloc-notes avec votre fichier `.env`. Il devrait ressembler à ceci :

```env
# Pinterest Login Credentials (required if session state doesn't exist)
PINTEREST_EMAIL=votre_email_pinterest@example.com
PINTEREST_PASSWORD=votre_mot_de_passe_pinterest

# Text AI provider
DEEPSEEK_API_KEY=your_deepseek_key_here

# OpenAI Images provider
OPENAI_API_KEY=your_openai_key_here

# Optional text provider fallback
GROQ_API_KEY=

# Image generation fallback (optional — leave blank for now)
TOGETHER_API_KEY=
HF_API_KEY=
```

Remplissez :
- `PINTEREST_EMAIL` — l'adresse e-mail que vous utilisez pour vous connecter à Pinterest.
- `PINTEREST_PASSWORD` — votre mot de passe Pinterest.
- `DEEPSEEK_API_KEY` — collez votre clé DeepSeek obtenue à l'étape 3.
- `OPENAI_API_KEY` — collez votre clé OpenAI obtenue à l'étape 3.

**Important :** La génération d'images OpenAI peut être payante. Pour tester uniquement la publication lorsqu'une épingle existe déjà, utilisez la commande `retry-post`, car elle ne régénère ni image ni métadonnées.

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

Pour un test encore plus sûr en ligne de commande, limitez l'exécution à une seule épingle :

```bash
python -m src.main run-now --force --schedule-mode immediate --max-pins 1
```

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
| **`07-run-headless.bat`** | Lancer un cycle sans afficher de fenêtre de navigateur. |
| **`08-run-gui.bat`** | Lancer un cycle avec une fenêtre de navigateur visible. |

Sur macOS ou Linux, utilisez les fichiers `.sh` correspondants, par exemple `./04-run-once.sh` ou `./07-run-headless.sh`.

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

Le planificateur attend maintenant l'heure de publication calculée pour chaque épingle. Pour publier immédiatement lors d'une exécution manuelle :

```bash
python -m src.main run-now --schedule-mode immediate
```

Pour réessayer la publication d'une épingle déjà présente dans la base de données locale :

```bash
python -m src.main retry-post <pin_id> --browser-mode gui
python -m src.main retry-post <pin_id> --browser-mode headless
```

C'est utile pour tester les corrections de publication sans régénérer d'image ni consommer d'appels OpenAI Images supplémentaires.

### Mode GUI et mode headless

Utilisez le mode GUI lorsque vous voulez observer l'automatisation du navigateur ou déboguer une connexion :

```yaml
browser:
  mode: gui
```

Utilisez le mode headless lorsque l'agent tourne sans surveillance ou sur un serveur :

```yaml
browser:
  mode: headless
```

En mode GUI sécurisé, l'agent utilise une seule fenêtre Chromium pour la connexion, la recherche Pinterest, la création d'épingle et la vérification.

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
| **Posted** | L'épingle a été vérifiée avec une vraie URL Pinterest `/pin/<id>/`. |
| **Unverified** | Pinterest a peut-être avancé dans le flux, mais aucune vraie URL n'a été vérifiée. |
| **Failed** | Une étape obligatoire a échoué avant la vérification. |

### Vérification de publication

L'agent ne compte une publication comme réussie que lorsqu'il capture et vérifie une vraie URL comme :

```text
https://www.pinterest.com/pin/123456789/
```

Si la vérification échoue, le rapport indiquera `unverified` ou `failed`, pas un faux succès. Les fichiers de diagnostic sont enregistrés dans :

```text
data/post_debug/
```

Ces dossiers peuvent contenir des captures d'écran, une copie HTML de la page et des journaux réseau montrant où le flux Pinterest s'est arrêté.

---

## Dépannage

### "Python not found" lors de la configuration
- Installez Python 3.11+ depuis [python.org](https://www.python.org/downloads/)
- Assurez-vous de cocher "Add Python to PATH" lors de l'installation.
- Redémarrez votre ordinateur après l'installation.

### Erreur "DEEPSEEK_API_KEY not set" ou "OPENAI_API_KEY not set"
- Ouvrez `.env` dans le Bloc-notes.
- Assurez-vous d'avoir collé votre clé correctement (sans espace supplémentaire).
- Vérifiez que le fournisseur choisi dans `config.yaml` possède une clé correspondante dans `.env`.

### Erreur "GROQ_API_KEY not set"
- Groq est optionnel sauf si vous définissez `ai.text_provider: "groq"` dans `config.yaml`.
- Si vous utilisez Groq, ajoutez sa clé dans `.env`.

### Épingle publiée mais invisible sur Pinterest
- Attendez 5 minutes — Pinterest peut être lent à se mettre à jour.
- Essayez d'actualiser votre profil Pinterest.
- Vérifiez si l'épingle a été enregistrée dans un tableau différent de celui prévu.
- Lancez `05-status.bat` pour voir l'URL enregistrée.
- Si le rapport indique `unverified`, ouvrez le dossier correspondant dans `data/post_debug/` pour inspecter les captures et le HTML.

### L'agent s'est arrêté ou a planté
- Vérifiez le message d'erreur en bas de la fenêtre.
- La plupart des erreurs sont temporaires (problème d'Internet, serveurs Pinterest occupés).
- Lancez simplement `04-run-once.bat` à nouveau pour continuer.

### Trop d'échecs dans validate.bat
- Assurez-vous d'avoir bien exécuté `01-install.bat` avec succès.
- Essayez de relancer `01-install.bat`.
- Vérifiez que votre connexion Internet fonctionne.

### La sélection du tableau a échoué
- Vérifiez que le tableau existe dans votre compte Pinterest.
- Si le tableau suggéré n'existe pas, l'agent peut choisir un tableau disponible en fallback.
- Le rapport indique le type de compte détecté : `personal`, `business` ou `unknown`.

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

**Q : Comment tester la publication sans payer une nouvelle image ?**
R : Utilisez `python -m src.main retry-post <pin_id> --browser-mode gui` ou `--browser-mode headless`. La commande réutilise une image et des métadonnées existantes.

**Q : L'outil fonctionne-t-il avec les comptes Pinterest professionnels ?**
R : Oui. L'agent détecte le type de compte après connexion et prend en charge l'interface actuelle des comptes professionnels. Le type de compte apparaît dans le rapport.

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
├── 07-run-headless.bat     ← Lancer sans fenêtre de navigateur
├── 08-run-gui.bat          ← Lancer avec une fenêtre de navigateur visible
├── config.yaml             ← Vos paramètres (modifiez-le !)
├── .env                    ← Vos clés d'API (créé automatiquement)
├── .env.example            ← Modèle pour le fichier .env
├── data/                   ← Base de données, session et rapports
│   └── post_debug/         ← Captures, HTML et journaux réseau en cas d'échec
├── assets/                 ← Images générées par l'IA
├── src/                    ← Le code de l'agent (ne pas modifier)
├── BEGINNERS_GUIDE_EN.md   ← Guide du débutant en anglais
├── BEGINNERS_GUIDE_AR.md   ← Guide du débutant en arabe
└── BEGINNERS_GUIDE_FR.md   ← Vous êtes ici !
```

---

*Bonne publication !*
