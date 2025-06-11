from typing import Union
from PIL import Image, ImageDraw, ImageFont
import os
import sys 
import time
import threading
current_dir = os.path.dirname(os.path.abspath(__file__))


def open_image(image_path):
    """
    Opens an image file, converts it to RGB mode if necessary, and resizes it
    if it exceeds the maximum dimensions.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        PIL.Image.Image: Processed image in RGB mode
    """
    # Open the image
    img = Image.open(image_path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Check if resize is needed
    max_width, max_height = 1200, 1000
    width, height = img.size
    
    if width > max_width or height > max_height:
        # Calculate new dimensions while preserving aspect ratio
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Resize the image
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    return img



def extract_critique_and_score(raw_response: str) -> dict:
    """
    Extracts the critique and score from the raw response.
    
    :param raw_response: The raw response string.
    :return: A dictionary containing the critique and score.
    """
    # Assuming the response is formatted as "Critique: <critique> Score: <score>"
    critique = raw_response
    final_score = 0

    if '### Critique' in raw_response and '### Score' in raw_response:
        critique = raw_response.split('### Critique')[1].split('### Score')[0].strip()
        score = raw_response.split('### Score')[1].strip()

        if len(critique) > 0 and critique[0] == ':':
            critique = critique[1:].strip()
        if len(score) > 0 and score[0] == ':':
            score = score[1:].strip()

        if score.isdigit():
            final_score = int(score)
        
        elif '\\boxed{' in score:
            score = score.split('\\boxed{')[1].split('}')[0]
            if score.isdigit():
                final_score = int(score)
        
        return {
            'critique': critique,
            'score': final_score
        }
    
    return {'critique': critique, 'score': final_score}



def merge_images(
    images: list[Union[str, Image.Image]], 
    titles: list[str] = None,
    rows: int = 1, 
    padding: int = 10,
    max_width: int = 1600,
    max_height: int = 800,
    run_name: str = '',
    tag: str = '', 
    save_folder: str = '',
    return_path: bool = False
) -> Union[Image.Image, str, None]:
    """
    Merge a list of images into a single image with specified number of rows.

    :param images: List of PIL Image objects or paths to merge.
    :param titles: Optional list of titles for each image.
    :param rows: Number of rows to arrange the images in.
    :param padding: Padding between images in pixels.
    :param max_width: Maximum width of the output image.
    :param max_height: Maximum height of the output image.
    :return: Merged PIL Image object.
    """
    if not images:
        return None
    
    # Convert string paths to PIL Images and filter out None values
    processed_images = []
    for img in images:
        if img is not None:
            if isinstance(img, str):
                if os.path.exists(img):
                    processed_images.append(Image.open(img))
            else:
                processed_images.append(img)
    
    if not processed_images:
        return None
    
    images = processed_images
    
    # Initialize titles if not provided
    if titles is None:
        titles = [""] * len(images)
    elif len(titles) < len(images):
        titles = titles + [""] * (len(images) - len(titles))
    
    # Load font for titles
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Calculate layout
    cols = (len(images) + rows - 1) // rows
    
    # Calculate title heights
    title_heights = []
    for title in titles:
        if title:
            # Create a temporary image to measure text dimensions
            temp = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(temp)
            bbox = draw.textbbox((0, 0), title, font=font)
            title_heights.append(bbox[3] - bbox[1] + 10)  # Add some extra padding
        else:
            title_heights.append(0)
    
    max_title_height = max(title_heights) if title_heights else 0
    
    # First, calculate what size each image should be to fit within constraints
    # Available space for images (excluding padding and titles)
    available_width = max_width - (padding * (cols + 1))
    available_height = max_height - (padding * (rows + 1)) - (max_title_height * rows)
    
    # Calculate maximum cell size
    max_cell_width = available_width // cols
    max_cell_height = available_height // rows
    
    # Resize all images to fit within the cell size while maintaining aspect ratio
    resized_images = []
    for img in images:
        # Calculate scale factor to fit within cell
        scale_w = max_cell_width / img.width
        scale_h = max_cell_height / img.height
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale, only downscale
        
        if scale < 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        else:
            resized_img = img.copy()
        
        resized_images.append(resized_img)
    
    # Find the actual dimensions needed
    max_img_width = max(img.width for img in resized_images)
    max_img_height = max(img.height for img in resized_images)
    
    # Calculate final canvas size
    canvas_width = cols * max_img_width + (cols + 1) * padding
    canvas_height = rows * (max_img_height + max_title_height) + (rows + 1) * padding
    
    # Create new image with calculated dimensions
    new_image = Image.new('RGB', (canvas_width, canvas_height), color='white')
    draw = ImageDraw.Draw(new_image)
    
    # Place each image and its title
    for index, (image, title) in enumerate(zip(resized_images, titles)):
        col = index % cols
        row = index // cols
        
        # Calculate position
        x = padding + col * (max_img_width + padding)
        y = padding + row * (max_img_height + max_title_height + padding)
        
        # Center the image within its cell if it's smaller than max dimensions
        img_x = x + (max_img_width - image.width) // 2
        img_y = y + (max_img_height - image.height) // 2
        
        # Paste the image
        new_image.paste(image, (img_x, img_y))
        
        # Add title if it exists
        if title:
            # Get text dimensions
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            
            # Center text below the image
            text_x = x + (max_img_width - text_width) // 2
            text_y = y + max_img_height + 5
            
            draw.text((text_x, text_y), title, fill='black', font=font)
    
    if return_path:
        # Save the merged image to a temporary path
        run_time = time.strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(current_dir, 'temp', 'merged', run_name, f"merged_{run_name}_{tag}_{run_time}.png")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        new_image.save(output_path)
        print(f"Merged image saved to {output_path}")
        return output_path

    if save_folder:
        
        def save_image_thread(img, folder, r_name, t):
            # Save the merged image to the specified path
            output_dir = os.path.join(folder, 'merged', r_name)
            os.makedirs(output_dir, exist_ok=True)
            run_time = time.strftime("%Y%m%d-%H%M%S")
            output_path = os.path.join(output_dir, f"merged_{t}_{run_time}.png")
            img.copy().save(output_path)
            print(f"Merged image saved to {output_path}")
        
        # Start a new thread to save the image
        save_thread = threading.Thread(
            target=save_image_thread,
            args=(new_image, save_folder, run_name, tag)
        )
        save_thread.daemon = True  # Set as daemon so it doesn't block program exit
        save_thread.start()

    return new_image

if __name__ == "__main__":

    text = "### Critique:\nThe code correctly converts the line graph data into a grouped bar chart as requested. It aligns the years across the three datasets, fills missing data with zero, and plots the bars side-by-side with appropriate width and spacing. The title and axis labels are added correctly, and the legend distinguishes the three groups. The figure size is reasonable for clarity.\n\nOne minor improvement could be to use `np.nan` instead of zero for missing data so that bars are not shown for missing years, but zero also works visually. Overall, the chart is clear, accurate, and aesthetically reasonable.\n\n### Score\n5"
    result = extract_critique_and_score(text)
    print(result)