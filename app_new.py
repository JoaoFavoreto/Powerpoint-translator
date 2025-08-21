import streamlit as st
import tempfile
import os
from datetime import datetime
from typing import Dict, Optional

from chains.translation_chain import PowerPointTranslationChain
from core.models import TranslationStyle
from core.config import settings
from utils.file_utils import is_powerpoint_file, format_file_size, cleanup_temp_file

# Configuração da página
st.set_page_config(
    page_title=settings.app_name,
    page_icon="🔤",
    layout="centered",
    initial_sidebar_state="auto",
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .upload-box {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Interface principal
st.markdown('<h1 class="main-header">🔤 SlideTranslator Pro</h1>', unsafe_allow_html=True)
st.markdown("**Traduza suas apresentações PowerPoint com IA mantendo a formatação perfeita**")

# Sidebar para configurações
st.sidebar.title("⚙️ Configurações")

# Seleção de idiomas
LANGUAGES = {
    "English": "🇺🇸 Inglês",
    "Spanish": "🇪🇸 Espanhol", 
    "French": "🇫🇷 Francês",
    "German": "🇩🇪 Alemão",
    "Portuguese (Brazil)": "🇧🇷 Português (Brasil)",
    "Italian": "🇮🇹 Italiano",
    "Japanese": "🇯🇵 Japonês",
    "Chinese (Simplified)": "🇨🇳 Chinês (Simplificado)",
    "Russian": "🇷🇺 Russo",
    "Korean": "🇰🇷 Coreano",
}

target_language_display = st.sidebar.selectbox(
    "🎯 Idioma de destino:",
    options=list(LANGUAGES.values()),
    index=0
)

# Encontrar a chave correspondente
target_language = [key for key, value in LANGUAGES.items() if value == target_language_display][0]

# Estilo de tradução
style_options = {
    TranslationStyle.FORMAL_TECHNICAL: "🎓 Formal/Técnico",
    TranslationStyle.CASUAL: "💬 Casual",
    TranslationStyle.ACADEMIC: "📚 Acadêmico"
}

translation_style = st.sidebar.selectbox(
    "📝 Estilo de tradução:",
    options=list(style_options.keys()),
    format_func=lambda x: style_options[x],
    index=0
)

# Glossário personalizado
st.sidebar.subheader("📖 Glossário Personalizado")
glossary_text = st.sidebar.text_area(
    "Termos específicos (um por linha: 'termo -> tradução'):",
    placeholder="API -> Interface de Programação\nCloud -> Nuvem\nSoftware -> Software",
    height=100
)

# Processar glossário
glossary: Dict[str, str] = {}
if glossary_text:
    for line in glossary_text.strip().split('\n'):
        if '->' in line:
            parts = line.split('->', 1)
            if len(parts) == 2:
                term = parts[0].strip()
                translation = parts[1].strip()
                if term and translation:
                    glossary[term] = translation

# Upload de arquivo
st.subheader("📁 Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Selecione seu arquivo PowerPoint:",
    type=["pptx"],
    help="Apenas arquivos .pptx são suportados",
)

if uploaded_file is not None:
    # Informações do arquivo
    file_size = len(uploaded_file.getvalue())
    st.info(f"📊 **{uploaded_file.name}** - {format_file_size(file_size)}")
    
    # Validação do arquivo
    if not is_powerpoint_file(uploaded_file.name):
        st.error("❌ Por favor, faça upload apenas de arquivos PowerPoint (.pptx)")
        st.stop()
    
    # Botão de tradução
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        translate_button = st.button(
            "🚀 Traduzir Apresentação",
            type="primary",
            use_container_width=True
        )
    
    if translate_button:
        if not settings.openai_api_key:
            st.error("❌ Chave da API OpenAI não configurada. Verifique suas variáveis de ambiente.")
            st.stop()
        
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        try:
            # Mostrar configurações selecionadas
            with st.expander("🔧 Configurações Aplicadas", expanded=False):
                st.write(f"**Idioma de destino:** {target_language_display}")
                st.write(f"**Estilo:** {style_options[translation_style]}")
                if glossary:
                    st.write("**Glossário personalizado:**")
                    for term, translation in glossary.items():
                        st.write(f"- {term} → {translation}")
                else:
                    st.write("**Glossário:** Não utilizado")
            
            # Inicializar a chain de tradução
            translation_chain = PowerPointTranslationChain()
            
            # Container para progresso
            progress_container = st.container()
            
            with progress_container:
                st.subheader("⚡ Progresso da Tradução")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current: int, total: int, message: str = ""):
                    if total > 0:
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"{message} ({current}/{total})")
                
                # Executar tradução
                result = translation_chain._call({
                    "file_path": temp_file_path,
                    "target_language": target_language,
                    "source_language": "auto",
                    "style": translation_style,
                    "glossary": glossary,
                    "progress_callback": update_progress
                })
                
                # Verificar sucesso
                if result["success"]:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Tradução concluída com sucesso!")
                    
                    # Estatísticas
                    stats = result["stats"]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📄 Slides", stats.get("slides", 0))
                    with col2:
                        st.metric("🔤 Textos", stats.get("total_texts", 0))
                    with col3:
                        st.metric("✅ Traduzidos", stats.get("translated", 0))
                    with col4:
                        st.metric("❌ Erros", len(result.get("errors", [])))
                    
                    # Download do arquivo traduzido
                    if os.path.exists(result["translated_file_path"]):
                        with open(result["translated_file_path"], "rb") as file:
                            file_data = file.read()
                        
                        # Nome do arquivo de saída
                        base_name = os.path.splitext(uploaded_file.name)[0]
                        output_filename = f"{base_name}_translated_{target_language.lower().replace(' ', '_')}.pptx"
                        
                        st.download_button(
                            label="📥 Baixar Apresentação Traduzida",
                            data=file_data,
                            file_name=output_filename,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            type="primary",
                            use_container_width=True
                        )
                        
                        # Limpar arquivo temporário traduzido
                        cleanup_temp_file(result["translated_file_path"])
                    
                    # Mostrar erros se houver
                    if result.get("errors"):
                        with st.expander("⚠️ Avisos e Erros", expanded=False):
                            for error in result["errors"]:
                                st.warning(f"⚠️ {error}")
                
                else:
                    progress_bar.progress(0)
                    status_text.text("❌ Erro na tradução")
                    
                    st.error("❌ Ocorreu um erro durante a tradução:")
                    for error in result.get("errors", ["Erro desconhecido"]):
                        st.error(f"• {error}")
                
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")
            
        finally:
            # Limpar arquivo temporário original
            cleanup_temp_file(temp_file_path)

else:
    # Instruções quando nenhum arquivo foi carregado
    st.markdown("""
    ### 👋 Como usar:
    
    1. **📁 Faça upload** do seu arquivo PowerPoint (.pptx)
    2. **🎯 Escolha o idioma** de destino na barra lateral
    3. **📝 Selecione o estilo** de tradução (formal, casual ou acadêmico)
    4. **📖 Adicione termos** ao glossário personalizado (opcional)
    5. **🚀 Clique em traduzir** e aguarde o processamento
    6. **📥 Baixe** sua apresentação traduzida!
    
    ### ✨ Recursos:
    - 🎨 **Preserva formatação** original (cores, fontes, layouts)
    - 🧠 **IA avançada** para traduções contextuais
    - 📖 **Glossário personalizado** para termos específicos
    - 🎯 **Múltiplos estilos** de tradução
    - ⚡ **Processamento rápido** e eficiente
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    f"Powered by {settings.app_name} | OpenAI GPT-4 | LangChain"
    "</div>", 
    unsafe_allow_html=True
)
