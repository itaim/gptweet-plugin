import pathlib
from loguru import logger

def find_relative_path(relative_path):
    # Get the absolute path of the script file
    script_path = pathlib.Path(__file__).resolve()

    # Get the directory containing the script file
    script_dir = script_path.parent

    # Get the parent directory of the script directory
    parent_dir = script_dir.parent

    # Check if the relative path exists in the script directory
    target_path_in_script_dir = script_dir / relative_path
    logger.debug(f'target_path_in_script_dir {target_path_in_script_dir}')
    if target_path_in_script_dir.exists():
        return target_path_in_script_dir

    # Check if the relative path exists in the parent directory
    target_path_in_parent_dir = parent_dir / relative_path
    if target_path_in_parent_dir.exists():
        logger.debug(f'target_path_in_parent_dir {target_path_in_parent_dir}')
        return target_path_in_parent_dir

    # Return None if the relative path is not found
    return None
