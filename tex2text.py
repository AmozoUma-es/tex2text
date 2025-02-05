import os
import re
import tarfile
import argparse
import time
import pandas as pd
from pylatexenc.latex2text import LatexNodes2Text
import shutil
import ftfy

def extract_tarfile(tar_file, path='.'):
    """
    Extracts the contents of a .tar.gz file to a specified directory.
    
    Parameters:
    tar_file (str): The path to the .tar.gz file.
    path (str): The directory to extract the contents to.
    
    Returns:
    None
    """
    if not tarfile.is_tarfile(tar_file):
        print(f"Error: {tar_file} is not a valid tar.gz file.")
        return
    
    try:
        with tarfile.open(tar_file, 'r:gz') as tar:
            members = tar.getmembers()
            if len(members) == 1 and members[0].isfile():
                tar.extract(members[0], path=path)
            else:
                tar.extractall(path=path)
        print(f"Successfully extracted {tar_file}")
    except Exception as e:
        print(f"Error extracting {tar_file}: {e}")

def read_file_with_fallback(file_path):
    """
    Reads a file with multiple fallback encodings.
    
    Parameters:
    file_path (str): The path to the file.
    
    Returns:
    str: The content of the file.
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Failed to read {file_path} with tried encodings")

def read_tex_files(directory):
    """
    Reads all .tex files in a directory.
    
    Parameters:
    directory (str): The directory containing .tex files.
    
    Returns:
    list of tuples: A list of tuples, each containing the file name and its content.
    """
    tex_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".tex"):
                file_path = os.path.join(root, file)
                content = read_file_with_fallback(file_path)
                tex_files.append((file, content))
    return tex_files

def find_main_tex_file(tex_files):
    """
    Finds the main .tex file, which contains the \documentclass command.
    
    Parameters:
    tex_files (list of tuples): A list of tuples, each containing the file name and its content.
    
    Returns:
    tuple: The main .tex file and its content.
    """
    for file, content in tex_files:
        if re.search(r'\\documentclass', content):
            return file, content
    if isinstance(tex_files, list) and len(tex_files) > 0:
        return tex_files[0]  # Return the first file if no documentclass is found
    return "", ""

def clean_tex_content(tex_content, debug=False):
    """
    Cleans the TeX content by removing tables, figures, and math blocks.
    
    Parameters:
    tex_content (str): The TeX content to be cleaned.
    debug (bool): If True, prints debug information.
    
    Returns:
    str: The cleaned TeX content.
    """
    def debug_print(message):
        if debug:
            print(message)

    def remove_pattern(pattern, description):
        matches = re.findall(pattern, tex_content, flags=re.DOTALL)
        if matches:
            debug_print(f"Found {len(matches)} {description} blocks.")
            for match in matches:
                debug_print(f"Removing {description} block: {match[:100]}...")  # Print the first 100 characters of each match
        return re.sub(pattern, '', tex_content, flags=re.DOTALL)

    tex_content = remove_pattern(r'\\begin\{table\}.*?\\end\{table\}', 'table')
    tex_content = remove_pattern(r'\\begin\{tabular\}.*?\\end\{tabular\}', 'tabular')
    tex_content = remove_pattern(r'\\begin\{figure\}.*?\\end\{figure\}', 'figure')  # Added for figures
    tex_content = remove_pattern(r'\$\$.*?\$\$', 'display math')
    tex_content = remove_pattern(r'\$.*?\$', 'inline math')

    return tex_content

def fix_text_issues(text):
    """
    Fixes text issues such as ligatures and other character problems.
    
    Parameters:
    text (str): The text to be fixed.
    
    Returns:
    str: The fixed text.
    """
    fixed_text = ftfy.fix_text(text)
    return fixed_text

def tex_to_text(tex_content):
    """
    Converts TeX content to plain text using pylatexenc.
    
    Parameters:
    tex_content (str): The TeX content to be converted.
    
    Returns:
    str: The converted plain text.
    """
    converter = LatexNodes2Text()
    try:
        text = converter.latex_to_text(tex_content)
        return text
    except Exception as e:
        print(f"Error converting TeX to text: {e}")
        return tex_content

def clean_text(text):
    """
    Cleans the plain text by removing LaTeX commands and unwanted tags, and fixing text issues.
    
    Parameters:
    text (str): The text to be cleaned.
    debug (bool): If True, prints debug information.
    
    Returns:
    str: The cleaned text.
    """
    # Fix text issues
    text = fix_text_issues(text)

    # Preserve paragraphs by keeping double newlines
    text = re.sub(r'(\n\s*\n)', '\n\n', text)
    
    # Remove common LaTeX commands and unwanted tags
    text = re.sub(r'\\cite\{.*?\}', '<cit.>', text)
    text = re.sub(r'\\ref\{.*?\}', '<ref>', text)
    text = re.sub(r'\\label\{.*?\}', '', text)
    text = re.sub(r'\\begin\{.*?\}', '', text)
    text = re.sub(r'\\end\{.*?\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\{.*?\}', '', text)
    
    # Remove specific unwanted tags
    text = re.sub(r'<cit.>', '', text)
    text = re.sub(r'<ref>', '', text)
    
    # Remove angle brackets around URLs
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    
    # Restore single newlines within blocks
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    
    # Ensure there is a newline after each block
    text = re.sub(r'(\n\n)+', '\n\n', text)
    
    return text.strip()

def extract_text_and_stats(input_folder, output_folder, output_file, force, debug):
    """
    Extracts text from TeX files in .tar.gz archives, cleans the text, and generates statistics.
    
    Parameters:
    input_folder (str): The folder containing the .tar.gz files.
    output_folder (str): The folder to save the extracted text files.
    output_file (str): The CSV file to save the statistics.
    force (bool): If True, forces reprocessing of already processed files.
    debug (bool): If True, prints debug information.
    
    Returns:
    None
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    data = []
    for file in os.listdir(input_folder):
        if file.endswith(".tar.gz"):
            tar_file = os.path.join(input_folder, file)
            extract_path = os.path.join(input_folder, file[:-7])  # Remove .tar.gz extension
            output_txt_file = os.path.join(output_folder, f"{file[:-7]}.txt")
            
            if os.path.exists(output_txt_file) and not force:
                print(f"Skipping already processed file: {file}")
                continue
            
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
            
            start_time = time.time()
            extract_tarfile(tar_file, extract_path)
            
            tex_files = read_tex_files(extract_path)
            main_tex_file, main_tex_content = find_main_tex_file(tex_files)

            clean_tex = clean_tex_content(main_tex_content, debug)
            text = tex_to_text(clean_tex)
            clean_text_content = clean_text(text)
            
            num_words = len(clean_text_content.split())
            num_paragraphs = clean_text_content.count('\n\n') + 1
            num_chars = len(clean_text_content)
            extraction_time = time.time() - start_time
            
            with open(output_txt_file, 'w', encoding='utf-8') as f:
                f.write(clean_text_content)
            
            data.append({
                'file': file,
                'num_words': num_words,
                'num_paragraphs': num_paragraphs,
                'num_chars': num_chars,
                'extraction_time': extraction_time
            })
            
            # Remove extracted files
            shutil.rmtree(extract_path)
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Extraction complete. Statistics saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from arXiv TeX files and generate statistics.")
    parser.add_argument('input_folder', type=str, help='Folder containing the tar.gz files')
    parser.add_argument('output_folder', type=str, help='Folder to save the extracted text files')
    parser.add_argument('output_file', type=str, help='CSV file to save the statistics')
    parser.add_argument('-f', '--force', action='store_true', help='Force reprocessing of already processed files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    extract_text_and_stats(args.input_folder, args.output_folder, args.output_file, args.force, args.debug)
