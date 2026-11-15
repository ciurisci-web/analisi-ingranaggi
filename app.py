import json
import math
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
    " estrarre i parametri geometrici avanzati ed eseguire i calcoli meccanici."
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
          "Analisi avanzata del documento in corso con intelligenza"
          " artificiale..."
      ):
        try:
          client = genai.Client(api_key=api_key_input)
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
                    - "diametro_base_mm": float o null
                    - "elica_base_gradi": float o null
                    - "coefficiente_spostamento": float o null
                    - "spessore_primitivo_mm": float o null
                    - "quota_wildhaber_mm": float o null
                    - "quota_rulli_mm": float o null
                    Se un valore non è esplicitamente indicato ma può essere dedotto o stimato con ragionevole certezza, segnalalo, altrimenti metti null.
                    """

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

          dati = json.loads(response.text)

          st.success("Analisi completata con successo!")

          with st.expander("🔍 Visualizza dati grezzi estratti (JSON)"):
            st.json(dati)

          # Estrazione dati primari
          m = dati.get("modulo")
          z = dati.get("numero_denti")

          if m and z:
            alpha_deg = dati.get("angolo_pressione_gradi") or 20.0
            beta_deg = dati.get("angolo_elica_gradi") or 0.0
            x = dati.get("coefficiente_spostamento")
            if x is None:
              x = 0.0

            alpha_rad = math.radians(alpha_deg)
            beta_rad = math.radians(beta_deg)

            # Calcoli geometrici e transizioni per ingranaggi cilindrici/elicoidali
            if beta_deg > 0:
              mt = m / math.cos(beta_rad)
              alpha_t_rad = math.atan(
                  math.tan(alpha_rad) / math.cos(beta_rad)
              )
              d = mt * z
              db_calc = d * math.cos(alpha_t_rad)
              beta_b_rad = math.asin(math.sin(beta_rad) * math.cos(alpha_rad))
              beta_b_calc = math.degrees(beta_b_rad)
            else:
              mt = m
              alpha_t_rad = alpha_rad
              d = m * z
              db_calc = d * math.cos(alpha_rad)
              beta_b_calc = 0.0

            # Assegnazione o calcolo automatico dei parametri avanzati
            db = dati.get("diametro_base_mm") or db_calc
            elica_base = dati.get("elica_base_gradi") or beta_b_calc
            s = dati.get("spessore_primitivo_mm") or mt * (
                math.pi / 2.0 + 2.0 * x * math.tan(alpha_t_rad)
            )

            # Quota Wildhaber (stimata tramite corda circolare se non presente)
            s_c = d * math.sin(s / d)
            quota_wildhaber = dati.get("quota_wildhaber_mm") or s_c

            # Quota Rulli (stima geometrica di riferimento se non presente)
            quota_rulli_est = (
                db + (mt * math.pi) / 2.0 + 2.0 * x * mt * math.tan(alpha_t_rad)
            )
            quota_rulli = dati.get("quota_rulli_mm") or quota_rulli_est

            da = (
                dati.get("diametro_esterno_mm")
                or mt * (z + 2.0 * (1.0 + x))
                or (d + 2 * mt)
            )
            df = da - 2.25 * mt
            passo = math.pi * mt

            # Visualizzazione risultati in metriche ordinate
            st.subheader("📐 Risultati Calcolo Meccanico e Geometrico")

            col1, col2 = st.columns(2)
            with col1:
              st.metric("Modulo (m / mt)", f"{mt:.3f} mm")
              st.metric("Numero Denti (z)", f"{z}")
              st.metric("Diametro Primitivo (d)", f"{d:.2f} mm")
              st.metric("Diametro di Base (db)", f"{db:.2f} mm")
              st.metric("Elica di Base (βb)", f"{elica_base:.2f}°")
              st.metric(
                  "Coefficiente Spostamento (x)", f"{x if x else '0.0'}"
              )

            with col2:
              st.metric("Spessore su Primitivo (s)", f"{s:.3f} mm")
              st.metric("Quota Wildhaber (Cordale)", f"{quota_wildhaber:.3f} mm")
              st.metric("Quota Rulli (M)", f"{quota_rulli:.3f} mm")
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
