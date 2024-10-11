import anthropic
import utils
import collections
from transformers import CLIPProcessor, CLIPModel
import json 

from PIL import Image
import torch
import numpy as np

def run_claude_on_image(input_prompt, client: anthropic.Anthropic, input_images: list, model_llm: str) -> str:
    """
    Run Claude AI on an encoded image.

    Args:
        client (anthropic.Anthropic): Anthropic client instance.
        image_encoded (str): Base64 encoded image data.

    Returns:
        str: JSON string containing extracted figure numbers.
    """
    user_input = input_prompt.replace('Return the information as a JSON using the following template with fields:', ' The attached retrieved images are the most informative for the claim use them additional information\n Return the information as a JSON using the following template with fields:')

    content = []

    # Add each image to the content
    for image in input_images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image,
            },
        })
    
    # Add the text input
    content.append({
        "type": "text",
        "text": user_input
    })


    # Send the request
    response = client.messages.create(
        model=model_llm,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    
    
    return response.content[0].text

def run_summary_with_retrieved_images(input_prompt: str, images: list, model_llm: str) -> dict:
    """
    Generates a summary of the claim based on a previous prompt and top retrieved images.

    Args:
        images (list): List of base64 encoded image data.
        model_llm (str): Name of the language model to use.

    Returns:
        dict: Dictionary containing extracted figure numbers for each image.
    """
    client = anthropic.Anthropic()
    dict_numbers = collections.defaultdict(dict)
    
    output_text = run_claude_on_image(input_prompt, client, images, model_llm)
    
    # Extract and parse JSON from the response
    json_start = output_text.index('{')
    json_end = output_text.rindex('}') + 1
    json_str = output_text[json_start:json_end]
    data_dict = json.loads(json_str)
    
    return data_dict['summary'], data_dict['reference']


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
