import base64
import json
import urllib.error
import urllib.request
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Analisi Ingranaggi AI", page_icon="⚙️", layout="centered"
)

st.title("⚙️ Analisi Ingranaggio con Gemini AI")
st.write(
    "Carica il disegno tecnico (blueprint) di un ingranaggio per estrarre i"
    " parametri geometrici ed eseguire i calcoli meccanici in tempo reale."
)

# Campo per inserire la chiave API o il token
api_key_input = st.text_input(
    "Chiave API Gemini / Token",
    type="password",
    value="AQ.Ab8RN6KJaaLdmFug342-gyeYIRsxj_-NRQmErz-Nfl_qgRVapQ",
)

# Pulsante nativo per caricare l'immagine
uploaded_file = st.file_uploader(
    "Scegli l'immagine del disegno (JPG o PNG)", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  # Mostra l'anteprima dell'immagine caricata
  st.image(uploaded_file, caption="Disegno caricato", width="stretch")

  if st.button("🚀 Avvia Analisi e Calcoli"):
    if not api_key_input:
      st.error("Per favore, inserisci una chiave API valida.")
    else:
      with st.spinner(
          "Analisi del disegno in corso con l'intelligenza artificiale..."
      ):
        try:
          # Legge i byte dell'immagine direttamente dal caricamento web
          image_bytes = uploaded_file.getvalue()
          image_base64 = base64.b64encode(image_bytes).decode("utf-8")
          mime_type = uploaded_file.type

          # Endpoint con il modello stabile gemini-1.5-flash
          url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key_input}"

          prompt = """
                    Analizza questo disegno tecnico di un ingranaggio meccanico. 
                    Estrai i parametri geometrici principali e restituisci ESCLUSIVAMENTE un oggetto JSON valido con le seguenti chiavi esatte:
                    - "modulo": float o null
                    - "numero_denti": int o null
                    - "angolo_pressione_gradi": float o null
                    - "diametro_esterno_mm": float o null
                    - "larghezza_dente_mm": float o null
                    - "angolo_elica_gradi": float o 0
                    Se un valore non è esplicitamente indicato ma può essere dedotto o stimato con ragionevole certezza, segnalalo, altrimenti metti null.
                    """

          payload = {
              "contents": [{
                  "parts": [
                      {"text": prompt},
                      {
                          "inline_data": {
                              "mime_type": mime_type,
                              "data": image_base64,
                          }
                      },
                  ]
              }],
              "generationConfig": {
                  "responseMimeType": "application/json",
                  "temperature": 0.1,
              },
          }

          req = urllib.request.Request(
              url,
              data=json.dumps(payload).encode("utf-8"),
              headers={"Content-Type": "application/json"},
              method="POST",
          )

          with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            text_output = res_data["candidates"][0]["content"]["parts"][0][
                "text"
            ]
            dati = json.loads(text_output)

          st.success("Analisi completata con successo!")

          # Mostra i dati grezzi estratti in formato JSON espandibile
          with st.expander("🔍 Visualizza dati grezzi estratti (JSON)"):
            st.json(dati)

          # Estrazione dati per i calcoli
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

        except urllib.error.HTTPError as e:
          # Cattura e mostra il testo esatto dell'errore restituito da Google
          error_details = e.read().decode("utf-8")
          st.error(
              f"Errore HTTP {e.code} dal server di Google:\n\n{error_details}"
          )
        except Exception as e:
          st.error(f"Errore imprevisto durante l'elaborazione: {e}")
