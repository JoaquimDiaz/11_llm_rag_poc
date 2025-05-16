# 🧠 Concevoir et déployer une infrastructure RAG

**Client :** Puls‑Events – société d’événements culturels

**Source de données :** [OpenAgenda](https://openagenda.com/)

---

## 📌 Vue d’ensemble du projet

Ce POC démontre l’usage d’une architecture **Retrieval‑Augmented Generation (RAG)** pour recommander des événements culturels pertinents, filtrés par région et fenêtre temporelle.

### Objectifs clés

* Recommandations contextualisées sur des evenements
* Portée géographique et temporelle configurable
* Chaîne complète d'alimentation du RAG : collecte → validation → indexation → chat LLM

### Livrables

* Dépôt Git avec *README* et **pyproject.toml**
* Indexation vectorielle **FAISS** 
* Réponses LLM via **Mistral API**
* Orchestration **LangChain**
* Pipeline de pré‑traitement reproductible
* Rapport technique (5‑10 pages)
* Tests unitaires (validation des données)

---

## ⚙️ Installation

```bash
# 1️⃣ Installer FAISS (version CPU) via conda
conda install -c pytorch faiss-cpu -y  

# 2️⃣ Installer les dépendances du projet
pip install uv  # si besoin
uv install

# 3️⃣ Configurer la clé API Mistral
echo "MISTRAL_API_KEY=<votre-cle>" > .env
```

---
## 🛠️ Scripts shell d’automatisation

Trois scripts facilitent les tâches les plus courantes :

| Script       | Rôle                                                                                     | Commande équivalente                                     |
| ------------ | ---------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `build.sh`   | Exécute la collecte (`fetch`) puis l’indexation (`index`) avec les paramètres par défaut | `python -m run fetch && python -m run index `            |
| `run_app.sh` | Lance l’application Streamlit sur le port 8501 (modifiable)                              | `python -m run app`                                      |
| `test.sh`    | Lance les tests unitaites pour les scripts/fonctions                                     | `pytest`                                                 |

### Exemples rapides

```bash
chmod +x run.sh run_app.sh
./build.sh        # met à jour les données puis recrée l’index
./run_app.sh      # ouvre le chatbot dans le navigateur par défaut
```

---
## 🏃‍♂️ Utilisation en ligne de commande

Tous les scripts sont regroupés derrière **un unique exécutable Python** grâce à l’*argparser* (voir `rag_poc/argument_parsing.py`).
La syntaxe générale :

```bash
python -m run [-v|-vv|-vvv] <commande> [options] 
```

| Commande  | Rôle                                                           | Options principales                                                                                                                                                                                  |
| --------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **fetch** | Interroger l’API OpenAgenda, valider et enregistrer en Parquet | `--region` : région FR (*default :* config)  <br>`--since` : jours passés à inclure   <br>`--until` : jours futurs  <br>`--limit` : nb événements max  <br>`--destination` : chemin Parquet <b>|
| **index** | Créer / mettre à jour l’index FAISS                            | `--source` : fichier Parquet  <br>`--destination` : dossier vecteurs  <br>`--columns` : colonnes texte à embarquer  <br>`--id` : colonne identifiant unique                                          |
| **app**   | Lancer l’app Streamlit (chatbot)                               | `--port` : port HTTP (déf. 8501)                                                                                                                                                                     |

> **Verbosity** : ajoutez `-v`, `-vv` ou `-vvv` pour passer du niveau **WARNING → INFO → DEBUG**.

### Exemples

1. **Collecter 1 000 événements** de Bratagne pour l’année à venir :

```bash
python -m rag_poc fetch \
  --region="Bretagne" \
  --since 0 \
  --until 365 \
  --limit 1000 \
  --destination data/events.parquet \
  -v
```

2. **Indexer** ces données :

```bash
python -m rag_poc index \
  --source data/events.parquet \
  --destination vectors_store \
  --columns title_fr description_fr longdescription_fr \
  --id uid \
  -vv
```

3. **Démarrer** le chatbot RAG :

```bash
python -m rag_poc app --port 8501
```

Rendez‑vous sur [http://localhost:8501](http://localhost:8501) pour tester !

---

## 🗄️ Structure des répertoires

```
.
├── data/                     # Parquet(api) & index(faiss) & erreurs de validation
├── rag_poc/                  # Directory qui contient les fonctions Python
│   ├── __init__.py
│   ├── argument_parsing.py   # Arguments CLI 
│   ├── config.py             # Constantes globales
│   └── validation.py         # Schémas Pydantic (données événements)
├── scripts/                  # Scripts opérationnels
│   ├── __init__.py
│   ├── fetching.py           # Collecte + validation
│   ├── indexing.py           # Embedding + FAISS
│   └── chat.py               # Interface Streamlit
├── tests/                    # Tests unitaires
│   └── ...
├── build.sh                  # Lance la Pipeline complete (fetch → index)
├── run_app.sh                # Démarre l’app Streamlit
├── run.py                    # Entrypoint alternatif (python -m run)
└── pyproject.toml            # Dépendances & configuration
```

---


## 🔄 Paramétrage et constantes (`config.py`)

Le fichier `rag_poc/config.py` est la **source unique de vérité** pour tous les paramètres du POC.
Chaque module l'importe (`import rag_poc.config as config`) afin de garantir une configuration homogène sur l'ensemble de la chaîne (fetch → index → app).

| Constante          | Rôle                                            | Valeur par défaut                         |
| ------------------ | ----------------------------------------------- | ----------------------------------------- |
| `REGION`           | Région française filtrée par défaut             | `"Bretagne"`                              |
| `SINCE` / `UNTIL`  | Fenêtre temporelle en jours (passé / futur)     | `365` / `365`                             |
| `LIMIT`            | Nombre maximal d'événements retournés par l'API | `5000`                                    |
| `DATA_FILE`        | Chemin du Parquet de données brutes             | `data/raw/api_data.parquet`               |
| `VECTORS_FOLDER`   | Dossier pour l'index FAISS                      | `data/vectors/`                           |
| `COLUMN_EMBEDDING` | Colonnes utilisées pour l'embedding             | `(\"title_fr\", \"description_fr\", ...)` |
| `ID_COLUMN`        | Colonne identifiant unique du dataframe         | `"uid"`                                   |
| `WRITE_ERRORS`     | Sauvegarder les erreurs de validation           | `True`                                    |

> **Bonnes pratiques**

> • **Aucune constante n'est codée en dur** dans les scripts ; toutes proviennent de `config.py`.

> • **Les parametres sont modifiable via la ligne de commande**

---

## 📚 Ressources utiles

* **FAISS Quickstart** – facebookresearch/faiss/wiki/getting-started
* **Mistral RAG Guide** – docs.mistral.ai/guides/rag/
* **LangChain x FAISS** – python.langchain.com/docs/integrations/vectorstores/faiss/

---

> Dernière mise à jour : 2025‑05‑15
