import os
import tempfile
from typing import Optional

def ensure_directory(directory_path: str) -> None:
    """Garante que um diretório existe, criando se necessário"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def get_file_extension(filename: str) -> str:
    """Retorna a extensão do arquivo"""
    return os.path.splitext(filename)[1].lower()

def is_powerpoint_file(filename: str) -> bool:
    """Verifica se o arquivo é um PowerPoint válido"""
    valid_extensions = ['.pptx', '.ppt']
    return get_file_extension(filename) in valid_extensions

def create_temp_file(original_filename: str, suffix: str = "_translated") -> str:
    """Cria um arquivo temporário baseado no nome original"""
    name, ext = os.path.splitext(original_filename)
    
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f"{suffix}{ext}",
        prefix=f"{name}_"
    )
    
    return temp_file.name

def cleanup_temp_file(file_path: str) -> None:
    """Remove arquivo temporário"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Ignorar erros de cleanup

def format_file_size(size_bytes: int) -> str:
    """Formata o tamanho do arquivo para exibição"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"
