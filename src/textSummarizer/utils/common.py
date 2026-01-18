import os
from box.exceptions import BoxValueError
import yaml
from textSummarizer.logging import logger
from ensure import ensure_annotations
from box import ConfigBox
from pathlib import Path
from typing import Any



@ensure_annotations
def read_yaml(path_to_yaml: Path) -> ConfigBox:
    """Reads a yaml file and returns

    Args:
        path_to_yaml (Path): The path to the yaml file.
    
    Raises:
        ValueError: if yaml file is empty
        e: empty file

    Returns:
        ConfigBox: ConfigBox type

    """

    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            logger.info(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("yaml file is empty")
    except Exception as e:
        raise e



@ensure_annotations
def create_directories(path_to_directories: list, verbose: bool = True):
    """
    Creates a list of directories.

    Args:
        path_to_directories (list): List of directory paths (str or Path)
        verbose (bool, optional): Whether to log directory creation. Defaults to True.
    """
    for path in path_to_directories:
        path = Path(path)   # normalize to Path
        os.makedirs(path, exist_ok=True)

        if verbose:
            logger.info(f"Created directory at: {path}")



@ensure_annotations
def get_size(path: Path) -> str:
    """Get size in KB

    Args:
        path (Path): Path to file

    Returns:
        str: Size in KB
    """
    size_in_kb = round(os.path.getsize(path) / 1024)
    return f"~ {size_in_kb} KB"