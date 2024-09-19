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

    try:
        # Execute the temporary Python file
        result = subprocess.run(['python', temp_filename], capture_output=True, text=True)
        
        # Print the output
        print("Execution output:")
        print(result.stdout)

        # Print any errors
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        else:
            print("Code executed successfully. Image written in 'images'folder ")

        
        return result.returncode == 0  # Return True if execution was successful
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        # Delete the temporary file
        os.unlink(temp_filename)

def generate_image_from_code(input_text, prompt_template, output_filename, max_tokens_code, print_prompt):

    Settings.llm.max_tokens = max_tokens_code
    input_prompt = PromptTemplate((prompt_template))

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output_{timestamp}.svg"
    output_filename = output_filename.replace('.svg','_' + timestamp+'.svg')

    # Mkdir for output images
    os.makedirs('./images', exist_ok=True)

    if print_prompt:
        print(input_prompt.format(output_filename=output_filename,information=input_text))
    
    # Query the LLM to generate the summary or answer
    summary = Settings.llm.complete(input_prompt.format(output_filename=output_filename,
                                                        information=input_text)
                                   )    
    result = utils.get_code_from_text(summary.text)

    # Execute code
    execute_dynamic_code(result)


