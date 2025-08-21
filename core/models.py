from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

class TranslationStyle(str, Enum):
    FORMAL_TECHNICAL = "formal_technical"
    CASUAL = "casual"
    ACADEMIC = "academic"

class TextRun(BaseModel):
    id: str
    text: str
    is_bold: bool = False
    is_italic: bool = False
    font_name: Optional[str] = None
    font_size: Optional[float] = None

class TranslationRequest(BaseModel):
    texts: Dict[str, str]  # {run_id: text}
    target_language: str
    source_language: str = "auto"
    style: TranslationStyle = TranslationStyle.FORMAL_TECHNICAL
    glossary: Optional[Dict[str, str]] = None  # {term: translation}

class TranslationResult(BaseModel):
    translations: Dict[str, str]  # {run_id: translated_text}
    success: bool = True
    errors: List[str] = []
