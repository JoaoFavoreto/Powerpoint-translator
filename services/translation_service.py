from typing import Dict, Optional, Callable
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from core.config import settings
from core.models import TranslationRequest, TranslationResult, TranslationStyle
from core.exceptions import TranslationError
import json
import asyncio

class TranslationService:
    """Serviço de tradução usando LangChain"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.default_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key
        )
        self.fallback_llm = ChatOpenAI(
            model=settings.fallback_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key
        )
    
    def _create_system_prompt(self, request: TranslationRequest) -> str:
        """Cria o prompt do sistema para tradução"""
        
        style_instructions = {
            TranslationStyle.FORMAL_TECHNICAL: "mantenha um tom formal e técnico, preservando termos especializados",
            TranslationStyle.CASUAL: "use um tom casual e coloquial, adaptando para linguagem cotidiana", 
            TranslationStyle.ACADEMIC: "mantenha um registro acadêmico formal com precisão terminológica"
        }
        
        system_prompt = f"""Você é um tradutor profissional especializado em apresentações PowerPoint.

TAREFA: Traduzir textos de slides do {request.source_language} para {request.target_language}.

ESTILO: {style_instructions.get(request.style, style_instructions[TranslationStyle.FORMAL_TECHNICAL])}

REGRAS IMPORTANTES:
1. Preserve EXATAMENTE a estrutura JSON de entrada
2. Traduza apenas os valores, nunca as chaves
3. Mantenha formatação de números, datas e símbolos
4. Se um texto estiver vazio ou for apenas espaços, mantenha igual
5. Para textos muito curtos (1-2 palavras), considere o contexto dos textos vizinhos"""

        if request.glossary:
            glossary_text = "\n".join([f"- {term}: {translation}" for term, translation in request.glossary.items()])
            system_prompt += f"\n\nGLOSSÁRIO OBRIGATÓRIO:\n{glossary_text}\nUse sempre estas traduções específicas quando encontrar estes termos."
        
        return system_prompt
    
    def _create_human_prompt(self, texts: Dict[str, str]) -> str:
        """Cria o prompt do usuário com os textos para tradução"""
        
        return f"""Traduza os seguintes textos mantendo a estrutura JSON:

{json.dumps(texts, ensure_ascii=False, indent=2)}

Responda APENAS com o JSON traduzido, sem explicações adicionais."""
    
    async def translate_batch(
        self, 
        request: TranslationRequest, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TranslationResult:
        """Traduz um lote de textos de forma assíncrona"""
        
        try:
            # Filtrar textos vazios ou só espaços
            filtered_texts = {
                run_id: text for run_id, text in request.texts.items() 
                if text.strip()
            }
            
            if not filtered_texts:
                return TranslationResult(
                    translations=request.texts,  # Retorna os textos originais
                    success=True
                )
            
            system_message = SystemMessage(content=self._create_system_prompt(request))
            human_message = HumanMessage(content=self._create_human_prompt(filtered_texts))
            
            messages = [system_message, human_message]
            
            # Tentar com modelo principal
            try:
                response = await self.llm.agenerate([messages])
                result_text = response.generations[0][0].text.strip()
            except Exception as e:
                # Fallback para modelo secundário
                print(f"Erro com modelo principal, usando fallback: {e}")
                response = await self.fallback_llm.agenerate([messages])
                result_text = response.generations[0][0].text.strip()
            
            # Parse do resultado
            try:
                # Remover possíveis marcadores de código
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                
                translated_texts = json.loads(result_text)
                
                # Mesclar textos traduzidos com textos originais vazios
                final_translations = {}
                for run_id, original_text in request.texts.items():
                    if run_id in translated_texts:
                        final_translations[run_id] = translated_texts[run_id]
                    else:
                        final_translations[run_id] = original_text  # Manter texto original se vazio
                
                if progress_callback:
                    progress_callback(len(filtered_texts), len(filtered_texts))
                
                return TranslationResult(
                    translations=final_translations,
                    success=True
                )
                
            except json.JSONDecodeError as e:
                raise TranslationError(f"Erro ao decodificar resposta JSON: {e}")
            
        except Exception as e:
            return TranslationResult(
                translations={},
                success=False,
                errors=[str(e)]
            )
    
    def translate_sync(self, request: TranslationRequest) -> TranslationResult:
        """Versão síncrona da tradução"""
        return asyncio.run(self.translate_batch(request))
