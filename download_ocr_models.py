"""Run this once to pre-download all EasyOCR language models."""
import easyocr

# EasyOCR restriction: Cyrillic languages must be in a separate reader from Latin ones.
GROUPS = [
    # Latin group
    ["en", "de", "fr", "es", "it", "nl", "pt", "pl", "cs", "sv"],
    # Cyrillic group (must include 'en')
    ["ru", "en"],
]

print("Downloading EasyOCR models in language groups...")
print("This may take a while (~500MB-1GB total). Please wait...\n")

for i, langs in enumerate(GROUPS, 1):
    print(f"[{i}/{len(GROUPS)}] Downloading group: {langs}")
    easyocr.Reader(langs, gpu=False)
    print(f"  Done.\n")

print("All models downloaded successfully!")
print("Models are stored in: C:\\Users\\<you>\\.EasyOCR\\model\\")
