# Standard library imports
import re
import json
import io
import base64

# Third-party library imports
import numpy as np
from pynvml import *

def encode_image_array(pil_image):
    """
    Encode a PIL Image to a base64 string.

    Args:
        pil_image (PIL.Image): The input PIL Image object.

    Returns:
        str: Base64 encoded string of the image.
    """
    # Save PIL Image to a byte stream
    byte_stream = io.BytesIO()
    pil_image.save(byte_stream, format='JPEG')
    byte_stream.seek(0)
    
    # Encode to base64
    return base64.b64encode(byte_stream.getvalue()).decode('utf-8')

def check_gpu_is_free(min_memory):
    """
    Check if the GPU has enough free memory.

    Args:
        min_memory (float): Minimum required free memory in GB.

    Returns:
        bool: True if GPU has enough free memory, False otherwise.
    """
    nvmlInit()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)
    return info.free * 1e-9 > min_memory  # Convert bytes to GB

def get_json_from_text(text):
    """
    Extract and parse JSON data from a text string.

    Args:
        text (str): Input text containing JSON data.

    Returns:
        dict: Parsed JSON data as a Python dictionary.
    """
    # Extract the JSON string by finding the first { and last }
    start = text.find('{')
    end = text.rfind('}') + 1  # Include the last }
    
    json_string = text[start:end]
    # Convert the JSON string into a Python dictionary
    return json.loads(json_string)

def get_code_from_text(text):
    """
    Extract Python code from a text string containing markdown-style code blocks.

    Args:
        text (str): Input text containing Python code blocks.

    Returns:
        str: Extracted Python code as a single string.
    """
    code_lines = []
    in_code_block = False
    
    for line in text.splitlines():
        # Check for the start or end of a code block
        if "```python" in line:
            in_code_block = True
            continue
        
        if in_code_block:
            if "```" in line:
                in_code_block = False
            else:
                code_lines.append(line)
            
    # Join all captured code lines into a single code block
    return "\n".join(code_lines)