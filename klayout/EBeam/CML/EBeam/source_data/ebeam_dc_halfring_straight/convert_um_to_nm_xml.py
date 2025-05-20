import os
import re

def convert_um_to_nm(text):
    # Match numbers followed by 'um' and convert them to nanometers
    return re.sub(r'(\d+)um', lambda m: f"{int(m.group(1)) * 1000}nm", text)

def process_xml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = convert_um_to_nm(content)

    if content != new_content:
        print(f"Modified: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

def process_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root, file)
                process_xml_file(file_path)

# Example usage
if __name__ == "__main__":
    folder = "."  # Replace with your folder path
    process_folder(folder)

