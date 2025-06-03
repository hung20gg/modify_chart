import matplotlib.pyplot as plt

# Sample data
categories = ['A', 'B', 'C', 'D']
values = [4, 3, 2, 5]

# Create bar chart
plt.figure(figsize=(8, 6))
plt.bar(categories, values, color='skyblue')

# Customize chart
plt.title('Sample Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Values')
