from typing import Dict, Optional, Callable, Any
from langchain.chains.base import Chain
from langchain.schema import BaseOutputParser
from pydantic import Extra
import asyncio
import os

from services.translation_service import TranslationService
from services.pptx_service import PPTXService
from core.models import TranslationRequest, TranslationStyle

class TranslationOutputParser(BaseOutputParser):
    """Parser personalizado para resultados de tradução"""
    
    def parse(self, text: str) -> Dict[str, str]:
        """Parse do resultado da tradução"""
        # Implementação básica - pode ser expandida
        return {"result": text}

class PowerPointTranslationChain(Chain):
    """Chain principal para tradução de PowerPoint usando LangChain"""
    
    translation_service: TranslationService
    pptx_service: PPTXService
    output_parser: TranslationOutputParser
    
    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.forbid
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        # Inicializar os serviços antes de chamar super()
        translation_service = TranslationService()
        pptx_service = PPTXService()
        output_parser = TranslationOutputParser()
        
        # Passar os serviços para o kwargs
        kwargs.update({
            'translation_service': translation_service,
            'pptx_service': pptx_service,
            'output_parser': output_parser
        })
        
        super().__init__(**kwargs)
    
    @property
    def input_keys(self) -> list[str]:
        return ["file_path", "target_language", "source_language", "style", "glossary"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["translated_file_path", "stats", "success", "errors"]
    
    def _call(
        self, 
        inputs: Dict[str, Any],
        run_manager = None
    ) -> Dict[str, Any]:
        """Executa a chain de tradução"""
        
        try:
            # Extrair parâmetros
            file_path = inputs["file_path"]
            target_language = inputs["target_language"]
            source_language = inputs.get("source_language", "auto")
            style = inputs.get("style", TranslationStyle.FORMAL_TECHNICAL)
            glossary = inputs.get("glossary", {})
            progress_callback = inputs.get("progress_callback")
            
            # 1. Extrair textos do PowerPoint
            texts = self.pptx_service.extract_texts(file_path)
            
            if not texts:
                return {
                    "translated_file_path": file_path,
                    "stats": {"total_texts": 0, "translated": 0},
                    "success": True,
                    "errors": []
                }
            
            # 2. Preparar requisição de tradução
            translation_request = TranslationRequest(
                texts=texts,
                target_language=target_language,
                source_language=source_language,
                style=style,
                glossary=glossary
            )
            
            # 3. Traduzir textos
            if progress_callback:
                progress_callback(0, len(texts), "Iniciando tradução...")
            
            translation_result = asyncio.run(self.translation_service.translate_batch(translation_request))
            
            if not translation_result.success:
                return {
                    "translated_file_path": "",
                    "stats": {"total_texts": len(texts), "translated": 0},
                    "success": False,
                    "errors": translation_result.errors
                }
            
            # 4. Aplicar traduções
            if progress_callback:
                progress_callback(len(texts), len(texts), "Aplicando traduções...")
            
            self.pptx_service.apply_translations(translation_result.translations)
            
            # 5. Salvar arquivo traduzido
            output_path = self.pptx_service.create_temp_file(
                os.path.basename(file_path)
            )
            
            translated_file_path = self.pptx_service.save_presentation(file_path, output_path)
            
            # 6. Obter estatísticas
            stats = self.pptx_service.get_presentation_stats(file_path)
            stats.update({
                "total_texts": len(texts),
                "translated": len([t for t in translation_result.translations.values() if t.strip()]),
                "errors": len(translation_result.errors)
            })
            
            if progress_callback:
                progress_callback(len(texts), len(texts), "Tradução concluída!")
            
            return {
                "translated_file_path": translated_file_path,
                "stats": stats,
                "success": True,
                "errors": translation_result.errors
            }
            
        except Exception as e:
            error_msg = str(e)
            if progress_callback:
                progress_callback(0, 1, f"Erro: {error_msg}")
            
            return {
                "translated_file_path": "",
                "stats": {"total_texts": 0, "translated": 0},
                "success": False,
                "errors": [error_msg]
            }
