import os
import re
import tarfile
import argparse
import time
import pandas as pd
from pylatexenc.latex2text import LatexNodes2Text
import shutil

def extract_tarfile(tar_file, path='.'):
    with tarfile.open(tar_file, 'r:gz') as tar:
        tar.extractall(path=path)

def read_file_with_fallback(file_path):
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Failed to read {file_path} with tried encodings")

def read_tex_files(directory):
    tex_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".tex"):
                file_path = os.path.join(root, file)
                content = read_file_with_fallback(file_path)
                tex_files.append((file, content))
    return tex_files

def find_main_tex_file(tex_files):
    for file, content in tex_files:
        if re.search(r'\\documentclass', content):
            return file, content
    return tex_files[0]  # Return the first file if no documentclass is found

def clean_tex_content(tex_content, debug=False):
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

def tex_to_text(tex_content):
    converter = LatexNodes2Text()
    text = converter.latex_to_text(tex_content)
    return text

def clean_text(text):
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
    text = re.sub(r'(\n\n)+', '\n', text)
    
    return text.strip()

def extract_text_and_stats(input_folder, output_folder, output_file, force, debug):
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

            tex_content = clean_tex_content(main_tex_content, debug)
            text = tex_to_text(tex_content)
            text_content = clean_text(text)
            
            num_words = len(text_content.split())
            num_paragraphs = text_content.count('\n\n') + 1
            num_chars = len(text_content)
            extraction_time = time.time() - start_time
            
            with open(output_txt_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
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
