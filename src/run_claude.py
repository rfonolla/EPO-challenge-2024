import os
from utils import *
import login_claude
import os
import requests
import json
import anthropic

# user_input = f"You are an expert patent attorney. Summarize the following claim. The JSON field is 'summary'. Extract the references numbers  and the term to which is referenced. The JSON field is 'ref'and the subfield are 'num' and 'term'. Return the information as a JSON only. 
    
def run_claude(claim, numbers_claim, description):
    
    #models = ["claude-3-5-sonnet-20240620","claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    
    user_input = f"You are an expert patent attorney. Summarize the following claim and list the referenced numbers. Output in JSON format with keys: 'summary', 'references' (list of dicts with 'num'and 'term'). Do not output preamble or explanations. The claim is the following: {claim}."# Use the information of the description to enhance your summary: {description}."

    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key=os.environ["CLAUDE_KEY_roger"],
    )
    messages = [
        {"role": "user", "content": user_input}
    ]
        
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=messages
    )
    print(response.content[0].text)

    with open('./res_claude_no_desc.txt', 'w') as file:
        file.write(response.content[0].text)

    # Read response
    with open('./res_claude_no_desc.txt', "r") as file:
        response = file.read()
        
    # Extract the JSON data from the text
    start_index = response.find('{')
    end_index = response.rfind('}') + 1
    json_data = response[start_index:end_index]
    
    # Convert the JSON part to a Python dictionary
    data = json.loads(json_data)
    print(data["summary"])  # Prints the summary
    print(data["references"])      # Prints the list of references

    
    # # Extract the summary using a regex pattern
    # summary_match = re.search(r'Summary:\n(.*?)(?=\nRef:)', response, re.DOTALL)
    # summary = summary_match.group(1).strip() if summary_match else ""
    
    # # Extract the reference information
    # ref = {}
    # ref_section = re.search(r'Ref:\n(.*)', response, re.DOTALL)
    # if ref_section:
    #     ref_lines = ref_section.group(1).strip().split('\n')
    #     for line in ref_lines:
    #         key, value = re.match(r'(\w+) - (.+)', line).groups()
    #         ref[key] = value
    
    # # Printing the extracted variables
    # print("Summary:")
    # print(summary)
    # print("\nReference Information:")
    # print(ref)
    
    # # Convert the array to a set for efficient lookup
    # array_set = set(numbers_claim)
    
    # # Find which keys in the dictionary are in the array
    # keys_in_array = {key for key in ref if key in array_set}
    
    # # Print the results
    # print("Keys in summary that exist in the processed image:")
    # print(keys_in_array)