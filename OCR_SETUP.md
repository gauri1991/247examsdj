# OCR Engine Setup

The PDF extractor uses OCR (Optical Character Recognition) for processing scanned PDFs and improving text extraction accuracy.

## System Requirements

### 1. Tesseract OCR (Required)
Tesseract is the primary OCR engine used by the system.

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
```

**Current Status:** ✅ Installed (version 5.3.4)

### 2. EasyOCR (Optional, High Accuracy)
EasyOCR provides better accuracy for complex documents but requires more resources.

**Installation:**
```bash
# From requirements.txt
pip install easyocr

# Manual installation
pip install easyocr torch torchvision
```

**Current Status:** ✅ Installed (version 1.7.2)

## Python Dependencies

The following Python packages are included in `requirements.txt`:

- `pytesseract==0.3.13` - Python wrapper for Tesseract OCR
- `easyocr==1.7.2` - Deep learning-based OCR (optional)
- `pdf2image==1.17.0` - PDF to image conversion
- `opencv-python==4.12.0.88` - Image preprocessing
- `pillow==11.3.0` - Image handling

## OCR Fallback Strategy

The system uses a smart fallback approach:

1. **Primary**: Try direct text extraction from searchable PDFs
2. **Secondary**: Use Tesseract OCR for scanned documents  
3. **Tertiary**: Use EasyOCR for complex/low-quality scans
4. **Fallback**: Graceful failure with informative error messages

## Troubleshooting

### "Tesseract not available" Error
```bash
# Check if tesseract is in PATH
which tesseract

# If not found, install:
sudo apt-get install tesseract-ocr
```

### "EasyOCR not available" Warning
This is non-critical. The system will work with just Tesseract. To install EasyOCR:
```bash
pip install easyocr
```

### Memory Issues with EasyOCR
EasyOCR requires significant memory. If you encounter memory issues:
1. Process documents one at a time
2. Consider using only Tesseract for basic needs
3. Increase system memory or use GPU acceleration

## Performance Optimization

- **For searchable PDFs**: OCR is skipped, providing fast processing
- **For scanned PDFs**: Images are cached to avoid reprocessing
- **GPU Acceleration**: EasyOCR can use CUDA if available
- **Batch Processing**: Multiple pages processed efficiently

## Configuration

OCR settings can be adjusted in:
- `pdf_extractor/ocr_processors.py` - OCR engine configuration
- `pdf_extractor/settings.py` - Performance and fallback settings