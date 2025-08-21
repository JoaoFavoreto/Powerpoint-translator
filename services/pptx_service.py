from typing import Dict, List, Tuple, Optional
from pptx import Presentation
from pptx.shapes.base import BaseShape
from pptx.text.text import TextFrame, _Paragraph, _Run
import tempfile
import os

from core.models import TextRun
from core.exceptions import FileProcessingError

class PPTXService:
    """Serviço para processamento de arquivos PowerPoint"""
    
    def __init__(self):
        self.run_mapping: Dict[str, _Run] = {}
        self.text_mapping: Dict[str, str] = {}
        self.presentation: Optional[Presentation] = None
    
    def extract_texts(self, file_path: str) -> Dict[str, str]:
        """Extrai textos do PowerPoint mantendo referências dos runs"""
        
        try:
            # Carregar e manter referência da apresentação
            self.presentation = Presentation(file_path)
            self.run_mapping = {}
            self.text_mapping = {}
            
            run_counter = 0
            
            for slide_idx, slide in enumerate(self.presentation.slides):
                for shape in slide.shapes:
                    if hasattr(shape, "text_frame") and shape.text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if run.text.strip():  # Apenas runs com texto
                                    run_id = f"run_{run_counter}"
                                    self.run_mapping[run_id] = run
                                    self.text_mapping[run_id] = run.text
                                    run_counter += 1
            
            return self.text_mapping
            
        except Exception as e:
            raise FileProcessingError(f"Erro ao extrair textos do PowerPoint: {e}")
    
    def get_text_runs_info(self) -> List[TextRun]:
        """Retorna informações detalhadas sobre os runs de texto"""
        
        runs_info = []
        
        for run_id, run in self.run_mapping.items():
            text_run = TextRun(
                id=run_id,
                text=run.text,
                is_bold=run.font.bold if run.font.bold is not None else False,
                is_italic=run.font.italic if run.font.italic is not None else False,
                font_name=run.font.name,
                font_size=run.font.size.pt if run.font.size else None
            )
            runs_info.append(text_run)
        
        return runs_info
    
    def apply_translations(self, translations: Dict[str, str]) -> None:
        """Aplica as traduções aos runs originais"""
        
        try:
            for run_id, translated_text in translations.items():
                if run_id in self.run_mapping:
                    original_run = self.run_mapping[run_id]
                    original_run.text = translated_text
        except Exception as e:
            raise FileProcessingError(f"Erro ao aplicar traduções: {e}")
    
    def save_presentation(self, original_path: str, output_path: str) -> str:
        """Salva a apresentação traduzida"""
        
        try:
            if self.presentation is None:
                raise FileProcessingError("Nenhuma apresentação carregada. Execute extract_texts primeiro.")
            
            # Salvar a apresentação com as modificações já aplicadas
            self.presentation.save(output_path)
            return output_path
            
        except Exception as e:
            raise FileProcessingError(f"Erro ao salvar apresentação: {e}")
    
    def create_temp_file(self, original_filename: str) -> str:
        """Cria um arquivo temporário para a apresentação traduzida"""
        
        try:
            # Extrair nome base e extensão
            name, ext = os.path.splitext(original_filename)
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_translated{ext}",
                prefix=f"{name}_"
            )
            
            return temp_file.name
            
        except Exception as e:
            raise FileProcessingError(f"Erro ao criar arquivo temporário: {e}")
    
    def get_presentation_stats(self, file_path: str) -> Dict[str, int]:
        """Retorna estatísticas da apresentação"""
        
        try:
            prs = Presentation(file_path)
            
            total_slides = len(prs.slides)
            total_shapes = 0
            total_text_runs = 0
            total_characters = 0
            
            for slide in prs.slides:
                for shape in slide.shapes:
                    total_shapes += 1
                    if hasattr(shape, "text_frame") and shape.text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if run.text.strip():
                                    total_text_runs += 1
                                    total_characters += len(run.text)
            
            return {
                "slides": total_slides,
                "shapes": total_shapes,
                "text_runs": total_text_runs,
                "characters": total_characters
            }
            
        except Exception as e:
            raise FileProcessingError(f"Erro ao obter estatísticas: {e}")
