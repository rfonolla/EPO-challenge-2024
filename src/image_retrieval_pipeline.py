import anthropic
import utils
import collections
from sentence_transformers import SentenceTransformer
from sentence_transformers import util as SentenceTrasnformerUtil
import utils
from PIL import Image
import torch
import numpy as np

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


def retrieve_similar_images(query_text, image_data, top_k=1):

    n_image = len(image_data)

    print("Images", n_image)

    # make sure we have the correct amount of top_k based on the amount of images
    top_k = min(top_k, n_image)

    if utils.check_gpu_is_free(min_memory=5): # 5GB should be more than enough for this model
        device = 'cuda'
    else:
        device = 'cpu'

    # Load a pre-trained model that can handle both text and images
    model = SentenceTransformer('clip-ViT-B-32',device=device)
    # Get the image embedding for all images
    image_embedding = model.encode(image_data, convert_to_tensor=True)

    # Encode the query text
    query_embedding = model.encode([query_text], convert_to_tensor=True)

    # Compute cosine similarities
    cos_scores = SentenceTrasnformerUtil.cos_sim(query_embedding, image_embedding)[0]
    
    # Get top k results
    top_results = torch.topk(cos_scores, k=top_k)
    
    # Print results
    for idx, score in zip(top_results.indices.tolist(), top_results.values.tolist()):
        print(f"Image index: {idx}, Similarity Score: {score:.4f}")

    return top_results.indices.tolist()


    

