import os
import re
import subprocess


def convert_um_to_nm_in_filename(filename):
    # This pattern matches numbers followed by 'um'
    pattern = re.compile(r'(\d+)um')
    def replacer(match):
        value_um = int(match.group(1))
        value_nm = value_um * 1000
        return f"{value_nm}nm"
    
    return pattern.sub(replacer, filename)

def rename_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)
        if not os.path.isfile(old_path):
            continue  # skip directories

        new_filename = convert_um_to_nm_in_filename(filename)
        new_path = os.path.join(folder_path, new_filename)

        if new_filename != filename:
            print(f"Renaming: {filename} -> {new_filename}")
#            os.rename(old_path, new_path)
            subprocess.run(["git", "mv", old_path, new_path], check=True)

# Example usage
if __name__ == "__main__":
    folder = "."  # Replace with your folder path
    rename_files_in_folder(folder)


