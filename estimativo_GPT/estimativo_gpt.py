import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import streamlit as st
import requests
import openpyxl

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
        return response.json()
    else:
        print("Errore nella ricerca:", response.status_code, response.text)
        return None

# Funzione aggiornata per ottenere suggerimenti con CATEGORIA e DESCRIZIONE DETTAGLIATA
def suggerisci_lavorazioni(macroarea, ricerca_testuale):
    # Recupera le istruzioni per la macroarea
    istruzioni = dict_lavorazioni.get(macroarea, [])

    # Filtra le voci dello storico con la categoria selezionata
    esempi_lavorazioni = df_esempio[
        df_esempio['CATEGORIA'].str.contains(macroarea, case=False, na=False)
    ].dropna(subset=["DESCRIZIONE DETTAGLIATA"])

    # Cerca nel file delle istruzioni e nell'esempio storico usando il campo di testo
    risultati_istruzioni = [istr for istr in istruzioni if ricerca_testuale.lower() in istr.lower()]
    risultati_esempi = esempi_lavorazioni[esempi_lavorazioni['DESCRIZIONE DETTAGLIATA'].str.contains(ricerca_testuale, case=False, na=False)]

    # Se non ci sono abbastanza informazioni, effettua una ricerca web
    risultati_ricerca = []
    if not risultati_istruzioni and risultati_esempi.empty:
        risultati_bing = ricerca_web(f"{ricerca_testuale} computo metrico {macroarea}")
        if risultati_bing:
            risultati_ricerca = [item["snippet"] for item in risultati_bing["webPages"]["value"]]

    # Struttura i risultati in un dizionario
    risultato = {
        "Istruzioni": risultati_istruzioni,
        "Esempi_Storici": risultati_esempi["DESCRIZIONE DETTAGLIATA"].to_dict(orient="records"),
        "Risultati_Web": risultati_ricerca
    }
    return risultato

# Impostazioni per Streamlit
st.title("Assistente per Computi Metrici Estimativi")

# Selezione della macroarea
macroarea = st.selectbox("Seleziona la macroarea", list(dict_lavorazioni.keys()))

# Campo di ricerca testuale
ricerca_testuale = st.text_input("Cosa ti serve? Descrivi cosa stai cercando:")

# Bottone per ottenere i suggerimenti
if st.button("Ottieni suggerimenti"):
    # Ottiene i suggerimenti per la macroarea selezionata e il campo di testo
    suggerimenti = suggerisci_lavorazioni(macroarea, ricerca_testuale)

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

    # Visualizza i risultati della ricerca web
    st.subheader("Risultati Web")
    if suggerimenti["Risultati_Web"]:
        for risultato in suggerimenti["Risultati_Web"]:
            st.write("- " + risultato)
    else:
        st.write("Nessun risultato trovato online.")

