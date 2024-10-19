import os
import subprocess
import tempfile
from datetime import datetime
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
import utils

def execute_dynamic_code(code_str: str) -> int:
    """
    Execute dynamically generated Python code.

    Args:
        code_str (str): Python code as a string.

    Returns:
        int: 0 if execution was successful, error message otherwise.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_filename = temp_file.name
        # Write the code to the temporary file
        temp_file.write(code_str)
    
    # Execute the temporary Python file
    result = subprocess.run(['python', temp_filename], capture_output=True, text=True)
    
    # Print any errors
    if result.stderr:
        print("Errors:")
        print(result.stderr)
        return result.stderr
    else:
        print("Code executed successfully. Image written in 'images' folder")
    
    # Delete the temporary file
    os.unlink(temp_filename)  
    
    return 0  # Return 0 if execution was successful

def generate_image_from_code(input_text: str, prompt_template: str, output_filename: str, max_tokens_code: int, print_prompt: bool) -> str:
    """
    Generate an SVG image from a text description using an LLM.

    Args:
        input_text (str): Text description of the image to generate.
        prompt_template (str): Template for the LLM prompt.
        output_filename (str): Desired output filename for the SVG.
        max_tokens_code (int): Maximum number of tokens for the LLM response.
        print_prompt (bool): Whether to print the generated prompt.

    Returns:
        str: The filename of the generated SVG image.
    """
    Settings.llm.max_tokens = max_tokens_code
    input_prompt = PromptTemplate(prompt_template)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_format = output_filename[output_filename.rfind('.')+1:]
    output_filename = output_filename.replace('.'+file_format, f'_{timestamp}.{file_format}')
    
    # Create output directory
    os.makedirs('./images', exist_ok=True)
    
    if print_prompt:
        print(input_prompt.format(output_filename=output_filename, information=input_text))
    
    # Generate initial code
    summary = Settings.llm.complete(input_prompt.format(output_filename=output_filename, information=input_text))
    result = utils.get_code_from_text(summary.text)
    
    # Execute code
    execution_result = execute_dynamic_code(result)

    # If the execution failed try to fix the code
    attempts = 1
    while execution_result != 0 and attempts <= 10:
        print(f'Found an error in the code: attempting to fix it. Attempt: {attempts}')
        input_text_correction = """
        You are an expert Python developer specializing in SVG image generation. You have provided the following script {code}. 
        Your code is incorrect and shows the following error : {error}
        Please correct the code and keep in mind the following points: 
        - Use the svgwrite library to create the SVG image.
        - Include the title of the invention.
        - Use a canvas size of 512x512 pixels
        - Choose appropriate shapes for each object in the claim.
        - Use distinct colors for each object or category.
        - Use arrows to indicate directions when needed.
        - Include a legend that doesn't overlap with the main image.
        - Every element needs to have a legend.
        - Position the legend in the top left corner of the image and make sure it does not fall outside of borders
        - Use small icons and text to represent each item in the legend
        - Add appropriate labels or text where necessary to clarify the image.
        - Ensure the code is well-commented and easy to understand.
        - Do not use mm as position.
        - Name the image {output_filename}
        """
        
        # Query the LLM to generate corrected code
        summary = Settings.llm.complete(input_text_correction.format(
            output_filename=output_filename,
            code=result,
            error=execution_result
        ))
        result = utils.get_code_from_text(summary.text)
        
        # Execute corrected code
        execution_result = execute_dynamic_code(result)
        attempts += 1
    
    return output_filename