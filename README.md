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

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-processing-pipeline.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `config.json`:
```json
{
    "model_llm": "claude-3-5-sonnet-20240620",
    "temperature": 0.0,
    "max_tokens": 1024,
    "max_tokens_code": 2048,
    "patent_number": "EP1356755A2",
    "claim_number": 1,
    "dependent_claims":true,
    "field_of_invention": true,
    "background_of_the_invention": true,
    "summary_of_the_invention": true,
    "brief_description_of_the_drawings": true,
    "detailed_description_of_the_embodiments": true,
    "retrieve_patent_images": true,
    "retrieve_top_k_images": 3,
    "output_filename": "./images/EP1356755A2.svg",
    
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


## 🗃️ Project Structure

```
├── images/                  # Image storage directory
├── app.py                   # Application entry point
├── config.json             # Configuration file
├── default_config.json     # Default configuration
├── image_generation_pipeline.py
├── image_retrieval_pipeline.py
├── logging_claude.py       # Logging configuration
├── main.py                # Main execution file
├── RAG_pipeline.py        # RAG implementation
├── utils.py               # Utility functions
└── validation.py          # Input validation
```

## ⚠️ Common Warnings and Solutions

### Warning: Invalid Image Directory
```python
WARNING: Image directory not found at path './images'
Solution: Create the 'images' directory or update the path in config.json
```

### Warning: Memory Usage
```python
WARNING: High memory usage detected during image processing
Solution: Adjust batch size in configuration or free up system memory
```

## 📝 Example Usage

```python
from image_generation_pipeline import ImageGenerator
from config import load_config

# Load configuration
config = load_config()

# Initialize generator
generator = ImageGenerator(config)

# Generate image
result = generator.process_image("input_image.jpg")
```

## 🔍 Logging

The system uses a structured logging approach through `logging_claude.py`. Logs are stored with timestamps and appropriate log levels:

```python
INFO: Pipeline initialized successfully
DEBUG: Processing image batch: 1/10
ERROR: Failed to process image: invalid format
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

Your Name - [@yourusername](https://twitter.com/yourusername)
Project Link: [https://github.com/yourusername/image-processing-pipeline](https://github.com/yourusername/image-processing-pipeline)
