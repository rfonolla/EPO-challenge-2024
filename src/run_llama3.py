import os
from utils import *
import login_hf
from llama_class import *
import torch


def run_llama3(claim, numbers_claim):
    
    login_hf.login_to_hf()
    
    # Check GPU
    device = 'cpu'
    
    if check_gpu_is_free(): 
        device='gpu'
        print('GPU  free :)')
    else:
        print('GPU not free :( using CPU')
        
    torch.cuda.empty_cache()        
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    llama3 = Llama3(model_id, device)
    
    # define the system and user messages
    system_input = "You are an expert patent summarizer."
    conversation = [{"role": "system", "content": system_input}]
    
    user_input = f"summarize the following claim. Start with 'Summary'. Extract all related references numbers. Start with 'Ref'. Do not infer information.{claim}."
    #Start the references with the word 'References'. Return the references in one paragraph Do not infer information. Here is the claim:

    print('Processing requested prompt')
    response, conversation = llama3.get_response(user_input, conversation)

    # Extract the summary using a regex pattern
    summary_match = re.search(r'Summary:\n\n(.*?)(?=\n\nRef:)', response, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    # Extract the reference information
    ref = {}
    ref_section = re.search(r'Ref:\n(.*)', response, re.DOTALL)
    if ref_section:
        ref_lines = ref_section.group(1).strip().split('\n')
        for line in ref_lines:
            key, value = re.match(r'\* (\w+): (.+)', line).groups()
            ref[key] = value
    
    # Printing the extracted variables
    print("Summary:")
    print(summary)
    print("\nReference Information:")
    print(ref)

    
    # Convert the array to a set for efficient lookup
    array_set = set(numbers_claim)
    
    # Find which keys in the dictionary are in the array
    keys_in_array = {key for key in ref if key in array_set}
    
    # Print the results
    print("Keys in summary that exist in the processed image:")
    print(keys_in_array)