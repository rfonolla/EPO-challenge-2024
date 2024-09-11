import os
import utils
# EPO libraries
from epo.tipdata.epab import EPABClient
from PIL import Image as PILImage
import numpy as np
import io

def get_data_from_patent(**kwargs):
    
    application_number = kwargs.get('application_number')
    claim_number = kwargs.get('claim_number')
    patent_description = kwargs.get('patent_description', False)
    patent_images = kwargs.get('patent_images', False)
    
    output_data = {'claim_text': None,
                   'description_text':None,
                   'images': None,
                   'encoded_images': None
                  } 

    # Start EPO Client
    epab = EPABClient(env='PROD')
    
    # Get patent by number
    q = epab.query_application_number(application_number)
 

    # To improve this part more dynamically
    if patent_description:
        print('Obtaining patent description')
        query_claims_description = q.get_results('claims, description', output_type='list')
        output_data['description_text']  = epab.clean_text(query_claims_description[0]['description']['text'])
        claim_text = query_claims_description[0]['claims'][claim_number-1]['text']
        
    else:
        query_claims_description = q.get_results('claims, description', output_type='list')
        claim_text = query_claims_description[0]['claims'][claim_number-1]['text']


    # Count number of claims
    number_of_claims = utils.count_claims(claim_text)
    selected_claim = utils.get_n_claim(claim_text, n_claim=claim_number)
    output_data['claim_text'] = epab.clean_text(selected_claim[0])

    # Images
    if patent_images:
        result = q.get_results(["publication.language"], attachment=["DRW", "PDF"], output_type="list", limit=1)
    
        # Convert IPython Image object to a byte stream
        image_bytes = io.BytesIO(result[0]["attachment"][1]["content"])
    
        # Open the image using PIL
        pil_image = PILImage.open(image_bytes)
    
        # Encode the image
        encoded_image = utils.encode_image_array(pil_image)
    
        # Convert the PIL image to a NumPy array
        image_array = np.array(pil_image)

        output_data['encoded_image'] = encoded_image
        output_data['images'] = image_array

    
    return output_data