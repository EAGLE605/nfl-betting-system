"""
Common path setup utility.

This module provides a standardized way to add the project root to sys.path,
eliminating the need for duplicate sys.path.insert/append calls across scripts.
"""

import sys
from pathlib import Path


def setup_project_path():
    """
    Add project root to sys.path if not already present.
    
    This should be called at the start of scripts that need to import
    from the src package.
    
    Example:
        from src.utils.path_setup import setup_project_path
        setup_project_path()
        
        from src.models.xgboost_model import XGBoostNFLModel
    """
    # Get project root (parent of src directory)
    project_root = Path(__file__).parent.parent.parent
    
    # Convert to string for sys.path
    project_root_str = str(project_root)
    
    # Add to sys.path if not already present
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root

