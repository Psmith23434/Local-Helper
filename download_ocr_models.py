"""Run this once to pre-download all EasyOCR language models."""
import easyocr

LANGS = ["en", "de", "fr", "es", "it", "nl", "pt", "ru", "pl", "cs", "sv"]

print(f"Downloading EasyOCR models for: {LANGS}")
print("This may take a while (~500MB-1GB total). Please wait...\n")

reader = easyocr.Reader(LANGS, gpu=False)

print("\nAll models downloaded successfully!")
print("Models are stored in: C:\\Users\\<you>\\.EasyOCR\\model\\")
