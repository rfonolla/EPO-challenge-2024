import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create a new figure
fig, ax = plt.subplots()

# Create a box for box A
boxA = patches.Rectangle((0.2, 0.2), 0.4, 0.4, linewidth=1, edgecolor='black', facecolor='lightblue')
ax.add_patch(boxA)

# Create a box for box B
boxB = patches.Rectangle((0.6, 0.2), 0.4, 0.4, linewidth=1, edgecolor='black', facecolor='lightgreen')
ax.add_patch(boxB)

# Set the title of box A
ax.text(0.2, 0.5, 'Claim 1', ha='center', va='center', size=14)

# Set the title of box B
ax.text(0.7, 0.5, 'Claim 1.1', ha='center', va='center', size=14)

# Create an arrow from box A to box B
ax.arrow(0.4, 0.5, 0.2, 0, head_width=0.05, head_length=0.1, fc='black', ec='black')

# Set the aspect ratio of the plot to be equal so that the boxes are not distorted
ax.set_aspect('equal')

# Show the plot
plt.savefig('test.png')