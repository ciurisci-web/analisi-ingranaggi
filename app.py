import json
import streamlit as st
import PIL.Image
from google import genai
from google.genai import types

# Configurazione della pagina
st.set_page_config(
    page_title="Analisi Ingranaggi AI", page_icon="⚙️", layout="centered"
)

st.title("⚙️ Analisi Ingranaggio con Gemini AI")
st.write(
    "Carica il disegno tecnico in formato **immagine (JPG/PNG)** o **PDF** per"
    " estrarre i parametri geometrici ed eseguire i calcoli meccanici in tempo"
    " reale."
)

# Campo per inserire la chiave API di tipo Auth (AQ...)
api_key_input = st.text_input(
    "Chiave API Gemini (Auth Key)",
    type="password",
    value="AQ.Ab8RN6I6EO0oJouGJgzxwoohao5ArEiq73sP-tG4UKVrQgQguA",
)

# Pulsante nativo per caricare file (immagini o PDF)
uploaded_file = st.file_uploader(
    "Scegli il file del disegno (JPG, PNG o PDF)",
    type=["jpg", "jpeg", "png", "pdf"],
)

if uploaded_file is not None:
  mime_type = uploaded_file.type

  # Mostra l'anteprima o le informazioni in base al tipo di file
  if mime_type in ["image/jpeg", "image/png"]:
    st.image(uploaded_file, caption="Disegno caricato (Immagine)", width="stretch")
  elif mime_type == "application/pdf":
    st.info(
        f"📄 File PDF caricato con successo: **{uploaded_file.name}**"
        " (Pronto per l'analisi nativa)"
    )

  if st.button("🚀 Avvia Analisi e Calcoli"):
    if not api_key_input:
      st.error("Per favore, inserisci una chiave API valida.")
    else:
      with st.spinner(
          "Analisi del documento in corso con intelligenza artificiale..."
      ):
        try:
          # Inizializza il client ufficiale Google GenAI
          client = genai.Client(api_key=api_key_input)

          # Legge i byte del file (funziona sia per immagini che per PDF)
          file_bytes = uploaded_file.getvalue()

          prompt = """
                    Analizza questo disegno tecnico o documento di un ingranaggio meccanico. 
                    Estrai i parametri geometrici principali e restituisci ESCLUSIVAMENTE un oggetto JSON valido con le seguenti chiavi esatte:
                    - "modulo": float o null
                    - "numero_denti": int o null
                    - "angolo_pressione_gradi": float o null
                    - "diametro_esterno_mm": float o null
                    - "larghezza_dente_mm": float o null
                    - "angolo_elica_gradi": float o 0
                    Se un valore non è esplicitamente indicato ma può essere dedotto o stimato con ragionevole certezza, segnalalo, altrimenti metti null.
                    """

          # Invoca il modello gemini-3.8-flash passando i byte e il mimetype corretto (immagine o PDF)
          response = client.models.generate_content(
              model="gemini-3.8-flash",
              contents=[
                  prompt,
                  types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
              ],
              config=types.GenerateContentConfig(
                  response_mime_type="application/json", temperature=0.1
              ),
          )

          # Estrae il testo della risposta
          text_output = response.text
          dati = json.loads(text_output)

          st.success("Analisi completata con successo!")

          # Mostra i dati grezzi estratti in formato JSON espandibile
          with st.expander("🔍 Visualizza dati grezzi estratti (JSON)"):
            st.json(dati)

          # Estrazione dati per i calcoli geometrici
          m = dati.get("modulo")
          z = dati.get("numero_denti")

          if m and z:
            d = m * z
            da = m * (z + 2)
            df = m * (z - 2.5)
            passo = 3.14159 * m

            st.subheader("📐 Risultati Calcolo Meccanico")
            col1, col2 = st.columns(2)
            with col1:
              st.metric("Modulo (m)", f"{m} mm")
              st.metric("Numero Denti (z)", f"{z}")
              st.metric("Diametro Primitivo (d)", f"{d:.2f} mm")
            with col2:
              st.metric("Diametro di Testa (da)", f"{da:.2f} mm")
              st.metric("Diametro di Fondo (df)", f"{df:.2f} mm")
              st.metric("Passo Circonferenziale", f"{passo:.2f} mm")
          else:
            st.warning(
                "Impossibile completare i calcoli geometrici: modulo o numero di"
                " denti non sono stati rilevati chiaramente dall'IA."
            )

        except Exception as e:
          st.error(f"Errore durante l'elaborazione della richiesta: {e}")
