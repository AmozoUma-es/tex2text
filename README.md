# TeX 2 Text Extraction System

## Overview

This script is designed to extract continuous text from scientific articles written in TeX format and generate statistics about the extracted text. The script processes `.tar.gz` files containing TeX files, cleans the content by removing tables, figures, and mathematical expressions, and converts the cleaned TeX content into plain text. The plain text is then saved in individual `.txt` files, and statistics such as the number of words, paragraphs, and characters, as well as the extraction time, are saved in a CSV file.

## Features

- Extracts and cleans text from TeX files.
- Removes tables, figures, and mathematical expressions.
- Converts cleaned TeX content into plain text.
- Saves extracted text in `.txt` files.
- Generates statistics about the extracted text.
- Handles multiple file encodings.
- Option to enable debug output for troubleshooting.

## Requirements

- Python 3.x
- Required Python libraries: `os`, `re`, `tarfile`, `argparse`, `time`, `pandas`, `pylatexenc`, `shutil`

## Usage Instructions

### Installation

1. Ensure you have Python 3 installed on your system.
2. Install the required Python libraries using pip:

    ```sh
    pip install pandas pylatexenc
    ```

### Downloading TeX Files from arXiv

1. Go to the [arXiv website](https://arxiv.org/).
2. Find the scientific articles you want to download.
3. Click on the "Download" link and select the "Other formats" option.
4. Download the source files as a `.tar.gz` archive.

### Running the Script

1. Save the script to a file, for example, `extract_text.py`.
2. Open a terminal or command prompt.
3. Navigate to the directory where the script is saved.
4. Run the script using the following command:

    ```sh
    python extract_text.py input_folder output_folder output_file.csv [-f] [--debug]
    ```

### Command-line Arguments

- `input_folder`: The folder containing the `.tar.gz` files with TeX articles.
- `output_folder`: The folder where the extracted text files will be saved.
- `output_file.csv`: The CSV file where the statistics will be saved.
- `-f, --force`: (Optional) Force reprocessing of already processed files.
- `--debug`: (Optional) Enable debug output for troubleshooting.

### Example

To process the files in the `input_files` folder, save the extracted text to the `output_texts` folder, and save the statistics to `stats.csv`, with debug output enabled, use the following command:

```sh
python extract_text.py input_files output_texts stats.csv -f --debug
```

## Script Explanation

The script performs the following steps:

1. **Extract `.tar.gz` Files**: Extracts the contents of each `.tar.gz` file to a temporary directory.
2. **Read TeX Files**: Reads the TeX files, handling multiple file encodings.
3. **Clean TeX Content**: Removes tables, figures, and mathematical expressions directly from the TeX content.
4. **Convert to Plain Text**: Converts the cleaned TeX content to plain text using `pylatexenc`.
5. **Clean Plain Text**: Applies additional cleaning to the plain text to remove LaTeX commands and unwanted tags.
6. **Save Extracted Text**: Saves the cleaned plain text to individual `.txt` files.
7. **Generate Statistics**: Computes and saves statistics about the extracted text (number of words, paragraphs, characters, and extraction time) to a CSV file.
8. **Debug Output**: If enabled, prints debug information to help troubleshoot issues.

## Troubleshooting

- Ensure all required Python libraries are installed.
- Check the input folder path and ensure it contains valid `.tar.gz` files.
- If encountering encoding issues, the script attempts to read files with different encodings (`utf-8`, `latin-1`, `iso-8859-1`).
- Enable debug output using the `--debug` option to see detailed information about the processing steps.