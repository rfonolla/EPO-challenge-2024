import utils
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings

def generate_image_from_code(input_text, prompt_template, output_filename, print_prompt):


    input_prompt = PromptTemplate((prompt_template))

    if print_prompt:
        print(input_prompt.format(output_filename=output_filename,information=input_text))
    
    # Query the LLM to generate the summary or answer
    summary = Settings.llm.complete(input_prompt.format(output_filename=output_filename,
                                                        information=input_text
                                                       )
                                   )    
    result = utils.get_code_from_text(summary.text)
        
    try:
        exec(result)
        print("Code executed successfully")
    except Exception as e:
        print(f"Error executing code: {e}")

