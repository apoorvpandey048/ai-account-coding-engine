import zipfile
import pathlib

# Remove old zip if exists
zip_path = pathlib.Path('deliverables/milestone1.zip')
zip_path.unlink(missing_ok=True)

# Create new zip
source_dir = pathlib.Path('deliverables/milestone1')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file in source_dir.rglob('*'):
        if file.is_file():
            zf.write(file, file.relative_to(source_dir.parent))

print(f"Successfully packaged {len(list(source_dir.rglob('*')))} items into milestone1.zip")
