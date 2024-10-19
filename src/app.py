# Import required libraries
import ipywidgets as widgets
from IPython.display import display, HTML
import json
import os
from main import main, load_config
import base64

"""
Patent Analysis Widget
A Jupyter widget for analyzing patents with an interactive UI.

This module implements a widget-based interface for patent analysis, providing
features like claim analysis, figure viewing, and metrics display.

"""

class PatentAnalysisWidget:\
    """
    A class that creates an interactive widget interface for patent analysis.
    
    This widget provides:
    - Input form for patent analysis parameters
    - Results display with SVG support
    - Claims information viewer
    - Figure browser
    - Metrics display dashboard
    """
    # Initialize the widget with configuration schema
    def __init__(self, json_schema):
        self.schema = json_schema
        self.input_widgets = {}
        # Create main output image widget
        self.output_image = widgets.Image(format='svg+xml', layout=widgets.Layout(width='600px', height='450px'))
        self.output_text = widgets.HTML()
        self.claim_info = widgets.HTML()
        self.metrics_display = widgets.VBox([])
        self.loading_indicator = widgets.Label("Processing...")
        
        # Set up widgets for displaying patent figures
        self.relevant_figures_dropdown = widgets.Dropdown(
            options=[],
            description='Select Figure:',
            layout=widgets.Layout(width='300px')
        )
        self.relevant_figures_image = widgets.Image(
            format='png', 
            layout=widgets.Layout(width='600px', height='450px')
        )
        self.relevant_figures_dropdown.observe(self.on_figure_change, names='value')
        
        self.create_ui()

    # Format metrics data for display
    def format_metrics(self, metrics):
        # Create overall metrics section
        overall_metrics = widgets.VBox([
            widgets.HTML("<h2>Overall Metrics</h2>"),
            widgets.GridBox(
                [widgets.Label(f"{key}: {value:.3f}") for key, value in metrics['overall_metrics'].items()],
                layout=widgets.Layout(
                    grid_template_columns='repeat(2, 1fr)',
                    grid_gap='10px',
                    padding='10px'
                )
            )
        ], layout=widgets.Layout(margin='10px'))

        # Create individual section metrics
        section_metrics = []
        for section, values in metrics.items():
            if section != 'overall_metrics':
                section_name = section.replace('_text', '').replace('_', ' ').title()
                section_box = widgets.VBox([
                    widgets.HTML(f"<h3>{section_name}</h3>"),
                    widgets.GridBox(
                        [widgets.Label(f"{k}: {v:.3f}") for k, v in values.items()],
                        layout=widgets.Layout(
                            grid_template_columns='repeat(2, 1fr)',
                            grid_gap='10px',
                            padding='10px'
                        )
                    )
                ], layout=widgets.Layout(margin='10px'))
                section_metrics.append(section_box)

        return widgets.VBox([
            overall_metrics,
            widgets.HTML("<h2>Section Metrics</h2>"),
            widgets.VBox(section_metrics)
        ], layout=widgets.Layout(padding='20px'))

    # Create the main user interface
    def create_ui(self):\
        """Create and layout the main user interface components."""

        # Create input widgets based on schema
        input_widgets = []
        for key, value in self.schema.items():
            if key in ['patent_number']:
                widget = widgets.Text(
                    description=key,
                    value=str(value),
                    layout=widgets.Layout(width='50%')
                )
            elif key == 'claim_number':
                widget = widgets.IntText(
                    description=key,
                    value=int(value),
                    layout=widgets.Layout(width='50%')
                )
            elif key in ['dependent_claims', 'field_of_invention', 'background_of_the_invention', 
                        'summary_of_the_invention', 'brief_description_of_the_drawings', 
                        'detailed_description_of_the_embodiments', 'retrieve_patent_images', 'print_prompt']:
                widget = widgets.Checkbox(
                    description=key,
                    value=bool(value),
                    indent=False
                )
            elif key == 'output_filename':
                widget = widgets.Text(
                    description=key,
                    value=str(value),
                    layout=widgets.Layout(width='50%')
                )
            # Skip certain configuration fields
            elif key in ['model_llm', 'prompt_template', 'prompt_template_image', 'temperature', 'max_tokens', 'max_tokens_code']:
                continue
            else:
                widget = widgets.Text(
                    description=key,
                    value=str(value),
                    layout=widgets.Layout(width='50%')
                )
            
            self.input_widgets[key] = widget
            input_widgets.append(widget)

        # Create Submit and Reset buttons
        submit_button = widgets.Button(
            description="Submit",
            button_style='primary',
            layout=widgets.Layout(width='150px')
        )
        submit_button.on_click(self.on_submit)

        reset_button = widgets.Button(
            description="Reset",
            button_style='warning',
            layout=widgets.Layout(width='150px')
        )
        reset_button.on_click(self.on_reset)

        # Create button container
        button_box = widgets.HBox(
            [submit_button, reset_button],
            layout=widgets.Layout(
                justify_content='space-around',
                padding='20px'
            )
        )
        
        # Create scrollable input area
        input_area = widgets.VBox(
            input_widgets,
            layout=widgets.Layout(
                overflow_y='auto',
                max_height='600px',
                padding='20px'
            )
        )
        
        input_box = widgets.VBox([input_area, button_box])
        
        # Create output area
        self.output_box = widgets.VBox(
            [self.output_image, self.output_text, self.loading_indicator],
            layout=widgets.Layout(padding='20px')
        )
        self.loading_indicator.layout.display = 'none'

        # Create tabs for different sections
        self.tab = widgets.Tab()
        self.tab.children = [
            input_box,
            self.output_box,
            self.claim_info,
            widgets.VBox(
                [self.relevant_figures_dropdown, self.relevant_figures_image],
                layout=widgets.Layout(padding='20px')
            ),
            self.metrics_display
        ]
        
        # Set tab titles
        titles = ['Inputs', 'Results', 'Claims', 'Relevant Figures', 'Metrics']
        for i, title in enumerate(titles):
            self.tab.set_title(i, title)

        display(self.tab)

    # Handle form submission
    def on_submit(self, b):
        """
        Handle form submission and process patent analysis.
        
        Args:
            b: Button click event
        """
        self.loading_indicator.layout.display = 'block'
        self.output_text.value = ""
        self.output_image.value = b''

        # Collect input data
        input_data = {key: widget.value for key, widget in self.input_widgets.items()}
        updated_schema = {**self.schema, **input_data}
        temp_json_path = 'temp_config.json'
        
        # Save temporary configuration
        with open(temp_json_path, 'w') as f:
            json.dump(updated_schema, f)
        
        try:
            # Run patent analysis
            summary, output_filename, claim_info, relevant_image, metrics = main(load_config(temp_json_path))

            # Format claims display
            claims_text = [
                f"<h3>Main Claim:</h3><p>{claim_info['claim_text']}</p>",
                "<h3>Dependent Claims:</h3>"
            ] + [f"<p>{claim}</p>" for claim in claim_info['dependent_claims_text']]
            
            self.claim_info.value = "<div style='padding: 20px'>" + "".join(claims_text) + "</div>"
            
            # Display output image if available
            if output_filename and os.path.exists(output_filename):
                with open(output_filename, 'rb') as f:
                    self.output_image.value = f.read()
            
            # Handle relevant figures
            if relevant_image:
                self.relevant_image = relevant_image
                self.relevant_figures_dropdown.options = [f'Figure {i+1}' for i in range(len(relevant_image))]
                self.relevant_figures_dropdown.value = self.relevant_figures_dropdown.options[0]
                self.update_relevant_figure(0)
            else:
                self.relevant_image = []
                self.relevant_figures_dropdown.options = []
                self.relevant_figures_image.value = b''

            # Update summary and metrics display
            self.output_text.value = f"<div style='padding: 20px'><h2>Summary</h2><p>{summary}</p></div>"
            self.metrics_display.children = [self.format_metrics(metrics)]

        except Exception as e:
            self.output_text.value = f"<div style='color: red; padding: 20px;'><strong>Error:</strong> {str(e)}</div>"

        finally:
            # Clean up temporary file and hide loading indicator
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)
            self.loading_indicator.layout.display = 'none'
            self.tab.selected_index = 1

    # Reset form to default values
    def on_reset(self, b):
        """
        Reset all input fields to their default values.
        
        Args:
            b: Button click event
        """
        for key, value in self.schema.items():
            if key in self.input_widgets:
                self.input_widgets[key].value = value

    # Update the displayed figure
    def update_relevant_figure(self, index):
        """
        Update the displayed figure based on selected index.
        
        Args:
            index (int): Index of the figure to display
        """
        if 0 <= index < len(self.relevant_image):
            image_data = self.relevant_image[index]
            self.relevant_figures_image.value = base64.b64decode(image_data)

    # Handle figure selection change
    def on_figure_change(self, change):
        """
        Handle figure selection change events.
        
        Args:
            ch
        if change.new:
            index = int(change.new.split()[-1]) - 1
            self.update_relevant_figure(index)

# Create widget instance
widget = PatentAnalysisWidget(load_config('./default_config.json'))