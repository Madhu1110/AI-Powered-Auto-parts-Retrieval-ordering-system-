import ollama
import os
import json
from pathlib import Path


def identify_part_from_image(image_path):
    """
    Takes an image and returns detected automotive part
    """

    try:
        response = ollama.chat(
            model='llava',
            messages=[
                {
                    'role': 'user',
                    'content': 'Identify the automotive part in this image. Respond with ONLY the part name.',
                    'images': [image_path]
                }
            ]
        )

        result = response['message']['content'].strip()

        # Clean result (avoid long sentences)
        result = result.lower()

        # Basic normalization
        keywords = [
            "brake pad", "oil filter", "air filter", "tyre",
            "battery", "clutch", "chain", "spark plug"
        ]

        for k in keywords:
            if k in result:
                return k

        return result

    except Exception as e:
        return f"Error detecting image: {str(e)}"


def get_product_image(product_name):
    """
    Retrieves image path/URL for a product.
    Looks for product images in data/images/ directory.
    
    Returns:
        dict: {
            'has_image': bool,
            'image_path': str or None,
            'image_url': str or None,
            'message': str
        }
    """
    try:
        # Normalize product name for filename
        normalized_name = product_name.lower().replace(" ", "_").replace("/", "_")
        
        # Check multiple possible image locations
        base_paths = [
            Path(__file__).parent.parent / "data" / "images",
            Path(__file__).parent.parent / "images",
            Path.cwd() / "data" / "images"
        ]
        
        for base_path in base_paths:
            if base_path.exists():
                # Check for common image extensions
                for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                    image_file = base_path / f"{normalized_name}{ext}"
                    if image_file.exists():
                        return {
                            'has_image': True,
                            'image_path': str(image_file.absolute()),
                            'image_url': f"file:///{image_file.absolute()}",
                            'message': f"Found image for {product_name}"
                        }
        
        # If no image found, return gracefully
        return {
            'has_image': False,
            'image_path': None,
            'image_url': None,
            'message': f"No image available for {product_name}"
        }
    
    except Exception as e:
        return {
            'has_image': False,
            'image_path': None,
            'image_url': None,
            'message': f"Error retrieving image: {str(e)}"
        }


def format_response_with_image(text_content, product_name=None, include_image=True):
    """
    Formats a response with optional image attachment.
    
    Args:
        text_content: str - The text response
        product_name: str - Product name to fetch image for (optional)
        include_image: bool - Whether to try to include image (default True)
    
    Returns:
        dict: {
            'text': str,
            'image': {
                'path': str,
                'url': str
            } or None,
            'has_image': bool
        }
    """
    response = {
        'text': text_content,
        'image': None,
        'has_image': False
    }
    
    if include_image and product_name:
        image_info = get_product_image(product_name)
        if image_info['has_image']:
            response['image'] = {
                'path': image_info['image_path'],
                'url': image_info['image_url']
            }
            response['has_image'] = True
    
    return response