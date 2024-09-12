import re
from pynvml import *
import base64
from PIL import Image as PILImage
import io
import cv2
import easyocr
import numpy as np

def count_claims(input_text):
    # Regular expression to match each claim in the text
    claim_pattern = r'<claim id="[^"]+" num="\d+"><claim-text>'
    
    # Find all matches using the regex
    claims = re.findall(claim_pattern, input_text)
    
    # Return the number of claims found
    return len(claims)

def get_n_claim(input_text, n_claim):

    if len(str(n_claim)) == 1:
        num_format = r'000' + str(n_claim) 
    elif len(str(n_claim)) == 2:
        num_format = r'00' + str(n_claim) 
    elif len(str(n_claim)) == 3:
        num_format = r'0' + str(n_claim) 
    else:
        num_format = r'\d{' + str(n_claim) + '}'
    
    # Regular expression to match each claim in the text with the adjusted number format
    #claim_pattern = rf'<claim id="[^"]+" num="{num_format}"><claim-text>'
    claim_pattern = rf'(<claim id="[^"]+" num="{num_format}"><claim-text>.*?)(?=<claim id|$)'

    # Regular expression to match each claim in the text
    # Find all matches using the regex
    claims = re.findall(claim_pattern, input_text,  re.DOTALL)
    
    # Return the number of claims found
    return claims

def encode_image_array(pil_image):
    # Save PIL Image to a byte stream
    byte_stream = io.BytesIO()
    pil_image.save(byte_stream, format='JPEG')
    byte_stream.seek(0)
    
    # Encode to base64
    return base64.b64encode(byte_stream.getvalue()).decode('utf-8')

def check_gpu_is_free():
    nvmlInit()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    if info.free*1e-9 > 12: #15 GB is llama3
        return True
    else:
        return False

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


def get_code_from_text(text):
    # Split the text by lines and filter out non-code content
    code_lines = []
    in_code_block = False
    
    for line in text.splitlines():
        # Check for the start or end of a code block
        if "```python" in line or "```" in line:
            in_code_block = not in_code_block
            continue
        
        # If inside a code block, capture the lines
        if in_code_block:
            code_lines.append(line)
    
    # Join all captured code lines into a single code block
    code_str = "\n".join(code_lines)

    return code_str


