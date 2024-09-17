import os
from RAG_pipeline import *
import utils
import utilsEPO
import warnings
from image_generation_pipeline import *
from login_claude import *
import argparse
import json
import sys

warnings.simplefilter(action='ignore', category=FutureWarning)

def load_config(file_path):
    try:
        with open(file_path, 'r') as config_file:
            return json.load(config_file)
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not a valid JSON file.")
        sys.exit(1)
    except IOError:
        print(f"Error: Could not read file {file_path}")
        sys.exit(1)

def main(args):

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
        'patent_number': args['patent_number'],
        'claim_number': args['claim_number'],
        'field_of_invention': args['field_of_invention'],
        'background_of_the_invetion': args['background_of_the_invetion'],
        'summary_of_the_invetion': args['summary_of_the_invetion'],
        'brief_description_of_the_drawings': args['brief_description_of_the_drawings'],
        'detailed_description_of_the_embodiments': args['detailed_description_of_the_embodiments'],
        'patent_images': args['patent_images']
    }

    print('Obtaining Claim data')
    data_patent = utilsEPO.get_data_from_patent(**dict_args)
    
    print('Detecting numbers from selected image')
    if dict_args['patent_images']:
        numbers_claim = utils.get_numbers_from_Image(data_patent['images'])
    
    print('Running RAG Pipeline')
    output_result = run_RAG_pipeline(llm=llm,
                                     data_patent=data_patent,
                                     prompt_template=args['prompt_template'],
                                     print_prompt=args['print_prompt']
                                     )
    
    _ = generate_image_from_code(output_result, 
                                 prompt_template=args['prompt_template_image'],
                                 output_filename = args['output_filename'],
                                 max_tokens_code = args['max_tokens_code'],
                                 print_prompt=args['print_prompt'])                        
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Runs claude with an input config JSON file.")
    parser.add_argument("-i", "--input_json", required=True, help="Path to the JSON config file")
    args = parser.parse_args()

    config = load_config(args.input_json)
    
    main(config)

        
    