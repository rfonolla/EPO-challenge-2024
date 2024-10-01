import utils
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
from datetime import datetime

import os
import subprocess
import tempfile

def execute_dynamic_code(code_str):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_filename = temp_file.name
        # Write the code to the temporary file
        temp_file.write(code_str)

    # Execute the temporary Python file
    result = subprocess.run(['python', temp_filename], capture_output=True, text=True)
    
    # Print the output
    print("Execution output:")
    print(result.stdout)

    # Print any errors
    if result.stderr:
        print("Errors:")
        print(result.stderr)
        return result.stderr
    else:
        print("Code executed successfully. Image written in 'images'folder ")
        
    # Delete the temporary file
    os.unlink(temp_filename)  
    
    return 0 # Return True if execution was successful


def generate_image_from_code(input_text, prompt_template, output_filename, max_tokens_code, print_prompt):

    Settings.llm.max_tokens = max_tokens_code
    input_prompt = PromptTemplate((prompt_template))

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_format = output_filename[output_filename.rfind('.')+1:]
    output_filename = output_filename.replace('.'+file_format,'_' + timestamp+'.'+file_format)

    # Mkdir for output images
    os.makedirs('./images', exist_ok=True)

    if print_prompt:
        print(input_prompt.format(output_filename=output_filename,information=input_text))

    # Execute once
    # Query the LLM to generate the summary or answer
    summary = Settings.llm.complete(input_prompt.format(output_filename=output_filename,
                                                        information=input_text)
                                   )
    result = utils.get_code_from_text(summary.text)
    # Execute code
    execution_result = execute_dynamic_code(result)
    
    attempts =0    
    while execution_result != 0 and attempts < 10:
        print('Found an error in the code: attempting to fix it. Attempt:', attempts)
        input_text_correction = "You are an expert Python developer specializing in SVG image generation. You have provided the following script {code}. \
        Your code is incorrect and shows the following error : {error}\
        Please correct the code and keep in mind the following points: \
        \nUse the svgwrite library to create the SVG image.\nInclude the title of the invention.\
        \nUse a canvas size of 512x512 pixels\nChoose appropriate shapes for each object in the claim.\nUse distinct colors for each object or category.\
        \n Use arrows to indicate directions when needed.\nInclude a legend that doesn't overlap with the main image.\nEvery element needs to have a legend.\
        \nPosition the legend in the top left corner of the image and make sure it does not fall outside of borders\
        \nUse small icons and text to represent each item in the legend\
        \nAdd appropriate labels or text where necessary to clarify the image.\
        \nEnsure the code is well-commented and easy to understand.\
        \n Do not use mm as position.\n Name the image {output_filename}"
        
        # Query the LLM to generate the summary or answer
        summary = Settings.llm.complete(input_text_correction.format(output_filename=output_filename,
                                                            code=result,
                                                            error=execution_result) 
                                       )
        result = utils.get_code_from_text(summary.text)
        # Execute code
        execution_result = execute_dynamic_code(result)
        attempts +=1
        
    return output_filename


