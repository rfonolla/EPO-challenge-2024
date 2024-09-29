import ipywidgets as widgets
from IPython.display import display, HTML
import json
import os
from main import main, load_config

class PatentAnalysisWidget:
    def __init__(self, json_schema):
        self.schema = json_schema
        self.input_widgets = {}
        self.output_image = widgets.Image(format='svg+xml', layout=widgets.Layout(width='600px', height='450px'))
        self.output_text = widgets.HTML()
        self.claim_info = widgets.HTML()
        self.relevant_figures = widgets.Image(format='svg+xml', layout=widgets.Layout(width='600px', height='450px'))        
        self.loading_indicator = widgets.Label("Processing...")
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
        
        # Create a scrollable area for inputs
        input_area = widgets.VBox(input_widgets, layout=widgets.Layout(overflow_y='auto', max_height='600px'))
        
        input_box = widgets.VBox([input_area, button_box])
        self.output_box = widgets.VBox([self.output_image, self.output_text, self.loading_indicator])
        self.loading_indicator.layout.display = 'none'  # Hide loading indicator initially

        # Tabs for Inputs and Results
        self.tab = widgets.Tab()
        self.tab.children = [input_box, self.output_box, self.claim_info, self.relevant_figures]
        self.tab.set_title(0, "Inputs")
        self.tab.set_title(1, "Results")
        self.tab.set_title(2, "Claim information")
        self.tab.set_title(3, "Relevant figure")

        display(self.tab)

    def on_submit(self, b):
        self.loading_indicator.layout.display = 'block'  # Show loading indicator
        self.output_text.value = ""  # Clear previous output
        self.output_image.value = b''  # Clear previous image

        # Collect input data
        input_data = {key: widget.value for key, widget in self.input_widgets.items()}
        
        # Save input data to a temporary JSON file
        temp_json_path = 'temp_config.json'
        with open(temp_json_path, 'w') as f:
            json.dump(input_data, f)
        
        try:
            # Call the main function with the temporary config file
            summary, output_filename, claim_info = main(load_config(temp_json_path))

            self.claim_info.value = f"<p><strong>Claim information:</strong> {claim_info}</p>"

            # Load and display the output image from the specified file path
            if output_filename and os.path.exists(output_filename):
                with open(output_filename, 'rb') as f:
                    self.output_image.value = f.read()  # Read the image file in binary mode
        
            # Display the summary text
            self.output_text.value = f"<p><strong>Summary:</strong> {summary}</p>"

        except Exception as e:
            self.output_text.value = f"<p style='color: red;'><strong>Error:</strong> {str(e)}</p>"

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)

            self.loading_indicator.layout.display = 'none'  # Hide loading indicator
            # Switch to the Results tab
            self.tab.selected_index = 1

    def on_reset(self, b):
        for key, value in self.schema.items():
            if key in self.input_widgets:
                self.input_widgets[key].value = value

# Create and display the widget
widget = PatentAnalysisWidget(load_config('./config.json'))