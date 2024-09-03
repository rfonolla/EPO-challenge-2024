import os
from getClaimInformation import *
from run_llama3 import *
from run_claude import *
from getNumbers_from_Image import *
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":

    print('Obtaining Claim data')
    description, claim, image = get_data__from_patent()
    
    print('Detecting numbers from selected image') # Recognize numbers from the image, this ideally needs to be done for each image
    numbers_claim = get_numbers_from_Image(image)

    
    print('Running claude')
    run_claude(claim, numbers_claim, description)
    # print('Running llama 3')
    # run_llama3(claim, numbers_claim)


#  1) generate 2 images, one based on the claim itself and the other based on the claim + description