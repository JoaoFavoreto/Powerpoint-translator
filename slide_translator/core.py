# slide_translator/core.py
from pptx import Presentation
from .pptx_processor import extract_paragraphs_with_run_mapping
from .translator import translate_text_batch
import os
import re

def create_formatted_text_with_markers(original_runs: list) -> str:
    """
    Creates a single text string with special markers indicating formatting changes.
    
    Args:
        original_runs: List of run objects from a paragraph
        
    Returns:
        A string with formatting markers like <BOLD_START>text<BOLD_END>
    """
    if not original_runs:
        return ""
    
    result = ""
    current_bold = None
    current_italic = None
    
    for run in original_runs:
        if not run.text:
            continue
            
        # Check if formatting changed
        run_bold = run.font.bold if run.font.bold is not None else False
        run_italic = run.font.italic if run.font.italic is not None else False
        
        # Handle bold formatting changes
        if run_bold != current_bold:
            if run_bold:
                result += "<BOLD_START>"
            else:
                result += "<BOLD_END>"
            current_bold = run_bold
        
        # Handle italic formatting changes  
        if run_italic != current_italic:
            if run_italic:
                result += "<ITALIC_START>"
            else:
                result += "<ITALIC_END>"
            current_italic = run_italic
        
        result += run.text
    
    # Close any open formatting at the end
    if current_bold:
        result += "<BOLD_END>"
    if current_italic:
        result += "<ITALIC_END>"
    
    return result

def apply_formatted_text_to_runs(original_runs: list, translated_text_with_markers: str) -> None:
    """
    Applies translated text with formatting markers back to the original runs.
    
    Args:
        original_runs: List of original run objects
        translated_text_with_markers: Translated text containing formatting markers
    """
    if not original_runs:
        return
    
    # Clear all runs first
    for run in original_runs:
        run.text = ""
    
    # If we only have one run, just put everything there and return
    if len(original_runs) == 1:
        # Remove all markers and put clean text
        clean_text = translated_text_with_markers
        for marker in ["<BOLD_START>", "<BOLD_END>", "<ITALIC_START>", "<ITALIC_END>"]:
            clean_text = clean_text.replace(marker, "")
        original_runs[0].text = clean_text
        return
    
    # Parse the marked text and apply to runs
    import re
    
    # Split by formatting markers while keeping the markers
    parts = re.split(r'(<BOLD_START>|<BOLD_END>|<ITALIC_START>|<ITALIC_END>)', translated_text_with_markers)
    
    current_bold = False
    current_italic = False
    current_run_idx = 0
    
    for part in parts:
        if part == "<BOLD_START>":
            current_bold = True
        elif part == "<BOLD_END>":
            current_bold = False
        elif part == "<ITALIC_START>":
            current_italic = True
        elif part == "<ITALIC_END>":
            current_italic = False
        elif part.strip():  # Actual text content
            # Find the best run to put this text in
            if current_run_idx < len(original_runs):
                run = original_runs[current_run_idx]
                run.text = part
                
                # Apply formatting
                if run.font.bold is not None:
                    run.font.bold = current_bold
                if run.font.italic is not None:
                    run.font.italic = current_italic
                
                current_run_idx += 1

def process_presentation(input_filepath: str, output_filepath: str, target_language: str):
    """
    Orchestrates the entire presentation translation process using paragraph-level
    translation with formatting markers to preserve both context and formatting.

    Args:
        input_filepath: Path to the source .pptx file.
        output_filepath: Path where the translated .pptx file will be saved.
        target_language: The language to translate the content into.
    """
    print(f"Loading presentation from: {input_filepath}")
    prs = Presentation(input_filepath)

    print("Extracting text paragraphs with formatting markers...")
    # Get paragraph texts and their corresponding runs
    paragraph_texts, paragraph_runs = extract_paragraphs_with_run_mapping(prs)

    # Create marked text for translation
    texts_to_translate = {}
    for para_id, runs in paragraph_runs.items():
        marked_text = create_formatted_text_with_markers(runs)
        if marked_text.strip():
            texts_to_translate[para_id] = marked_text

    if not texts_to_translate:
        print("No text found in the presentation. Saving a copy of the original.")
        prs.save(output_filepath)
        return

    print(f"Found {len(texts_to_translate)} paragraphs to translate.")
    
    print(f"Translating texts to {target_language} in a single batch...")
    # Translate text with formatting markers
    translated_paragraphs = translate_text_batch(texts_to_translate, target_language)
    print("Translation complete.")

    print("Applying translated text with preserved formatting...")
    # Apply translated text with formatting back to runs
    for para_id, translated_marked_text in translated_paragraphs.items():
        if para_id in paragraph_runs:
            original_runs = paragraph_runs[para_id]
            apply_formatted_text_to_runs(original_runs, translated_marked_text)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Saving translated presentation to: {output_filepath}")
    prs.save(output_filepath)
    print("Process completed successfully.")
