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
path_istruzioni = "estimativo_GPT/istruzioni estimativo.xls"
path_esempio = "estimativo_GPT/esempio.xls"

# Carica i file delle istruzioni ed esempio usando solo 'openpyxl'
istruzioni = pd.read_excel(path_istruzioni, engine='openpyxl')
df_esempio = pd.read_excel(path_esempio, engine='openpyxl')

# Creiamo un dizionario con categoria come chiave e descrizione come valore
dict_lavorazioni = {}
for index, row in istruzioni.iterrows():
    categoria = row['Categoria']
    descrizione = row['Descrizione dettagliata']
    if categoria not in dict_lavorazioni:
        dict_lavorazioni[categoria] = [descrizione]
    else:
        dict_lavorazioni[categoria].append(descrizione)

# Carica solo le colonne "CATEGORIA" e "DESCRIZIONE DETTAGLIATA" dal file degli esempi
df_esempio = df_esempio[["CATEGORIA", "DESCRIZIONE DETTAGLIATA"]]

# Imposta la chiave API e l'endpoint per la Bing Search API
api_key = "98721019-813a-4987-94ce-ee3ac6e28ad2"  # Sostituisci con la tua chiave API di Azure
endpoint = "https://api.bing.microsoft.com/v7.0/search"

# Funzione per fare una ricerca web su Bing
def ricerca_web(query):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(endpoint, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print("Risposta Bing:", data)  # Stampa la risposta completa per debug
        return [item["snippet"] for item in data.get("webPages", {}).get("value", [])]
    else:
        print("Errore nella ricerca:", response.status_code, response.text)
        return []

# Funzione aggiornata per ottenere suggerimenti con priorità alla ricerca web
def suggerisci_lavorazioni(macroarea, query):
    # Risultati della ricerca web
    risultati_web = ricerca_web(f"{macroarea} {query}")

    # Istruzioni per la macroarea dai file locali
    istruzioni_locale = dict_lavorazioni.get(macroarea, [])

    # Esempi storici per la categoria selezionata
    esempi_lavorazioni = df_esempio[
        df_esempio['CATEGORIA'].str.contains(macroarea, case=False, na=False)
    ].dropna(subset=["DESCRIZIONE DETTAGLIATA"])

    # Costruisce il dizionario dei risultati
    risultato = {
        "Risultati Web": risultati_web,
        "Istruzioni": istruzioni_locale if istruzioni_locale else ["Nessuna istruzione specifica trovata."],
        "Esempi_Storici": esempi_lavorazioni["DESCRIZIONE DETTAGLIATA"].tolist() or ["Nessun esempio disponibile per questa categoria."]
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

    # Visualizza i risultati web
    st.subheader("Risultati Web")
    if suggerimenti["Risultati Web"]:
        for risultato in suggerimenti["Risultati Web"]:
            st.write("- " + risultato)
    else:
        st.write("Nessun risultato trovato online.")

    # Visualizza le istruzioni
    st.subheader("Istruzioni dalla documentazione")
    for istruzione in suggerimenti["Istruzioni"]:
        st.write("- " + istruzione)

    # Visualizza gli esempi storici
    st.subheader("Esempi Storici")
    for esempio in suggerimenti["Esempi_Storici"]:
        st.write("- " + esempio)
