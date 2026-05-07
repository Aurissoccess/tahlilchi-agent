import os
import zipfile

def find_and_zip(folder_name):
    # Qidiriladigan asosiy joylar
    search_paths = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Downloads")
    ]
    
    target_path = None
    
    # Papkani qidirish
    for path in search_paths:
        for root, dirs, files in os.walk(path):
            if folder_name in dirs:
                target_path = os.path.join(root, folder_name)
                break
        if target_path:
            break
            
    if target_path:
        zip_filename = f"{folder_name}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(target_path)))
        return zip_filename
    return None

folder_to_find = "c9249d15-1981-48b1-b054-d07e350eb66c"
result = find_and_zip(folder_to_find)

if result:
    print(f"SEND_FILE:{result}")
else:
    print("Papka topilmadi. Desktop, Documents yoki Downloads papkalarida yo'q ekan.")