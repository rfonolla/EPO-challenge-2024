import os
import io

import numpy as np
from bs4 import BeautifulSoup
from PIL import Image as PILImage

# EPO libraries
from epo.tipdata.epab import EPABClient

# Own libs
import utils


def get_patent_info_from_description(query):

    html_content = query[0]['description']['text']
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(['heading', 'p'])
    headings_patent = [
        "FIELD OF THE INVENTION",
        "BACKGROUND OF THE INVENTION",
        "SUMMARY OF THE INVENTION",
        "BRIEF DESCRIPTION OF THE DRAWINGS",
        "DETAILED DESCRIPTION OF THE EMBODIMENTS"
    ]
    
    patent_dict = {heading: "" for heading in headings_patent}
    current_heading = None
    detailed_description_found = False
    
    for element in elements:
        text = element.text.strip()
        if text.strip().isupper() and text.strip() in headings_patent:
            current_heading = text.strip()
            if current_heading == "DETAILED DESCRIPTION OF THE EMBODIMENTS":
                detailed_description_found = True
        else:
            if current_heading:
                if detailed_description_found:
                    patent_dict[current_heading] += f"{text}"
                elif current_heading != "DETAILED DESCRIPTION OF THE EMBODIMENTS":
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
    
    output_data = {'claim_text': None,
                   'field_of_invention_text':None,
                   'background_of_the_invetion_text':None,
                   'summary_of_the_invention_text':None,
                   'brief_description_of_the_drawings_text':None,
                   'detailed_description_of_the_embodiments_text':None,
                   'image_array': None,
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
    number_of_claims = utils.count_claims(claim_text)
    selected_claim = utils.get_n_claim(claim_text, n_claim=claim_number)

    # Assign data:
    output_data['claim_text'] = epab.clean_text(selected_claim[0])
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

    # Images TBD improve the retrieval
    if retrieve_patent_images:
        result = q.get_drawings(output_type="dataframe")

        # Convert IPython Image object to a byte stream
        number_images = len(result["attachment"][0])
        print('There a total of' , number_images, ' images')

        output_data['image_array'] = [None] * number_images
        output_data['encoded_image'] = [None] * number_images

        for idx, image in enumerate(result["attachment"][0]):
            image_bytes = io.BytesIO(result["attachment"][0][idx]['content'])
        
            # Open the image using PIL
            pil_image = PILImage.open(image_bytes)
        
            # Encode the image
            encoded_image = utils.encode_image_array(pil_image)
        
            # Convert the PIL image to a NumPy array
            image_array = np.array(pil_image)
    
            output_data['encoded_image'][idx] = encoded_image
            output_data['image_array'][idx] = image_array

    
    return output_data