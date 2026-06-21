"""
Prompt Template Loader

This module provides utilities for loading and managing prompt templates.
"""

import os
from pathlib import Path
from typing import Optional, Dict


class PromptLoader:
    """Load prompt templates from the prompts directory"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the prompt loader
        
        Args:
            base_dir (str, optional): Base directory for prompts. 
                                     Defaults to src/prompts
        """
        if base_dir is None:
            # Default to src/prompts directory
            current_file = Path(__file__)
            self.base_dir = current_file.parent
        else:
            self.base_dir = Path(base_dir)
    
    def load_template(self, template_path: str) -> str:
        """
        Load a prompt template from a file
        
        Args:
            template_path (str): Relative path to template file from prompts directory
                                Example: 'ocr/ui_elements_extraction.md'
        
        Returns:
            str: Content of the template file
        
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        full_path = self.base_dir / template_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Template not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_template_with_params(self, template_path: str, **kwargs) -> str:
        """
        Load a template and replace parameters
        
        Args:
            template_path (str): Relative path to template file
            **kwargs: Parameters to replace in template using {param_name} syntax
        
        Returns:
            str: Template content with parameters replaced
        
        Example:
            prompt = loader.load_template_with_params(
                'ocr/custom_template.md',
                target_element='buttons',
                language='English'
            )
        """
        template = self.load_template(template_path)
        
        # Replace parameters
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {e}")
    
    def list_templates(self, subdirectory: Optional[str] = None) -> list:
        """
        List all available templates
        
        Args:
            subdirectory (str, optional): Subdirectory to list templates from
        
        Returns:
            list: List of template file paths
        """
        search_dir = self.base_dir
        if subdirectory:
            search_dir = search_dir / subdirectory
        
        if not search_dir.exists():
            return []
        
        templates = []
        for file_path in search_dir.rglob('*.md'):
            relative_path = file_path.relative_to(self.base_dir)
            templates.append(str(relative_path))
        
        return sorted(templates)


# Predefined OCR prompt templates
class OCRPrompts:
    """Predefined OCR prompt template paths"""
    
    UI_ELEMENTS_EXTRACTION = 'ocr/ui_elements_extraction.md'
    TEXT_EXTRACTION_SIMPLE = 'ocr/text_extraction_simple.md'
    UI_SR_COMPARISON = 'ocr/ui_sr_comparison.md'
    CONTROL_VISIBILITY_CHECK = 'ocr/control_visibility_check.md'
    
    @staticmethod
    def get_all():
        """Get all OCR prompt template paths"""
        return [
            OCRPrompts.UI_ELEMENTS_EXTRACTION,
            OCRPrompts.TEXT_EXTRACTION_SIMPLE,
            OCRPrompts.UI_SR_COMPARISON,
            OCRPrompts.CONTROL_VISIBILITY_CHECK,
        ]


# Convenience function
def load_prompt(template_path: str, **params) -> str:
    """
    Convenience function to load a prompt template
    
    Args:
        template_path (str): Template path or predefined constant
        **params: Parameters for template substitution
    
    Returns:
        str: Loaded and processed prompt
    
    Example:
        from prompts.prompt_loader import load_prompt, OCRPrompts
        
        # Load predefined template
        prompt = load_prompt(OCRPrompts.UI_ELEMENTS_EXTRACTION)
        
        # Load with parameters
        prompt = load_prompt('custom/template.md', language='en')
    """
    loader = PromptLoader()
    
    if params:
        return loader.load_template_with_params(template_path, **params)
    else:
        return loader.load_template(template_path)
