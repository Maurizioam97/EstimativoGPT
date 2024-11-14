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
    descrizione = row['Descrizione Dettagliata']
    if categoria not in dict_lavorazioni:
        dict_lavorazioni[categoria] = [descrizione]
    else:
        dict_lavorazioni[categoria].append(descrizione)

# Carica solo le colonne "CATEGORIA" e "DESCRIZIONE DETTAGLIATA" dal file degli esempi
df_esempio = df_esempio[["CATEGORIA", "DESCRIZIONE DETTAGLIATA"]]

# Configura la Bing Search API
bing_api_key = "52e5a5be8d4e4a72aa97246b33c429f1"  # Sostituisci con la tua chiave API di Bing
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
    # Prepara il prompt con i risultati di Bing e i dati locali
    prompt = f"Domanda: Stai lavorando sulla categoria {macroarea}. Fornisci una lista dettagliata delle lavorazioni necessarie per eseguire il seguente lavoro: '{query}'\n\n"
    prompt += "Ecco alcune informazioni trovate online:\n"
    for i, snippet in enumerate(snippets, start=1):
        prompt += f"{i}. {snippet}\n"
    
    # Aggiungi istruzioni senza etichette esplicite
    prompt += "\nEcco alcune istruzioni trovate nella documentazione relative alla categoria selezionata:\n"
    for i, istruzione in enumerate(istruzioni_locale, start=1):
        prompt += f"- {istruzione}\n"

    # Aggiungi esempi storici senza etichette esplicite
    prompt += "\nEcco alcuni esempi storici correlati:\n"
    for i, esempio in enumerate(esempi_lavorazioni, start=1):
        prompt += f"- {esempio}\n"
    
    prompt += "\nIn base a queste informazioni, fornisci un elenco dettagliato delle lavorazioni necessarie solo per la categoria {macroarea}. Elenca solo le lavorazioni, senza includere etichette come 'Sottocategoria' o 'Note Aggiuntive'. Concentrati solo sull'elenco delle attività pratiche da eseguire."

    # Chiamata a Azure OpenAI API
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
    # Risultati della ricerca web
    risultati_web = ricerca_web(f"{macroarea} {query}")

    # Istruzioni per la macroarea dai file locali
    istruzioni_locale = dict_lavorazioni.get(macroarea, [])

    # Esempi storici per la categoria selezionata
    esempi_lavorazioni = df_esempio[
        df_esempio['CATEGORIA'].str.contains(macroarea, case=False, na=False)
    ]["DESCRIZIONE DETTAGLIATA"].dropna().tolist()

    # Sintetizza la risposta combinando i risultati
    risposta_sintetizzata = sintetizza_risposta(macroarea, query, risultati_web, istruzioni_locale, esempi_lavorazioni)

    # Costruisce il dizionario dei risultati, includendo istruzioni ed esempi storici
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
# Campo di testo per la ricerca
query = st.text_input("Inserisci una descrizione o un dettaglio per arricchire la ricerca")

# Bottone per ottenere i suggerimenti
if st.button("Ottieni suggerimenti"):
    # Ottiene i suggerimenti per la macroarea selezionata
    suggerimenti = suggerisci_lavorazioni(macroarea, query)

    # Visualizza la risposta sintetizzata
    st.subheader("Risposta AI Sintetizzata")
    st.write(suggerimenti["Risposta_Sintetizzata"])

    # Visualizza le istruzioni
    st.subheader("Istruzioni dalla documentazione")
    if suggerimenti["Istruzioni"]:
        for istruzione in suggerimenti["Istruzioni"]:
            st.write("- " + istruzione)
    else:
        st.write("Nessuna istruzione specifica trovata.")

    # Visualizza gli esempi storici
    st.subheader("Esempi Storici")
    if suggerimenti["Esempi_Storici"]:
        for esempio in suggerimenti["Esempi_Storici"]:
            st.write("- " + esempio)
    else:
        st.write("Nessun esempio disponibile per questa categoria.")
