import os
import re

def sanitize_filename(name):
    """
    Sanitizes a string to be used as a filename by removing or replacing
    invalid characters.
    """
    # Remove invalid characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    return name

def save_document_to_file(opportunity_id, opportunity_title, doc_type, content, version=1):
    """
    Saves a document (like a BRD or PRD) to a local Markdown file.

    Args:
        opportunity_id (int): The ID of the opportunity.
        opportunity_title (str): The title of the opportunity for the folder name.
        doc_type (str): The type of the document (e.g., 'BRD', 'PRD').
        content (str): The Markdown content of the document.
        version (int): The version number of the document.

    Returns:
        The file path where the document was saved, or None on failure.
    """
    if not content:
        return None

    try:
        # Sanitize the title for the directory name
        sane_title = sanitize_filename(opportunity_title) if opportunity_title else f"opportunity_{opportunity_id}"
        
        # Define the directory path
        directory_path = os.path.join("picopitch_outputs", f"{opportunity_id}_{sane_title}")
        
        # Create the directory if it doesn't exist
        os.makedirs(directory_path, exist_ok=True)
        
        # Define the file path
        file_name = f"{doc_type}_v{version}.md"
        file_path = os.path.join(directory_path, file_name)
        
        # Write the content to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Successfully saved document to: {file_path}")
        return file_path

    except Exception as e:
        print(f"Error saving document to file: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    mock_content = """
# Business Requirements Document (BRD)

## 1. Introduction

This is a test BRD.
    """
    saved_path = save_document_to_file(1, "Test Opportunity", "BRD", mock_content)
    if saved_path:
        print(f"File saved at: {os.path.abspath(saved_path)}")

    saved_path_no_title = save_document_to_file(2, None, "PRD", mock_content)
    if saved_path_no_title:
        print(f"File saved at: {os.path.abspath(saved_path_no_title)}") 