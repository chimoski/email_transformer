# HTML Email Template Transformer

A Python script and Streamlit web app that automates the transformation of HTML email templates by replacing specific content with placeholder variables. This tool is designed to convert raw HTML emails into reusable templates.

## 🚀 Quick Start (Streamlit Web App)

The easiest way to use this tool is through the Streamlit web interface:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

3. **Open your browser** and go to the URL shown in the terminal (usually `http://localhost:8501`)

4. **Upload an HTML file** and click "Transform HTML Template"

5. **Download your transformed template** with the download button

## 🌐 Deploy to Streamlit Cloud

### Option 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set the main file path to `app.py`
   - Click "Deploy"

### Option 2: Deploy from Local Files

1. **Create a requirements.txt file** (already done)
2. **Create a .streamlit/config.toml file** (already done)
3. **Upload to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Upload your files directly

## 💻 Command Line Usage

For command-line usage, you can still use the original script:

## Features

The script performs the following transformations:

### Text Content Replacement
- **Body text**: Replaces text in `<p>`, `<a>`, `<li>`, `<span>`, `<em>`, `<strong>`, `<div>` tags with `{{body_text}}`
- **Headlines**: Replaces text in `<h1>` tags with `{{headline}}`
- **Subheadlines**: Replaces text in `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>` tags with `{{subheadline}}`

### Image Processing
- Extracts width and height from multiple sources:
  - HTML attributes (`width` and `height`)
  - Inline CSS styles (`width`, `height`, `max-width`, `max-height`, `min-width`, `min-height`)
  - CSS classes and style rules
  - Percentage-based sizing (converted to reasonable pixel values)
- Replaces `src` with placeholder image URL: `https://dummyimage.com/{width}x{height}/ffffff/000000&text=Image+{width}x{height}`
- Replaces `alt` and `title` attributes with `{{alt_text}}`
- Preserves original dimensions and applies smart fallbacks for missing sizes

### Link Processing
- Replaces all `href` values in `<a>` tags with `"{{product_image_url}}"`
- Replaces link text with `{{body_text}}`

### Font Family Standardization
- Changes all font-family styles to: `font-family: Arial, Helvetica, sans-serif;`
- Works with both inline styles and `<style>` tags

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Process a Single File

```bash
python main.py input_email.html
```

This will create `input_email_templated.html` in the same directory.

### Process a Single File with Custom Output

```bash
python main.py input_email.html --output my_template.html
```

### Process Multiple Files in a Directory

```bash
python main.py ./email_templates/ --output ./templated_emails/
```

This will process all `.html` files in the `email_templates/` directory and save the results in `templated_emails/` with `_templated` appended to filenames.

## Example

### Input HTML (`sample_email.html`)
```html
<div class="header">
    <h1>Welcome to Our Newsletter</h1>
    <p>Stay updated with our latest news and offers!</p>
</div>
<div class="content">
    <h2>Featured Article</h2>
    <p>This is a sample paragraph with some <strong>important text</strong>.</p>
    <img src="https://example.com/banner.jpg" alt="Promotional banner" width="600" height="200">
    <a href="https://example.com/sale">special sale</a>
</div>
```

### Output HTML (`sample_email_templated.html`)
```html
<div class="header">
    <h1>{{headline}}</h1>
    <p>{{body_text}}</p>
</div>
<div class="content">
    <h2>{{subheadline}}</h2>
    <p>{{body_text}} <strong>{{body_text}}</strong>.</p>
                   <img src="https://dummyimage.com/600x200/ffffff/000000&text=Image+600x200" alt="{{alt_text}}" title="{{alt_text}}" width="600" height="200">
         <a href="{{product_image_url}}">{{body_text}}</a>
</div>
```

## Command Line Options

- `input`: Path to input HTML file or directory (required)
- `--output` or `-o`: Path to output file or directory (optional)

## Requirements

- Python 3.6+
- BeautifulSoup4
- lxml parser
- Streamlit (for web app)

## Notes

- The script preserves the HTML structure and only replaces specified content
- Child elements within tags are preserved (only direct text content is replaced)
- Font family changes apply to both inline styles and CSS in `<style>` tags
- Image dimensions are extracted from multiple sources in order: HTML attributes, inline CSS, CSS classes, and style rules
- Smart fallback dimensions use width as height (square images) when height cannot be determined
- Percentage-based sizing is converted to reasonable pixel values
- The script handles different file encodings automatically with robust UTF-8 support
- Cleans encoding artifacts and non-breaking spaces to prevent display issues
- Ensures proper UTF-8 meta tags are present in the output HTML

## Error Handling

- Validates input file/directory existence
- Handles encoding issues gracefully
- Provides informative error messages
- Continues processing multiple files even if one fails

## Files

- `app.py` - Streamlit web application
- `main.py` - Command-line script
- `sample_test.html` - Sample HTML file for testing
- `requirements.txt` - Python dependencies

## License

This script is provided as-is for educational and practical use. 