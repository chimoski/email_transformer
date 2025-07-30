#!/usr/bin/env python3
"""
Test script to verify that main.py and app.py produce identical results.
"""

import os
import tempfile
from main import process_html_file
from app import process_html_content

def test_equivalence():
    """Test that both scripts produce identical results."""
    
    # Test HTML content
    test_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Email</title>
    <style>
        body { font-family: Georgia, serif; }
        .content { font-family: Verdana, sans-serif; }
    </style>
</head>
<body>
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
</body>
</html>"""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(test_html)
        temp_input = f.name
    
    temp_output_main = temp_input.replace('.html', '_main_output.html')
    temp_output_app = temp_input.replace('.html', '_app_output.html')
    
    try:
        # Process with main.py
        process_html_file(temp_input, temp_output_main)
        
        # Process with app.py
        processed_html = process_html_content(test_html)
        
        # Write app.py output to file for comparison
        with open(temp_output_app, 'w', encoding='utf-8-sig') as f:
            f.write(processed_html)
        
        # Read both outputs
        with open(temp_output_main, 'r', encoding='utf-8-sig') as f:
            main_output = f.read()
        
        with open(temp_output_app, 'r', encoding='utf-8-sig') as f:
            app_output = f.read()
        
        # Compare outputs
        if main_output == app_output:
            print("✅ SUCCESS: Both scripts produce identical results!")
            print(f"Main.py output length: {len(main_output)} characters")
            print(f"App.py output length: {len(app_output)} characters")
            
            # Show a sample of the output
            print("\n📋 Sample of processed output:")
            print("=" * 50)
            lines = main_output.split('\n')[:20]
            for line in lines:
                print(line)
            if len(main_output.split('\n')) > 20:
                print("...")
            
        else:
            print("❌ FAILURE: Scripts produce different results!")
            print(f"Main.py output length: {len(main_output)} characters")
            print(f"App.py output length: {len(app_output)} characters")
            
            # Find differences
            main_lines = main_output.split('\n')
            app_lines = app_output.split('\n')
            
            print("\n🔍 Differences found:")
            for i, (main_line, app_line) in enumerate(zip(main_lines, app_lines)):
                if main_line != app_line:
                    print(f"Line {i+1}:")
                    print(f"  Main: {main_line}")
                    print(f"  App:  {app_line}")
                    break
            
    finally:
        # Clean up temporary files
        for file_path in [temp_input, temp_output_main, temp_output_app]:
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    test_equivalence() 