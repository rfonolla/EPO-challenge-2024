import os
from RAG_pipeline import *
import utils
import utilsEPO
import warnings
from image_generation_pipeline import *
from login_claude import *
import json

warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":


    # Read the JSON file
    with open('config.json', 'r') as file:
        args = json.load(file)

    # Initialize the appropriate LLM based on the model name
    model_llm = args['model_llm']
    if 'claude' in model_llm.lower():
        llm = Anthropic(model=model_llm, temperature=args['temperature'], max_tokens=args['max_tokens']) # ["claude-3-5-sonnet-20240620","claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307","gpt-3.5-turbo"]
    elif 'gpt' in model_llm.lower():
        llm = OpenAI(model=model_llm, temperature=args['temperature'], max_tokens=args['max_tokens'])
    else:
        raise ValueError(f"Unsupported model: {model_llm}")


    # Prepare arguments for get_data_from_patent
    dict_args = {
        'application_number': args['application_number'],
        'claim_number': args['claim_number'],
        'patent_description': args['patent_description'],
        'patent_images': args['patent_images']
    }
    
    print('Obtaining Claim data')
    data_patent = utilsEPO.get_data_from_patent(**dict_args)
    
    print('Detecting numbers from selected image')
    if dict_args['patent_images']:
        numbers_claim = utils.get_numbers_from_Image(data_patent['images'])
    
    print('Running RAG Pipeline')
    output_result = run_RAG_pipeline(llm=llm,
                                     prompt_template=args['prompt_template'],
                                     claim_text=data_patent['claim_text'], 
                                     description_text=data_patent['description_text'],
                                     print_prompt=args['print_prompt'])
    print(output_result)
    
    image_code = generate_image_from_code(output_result, 
                                          prompt_template=args['prompt_template_image'])                        

        
    