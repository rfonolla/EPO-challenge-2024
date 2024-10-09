import anthropic
import utils
import collections
from transformers import CLIPProcessor, CLIPModel

from PIL import Image
import torch
import numpy as np

def run_claude_on_image(client: anthropic.Anthropic, image_encoded: str) -> str:
    """
    Run Claude AI on an encoded image to extract figure numbers.

    Args:
        client (anthropic.Anthropic): Anthropic client instance.
        image_encoded (str): Base64 encoded image data.

    Returns:
        str: JSON string containing extracted figure numbers.
    """
    user_input = "Extract the numbers of each figure and return a json with fields 'FIGX' containing all variations of the numbers as strings."
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

def retrieve_numbers_from_image(images: list, model_llm: str) -> dict:
    """
    Retrieve figure numbers from a list of images using Claude AI.

    Args:
        images (list): List of base64 encoded image data.
        model_llm (str): Name of the language model to use.

    Returns:
        dict: Dictionary containing extracted figure numbers for each image.
    """
    client = anthropic.Anthropic()
    dict_numbers = collections.defaultdict(dict)
    
    if 'claude' in model_llm.lower():
        for idx, image_encoded in enumerate(images):
            output_text = run_claude_on_image(client, image_encoded)
            tmp_dict = utils.get_json_from_text(output_text)
            for d in tmp_dict:
                dict_numbers[d] = tmp_dict[d]            
    else:
        print('N.A')
        return {}
    
    return dict(dict_numbers)


def retrieve_similar_images(query_text: str, image_data: list, top_k: int = 1) -> list:
    """
    Retrieve similar images based on a text query using CLIP model.

    Args:
        query_text (str): Text query to match against images.
        image_data (list): List of image data (PIL Images or file paths).
        top_k (int): Number of top similar images to retrieve.

    Returns:
        list: Indices of top similar images.
    """
    n_image = len(image_data)
    print(f"Number of images: {n_image}")
    
    # Ensure top_k doesn't exceed the number of available images
    top_k = min(top_k, n_image)
    
    # Check for GPU availability
    device = 'cuda' if utils.check_gpu_is_free(min_memory=5) else 'cpu'
    print(f"Using device: {device}")
    
    # Load pre-trained CLIP model and processor
    model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
    
    # Process the text input
    text_inputs = processor(text=[query_text], return_tensors="pt", padding=True, truncation=True)
    text_inputs = {k: v.to(device) for k, v in text_inputs.items()}
    
    # Process the images
    image_inputs = processor(images=image_data, return_tensors="pt", padding=True)
    image_inputs = {k: v.to(device) for k, v in image_inputs.items()}
    
    # Generate embeddings
    with torch.no_grad():
        text_features = model.get_text_features(**text_inputs)
        image_features = model.get_image_features(**image_inputs)
    
    # Normalize features
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    
    # Compute similarity scores
    similarity_scores = (text_features @ image_features.T).squeeze(0)
    
    # Get top k results
    top_results = torch.topk(similarity_scores, k=top_k)
    
    # Print results
    for idx, score in zip(top_results.indices.tolist(), top_results.values.tolist()):
        print(f"Image index: {idx}, Similarity Score: {score:.4f}")
    
    return top_results.indices.tolist()


# def retrieve_similar_images(query_text: str, image_data: list, top_k: int = 1) -> list:
#     """
#     Retrieve similar images based on a text query using CLIP model.

#     Args:
#         query_text (str): Text query to match against images.
#         image_data (list): List of image data (PIL Images or file paths).
#         top_k (int): Number of top similar images to retrieve.

#     Returns:
#         list: Indices of top similar images.
#     """
#     from transformers import CLIPTokenizer

#     n_image = len(image_data)
#     print(f"Number of images: {n_image}")
    
#     # Ensure top_k doesn't exceed the number of available images
#     top_k = min(top_k, n_image)
    
#     # Check for GPU availability
#     device = 'cuda' if utils.check_gpu_is_free(min_memory=5) else 'cpu'
#     print(f"Using device: {device}")
#     print(query_text)
#     # Load pre-trained CLIP model
#     model = SentenceTransformer('clip-ViT-L-14', device=device)
#     text_token = model.tokenizer(query_text)

#     tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")
#     tokens = tokenizer.tokenize(query_text)
#     print(len(tokens))
#     # Encode images and query text
#     image_embedding = model.encode(image_data, convert_to_tensor=True)
#     query_embedding = model.encode(text_token, convert_to_tensor=True)
#     # Compute cosine similarities
#     cos_scores = SentenceTransformerUtil.cos_sim(query_embedding, image_embedding)[0]
    
#     # Get top k results
#     top_results = torch.topk(cos_scores, k=top_k)
    
#     # Print results
#     for idx, score in zip(top_results.indices.tolist(), top_results.values.tolist()):
#         print(f"Image index: {idx}, Similarity Score: {score:.4f}")
    
#     return top_results.indices.tolist()