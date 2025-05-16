from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
import streamlit as st
import time

from rag_poc import config

api_key = config.load_api_key()

temperature = st.sidebar.slider("Température de génération", 0.0, 1.0, 0.7)

model = ChatMistralAI(
    temperature=temperature, 
    api_key=api_key
    )

# Remove obselete attribute 'language' from the model
if hasattr(model, "language"):
    model.language = None  

embeddings = MistralAIEmbeddings(
        api_key=config.load_api_key(),
        model="mistral-embed"     
    )

vector_store = FAISS.load_local(
    folder_path = config.VECTORS_FOLDER,
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)

def format_context_markdown(docs):
    blocks = []
    for doc in docs:
        title = doc.metadata.get("title_fr", "Sans titre")
        date = doc.metadata.get("daterange_fr", "Date inconnue")
        url = doc.metadata.get("canonicalurl", "")
        desc = doc.page_content.strip()

        block = f"""
**Lien**: [{url}]({url})  

{desc}
"""
        blocks.append(block)
    return "\n---\n".join(blocks)


def generate_recommendation(input_text: str):
    docs = vector_store.similarity_search(
        query=input_text,
        k=3
        )

    context = "\n\n".join(
        f"""
        📌 **{doc.metadata.get('title_fr', 'Titre inconnu')}**\n
        📅 Date : {doc.metadata.get('daterange_fr', 'Inconnue')}\n
        🔗 Lien : {doc.metadata.get('canonicalurl', 'Non disponible')}\n\n

        {doc.page_content}
        """ for doc in docs
    )

    prompt = f"""
    Tu es un assistant intelligent qui aide à recommander des événements à partir de leurs descriptions.

    Voici une liste d'événements susceptible d'intéresser l'utilisateur :

    ---------------------
    {context}
    ---------------------

    En te basant uniquement sur ces événements, pas tes connaissances antérieures, réponds à la question suivante en français :
    **{input_text}**

    Ta réponse doit être concise, utile et faire référence aux événements les plus pertinents (pas besoin de recopier les descriptions, elles sont déjà affichées à l'utilisateur).
    
    Si les événements qui sont dans ta liste ne semblent pas correspondre, ou si la question qui est posé n'est pas pertinente pour un assistant de recommandation d'événements,
    précise ta mission, et invite les utilisateurs à reposer leur question.
    """

    with st.spinner("Génération de la réponse..."):
        response = model.invoke(prompt)
        st.subheader("🧠 Réponse de l'assistant")
        st.markdown(response.content)

    st.subheader("📄 Événements correspondants")
    st.markdown(format_context_markdown(docs), unsafe_allow_html=True)


st.title("🦜🔗 Mistral RAG bot for events")

with st.form("my_form"):
    text = st.text_area(
        "Entrez votre question :",
        f"Vous recherchez un evenement dans la region de {config.REGION}?",
    )
    submitted = st.form_submit_button("Submit")
    if submitted:
        with st.spinner("Recherche en cours..."):
            generate_recommendation(
                input_text=text
            ) 

