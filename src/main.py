import os
from utils import *
import login_hf
from llama_class import *
import torch
# EPO libraries
from epo.tipdata.epab import EPABClient

login_hf.login_to_hf()

# Get EPO data

# Start EPO Client
epab = EPABClient(env='PROD')

# Get patent by number

q = epab.query_application_number("21198556")

query_claims = q.get_results('claims', output_type='list')
claim_text = query_claims[0]['claims'][0]['text']

# Count number of claims
number_of_claims = count_claims(claim_text)
selected_claim = get_n_claim(claim_text, n_claim=1)
clean_claim = epab.clean_text(selected_claim[0])

print(clean_claim)

# Initialize model
# define the system and user messages
system_input = "You are an expert patent summarizer."
conversation = [{"role": "system", "content": system_input}]
user_input = f"summarize the following claim and extract all related references: {clean_claim}"

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
llama3 = Llama3(model_id, 'cpu')
torch.cuda.empty_cache()
print('Processing requested prompt')
response, conversation = llama3.get_response(user_input, conversation)


  
# if __name__ == "__main__":