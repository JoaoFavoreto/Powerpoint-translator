class SlideTranslatorError(Exception):
    """Base exception for SlideTranslator"""

class TranslationError(SlideTranslatorError):
    """Error during translation process"""

class FileProcessingError(SlideTranslatorError):
    """Error during file processing"""

class ConfigurationError(SlideTranslatorError):
    """Error in application configuration"""
