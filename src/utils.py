import re
import numpy as np
import json
import io
import base64
from pynvml import *

def encode_image_array(pil_image):
    # Save PIL Image to a byte stream
    byte_stream = io.BytesIO()
    pil_image.save(byte_stream, format='JPEG')
    byte_stream.seek(0)
    
    # Encode to base64
    return base64.b64encode(byte_stream.getvalue()).decode('utf-8')

def check_gpu_is_free(min_memory):
    nvmlInit()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    if info.free*1e-9 > min_memory: #15 GB is llama3
        return True
    else:
        return False

def get_json_from_text(text):

    # Extract the JSON string by finding the first { and last }
    start = text.find('{')
    end = text.rfind('}') + 1  # to include the last }
    
    json_string = text[start:end]
    # Convert the JSON string into a Python dictionary
    data_dict = json.loads(json_string)

    return data_dict

def get_code_from_text(text):
    # Split the text by lines and filter out non-code content
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
    code_str = "\n".join(code_lines)

    return code_str


