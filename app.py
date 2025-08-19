# app.py
import streamlit as st
from slide_translator.core import process_presentation
import os
import tempfile
from datetime import datetime

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="SlideTranslator",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

# --- Main Application UI ---
st.title("SlideTranslator 🤖")
st.markdown("Traduza suas apresentações `.pptx` com IA, preservando a formatação original.")

# --- Language Selection ---
# A more comprehensive list of languages
LANGUAGES = {
    "English": "Inglês",
    "Spanish": "Espanhol",
    "French": "Francês",
    "German": "Alemão",
    "Portuguese (Brazil)": "Português (Brasil)",
    "Italian": "Italiano",
    "Japanese": "Japonês",
    "Chinese (Simplified)": "Chinês (Simplificado)",
    "Russian": "Russo",
    "Korean": "Coreano",
}
# We display the friendly name but pass the key (English name) to the API
target_language_display = st.selectbox(
    "Selecione o Idioma de Destino",
    options=list(LANGUAGES.values())
)
# Find the key corresponding to the selected value
target_language = [key for key, value in LANGUAGES.items() if value == target_language_display][0]


# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Faça o upload do seu arquivo `.pptx`",
    type=["pptx"],
    help="Apenas arquivos do tipo PowerPoint (.pptx) são aceitos."
)

# --- Translate Button and Process ---
if st.button("Traduzir Apresentação", type="primary", disabled=(uploaded_file is None)):
    if uploaded_file is not None:
        with st.spinner("Tradução em andamento... Isso pode levar alguns minutos. ⏳"):
            try:
                # Create temporary files to handle the upload and output
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name

                # Define a unique output filename
                original_filename = os.path.splitext(uploaded_file.name)[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"translated_{original_filename}_{timestamp}.pptx"
                
                # Use a temporary directory for the output file
                output_dir = tempfile.gettempdir()
                output_path = os.path.join(output_dir, output_filename)

                # --- Core Logic Execution ---
                process_presentation(input_path, output_path, target_language)
                # --- End of Core Logic ---

                st.success("Apresentação traduzida com sucesso! 🎉")

                # Provide the download link
                with open(output_path, "rb") as file:
                    st.download_button(
                        label=f"Baixar {output_filename}",
                        data=file,
                        file_name=output_filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )

            except Exception as e:
                st.error(f"Ocorreu um erro durante o processo: {e}")
                st.error("Por favor, verifique sua chave de API no arquivo .env e tente novamente.")
            
            finally:
                # Clean up temporary files
                if 'input_path' in locals() and os.path.exists(input_path):
                    os.remove(input_path)
                # The output file will be cleaned up by the OS eventually, 
                # but it's needed for the download button to work.
    else:
        st.warning("Por favor, faça o upload de um arquivo antes de traduzir.")

# --- Instructions and Footer ---
st.markdown("---")
st.subheader("Como Funciona")
st.info(
    """
    1.  **Faça o Upload:** Escolha um arquivo `.pptx` do seu computador.
    2.  **Selecione o Idioma:** Escolha para qual idioma você deseja traduzir.
    3.  **Clique em Traduzir:** A IA irá processar todos os textos (títulos, parágrafos, tabelas, notas) e os traduzirá.
    4.  **Baixe o Resultado:** Um novo arquivo será gerado com o texto traduzido, mantendo o layout e design intactos.
    """
)
st.warning(
    "**Importante:** Certifique-se de que você tem um arquivo `.env` na raiz do projeto com sua `OPENAI_API_KEY` válida.",
    icon="⚠️"
)
