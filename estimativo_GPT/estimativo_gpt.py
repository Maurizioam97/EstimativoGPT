import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import streamlit as st
import openpyxl
import requests

# Scarica le risorse di NLTK se necessario
nltk.download('punkt')
nltk.download('wordnet')

# Percorso dei file
path_istruzioni = "estimativo_GPT/Istruzioni estimativo.xlsx"
path_esempio = "estimativo_GPT/esempio.xls"

# Carica i file delle istruzioni ed esempio usando solo 'openpyxl'
istruzioni = pd.read_excel(path_istruzioni, engine='openpyxl')
df_esempio = pd.read_excel(path_esempio, engine='openpyxl')

# Creiamo un dizionario con categoria come chiave e descrizione come valore
dict_lavorazioni = {}
for index, row in istruzioni.iterrows():
    categoria = row['Categoria']
    sottocategoria = row['Sottocategoria']  # Aggiornato da 'Macroarea' a 'Sottocategoria'
    descrizione = row['Descrizione Dettagliata']
    note_aggiuntive = row['Note Aggiuntive']

    # Aggiungi alla struttura del dizionario per includere sottocategoria e note aggiuntive
    if categoria not in dict_lavorazioni:
        dict_lavorazioni[categoria] = []
    dict_lavorazioni[categoria].append({
        "Sottocategoria": sottocategoria,
        "Descrizione": descrizione,
        "Note Aggiuntive": note_aggiuntive
    })

# Carica solo le colonne "CATEGORIA" e "DESCRIZIONE DETTAGLIATA" dal file degli esempi
df_esempio = df_esempio[["CATEGORIA", "DESCRIZIONE DETTAGLIATA"]]

# Configura la Bing Search API
bing_api_key = "52e5a5be8d4e4a72aa97246b33c429f1"
bing_endpoint = "https://api.bing.microsoft.com/v7.0/search"

# Configura Azure OpenAI API
azure_openai_api_key = "2ill4A68l6BfyxK9xm6drYIzbKPX8yuPMg2BvJKtPgeXlJyn9bgsJQQJ99AKAC5RqLJXJ3w3AAABACOGIslu"
azure_openai_endpoint = "https://estimativogpt.openai.azure.com/openai/deployments/gpt-35-turbo"
api_version = "2024-08-01-preview"

# Funzione per fare una ricerca web su Bing
def ricerca_web(query):
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(bing_endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        results = response.json().get("webPages", {}).get("value", [])
        return [result["snippet"] for result in results]
    else:
        print("Errore:", response.status_code, response.text)
        return []

# Funzione per sintetizzare i risultati usando Azure OpenAI GPT-4
def sintetizza_risposta(macroarea, query, snippets, istruzioni_locale, esempi_lavorazioni):
    prompt = f"Domanda: Stai lavorando sulla categoria {macroarea}. Fornisci una lista dettagliata delle lavorazioni necessarie per eseguire il seguente lavoro: '{query}'\n\n"
    prompt += "Ecco alcune informazioni trovate online:\n"
    for i, snippet in enumerate(snippets, start=1):
        prompt += f"{i}. {snippet}\n"
    
    prompt += "\nEcco alcune istruzioni trovate nella documentazione:\n"
    for i, istruzione in enumerate(istruzioni_locale, start=1):
        prompt += f"{i}. Sottocategoria: {istruzione['Sottocategoria']} - Descrizione: {istruzione['Descrizione']} - Note Aggiuntive: {istruzione['Note Aggiuntive']}\n"

    prompt += "\nEcco alcuni esempi storici correlati:\n"
    for i, esempio in enumerate(esempi_lavorazioni, start=1):
        prompt += f"{i}. {esempio}\n"
    
    prompt += "\nIn base a queste informazioni, fornisci un elenco di lavorazioni necessarie solo per la categoria {macroarea}. Questo elenco mi servirà per sapere quali voci andare a cercare all'interno del mio prezzario regionale di riferimento e di conseguenza creare un computo metrico estimativo."

    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_api_key
    }
    data = {
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.7
    }
    completions_endpoint = f"{azure_openai_endpoint}/completions?api-version={api_version}"
    response = requests.post(completions_endpoint, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["text"].strip()
    else:
        print("Errore nella risposta di Azure OpenAI:", response.status_code, response.text)
        return "Errore nella generazione della risposta."

# Funzione aggiornata per ottenere suggerimenti con priorità alla ricerca web
def suggerisci_lavorazioni(macroarea, query):
    risultati_web = ricerca_web(f"{macroarea} {query}")
    istruzioni_locale = dict_lavorazioni.get(macroarea, [])
    esempi_lavorazioni = df_esempio[
        df_esempio['CATEGORIA'].str.contains(macroarea, case=False, na=False)
    ]["DESCRIZIONE DETTAGLIATA"].dropna().tolist()

    risposta_sintetizzata = sintetizza_risposta(macroarea, query, risultati_web, istruzioni_locale, esempi_lavorazioni)

    risultato = {
        "Risposta_Sintetizzata": risposta_sintetizzata,
        "Istruzioni": istruzioni_locale,
        "Esempi_Storici": esempi_lavorazioni
    }
    return risultato

# Impostazioni per Streamlit
st.title("Assistente per Computi Metrici Estimativi")

# Selezione della macroarea
macroarea = st.selectbox("Seleziona la macroarea", list(dict_lavorazioni.keys()))
query = st.text_input("Inserisci una descrizione o un dettaglio per arricchire la ricerca")

# Bottone per ottenere i suggerimenti
if st.button("Ottieni suggerimenti"):
    suggerimenti = suggerisci_lavorazioni(macroarea, query)

    st.subheader("Risposta AI Sintetizzata")
    st.write(suggerimenti["Risposta_Sintetizzata"])

    st.subheader("Istruzioni dalla documentazione")
    if suggerimenti["Istruzioni"]:
        for item in suggerimenti["Istruzioni"]:
            st.write(f"- Sottocategoria: {item['Sottocategoria']}")
            st.write(f"  Descrizione: {item['Descrizione']}")
            st.write(f"  Note Aggiuntive: {item['Note Aggiuntive']}")
    else:
        st.write("Nessuna istruzione specifica trovata.")

    st.subheader("Esempi Storici")
    if suggerimenti["Esempi_Storici"]:
        for esempio in suggerimenti["Esempi_Storici"]:
            st.write("- " + esempio)
    else:
        st.write("Nessun esempio disponibile per questa categoria.")
