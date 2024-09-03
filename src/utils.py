import re
from pynvml import *

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

def check_gpu_is_free():
    nvmlInit()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    if info.free*1e-9 > 12: #15 GB is llama3
        return True
    else:
        return False