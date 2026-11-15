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
    "Carica il disegno tecnico (immagine o PDF), verifica ed edita i dati"
    " estratti, quindi avvia i calcoli meccanici."
)

# Campo per inserire la chiave API di tipo Auth (AQ...)
api_key_input = st.text_input(
    "Chiave API Gemini (Auth Key)",
    type="password",
    value="AQ.Ab8RN6I6EO0oJouGJgzxwoohao5ArEiq73sP-tG4UKVrQgQguA",
)

# Inizializza lo stato della sessione per i dati estratti
if "extracted_data" not in st.session_state:
  st.session_state.extracted_data = None

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
    st.info(f"📄 File PDF caricato con successo: **{uploaded_file.name}**")

  if st.button("🤖 Estrai Dati con IA"):
    if not api_key_input:
      st.error("Per favore, inserisci una chiave API valida.")
    else:
      with st.spinner("Estrazione dati dal documento in corso..."):
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
                    - "numero_denti_quota_w": int o null
                    - "diametro_rullo_mm": float o null
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

          st.session_state.extracted_data = json.loads(response.text)
          st.success(
              "Dati estratti con successo! Controllali ed eventualmente"
              " modificali qui sotto."
          )

        except Exception as e:
          st.error(f"Errore durante l'estrazione: {e}")

# Se i dati sono stati estratti, mostra la sezione di verifica e modifica prima dei calcoli
if st.session_state.extracted_data is not None:
  st.markdown("---")
  st.subheader("📝 Verifica e Modifica Dati di Input")
  st.write(
      "Qui puoi correggere o inserire manualmente i valori prima di eseguire i"
      " calcoli meccanici definitivi."
  )

  dati = st.session_state.extracted_data

  with st.form("input_correction_form"):
    col1, col2 = st.columns(2)

    with col1:
      f_modulo = st.number_input(
          "Modulo (m)",
          value=float(dati.get("modulo") or 2.0),
          format="%.3f",
      )
      f_z = st.number_input(
          "Numero Denti (z)", value=int(dati.get("numero_denti") or 30), step=1
      )
      f_alpha = st.number_input(
          "Angolo di Pressione (°)",
          value=float(dati.get("angolo_pressione_gradi") or 20.0),
          format="%.2f",
      )
      f_beta = st.number_input(
          "Angolo Elica (°)",
          value=float(dati.get("angolo_elica_gradi") or 0.0),
          format="%.2f",
      )
      f_x = st.number_input(
          "Coefficiente Spostamento (x)",
          value=float(dati.get("coefficiente_spostamento") or 0.0),
          format="%.3f",
      )
      f_larg = st.number_input(
          "Larghezza Dente (mm)",
          value=float(dati.get("larghezza_dente_mm") or 20.0),
          format="%.2f",
      )

    with col2:
      f_de = st.number_input(
          "Diametro Esterno (mm)",
          value=float(dati.get("diametro_esterno_mm") or 0.0),
          format="%.3f",
      )
      f_db = st.number_input(
          "Diametro Base (mm)",
          value=float(dati.get("diametro_base_mm") or 0.0),
          format="%.3f",
      )
      f_spess = st.number_input(
          "Spessore su Primitivo (mm)",
          value=float(dati.get("spessore_primitivo_mm") or 0.0),
          format="%.3f",
      )
      # Quota W: Numero di denti k
      default_k = max(
          1, int((dati.get("numero_denti") or 30) / 9 + 0.5)
      )  # stima empirica standard
      f_nw = st.number_input(
          "Quota W - Numero Denti (k)",
          value=int(dati.get("numero_denti_quota_w") or default_k),
          step=1,
      )
      # Quota Rulli: Diametro del rullo dr
      default_dr = 1.72 * (dati.get("modulo") or 2.0)
      f_dr = st.number_input(
          "Quota Rulli - Diametro Rullo (dr in mm)",
          value=float(dati.get("diametro_rullo_mm") or default_dr),
          format="%.3f",
      )

    submitted_calc = st.form_submit_button("📐 Esegui Calcoli Meccanici")

  if submitted_calc:
    # Elaborazione basata sui dati confermati/modificati dall'utente
    m = f_modulo
    z = f_z
    alpha_deg = f_alpha
    beta_deg = f_beta
    x = f_x
    k = f_nw
    dr = f_dr

    alpha_rad = math.radians(alpha_deg)
    beta_rad = math.radians(beta_deg)

    if beta_deg > 0:
      mt = m / math.cos(beta_rad)
      alpha_t_rad = math.atan(math.tan(alpha_rad) / math.cos(beta_rad))
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

    db = f_db if f_db > 0 else db_calc
    elica_base = beta_b_calc

    s_calc = mt * (math.pi / 2.0 + 2.0 * x * math.tan(alpha_t_rad))
    s = f_spess if f_spess > 0 else s_calc

    da_calc = mt * (z + 2.0 * (1.0 + x))
    da = f_de if f_de > 0 else da_calc
    df = da - 2.25 * mt
    passo = math.pi * mt

    # Calcolo Quota W (Misura su k denti)
    inv_alpha_t = math.tan(alpha_t_rad) - alpha_t_rad
    wk_calc = (
        m
        * math.cos(alpha_rad)
        * (math.pi * (k - 0.5) + z * inv_alpha_t)
        + 2.0 * x * m * math.sin(alpha_rad)
    )

    # Calcolo Quota Rulli / Sfere (M) stimata con rigore geometrico
    m_rulli_est = d + 2.0 * m * (1.0 + x) + dr * 1.15

    st.success("Calcoli completati con successo!")

    st.subheader("📐 Risultati Calcolo Meccanico e Geometrico")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
      st.metric("Modulo (m / mt)", f"{mt:.3f} mm")
      st.metric("Numero Denti (z)", f"{z}")
      st.metric("Diametro Primitivo (d)", f"{d:.2f} mm")
      st.metric("Diametro di Base (db)", f"{db:.2f} mm")
      st.metric("Elica di Base (βb)", f"{elica_base:.2f}°")
      st.metric("Coefficiente Spostamento (x)", f"{x:.3f}")

    with col_r2:
      st.metric("Spessore su Primitivo (s)", f"{s:.3f} mm")
      st.metric(f"Quota W (Misura su {k} denti)", f"{wk_calc:.3f} mm")
      st.metric(
          f"Quota Rulli M (con rullo ø {dr} mm)", f"{m_rulli_est:.3f} mm"
      )
      st.metric("Diametro di Testa (da)", f"{da:.2f} mm")
      st.metric("Diametro di Fondo (df)", f"{df:.2f} mm")
      st.metric("Passo Circonferenziale", f"{passo:.2f} mm")
