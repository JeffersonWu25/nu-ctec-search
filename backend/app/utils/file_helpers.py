"""
Common file and data operations.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(file_path: Path, description: str = "data") -> List[Dict]:
    """
    Load and validate JSON file.
    
    Args:
        file_path: Path to JSON file
        description: Description for error messages
        
    Returns:
        Loaded JSON data
        
    Raises:
        SystemExit on file not found or invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📂 Loaded {len(data) if isinstance(data, list) else 'JSON'} {description} from {file_path}")
        return data
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        print(f"Please ensure the {description} file exists")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        sys.exit(1)

def save_json_file(data: Any, file_path: Path, description: str = "data") -> Path:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Output file path
        description: Description for logging
        
    Returns:
        Path to saved file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {description} to: {file_path}")
    return file_path

def find_pdf_files(directory: Path) -> List[Path]:
    """
    Find all PDF files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of PDF file paths
    """
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return []
    
    pdf_files = list(directory.glob("*.pdf"))
    print(f"📁 Found {len(pdf_files)} PDF files in {directory}")
    
    return sorted(pdf_files)

def confirm_operation(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default response if user presses enter
        
    Returns:
        True if user confirms, False otherwise
    """
    suffix = "(Y/n)" if default else "(y/N)"
    try:
        response = input(f"{message} {suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response.startswith('y')
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return False