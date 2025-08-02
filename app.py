import streamlit as st
import os
import re
import tempfile
from bs4 import BeautifulSoup, NavigableString
import base64

# Page configuration
st.set_page_config(
    page_title="HTML Email Template Transformer",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def clean_text_content(text):
    """
    Clean text content by removing encoding artifacts and non-breaking spaces.
    """
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
    """
    Replace text content in specified tags with placeholder.
    If the tag contains only text, replace it. Otherwise, replace only text nodes, preserving inline elements like <br> and <span>.
    """
    for tag in soup.find_all(tags):
        if tag.string and not tag.find(True):
            tag.string.replace_with(placeholder)
        else:
            new_contents = []
            for content in tag.contents:
                if isinstance(content, NavigableString) and content.strip():
                    new_contents.append(NavigableString(placeholder))
                else:
                    new_contents.append(content)
            tag.clear()
            for content in new_contents:
                tag.append(content)

def replace_img_tags(soup):
    """
    Replace img tag attributes with placeholders and placeholder image URLs.
    Preserves original image dimensions from various sources.
    """
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
        a['href'] = '{{product_url}}'
        
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

import re
from bs4 import BeautifulSoup

def replace_background_images(soup):
    """
    Replace all background image URLs (both inline styles and internal <style> tags) with link.com
    """

    # 1. Handle inline style attributes
    for tag in soup.find_all(style=True):
        style = tag['style']

        # Replace background-image:url(...) or background:url(...)
        updated_style = re.sub(
            r'(background(?:-image)?\s*:\s*url\()[\'"]?[^)\'"]+[\'"]?(\))',
            r'\1link.com\2',
            style,
            flags=re.IGNORECASE
        )

        tag['style'] = updated_style.strip()

    # 2. Handle <style> tags with internal CSS
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            new_css = re.sub(
                r'(background(?:-image)?\s*:\s*url\()[\'"]?[^)\'"]+[\'"]?(\))',
                r'\1link.com\2',
                style_tag.string,
                flags=re.IGNORECASE
            )
            style_tag.string.replace_with(new_css)

def replace_font_family_styles(soup):
    """
    Replace all font-family styles with Arial, Helvetica, sans-serif,
    avoiding duplicate semicolons or broken CSS syntax.
    """
    font_declaration = 'font-family: Arial, Helvetica, sans-serif'

    # Handle inline style attributes
    for tag in soup.find_all(style=True):
        style = tag['style']

        # Replace any existing font-family declarations
        updated_style = re.sub(
            r'font-family\s*:\s*[^;]+;?',
            font_declaration + ';',
            style,
            flags=re.IGNORECASE
        )

        # If no font-family was found, append it safely
        if 'font-family' not in updated_style.lower():
            updated_style = updated_style.strip()
            # Ensure a semicolon before appending
            if not updated_style.endswith(';') and updated_style != '':
                updated_style += ';'
            updated_style += ' ' + font_declaration + ';'

        tag['style'] = updated_style.strip()

    # Handle <style> tags with actual CSS code inside
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            new_css = re.sub(
                r'font-family\s*:\s*[^;]+;?',
                font_declaration + ';',
                style_tag.string,
                flags=re.IGNORECASE
            )
            style_tag.string.replace_with(new_css)


def process_html_content(html_content):
    """
    Process HTML content according to the transformation rules.
    """
    # Clean the HTML content before parsing
    html_content = clean_text_content(html_content)
    
    # Parse with explicit encoding
    soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
    
    # Ensure proper UTF-8 meta tags are present
    ensure_utf8_meta_tag(soup)
    
    # Apply transformations in order
    replace_text_content(soup, ['p', 'li', 'span', 'em', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], '{{body_text}}')
    replace_text_content(soup, ['h1'], '{{headline}}')
    replace_text_content(soup, ['h2', 'h3', 'h4', 'h5', 'h6'], '{{subheadline}}')
    replace_img_tags(soup)
    replace_a_tags(soup)
    replace_font_family_styles(soup)
    replace_background_images(soup) 
    
    return soup.prettify(formatter="html")

def get_download_link(file_content, filename, text="Download"):
    """
    Generate a download link for the processed HTML file.
    """
    b64 = base64.b64encode(file_content.encode()).decode()
    href = f'data:text/html;charset=utf-8;base64,{b64}'
    return f'<a href="{href}" download="{filename}" target="_blank">{text}</a>'

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        text-align: center;
        margin: 2rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .download-section {
        background-color: #e7f3ff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #b3d9ff;
        text-align: center;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
        background-color: #28a745;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #218838;
    }
    .info-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">📧 HTML Email Template Transformer</h1>', unsafe_allow_html=True)
    
    # Description
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.1rem; color: #666;">
            Transform your HTML email templates by replacing content with placeholder variables. 
            Upload an HTML file and get a clean, templated version ready for customization.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
  
    
    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<h3>📁 Upload Your HTML File</h3>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose an HTML file",
        type=['html', 'htm'],
        help="Upload a single HTML file to transform it into a template"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process button
    if uploaded_file is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Transform HTML Template", use_container_width=True):
                with st.spinner("Processing your HTML file..."):
                    try:
                        # Read the uploaded file
                        html_content = uploaded_file.read().decode('utf-8')
                        
                        # Process the HTML
                        processed_html = process_html_content(html_content)
                        
                        # Generate output filename
                        original_filename = uploaded_file.name
                        base_name = os.path.splitext(original_filename)[0]
                        output_filename = f"{base_name}_templated.html"
                        
                        # Store in session state for download
                        st.session_state.processed_html = processed_html
                        st.session_state.output_filename = output_filename
                        st.session_state.processing_complete = True
                        
                        # Success message
                        st.markdown(f"""
                        <div class="success-message">
                            ✅ <strong>Success!</strong> Your HTML file has been transformed into a template.
                            <br>Original file: <code>{original_filename}</code> → Output file: <code>{output_filename}</code>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show preview
                        with st.expander("👀 Preview of transformed HTML", expanded=False):
                            st.code(processed_html, language='html')
                        
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.session_state.processing_complete = False
    
    # Download section
    if hasattr(st.session_state, 'processing_complete') and st.session_state.processing_complete:
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown('<h3>💾 Download Your Template</h3>', unsafe_allow_html=True)
        
        # Create download link
        download_link = get_download_link(
            st.session_state.processed_html,
            st.session_state.output_filename,
            "📥 Download Transformed HTML Template"
        )
        
        st.markdown(download_link, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        


if __name__ == "__main__":
    main() 