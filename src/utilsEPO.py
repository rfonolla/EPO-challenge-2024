import os
import io
import re
import json

import numpy as np
from bs4 import BeautifulSoup
from PIL import Image as PILImage

# EPO libraries
from epo.tipdata.epab import EPABClient

# Own libs
import utils

#llama-index
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic


def get_dependant_claims(claim_info, model_llm):
    if 'claude' in model_llm.lower():
        llm = Anthropic(model=model_llm, temperature=0.0, max_tokens=1024) # ["claude-3-5-sonnet-20240620","claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307","gpt-3.5-turbo"]
    elif 'gpt' in model_llm.lower():
        llm = OpenAI(model=model_llm, temperature=0.0, max_tokens=1024)
    else:
        raise ValueError(f"Unsupported model: {model_llm}")

    Settings.llm = llm
    
    prompt_template = 'You are an expert patent examienr. I want to know information about claim number 4. The claim text is the following:\
    {claim_info}\n\
    Are there any depedant claims? Return the number of claims I need to know for this specific claim. \nReturn the information as a JSON using the following template:\n\"dependant_claims\":\"list of integer claims\
    Do not return any additional information or explanation.'

    input_prompt = PromptTemplate((prompt_template))

    summary = Settings.llm.complete(input_prompt.format(claim_info=claim_info))

    response = summary.text
    
    # Extract the JSON part from the text
    json_start = response.index('{')
    json_end = response.rindex('}') + 1
    json_str = response[json_start:json_end]
    
    # Parse the JSON string into a Python dictionary
    data_dict = json.loads(json_str)

    return data_dict
    
def count_claims(input_text):
    # Regular expression to match each claim in the text
    claim_pattern = r'<claim id="[^"]+" num="\d+"><claim-text>'
    
    # Find all matches using the regex
    claims = re.findall(claim_pattern, input_text)
    
    # Return the number of claims found
    return len(claims)

def get_n_claim_alt(input_text):
    
    soup = BeautifulSoup(input_text, 'html.parser')
    elements = soup.find_all('claim-text')
    claim_info = []
    for idx,element in enumerate(elements):
        text = element.text.strip()
        if text.isupper(): # HEADER
            continue
        else:  
            claim_info.append(text)
            
    return claim_info

def get_n_claim(input_text, number_of_claims):


    claim_info = []

    for n in range(number_of_claims):
        
        if len(str(n)) == 1:
            num_format = r'000' + str(n) 
        elif len(str(n)) == 2:
            num_format = r'00' + str(n) 
        elif len(str(n)) == 3:
            num_format = r'0' + str(n) 
        else:
            num_format = r'\d{' + str(n) + '}'
            
        # Regular expression to match each claim in the text with the adjusted number format
        claim_pattern = rf'(<claim id="[^"]+" num="{num_format}"><claim-text>.*?)(?=<claim id|$)'
        claims = re.findall(claim_pattern, input_text,  re.DOTALL)
        claim_info.append(claims)

    # Regular expression to match each claim in the text
    # Find all matches using the regex
    
    # Return the number of claims found
    return claim_info
    
def get_patent_info_from_description(query):
    
    if not query or not isinstance(query, list) or len(query) == 0:
        raise ValueError("Query is None, empty, or not a list: Manually check contents of the patent number")
    
    if not isinstance(query[0], dict):
        raise ValueError("First element of query is not a dictionary: Manually check contents of the patent number")
    
    description = query[0].get('description')
    if description is None:
        raise ValueError("No 'description' field in the query: Manually check contents of the patent number")
    
    if not isinstance(description, dict) or 'text' not in description:
        raise ValueError("'description' field is not a dictionary or does not contain 'text': Manually check contents of the patent number")
    
    
    html_content = query[0]['description']['text']

    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(['heading', 'p'])
    headings_patent = [
        "FIELD OF THE INVENTION",
        "BACKGROUND OF THE INVENTION",
        "SUMMARY OF THE INVENTION",
        "BRIEF DESCRIPTION OF THE DRAWINGS",
        "DETAILED DESCRIPTION OF THE EMBODIMENTS",
        # Alternative headings
        "TECHNICAL FIELD AND BACKGROUND",
        "BRIEF DESCRIPTION OF DRAWINGS",
        "SUMMARY",
        "DESCRIPTION OF EMBODIMENTS",
    ]
    
    patent_dict = {heading: "" for heading in headings_patent}
    current_heading = None
    detailed_description_found = False
    for element in elements:
        text = element.text.strip()
        if text.strip().isupper() and text.strip() in headings_patent:
            current_heading = text.strip()
            if current_heading == "DETAILED DESCRIPTION OF THE EMBODIMENTS" or current_heading == "DESCRIPTION OF EMBODIMENTS":
                detailed_description_found = True
        else:
            if current_heading:
                if detailed_description_found:
                    patent_dict[current_heading] += f"{text}"
                elif current_heading != "DETAILED DESCRIPTION OF THE EMBODIMENTS" or curren_heading != "DESCRIPTION OF EMBODIMENTS":
                    patent_dict[current_heading] += f"{text}"
                    
    # Remove leading/trailing whitespace from each section
    for heading in patent_dict:
        patent_dict[heading] = patent_dict[heading].strip()

    patent_dict = {k: None if v == "" else v for k, v in patent_dict.items()}
    return patent_dict

def get_data_from_patent(**kwargs):
    
    search_number = kwargs.get('patent_number', False)
    claim_number = kwargs.get('claim_number')
    field_of_invention = kwargs.get('field_of_invention', False)
    background_of_the_invetion = kwargs.get('background_of_the_invetion', False)
    summary_of_the_invetion = kwargs.get('summary_of_the_invetion', False)
    brief_description_of_the_drawings = kwargs.get('brief_description_of_the_drawings', False)
    detailed_description_of_the_embodiments = kwargs.get('detailed_description_of_the_embodiments', False)
    retrieve_patent_images = kwargs.get('retrieve_patent_images', False)
    model_llm = kwargs.get('model_llm')
    
    output_data = {'claim_text': None,
                   'depedant_claims_text': None,
                   'field_of_invention_text':None,
                   'background_of_the_invetion_text':None,
                   'summary_of_the_invention_text':None,
                   'brief_description_of_the_drawings_text':None,
                   'detailed_description_of_the_embodiments_text':None,
                   'pil_image': None,
                   'encoded_image': None
                  } 

    # Start EPO Client
    epab = EPABClient(env='PROD')
    
    # Get patent by number
    print('Patent number:', search_number)
    q = epab.query_epab_doc_id(search_number)

    query_claims_description =  q.get_results('claims, description', output_type='list')
    # Get relevant information from the patent description
    patent_desc_info = get_patent_info_from_description(query_claims_description)

    ## CLAIM INFORMATION
    claim_text = query_claims_description[0]['claims'][0]['text']    
    number_of_claims = count_claims(claim_text)
    depedant_claims_text = []
    if number_of_claims == 0: # try reading as if all claims are inside claim 1.

        claim_info = get_n_claim_alt(claim_text)
        selected_claim = claim_info[claim_number]
        dependant_claims = get_dependant_claims(selected_claim, model_llm)
        
        if dependant_claims['dependant_claims']:
            
            print('Found depedant claims for the selected claim', dependant_claims['dependant_claims'])
            
            for dependant_claim_number in dependant_claims['dependant_claims']:
                depedant_claims_text.append('Claim ' + str(dependant_claim_number) + '\n' + claim_info[dependant_claim_number])

        output_data['claim_text'] = selected_claim
        output_data['depedant_claims_text'] = depedant_claims_text
        
    elif number_of_claims != 0: # standard structure
        
        claim_info = get_n_claim(claim_text,number_of_claims=number_of_claims)
        selected_claim = epab.clean_text(claim_info[claim_number][0])

        # Dependant claims
        dependant_claims = get_dependant_claims(selected_claim, model_llm)
        
        if dependant_claims['dependant_claims']:
            
            print('Found depedant claims for the selected claim', dependant_claims['dependant_claims'])
            
            for dependant_claim_number in dependant_claims['dependant_claims']:
                depedant_claim_text = epab.clean_text(claim_info[dependant_claim_number][0])
                depedant_claims_text.append('Claim ' + str(dependant_claim_number) + '\n' + depedant_claim_text)
                
        output_data['claim_text'] = selected_claim
        output_data['depedant_claims_text'] = depedant_claims_text # list of depedant claims
    else:
        raise ValueError("Could not read Claim information. Is the HTML in a correct format?")
        
    
    if field_of_invention:
        output_data['field_of_invention_text'] = patent_desc_info['FIELD OF THE INVENTION']
    if background_of_the_invetion:
        output_data['background_of_the_invetion_text'] = patent_desc_info['BACKGROUND OF THE INVENTION']
    if summary_of_the_invetion:    
        output_data['summary_of_the_invention_text'] = patent_desc_info['SUMMARY OF THE INVENTION']
    if brief_description_of_the_drawings:
        output_data['brief_description_of_the_drawings_text'] = patent_desc_info['BRIEF DESCRIPTION OF THE DRAWINGS']
    if detailed_description_of_the_embodiments:
        output_data['detailed_description_of_the_embodiments_text'] = patent_desc_info['DETAILED DESCRIPTION OF THE EMBODIMENTS']

    if retrieve_patent_images:
        result = q.get_drawings(output_type="dataframe")

        # Convert IPython Image object to a byte stream
        number_images = len(result["attachment"][0])
        if number_images < 1:
            print('No attachments were found')
        else:        
            print('Found' , number_images, ' images')
    
            output_data['pil_image'] = [None] * number_images
            output_data['encoded_image'] = [None] * number_images
    
            for idx, image in enumerate(result["attachment"][0]):
                image_bytes = io.BytesIO(result["attachment"][0][idx]['content'])
            
                # Open the image using PIL
                pil_image = PILImage.open(image_bytes)
            
                # Encode the image
                encoded_image = utils.encode_image_array(pil_image)
            
                # # Convert the PIL image to a NumPy array
                # image_array = np.array(pil_image)
        
                output_data['encoded_image'][idx] = encoded_image
                output_data['pil_image'][idx] = pil_image

    
    return output_data