import cv2
import easyocr
import re
from PIL import Image
import numpy as np

def get_numbers_from_Image(image):
    
    # Initialize the EasyOCR reader
    reader = easyocr.Reader(['en'])  # Specify the language(s) for OCR

    # Use EasyOCR to extract text from the image
    result = reader.readtext(image, detail=0)  # detail=0 to get only the text
    
    # Join the detected text into a single string
    text = " ".join(result)
    
    # Use regular expressions to extract alphanumeric sequences
    numbers_claim = re.findall(r'\b\w+\b', text)

    return numbers_claim


