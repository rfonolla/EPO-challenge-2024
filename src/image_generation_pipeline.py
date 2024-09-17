import utils
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
from datetime import datetime



# Create filename with timestamp
def generate_image_from_code(input_text, prompt_template, output_filename, max_tokens_code, print_prompt):

    Settings.llm.max_tokens = max_tokens_code

    input_prompt = PromptTemplate((prompt_template))

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"output_{timestamp}.svg"

    output_filename = output_filename.replace('.','_' + timestamp+'.')

    if print_prompt:
        print(input_prompt.format(output_filename=output_filename,information=input_text))
    
    # Query the LLM to generate the summary or answer
    summary = Settings.llm.complete(input_prompt.format(output_filename=output_filename,
                                                        information=input_text
                                                       )
                                   )    
    result = utils.get_code_from_text(summary.text)

    print(result)
        
    try:
        exec(result)
        print("Code executed successfully")
    except Exception as e:            
        print(f"Error executing code: {e}")

