import os
from utils import *
import login_claude
import os
import requests
import json
import anthropic

# user_input = f"You are an expert patent attorney. Summarize the following claim. The JSON field is 'summary'. Extract the references numbers  and the term to which is referenced. The JSON field is 'ref'and the subfield are 'num' and 'term'. Return the information as a JSON only. 
    
def run_claude(claim, numbers_claim,  description, image, use_description= True, use_image=True):
    
    #models = ["claude-3-5-sonnet-20240620","claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key=os.environ["CLAUDE_KEY_roger"],
    )    
    user_input = f"You are an expert patent attorney. Summarize the following claim and list the referenced numbers. Output in JSON format with keys: 'summary', 'references' (list of dicts with 'num'and 'term'). Do not output preamble or explanations. The claim is the following: {claim}. Use the information of the description to enhance your summary: {description}."


    messages = [
        {"role": "user", "content": user_input}
    ]
        
    response_msg = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=messages
    )
    
    response = response_msg.content[0].text

    # Extract the JSON data from the text
    start_index = response.find('{')
    end_index = response.rfind('}') + 1
    json_data = response[start_index:end_index]
    
    # Convert the JSON part to a Python dictionary
    data = json.loads(json_data)
    summary = data["summary"] 
    ref = data["references"]   
    print(summary,ref)

    user_input = f"You are an expert patent attorney. You previously summarized the claim: {summary}: Enrich the summary utilizing the information of this image. Output in JSON format with keys: 'summary'. Only use information about the numbers present in the following json {ref}. If a number is not present in the json do not mention it." 
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image,
                        },
                    },
                    {
                        "type": "text",
                        "text": user_input
                    }
                ],
            }
        ],
    )
    print(response.content[0].text)

    with open('./res_claude_image.txt', 'w') as file:
        file.write(response.content[0].text)

    # # Read response
    # with open('./res_claude_image.txt', "r") as file:
    #     response = file.read()
        

    
    # # Convert the array to a set for efficient lookup
    # array_set = set(numbers_claim)
    
    # # Find which keys in the dictionary are in the array
    # keys_in_array = {key for key in ref if key in array_set}
    
    # # Print the results
    # print("Keys in summary that exist in the processed image:")
    # print(keys_in_array)