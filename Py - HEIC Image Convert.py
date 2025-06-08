import os
from pillow_heif import register_heif_opener
from PIL import Image

# Register HEIC support
register_heif_opener()

# Folder containing your .HEIC images
input_folder = r"C:\Users\X\Desktop\Photos-1-001"
output_folder = r"C:\Users\X\Desktop\Photos-1-001\jpg"
os.makedirs(output_folder, exist_ok=True)

# Convert all HEIC files to JPG
for filename in os.listdir(input_folder):
    if filename.lower().endswith(".heic"):
        heic_path = os.path.join(input_folder, filename)
        jpg_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".jpg")
        
        try:
            img = Image.open(heic_path)
            img.save(jpg_path, "JPEG", quality=95)
            print(f"Converted: {filename} -> {jpg_path}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")
