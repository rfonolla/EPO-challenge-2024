import svgwrite

# Create a new SVG document
dwg = svgwrite.Drawing('tooth_schematic.svg')

# Define the dimensions and coordinates
width = 400
height = 400
x_scale = 100
y_scale = 100

# Define the layers and colors
enamel_color = '#FFFFFF'  # White
dentine_color = '#C0C0C0'  # Light gray
pulp_color = '#FF0000'  # Red
green_light_color = '#00FF00'  # Green
red_light_color = '#FF0000'  # Red
camera_color = '#0000FF'  # Blue
processor_color = '#666666'  # Dark gray

# Draw the tooth cross-section
dwg.add(dwg.rect((0, 0), (width, height), fill=enamel_color))
dwg.add(dwg.rect((x_scale, 0), (width - 2*x_scale, height/3), fill=dentine_color))
dwg.add(dwg.rect((x_scale, height/3), (width - 2*x_scale, height/3), fill=pulp_color))

# Draw the light sources
dwg.add(dwg.circle((x_scale/2, height/2), r=x_scale/4, fill=green_light_color))
dwg.add(dwg.circle((x_scale/2, height/2 + height/6), r=x_scale/4, fill=red_light_color))

# Draw the light paths
dwg.add(dwg.line((x_scale/2, height/2), (x_scale, height/2), stroke=green_light_color, stroke_width=2))
dwg.add(dwg.line((x_scale/2, height/2 + height/6), (x_scale, height/2 + height/6), stroke=red_light_color, stroke_width=2))
dwg.add(dwg.line((x_scale, height/2), (x_scale, height/2 - height/3), stroke=green_light_color, stroke_width=2))
dwg.add(dwg.line((x_scale, height/2 + height/6), (x_scale, height/2 + height/3), stroke=red_light_color, stroke_width=2))

# Draw the reflected light
dwg.add(dwg.circle((x_scale/2, height/2 - height/3), r=x_scale/4, fill=green_light_color, opacity=0.5))
dwg.add(dwg.circle((x_scale/2, height/2 + height/3), r=x_scale/4, fill=red_light_color, opacity=0.5))

# Draw the camera
dwg.add(dwg.circle((x_scale/2, height/2 + height), r=x_scale/4, fill=camera_color))

# Draw the intensity maps
dwg.add(dwg.rect((x_scale*2, height/2 + height), (x_scale, x_scale), fill='none', stroke=green_light_color, stroke_width=2))
dwg.add(dwg.rect((x_scale*2 + x_scale, height/2 + height), (x_scale, x_scale), fill='none', stroke=red_light_color, stroke_width=2))
dwg.add(dwg.text('Intensity Map (λ1)', (x_scale*2 + x_scale/2, height/2 + height + x_scale/2), font_size=14, fill=green_light_color))
dwg.add(dwg.text('Intensity Map (λ2)', (x_scale*2 + x_scale + x_scale/2, height/2 + height + x_scale/2), font_size=14, fill=red_light_color))

# Draw the processor
dwg.add(dwg.rect((x_scale*3, height/2 + height), (x_scale, x_scale), fill=processor_color))
dwg.add(dwg.text('Processor', (x_scale*3 + x_scale/2, height/2 + height + x_scale/2), font_size=14, fill=processor_color))

# Draw the thickness map
dwg.add(dwg.rect((x_scale*4, height/2 + height), (x_scale, x_scale), fill='none', stroke=processor_color, stroke_width=2))
dwg.add(dwg.text('Dentine Thickness Map', (x_scale*4 + x_scale/2, height/2 + height + x_scale/2), font_size=14, fill=processor_color))

# Save the SVG file
dwg.save()