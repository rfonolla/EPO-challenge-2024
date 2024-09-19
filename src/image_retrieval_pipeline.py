import anthropic
import utils
import collections


def run_claude_on_image(client,image_encoded):

    user_input = f"Extract the numbers of each figure and return a json with fields 'FIGX' containing all variations of the numbers as strings." 
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {"role": "user",
             "content": [
                 {"type": "image",
                  "source": {"type": "base64",
                             "media_type": "image/jpeg",
                             "data": image_encoded,
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
    
    return response.content[0].text

def retrieve_numbers_from_image(images, model_llm):

    client = anthropic.Anthropic()
    dict_numbers = collections.defaultdict(dict)

    if 'claude' in model_llm.lower():
        for idx,image_encoded in enumerate(images):
            output_text = run_claude_on_image(client,image_encoded)
            _tmpdict = utils.get_json_from_text(output_text)
            for d in _tmpdict:
                dict_numbers[d] = _tmpdict[d]            
    else:
        print('N.A')
        return 0

    return  dict_numbers
