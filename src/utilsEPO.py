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

# llama-index
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic

# Initialize EPAB Client for production environment
epab = EPABClient(env='PROD')

def extract_dependent_claims(selected_claim, claim_number, model_llm, claim_info, flag_alt, dependent_claim_exists=None):
    """
    Recursively extract dependent claims for a given claim.
    
    Args:
        selected_claim (str): The claim to extract dependents for.
        claim_number (int): The number of the selected claim.
        model_llm (str): The language model to use for extraction.
        claim_info (list): Information about all claims.
        flag_alt (bool): Flag to determine text cleaning method.
        dependent_claim_exists (set, optional): Set to track processed claims.
    
    Returns:
        list: List of dependent claim texts.
    """
    dependent_claim_exists = dependent_claim_exists or set()
    dependent_claims_info = get_dependent_claims(selected_claim, claim_number, model_llm)
    dependent_claims_text = []

    if dependent_claims_info['dependent_claims']:
        print('Found dependent claims', dependent_claims_info["dependent_claims"])

        for dependent_claim_number in dependent_claims_info['dependent_claims']:
            if dependent_claim_number not in dependent_claim_exists:
                dependent_claim_exists.add(dependent_claim_number)
                
                # Format dependent claim text based on flag_alt
                if flag_alt:
                    dependent_claim_text = epab.clean_text(claim_info[dependent_claim_number-1][0])
                    dependent_claims_text.append(f'Claim {dependent_claim_number}\n{dependent_claim_text}')
                else:
                    dependent_claim_text = f'Claim {dependent_claim_number}\n{claim_info[dependent_claim_number-1]}'
                dependent_claims_text.append(dependent_claim_text)
                
                # Recursively get nested dependent claims
                nested_claims = extract_dependent_claims(dependent_claim_text, dependent_claim_number, model_llm, claim_info, flag_alt, dependent_claim_exists)
                dependent_claims_text.extend(nested_claims)

    return dependent_claims_text

def get_dependent_claims(claim_info, claim_number, model_llm):
    """
    Use a language model to identify dependent claims.
    
    Args:
        claim_info (str): The claim text.
        claim_number (int): The number of the claim.
        model_llm (str): The language model to use.
    
    Returns:
        dict: Dictionary containing dependent claim numbers.
    """
    # Initialize language model based on the model name
    llm = Anthropic(model=model_llm, temperature=0.0, max_tokens=1024)
    Settings.llm = llm
    
    # Define prompt template for the language model
    prompt_template = '''You are an expert patent examiner. I want to know information about claim number {claim_number}. The claim text is the following:
    {claim_info}
    Are there any dependent claims? Return the number of claims I need to know for this specific claim.
    Only return dependent claims if it is explicitly mentioned in the claim information.
    Do not infer information.
    Return the information as a JSON using the following template:
    "dependent_claims":"list of integer claims"
    Do not return any additional information or explanation.'''

    input_prompt = PromptTemplate((prompt_template))

    # Get response from the language model
    summary = Settings.llm.complete(input_prompt.format(claim_number=claim_number, claim_info=claim_info))
    response = summary.text

    # Extract and parse JSON from the response
    json_start = response.index('{')
    json_end = response.rindex('}') + 1
    json_str = response[json_start:json_end]
    data_dict = json.loads(json_str)

    # Filter out invalid dependent claims
    data_dict['dependent_claims'] = [num for num in data_dict['dependent_claims'] if num < claim_number]

    print(data_dict)
    return data_dict

def count_claims(input_text):
    """
    Count the number of claims in the input text.
    
    Args:
        input_text (str): The text containing claims.
    
    Returns:
        int: The number of claims found.
    """
    claim_pattern = r'<claim id="[^"]+" num="\d+"><claim-text>'
    claims = re.findall(claim_pattern, input_text)
    return len(claims)

def get_n_claim_alt(input_text):
    """
    Alternative method to extract claim information when standard structure is not present.
    
    Args:
        input_text (str): The text containing claims.
    
    Returns:
        list: List of claim texts.
    """
    soup = BeautifulSoup(input_text, 'html.parser')
    elements = soup.find_all('claim-text')
    claim_info = []
    for element in elements:
        text = element.text.strip()
        if not text.isupper():  # Exclude headers
            claim_info.append(text)
    return claim_info

def get_n_claim(input_text, number_of_claims):
    """
    Extract claim information for a given number of claims.
    
    Args:
        input_text (str): The text containing claims.
        number_of_claims (int): The number of claims to extract.
    
    Returns:
        list: List of claim texts.
    """
    claim_info = []

    for n in range(1, number_of_claims + 1):
        # Format claim number for regex pattern
        if len(str(n)) == 1:
            num_format = r'000' + str(n) 
        elif len(str(n)) == 2:
            num_format = r'00' + str(n) 
        elif len(str(n)) == 3:
            num_format = r'0' + str(n) 
        else:
            num_format = r'\d{' + str(n) + '}'
        
        # Extract claim using regex
        claim_pattern = rf'(<claim id="[^"]+" num="{num_format}"><claim-text>.*?)(?=<claim id|$)'
        claims = re.findall(claim_pattern, input_text, re.DOTALL)
        claim_info.append(claims)

    return claim_info

def get_patent_info_from_description(query):
    """
    Extract patent information from the description.
    
    Args:
        query (list): List containing patent information.
    
    Returns:
        dict: Dictionary of patent information sections.
    """
    # Input validation
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
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(['heading', 'p'])

    # Define standard and alternative headings
    headings_patent = [
        "field of the invention",
        "background of the invention",
        "summary of the invention",
        "brief description of the drawings",
        "detailed description of the embodiments",
        # Alternative headings
        "technical field and background",
        "brief description of drawings",
        "summary",
        "description of embodiments",
    ]
    
    patent_dict = {heading: "" for heading in headings_patent}
    current_heading = None
    detailed_description_found = False

    # Extract content for each heading
    for element in elements:
        text = element.text.strip()
        if text.strip().lower() in headings_patent:
            current_heading = text.strip().lower()
            print(current_heading)
            if current_heading.lower() in ["detailed description of the embodiments", "description of embodiments"]:
                detailed_description_found = True
        elif current_heading:
            if detailed_description_found or current_heading not in ["detailed description of the embodiments", "description of embodiments"]:
                patent_dict[current_heading] += f"{text}"

    # Clean up the extracted content
    for heading in patent_dict:
        patent_dict[heading] = patent_dict[heading].strip()

    patent_dict = {k: v if v else None for k, v in patent_dict.items()}
    return patent_dict

def get_data_from_patent(**kwargs):
    """
    Retrieve and process patent data based on provided parameters.
    
    Args:
        **kwargs: Input parameters for data retrieval and processing.
    
    Returns:
        dict: Processed patent data including claims, descriptions, and images.
    """
    # Extract parameters from kwargs
    search_number = kwargs.get('patent_number', False)
    claim_number = kwargs.get('claim_number')
    dependent_claims = kwargs.get('dependent_claims')
    field_of_invention = kwargs.get('field_of_invention', False)
    background_of_the_invention = kwargs.get('background_of_the_invention', False)
    summary_of_the_invention = kwargs.get('summary_of_the_invention', False)
    brief_description_of_the_drawings = kwargs.get('brief_description_of_the_drawings', False)
    detailed_description_of_the_embodiments = kwargs.get('detailed_description_of_the_embodiments', False)
    retrieve_patent_images = kwargs.get('retrieve_patent_images', False)
    model_llm = kwargs.get('model_llm')
    
    # Initialize output data structure
    output_data = {
        'claim_text': None,
        'dependent_claims_text': None,
        'field_of_invention_text': None,
        'background_of_the_invention_text': None,
        'summary_of_the_invention_text': None,
        'brief_description_of_the_drawings_text': None,
        'detailed_description_of_the_embodiments_text': None,
        'pil_image': None,
        'encoded_image': None
    }

    print('summary invention flag:', summary_of_the_invention)

    # Retrieve patent data
    print('Patent number:', search_number)
    q = epab.query_epab_doc_id(search_number)
    query_claims_description = q.get_results('claims, description', output_type='list')
    patent_desc_info = get_patent_info_from_description(query_claims_description)

    # Process claim information
    claim_text = query_claims_description[0]['claims'][0]['text']    
    number_of_claims = count_claims(claim_text)
    dependent_claims_text = []

    if number_of_claims == 0:
        # Handle alternative claim structure
        claim_info = get_n_claim_alt(claim_text)
        if claim_number > len(claim_info):
            raise ValueError(f'Claim number not available, the number of claims for this patent is: {len(claim_info)}')
        selected_claim = claim_info[claim_number]
        if dependent_claims:
            dependent_claims_text = extract_dependent_claims(selected_claim, claim_number, model_llm, claim_info, False)
    elif number_of_claims != 0:
        # Handle standard claim structure
        if claim_number > number_of_claims:
            raise ValueError(f'Claim number not available, the number of claims for this patent is: {number_of_claims}')
        claim_info = get_n_claim(claim_text, number_of_claims=number_of_claims)
        selected_claim = epab.clean_text(claim_info[claim_number-1][0])
        if dependent_claims:
            dependent_claims_text = extract_dependent_claims(selected_claim, claim_number, model_llm, claim_info, True, None)
    else:
        raise ValueError("Could not read Claim information. Is the HTML in a correct format?")

    # Populate output data
    output_data['claim_text'] = selected_claim
    output_data['dependent_claims_text'] = dependent_claims_text

    # Add requested patent description sections to output
    if field_of_invention:
        if 'field of the invention' in patent_desc_info:
            output_data['field_of_invention_text'] = patent_desc_info['field of the invention']
        elif 'technical field and background' in patent_desc_info:
            output_data['field_of_invention_text'] = patent_desc_info['technical field and background']
            
    if background_of_the_invention:
        if 'background of the invention' in patent_desc_info:
            output_data['background_of_the_invention_text'] = patent_desc_info['background of the invention']
        elif 'technical field and background' in patent_desc_info:
            output_data['background_of_the_invention_text'] = patent_desc_info['technical field and background']
    
    if summary_of_the_invention:
        if 'summary of the invention' in patent_desc_info:
            output_data['summary_of_the_invention_text'] = patent_desc_info['summary of the invention']
        elif 'summary' in patent_desc_info:
            output_data['summary_of_the_invention_text'] = patent_desc_info['summary']
    
    if brief_description_of_the_drawings:
        if 'brief description of the drawings' in patent_desc_info:
            output_data['brief_description_of_the_drawings_text'] = patent_desc_info['brief description of the drawings']
        elif 'brief description of drawings' in patent_desc_info:
            output_data['brief_description_of_the_drawings_text'] = patent_desc_info['brief description of drawings']
    
    if detailed_description_of_the_embodiments:
        if 'detailed description of the embodiments' in patent_desc_info:
            output_data['detailed_description_of_the_embodiments_text'] = patent_desc_info['detailed description of the embodiments']
        elif 'description of embodiments' in patent_desc_info:
            output_data['detailed_description_of_the_embodiments_text'] = patent_desc_info['description of embodiments']
    
    if detailed_description_of_the_embodiments:
        if patent_desc_info['detailed description of the embodiments']:
            output_data['detailed_description_of_the_embodiments_text'] = patent_desc_info['detailed description of the embodiments']
        elif patent_desc_info['description of embodiments']:
            output_data['detailed_description_of_the_embodiments_text'] = patent_desc_info['description of embodiments']

    # Retrieve and process patent images if requested
    if retrieve_patent_images:
        result = q.get_drawings(output_type="dataframe")
        number_images = len(result["attachment"][0])
        
        if number_images < 1:
            print('No attachments were found')
        else:        
            print('Found', number_images, 'images')
            output_data['pil_image'] = [None] * number_images
            output_data['encoded_image'] = [None] * number_images
    
            for idx, image in enumerate(result["attachment"][0]):
                image_bytes = io.BytesIO(result["attachment"][0][idx]['content'])
                pil_image = PILImage.open(image_bytes)
                encoded_image = utils.encode_image_array(pil_image)
                output_data['encoded_image'][idx] = encoded_image
                output_data['pil_image'][idx] = pil_image

    return output_data