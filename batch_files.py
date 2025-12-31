from pathlib import Path
import shutil
import math

def copy_files_into_batches(source_path, dest_path, batch_size):
    source = Path(source_path)
    destination = Path(dest_path)

    if not source.exists():
        print(f"Error: Source directory '{source}' not found.")
        return

    files = [f for f in source.iterdir() if f.is_file()]
    files.sort()
    
    total_files = len(files)
    print(f"Found {total_files} files to process.")

    if total_files == 0:
        return

    # Create destination directory
    destination.mkdir(parents=True, exist_ok=True)

    # Process files in chunks
    num_batches = math.ceil(total_files / batch_size)

    for i in range(num_batches):
        start_index = i * batch_size
        end_index = start_index + batch_size
        
        current_batch = files[start_index:end_index]
        
        subfolder_name = f"Batch_{i + 1}"
        subfolder_path = destination / subfolder_name
        
        subfolder_path.mkdir(exist_ok=True)

        print(f"Copying to {subfolder_name} ({len(current_batch)} files)...")

        for file_path in current_batch:
            new_file_path = subfolder_path / file_path.name
            
            try:
                shutil.copy2(file_path, new_file_path)
            except Exception as e:
                print(f"Failed to copy {file_path.name}: {e}")

    print("--- Operation Complete (Original files remained untouched) ---")

if __name__ == "__main__":
    
    input_dir = r"C:\Users\YourName\Downloads\MySourceFiles"
    output_dir = r"C:\Users\YourName\Downloads\MySourceFiles\Organized_Copies"
    
    files_per_folder = 10 

    copy_files_into_batches(input_dir, output_dir, files_per_folder)