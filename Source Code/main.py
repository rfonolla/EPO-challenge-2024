import os
import sys
import json
import argparse
import warnings
from pprint import pprint

# Custom module imports
from RAG_pipeline import *
import utils
import utilsEPO
from image_generation_pipeline import *
import image_retrieval_pipeline
from login_claude import *
import validation
from transformers.utils.logging import disable_progress_bar
disable_progress_bar()
# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def load_config(file_path):
    """
    Load and parse a JSON configuration file.

    Args:
        file_path (str): Path to the JSON config file.

    Returns:
        dict: Parsed configuration data.

    Raises:
        SystemExit: If file cannot be read or parsed.
    """
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
    """
    Main function to process patent data and generate images.

    Args:
        args (dict): Configuration parameters.

    Returns:
        tuple: Summary, output filename, patent data, and top images.
    """
    # Initialize the appropriate LLM based on the model name
    model_llm = args['model_llm']
    llm = Anthropic(model=model_llm, temperature=int(args['temperature']), max_tokens=int(args['max_tokens']))

    
    # Prepare arguments for get_data_from_patent
    dict_args = {
        'model_llm': args['model_llm'],
        'patent_number': args['patent_number'],
        'claim_number': args['claim_number'],
        'dependent_claims': args['dependent_claims'],
        'field_of_invention': args['field_of_invention'],
        'background_of_the_invention': args['background_of_the_invention'],
        'summary_of_the_invention': args['summary_of_the_invention'],
        'brief_description_of_the_drawings': args['brief_description_of_the_drawings'],
        'detailed_description_of_the_embodiments': args['detailed_description_of_the_embodiments'],
        'retrieve_patent_images': args['retrieve_patent_images']
    }
    
    print('Obtaining Claim data')
    data_patent = utilsEPO.get_data_from_patent(**dict_args)

    print('Summarizing claim...')
    summary, references, input_prompt = run_RAG_pipeline(
            llm=llm,
            retrieved_images=None,
            data_patent=data_patent,
            prompt_template=args['prompt_template'],
            print_prompt=args['print_prompt']
        )
    
    top_images = None
    if args['retrieve_patent_images'] and data_patent['pil_image'] and data_patent['encoded_image']:
        print('Retrieving most informative images...')
        top_indices = image_retrieval_pipeline.retrieve_similar_images(
            summary, 
            data_patent['pil_image'], 
            top_k=int(args['retrieve_top_k_images'])
        )
        top_images = [data_patent['encoded_image'][idx] for idx in top_indices]
        
        print('Summarizing claim based on most informative images...')
        summary, references = image_retrieval_pipeline.run_summary_with_retrieved_images(input_prompt, top_images, model_llm)

    print('Generating image from summary...')
    output_filename = generate_image_from_code(
        summary, 
        prompt_template=args['prompt_template_image'],
        output_filename=args['output_filename'],
        max_tokens_code=int(args['max_tokens_code']),
        print_prompt=args['print_prompt']
    )


    print("Patent Claim Summary Evaluation Results:")
    metrics = validation.evaluate_patent_claim_summary(data_patent, summary)
    pprint(metrics, width=100, sort_dicts=False)

    return summary, output_filename, data_patent, top_images, metrics
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs claude with an input config JSON file.")
    parser.add_argument("-i", "--input_json", required=True, help="Path to the JSON config file")
    args = parser.parse_args()
    config = load_config(args.input_json)
    
    main(config)