import os
from utils import *
# EPO libraries
from epo.tipdata.epab import EPABClient
from PIL import Image as PILImage
import numpy as np
import io

def get_data__from_patent(application_number='21198556', claim_number=1):

    # Start EPO Client
    epab = EPABClient(env='PROD')
    
    # Get patent by number
    
    q = epab.query_application_number(application_number)

    query_claims_description = q.get_results('claims, description', output_type='list')
    claim_text = query_claims_description[0]['claims'][0]['text']
    description_text = epab.clean_text(query_claims_description[0]['description']['text'])
    # Count number of claims
    number_of_claims = count_claims(claim_text)
    selected_claim = get_n_claim(claim_text, n_claim=claim_number)
    clean_claim = epab.clean_text(selected_claim[0])

    # Images
    result = q.get_results(["publication.language"], attachment=["DRW", "PDF"], output_type="list", limit=1)
    
    # Convert IPython Image object to a byte stream
    image_bytes = io.BytesIO(result[0]["attachment"][1]["content"])

    # Open the image using PIL
    pil_image = PILImage.open(image_bytes)
    
    # Convert the PIL image to a NumPy array
    image_array = np.array(pil_image)
    
    return description_text, clean_claim, image_array