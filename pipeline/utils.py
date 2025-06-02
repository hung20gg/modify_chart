from typing import Union
from PIL import Image, ImageDraw, ImageFont

def merge_images(
    images: list[Union[str, Image.Image]], 
    titles: list[str] = None,
    rows: int = 1, 
    padding: int = 10,
    max_width: int = None,
    max_height: int = None
) -> Image.Image:
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
    
    # Convert string paths to PIL Images
    images = [Image.open(img) if isinstance(img, str) else img for img in images]
    
    # Initialize titles if not provided
    if titles is None:
        titles = [""] * len(images)
    elif len(titles) < len(images):
        titles = titles + [""] * (len(images) - len(titles))
    
    # We need ImageDraw for adding text
    font = ImageFont.load_default()
    
    # Calculate layout
    cols = (len(images) + rows - 1) // rows
    
    # Get dimensions of each image
    image_widths = [img.width for img in images]
    image_heights = [img.height for img in images]
    
    # Calculate title heights
    title_heights = []
    for title in titles:
        if title:
            # Create a temporary image to measure text dimensions
            temp = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(temp)
            left, top, right, bottom = draw.textbbox((0, 0), title, font=font)
            title_heights.append(bottom - top)
        else:
            title_heights.append(0)
    
    # Calculate cell dimensions with padding
    cell_width = max(image_widths) + padding
    cell_height = max(image_heights) + max(title_heights) + padding * 2  # Extra padding for title
    
    # Calculate total dimensions
    total_width = cell_width * cols
    total_height = cell_height * rows
    
    # Apply max constraints if provided
    if max_width and total_width > max_width:
        # Scale down to fit max_width
        scale = max_width / total_width
        cell_width *= scale
        cell_height *= scale
        total_width = max_width
        total_height *= scale
        
    if max_height and total_height > max_height:
        # Scale down to fit max_height
        scale = max_height / total_height
        cell_width *= scale
        cell_height *= scale
        total_width *= scale
        total_height = max_height
    
    # Create new image
    new_image = Image.new('RGB', (int(total_width), int(total_height)), color='white')
    draw = ImageDraw.Draw(new_image)
    
    # Place each image and its title
    for index, (image, title) in enumerate(zip(images, titles)):
        col = index % cols
        row = index // cols
        
        # Calculate position with padding
        x = col * cell_width + padding // 2
        y = row * cell_height + padding // 2
        
        # Paste the image
        new_image.paste(image, (int(x), int(y)))
        
        # Add title if it exists
        if title:
            # Get text dimensions
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            
            # Center text under the image
            text_x = x + (image.width - text_width) // 2
            text_y = y + image.height + padding // 2
            
            draw.text((text_x, text_y), title, fill='black', font=font)
    
    return new_image