import ipywidgets as widgets
from IPython.display import display, HTML
import json
import os
from main import main, load_config

def main(config):
    # Mocking your main function
    summary = "This is a summary based on the config"
    output_filename = config.get("output_filename", "")
    return summary, output_filename

class PatentAnalysisWidget:
    def __init__(self, json_schema):
        self.schema = json_schema
        self.input_widgets = {}
        self.output_image = widgets.Image(format='svg+xml')
        self.output_text = widgets.HTML()
        self.create_ui()

    def create_ui(self):
        input_widgets = []
        for key, value in self.schema.items():
            if key in ['model_llm', 'patent_number']:
                widget = widgets.Text(description=key, value=str(value))
            elif key in ['temperature', 'max_tokens', 'max_tokens_code']:
                widget = widgets.FloatText(description=key, value=float(value))
            elif key == 'claim_number':
                widget = widgets.IntText(description=key, value=int(value))
            elif key in ['field_of_invention', 'background_of_the_invetion', 'summary_of_the_invetion', 
                         'brief_description_of_the_drawings', 'detailed_description_of_the_embodiments', 
                         'retrieve_patent_images', 'print_prompt']:
                widget = widgets.Checkbox(description=key, value=bool(value))
            elif key == 'output_filename':
                widget = widgets.Text(description=key, value=str(value))
            elif key in ['prompt_template', 'prompt_template_image']:
                widget = widgets.Textarea(description=key, value=str(value), layout=widgets.Layout(width='100%', height='100px'))
            else:
                widget = widgets.Text(description=key, value=str(value))
            
            self.input_widgets[key] = widget
            input_widgets.append(widget)

        # Submit and Reset Buttons
        submit_button = widgets.Button(description="Submit")
        submit_button.on_click(self.on_submit)

        reset_button = widgets.Button(description="Reset to Default")
        reset_button.on_click(self.on_reset)

        button_box = widgets.HBox([submit_button, reset_button])
        input_box = widgets.VBox(input_widgets + [button_box])
        self.output_box = widgets.VBox([self.output_image, self.output_text])

        # Tabs for Inputs and Results
        self.tab = widgets.Tab()
        self.tab.children = [input_box, self.output_box]
        self.tab.set_title(0, "Inputs")
        self.tab.set_title(1, "Results")

        display(self.tab)

    def on_submit(self, b):
        # Collect input data
        input_data = {key: widget.value for key, widget in self.input_widgets.items()}
        
        # Save input data to a temporary JSON file
        temp_json_path = 'temp_config.json'
        with open(temp_json_path, 'w') as f:
            json.dump(input_data, f)
        
        # Call the main function with the temporary config file
        summary, output_filename = main(load_config(temp_json_path))
        
        # Display the summary text
        self.output_text.value = f"<p><strong>Summary:</strong> {summary}</p>"

        # Clean up the temporary file
        os.remove(temp_json_path)

        # Switch to the Results tab
        self.tab.selected_index = 1

    def on_reset(self, b):
        for key, value in self.schema.items():
            if key in self.input_widgets:
                self.input_widgets[key].value = value

# JSON schema
json_schema = {
    "model_llm": "claude-3-5-sonnet-20240620",
    "temperature": 0.0,
    "max_tokens": 1024,
    "max_tokens_code": 2048,
    "patent_number": "EP4014844A1",
    "claim_number": 1,
    "field_of_invention": True,
    "background_of_the_invetion": True,
    "summary_of_the_invetion": True,
    "brief_description_of_the_drawings": True,
    "detailed_description_of_the_embodiments": True,
    "retrieve_patent_images": False,
    "output_filename": "./images/EP4014844A1.svg",
    "prompt_template": "You are an expert patent examiner. Summarize the following claim and extract the reference numbers: \n{information}\n. Return the information as a JSON using the following template: \n  \"summary\": \"summary description\",\n  \"reference\": \n        \"number_reference1\": \"reference1\",\n        \"number_reference2\": \"reference2\"\n\n",
    "prompt_template_image": "You are an expert Python developer specializing in SVG image generation. Create a Python script to draw an SVG image for the following claim:\n\n{information}\n\nUse the following requirements and return the complete Python script:\n\nUse the svgwrite library to create the SVG image.\nInclude the title of the invention. \nUse a canvas size of 800x600 pixels\nChoose appropriate shapes for each object in the claim.\n. Use distinct colors for each object or category.\n Use arrows to indicate directions when needed.\nInclude a legend that doesn't overlap with the main image.\nEvery eleement needs to have a legend.\nPosition the legend in the top left corner of the image and make sure it does not fall outside of borders\nUse small icons and text to represent each item in the legend\nAdd appropriate labels or text where necessary to clarify the image.\nEnsure the code is well-commented and easy to understand.\n Do not use mm as position.\n Name the image {output_filename}",
    "print_prompt": False
}

# Create and display the widget
widget = PatentAnalysisWidget(json_schema)
