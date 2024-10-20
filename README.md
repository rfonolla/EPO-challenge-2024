# ORBIS PICTUS PATENS Solution

This is the repository for OPP solution. Our solution summarizes the key concepts of a patent in just once picture

This is a Python-based solution with the following features:

## 🌟 Features

- Claim patent summarization with customazible patent information.
- RAG (Retrieval-Augmented Generation) pipeline integration for text and image retrieval.
- Intelligent image retrieval system based on the generated summary.
- Summary improvement based on the retrieved images.
- Validation metrics based on Term Frequency Inverse Document Frequency (TF-IDF) to measure the importance of the summary respect to the patent information.
- Configurable settings via JSON.
- User interface via Pywidget launched via Jupyter.

## 📋 Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`)

## 🚀 Quick Start

The following commands will quickly set up everything you need. We assume that the base enviroment contains the EPO libraries since these cannot be downloaded with pip

1. Clone the repository:
```bash
git clone https://github.com/epo/CF24-ORBIS-PICTUS-PATENS.git
conda create --name orbis-pictus --clone base
conda activate orbis-pictus
cd CF24-ORBIS-PICTUS-PATENS/Source Code 
pip install -r requirements.txt
```

3. Configure your settings in `config.json` or leave it as it is:
```json
{
    "model_llm": "claude-3-5-sonnet-20240620",
    "temperature": 0.0,
    "max_tokens": 1024,
    "max_tokens_code": 2048,
    "patent_number": "EP4014838A1",
    "claim_number": 1,
    "dependent_claims":true,
    "field_of_invention": true,
    "background_of_the_invention": false,
    "summary_of_the_invention": true,
    "brief_description_of_the_drawings": true,
    "detailed_description_of_the_embodiments": true,
    "retrieve_patent_images": true,
    "retrieve_top_k_images": 3,
    "output_filename": "./images/EP4014838A1.svg",
    
     "prompt_template": "You are an expert patent examiner. Summarize the following claim and extract the reference numbers:\n{information}\nReturn the information as a JSON using the following template with fields:\n\"summary\":\"summary description\",\n\"reference\":\n with subfields the reference number \"reference number\":\"reference1\",\n        \"reference number\": \"reference2\"",
    
    "prompt_template_image": "You are an expert Python developer specializing in SVG image generation.Create a Python script to draw an SVG image for the following claim:\n{information}\nUse the following requirements and return the complete Python script:\nUse the svgwrite library to create the SVG image.\nInclude the title of the invention.\nUse a canvas size of 512x512 pixels\nChoose appropriate shapes for each object in the claim.\nUse distinct colors for each object or category.\n Use arrows to indicate directions when needed.\nInclude a legend that doesn't overlap with the main image.\nEvery element needs to have a legend.\nPosition the legend in the top left corner of the image and make sure it does not fall outside of borders\nUse small icons and text to represent each item in the legend\nAdd appropriate labels or text where necessary to clarify the image.\nEnsure the code is well-commented and easy to understand.\n Do not use mm as position.\n Name the image {output_filename}",
    
    "print_prompt": false
}

```

4. Run the main application:

Navigate to Source folder and run the following command:

```bash
python main.py -i config.json
```
The resulting output are three folders images, summary and retrieved images.
- Images contain the generated claim image
- Summary contains the summary of the claim with the validation metrics
- Retrieved images contains the top K selected images that are most informative respect to the selected claim.


The system uses two configuration files:
- `config.json`: Main configuration settings
- `default_config.json`: Default fallback values

5. Run the application via the User Interface.

- We have created a user interface using Pywidget. On the EPO enviroment select VSCode , double click app.py and Run Current File as Interactive Window as Interactive Window

- ![image](https://github.com/user-attachments/assets/aac00e0e-181c-44ff-a233-307d65adb8bc)

Click Submit and wait until the processing is done. The different tabs will be populated based on the selected flags. Enjoy!

6. The prompts in this solution have been highly optimized for the purpose of patents and claims. Feel free to play around.

![image](https://github.com/user-attachments/assets/d3bd909e-33f5-4c21-880c-762426a42928)


## ⚠️ Important information about LLM API, GPU and CPU and more

### CLAUDE API KEY

Due to the complexity of this project and the limited shared resources of the GPU of the EPO platform we cannot expect to run everything locally. Therefore CLAUDE has been chosen has the preferd LLM to perform our query tasks. Several prompts are designed to obtain relevant information about the claims and patent information. An API Key has been provided which contains enough credits and resources to run the program for plenty of hours and examples!

The following points and files utilize Claude API LLM:


- The RAG pipeline in `RAG_pipeline.py` utilizes the claim information in addition to the most important retrieved information from the patent to generate the summary. Which requires a prompt incorporating all the necessary information.
- The image retrieval pipeline in `image_retrieval_pipeline.py` utilizes CLAUDE to analyze the patent images and enhance the summary. This requires an API call to Claude in addition to a prompt template.
- The image generation pipeline in `image_generation_pipeline.py` utilizes a prompt to create the code that will generate the patent images.

Overall the cost of running this solution is about

### Local models and CPU vs GPU

Not everything is computed on the cloud. Wherever possible we have implemented local solutions. The following points are run locally:

- The RAG pipeline in `RAG_pipeline.py` utilizes the package `llama-index` to Vectorize claim information, and the patent information (brief description of embodings, etc). This utilizes a local model dowloaded from Hugging Face ("BAAI/bge-m3")

- The image retrieval pipeline in `image_retrieval_pipeline.py` utilizes openai/clip-vit-large-patch14 from Hugging Face to extract embeddings from a query text (related to the claim) and from the attachments to retrieve the most important and related images given a specific query.

- All this local models run by default on GPU but if the GPU is busy then it will run on CPU (We experienced a high demand of GPU resources)

### Automated python code generation

An important aspect of this project is the capability to generate images from the claim summary. These images are generated via python code which has been automatically created with LLMS. Somestimes the code will fail BUT DO NOT PANIC if you see an error :), we have incorporated a self mechanism that attempts to correct the code and continues the execution.



