import os
from RAG_pipeline import *
import utils
import utilsEPO
import warnings
from login_claude import *

warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":


    dict_args = { 'application_number': '21198556', 
             'claim_number':1,  
             'patent_description':True, 
             'patent_images':False
    }

    
    print('Obtaining Claim data')
    data_patent = utilsEPO.get_data_from_patent(**dict_args)
    
    print('Detecting numbers from selected image') # Recognize numbers from the image, this ideally needs to be done for each image
    if dict_args['patent_images']:
        numbers_claim = utils.get_numbers_from_Image(data_patent['images'])
    
    print('Running RAG Pipeline')
    output_result = run_RAG_pipeline(claim_text = data_patent['claim_text'], 
                                     description_text=data_patent['description_text']
                                    print_prompt=True)

    print(output_result)

#  1) generate 2 images, one based on the claim itself and the other based on the claim + description