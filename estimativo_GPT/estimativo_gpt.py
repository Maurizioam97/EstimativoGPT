import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import streamlit as st
import openpyxl

# Scarica le risorse di NLTK se necessario
nltk.download('punkt')
nltk.download('wordnet')

# Percorso dei file
path_istruzioni = r"C:\Users\mauri\Documents\estimativo GPT\istruzioni estimativo.xls"
path_esempio = r"C:\Users\mauri\Documents\estimativo GPT\esempio.xls"

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

# Funzione aggiornata per ottenere suggerimenti con CATEGORIA e DESCRIZIONE DETTAGLIATA
def suggerisci_lavorazioni(macroarea):
    # Recupera le istruzioni per la macroarea
    istruzioni = dict_lavorazioni.get(macroarea, [])

    # Filtra le voci dello storico con la categoria selezionata
    esempi_lavorazioni = df_esempio[
        df_esempio['CATEGORIA'].str.contains(macroarea, case=False, na=False)
    ].dropna(subset=["DESCRIZIONE DETTAGLIATA"])

    # Struttura i risultati in un dizionario
    risultato = {
        "Istruzioni": istruzioni,
        "Esempi_Storici": esempi_lavorazioni[["DESCRIZIONE DETTAGLIATA"]].to_dict(orient="records")
    }
    return risultato

# Impostazioni per Streamlit
st.title("Assistente per Computi Metrici Estimativi")

# Selezione della macroarea
macroarea = st.selectbox("Seleziona la macroarea", list(dict_lavorazioni.keys()))

# Bottone per ottenere i suggerimenti
if st.button("Ottieni suggerimenti"):
    # Ottiene i suggerimenti per la macroarea selezionata
    suggerimenti = suggerisci_lavorazioni(macroarea)

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
            st.write("- " + esempio["DESCRIZIONE DETTAGLIATA"])
    else:
        st.write("Nessun esempio disponibile per questa categoria.")

