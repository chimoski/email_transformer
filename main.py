import os
import re
from bs4 import BeautifulSoup, NavigableString

def clean_text_content(text):
    if not text:
        return text
    
    # Convert to string if it's not already
    text = str(text)
    
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')
    
    # Remove other common encoding artifacts
    text = text.replace('\u00a0', ' ')  # Another form of non-breaking space
    text = text.replace('\u200b', '')   # Zero-width space
    text = text.replace('\u200c', '')   # Zero-width non-joiner
    text = text.replace('\u200d', '')   # Zero-width joiner
    text = text.replace('\u2060', '')   # Word joiner
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def ensure_utf8_meta_tag(soup):
    """
    Ensure the HTML has proper UTF-8 meta tag in the head.
    """
    head = soup.find('head')
    if not head:
        # Create head tag if it doesn't exist
        head = soup.new_tag('head')
        soup.html.insert(0, head)
    
    # Check if charset meta tag already exists
    charset_meta = head.find('meta', charset=True)
    if charset_meta:
        charset_meta['charset'] = 'UTF-8'
    else:
        # Create new charset meta tag
        meta_charset = soup.new_tag('meta', charset='UTF-8')
        head.insert(0, meta_charset)
    
    # Also add content-type meta tag for better compatibility
    content_meta = head.find('meta', attrs={'http-equiv': 'Content-Type'})
    if not content_meta:
        meta_content = soup.new_tag('meta', http_equiv='Content-Type', content='text/html; charset=UTF-8')
        head.insert(1, meta_content)

def replace_text_content(soup, tags, placeholder):
    for tag in soup.find_all(tags):
        # Clear existing text content but preserve child elements
        new_contents = []
        for content in tag.contents:
            if isinstance(content, NavigableString) and content.strip():
                # Clean the text content and replace with placeholder
                cleaned_text = clean_text_content(content)
                if cleaned_text:
                    new_contents.append(NavigableString(placeholder))
            else:
                # Keep child elements as they are
                new_contents.append(content)
        
        # Clear and rebuild contents
        tag.clear()
        for content in new_contents:
            tag.append(content)

def replace_img_tags(soup):
    for img in soup.find_all('img'):
        # Extract width and height from multiple sources
        width = None
        height = None
        
        # 1. Try HTML attributes first
        width = img.get('width')
        height = img.get('height')
        
        # 2. Try inline CSS if attributes not found
        if not width or not height:
            style = img.get('style', '')
            if style:
                # Look for width/height in various formats
                width_patterns = [
                    r'width\s*:\s*(\d+)px',      # width: 300px
                    r'width\s*:\s*(\d+)%',       # width: 50%
                    r'width\s*:\s*(\d+)',        # width: 300
                    r'max-width\s*:\s*(\d+)px',  # max-width: 300px
                    r'min-width\s*:\s*(\d+)px'   # min-width: 300px
                ]
                height_patterns = [
                    r'height\s*:\s*(\d+)px',     # height: 200px
                    r'height\s*:\s*(\d+)%',      # height: 50%
                    r'height\s*:\s*(\d+)',       # height: 200
                    r'max-height\s*:\s*(\d+)px', # max-height: 200px
                    r'min-height\s*:\s*(\d+)px'  # min-height: 200px
                ]
                
                # Try each pattern for width
                if not width:
                    for pattern in width_patterns:
                        match = re.search(pattern, style, re.IGNORECASE)
                        if match:
                            width = match.group(1)
                            break
                
                # Try each pattern for height
                if not height:
                    for pattern in height_patterns:
                        match = re.search(pattern, style, re.IGNORECASE)
                        if match:
                            height = match.group(1)
                            break
        
        # 3. Try to extract from CSS classes and style rules
        if not width or not height:
            # Look for common image size classes
            class_names = img.get('class', [])
            for class_name in class_names:
                if 'width' in class_name.lower() or 'size' in class_name.lower():
                    # Extract numbers from class names like "img-300x200" or "width-300"
                    size_match = re.search(r'(\d+)x(\d+)', class_name)
                    if size_match and not width and not height:
                        width = size_match.group(1)
                        height = size_match.group(2)
                        break
                    # Try single dimension patterns
                    width_match = re.search(r'width-(\d+)', class_name)
                    if width_match and not width:
                        width = width_match.group(1)
                    height_match = re.search(r'height-(\d+)', class_name)
                    if height_match and not height:
                        height = height_match.group(1)
            
            # If still no dimensions, try to find CSS rules for the classes
            if (not width or not height) and class_names:
                for style_tag in soup.find_all('style'):
                    if style_tag.string:
                        css_content = style_tag.string
                        for class_name in class_names:
                            # Look for CSS rules for this class
                            class_pattern = rf'\.{re.escape(class_name)}\s*{{[^}}]*}}'
                            class_match = re.search(class_pattern, css_content, re.DOTALL)
                            if class_match:
                                rule_content = class_match.group(0)
                                # Extract width/height from the CSS rule
                                if not width:
                                    width_match = re.search(r'width\s*:\s*(\d+)px', rule_content)
                                    if width_match:
                                        width = width_match.group(1)
                                if not height:
                                    height_match = re.search(r'height\s*:\s*(\d+)px', rule_content)
                                    if height_match:
                                        height = height_match.group(1)
        
        # 4. Smart fallbacks based on common email image sizes
        if not width:
            # Common email image widths
            width = '600'  # Standard email width
        if not height:
            # Use width as height to make square images when height is unknown
            if width and width.isdigit():
                height = width  # Make it square
            else:
                height = '600'  # Default square size
        
        # Ensure dimensions are valid numbers
        try:
            width_int = int(width)
            height_int = int(height)
            # Set reasonable limits
            width_int = max(50, min(width_int, 1200))
            height_int = max(50, min(height_int, 800))
            width = str(width_int)
            height = str(height_int)
        except (ValueError, TypeError):
            width = '600'
            height = '300'
        
        # Replace attributes with a reliable placeholder service
        img['src'] = f'https://placehold.jp/ffffff/{width}x{height}.png'
        img['alt'] = '{{alt_text}}'
        img['title'] = '{{alt_text}}'
        
        # Preserve original width/height attributes if they existed
        if not img.get('width'):
            img['width'] = width
        if not img.get('height'):
            img['height'] = height

def replace_a_tags(soup):
    """
    Replace href attributes in anchor tags and text content.
    """
    for a in soup.find_all('a'):
        a['href'] = '{{product_image_url}}'
        
        # Replace text content with placeholder
        new_contents = []
        for content in a.contents:
            if isinstance(content, NavigableString) and content.strip():
                # Clean the text content and replace with placeholder
                cleaned_text = clean_text_content(content)
                if cleaned_text:
                    new_contents.append(NavigableString('{{body_text}}'))
            else:
                new_contents.append(content)
        
        a.clear()
        for content in new_contents:
            a.append(content)

def replace_font_family_styles(soup):
    """
    Replace all font-family styles with Arial, Helvetica, sans-serif.
    """
    # Handle inline style attributes
    for tag in soup.find_all(style=True):
        style = tag['style']
        # Replace existing font-family declarations
        new_style = re.sub(
            r'font-family\s*:\s*[^;]+;?',
            'font-family: Arial, Helvetica, sans-serif;',
            style,
            flags=re.IGNORECASE
        )
        # Add font-family if it doesn't exist
        if 'font-family' not in new_style.lower():
            new_style = new_style.rstrip(';') + '; font-family: Arial, Helvetica, sans-serif;'
        tag['style'] = new_style
    
    # Handle <style> tags
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            new_css = re.sub(
                r'font-family\s*:\s*[^;]+;?',
                'font-family: Arial, Helvetica, sans-serif;',
                style_tag.string,
                flags=re.IGNORECASE
            )
            style_tag.string.replace_with(new_css)

def process_html_file(input_path, output_path):
    """
    Process a single HTML file according to the transformation rules.
    """
    # Read the HTML file with proper encoding handling
    html = None
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                html = f.read()
            print(f"Successfully read file with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    
    if html is None:
        raise ValueError(f"Could not read {input_path} with any of the attempted encodings")
    
    # Clean the HTML content before parsing
    html = clean_text_content(html)
    
    # Parse with explicit encoding
    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
    
    # Ensure proper UTF-8 meta tags are present
    ensure_utf8_meta_tag(soup)
    
    # Apply transformations in order
    replace_text_content(soup, ['p', 'li', 'span', 'em', 'strong', 'div'], '{{body_text}}')
    replace_text_content(soup, ['h1'], '{{headline}}')
    replace_text_content(soup, ['h2', 'h3', 'h4', 'h5', 'h6'], '{{subheadline}}')
    replace_img_tags(soup)
    replace_a_tags(soup)
    replace_font_family_styles(soup)
    
    # Write the transformed HTML with proper UTF-8 encoding and BOM
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(str(soup))
    
    print(f'Successfully processed: {input_path} -> {output_path}')

def process_directory(input_dir, output_dir):
    """
    Process all HTML files in a directory.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    html_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.html')]
    
    if not html_files:
        print(f"No HTML files found in '{input_dir}'")
        return
    
    for filename in html_files:
        input_path = os.path.join(input_dir, filename)
        output_filename = filename.replace('.html', '_templated.html')
        output_path = os.path.join(output_dir, output_filename)
        process_html_file(input_path, output_path)

def main():
    """
    Main function to handle command line arguments and execute the script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Transform HTML email templates by replacing content with placeholders.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py task_email.html
  python main.py task_email.html --output my_template.html
  python main.py ./email_templates/ --output ./templated_emails/
        """
    )
    
    parser.add_argument('input', help='Input HTML file or directory containing HTML files')
    parser.add_argument('--output', '-o', help='Output file or directory (optional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input path '{args.input}' does not exist.")
        return
    
    if os.path.isdir(args.input):
        # Process directory
        output_dir = args.output or args.input + '_templated'
        process_directory(args.input, output_dir)
    else:
        # Process single file
        if not args.input.lower().endswith('.html'):
            print("Warning: Input file doesn't have .html extension")
        
        output_file = args.output or args.input.replace('.html', '_templated.html')
        process_html_file(args.input, output_file)

if __name__ == '__main__':
    main()

    