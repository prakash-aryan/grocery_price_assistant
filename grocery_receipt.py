import os
import sys
import re
import tempfile
import subprocess
from datetime import datetime

# Import main application functionality
from main import create_app
from config import CURRENCY, CURRENCY_SYMBOL

def clean_response(text):
    """Remove thinking sections and tidy up the receipt content."""
    # Remove <think>...</think> sections
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove any extra newlines resulting from removed sections
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()

def generate_receipt(grocery_query):
    """Generate a receipt based on the user's grocery query."""
    # Use the main application's answer generation
    get_answer = create_app()
    receipt_content = get_answer(grocery_query)
    
    # Clean the content to remove thinking sections
    cleaned_content = clean_response(receipt_content)
    
    # Improve the receipt with additional formatting
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    store_name = "GroceryMart"
    receipt_number = datetime.now().strftime("%Y%m%d%H%M%S")
    
    enhanced_receipt = f"""
# {store_name} - Receipt #{receipt_number}

**Date:** {current_date}

{cleaned_content}

---

Thank you for shopping with us!
*Prices include all applicable taxes*

"""
    return enhanced_receipt

def create_latex_header():
    """Create a LaTeX header file with proper font configuration."""
    header_content = r"""
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{DejaVu Sans}[Scale=0.9]
\setsansfont{DejaVu Sans}[Scale=0.9]
\setmonofont{DejaVu Sans Mono}[Scale=0.9]
"""
    header_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tex')
    header_file.write(header_content)
    header_file.close()
    return header_file.name

def generate_png_with_markitdown(markdown_text, output_path=None):
    """Use MarkItDown to generate a PNG receipt with proper currency symbol support."""
    try:
        # Generate default output path if not provided
        if not output_path:
            output_path = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        # Ensure it ends with .png
        if not output_path.endswith('.png'):
            output_path += '.png'
            
        # Create a temporary markdown file for processing
        temp_md_file = None
        header_file = None
        
        try:
            # Save markdown content to temp file
            with tempfile.NamedTemporaryFile(mode='w', 
                                            delete=False, 
                                            suffix='.md', 
                                            encoding='utf-8') as f:
                temp_md_file = f.name
                f.write(markdown_text)
            
            print(f"Converting to PNG using MarkItDown...")
            
            # Method 1: Try with a Unicode-compatible font
            try:
                # Create LaTeX header for unicode support
                header_file = create_latex_header()
                
                # Create a temporary output directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Get base filename without extension
                    base_filename = os.path.basename(output_path).split('.')[0]
                    temp_output = os.path.join(temp_dir, f"{base_filename}")
                    
                    # Convert markdown to PDF with proper font support
                    md_to_pdf_cmd = [
                        'pandoc',
                        temp_md_file,
                        '--pdf-engine=xelatex',
                        f'--include-in-header={header_file}',
                        '-o',
                        f"{temp_output}.pdf"
                    ]
                    subprocess.run(md_to_pdf_cmd, check=True)
                    
                    # Convert PDF to PNG
                    from pdf2image import convert_from_path
                    images = convert_from_path(f"{temp_output}.pdf", dpi=300)
                    images[0].save(output_path)
                    
                    print(f"Receipt saved as PNG: {output_path}")
                    return output_path
                    
            except Exception as e:
                print(f"Error with Unicode font method: {str(e)}")
                
                # Method 2: Replace Rupee symbol with text equivalent
                print("Trying alternative approach...")
                
                # Replace ₹ with "Rs." for better compatibility
                alt_markdown = markdown_text.replace(CURRENCY_SYMBOL, 'Rs.')
                
                # Save the modified content
                with open(temp_md_file, 'w', encoding='utf-8') as f:
                    f.write(alt_markdown)
                
                # Create a temporary output directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Get base filename without extension
                    base_filename = os.path.basename(output_path).split('.')[0]
                    temp_output = os.path.join(temp_dir, f"{base_filename}")
                    
                    # Convert to PDF with standard settings
                    md_to_pdf_cmd = [
                        'pandoc',
                        temp_md_file,
                        '--pdf-engine=xelatex',
                        '-o',
                        f"{temp_output}.pdf"
                    ]
                    subprocess.run(md_to_pdf_cmd, check=True)
                    
                    # Convert PDF to PNG
                    from pdf2image import convert_from_path
                    images = convert_from_path(f"{temp_output}.pdf", dpi=300)
                    images[0].save(output_path)
                    
                    print(f"Receipt saved as PNG (with 'Rs.' instead of ₹): {output_path}")
                    return output_path
                
        finally:
            # Clean up temp files
            if temp_md_file and os.path.exists(temp_md_file):
                os.unlink(temp_md_file)
            if header_file and os.path.exists(header_file):
                os.unlink(header_file)
                
    except ImportError as e:
        print(f"Required package not available: {str(e)}")
        print("Please install required packages with: pip install pdf2image pillow")
        return None
    except Exception as e:
        print(f"Error generating PNG: {str(e)}")
        return None

def main():
    """Main function to process grocery queries and generate receipts."""
    print("Grocery Receipt PNG Generator")
    print(f"All prices are in {CURRENCY} ({CURRENCY_SYMBOL})")
    
    if len(sys.argv) > 1:
        # If argument provided, use it as the query
        query = ' '.join(sys.argv[1:])
    else:
        # Otherwise, ask for input
        query = input("\nEnter your grocery list (e.g., '2.5kg rice, 750ml cooking oil, 3 packets of biscuits'): ")
    
    if not query.strip():
        print("No query provided. Exiting.")
        return
    
    # Generate receipt content
    print("\nGenerating receipt...")
    receipt_md = generate_receipt(query)
    
    # Save markdown version for reference (without think sections)
    md_path = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(receipt_md)
    print(f"Receipt content saved as: {md_path}")
    
    # Generate PNG
    png_path = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    png_path = generate_png_with_markitdown(receipt_md, png_path)
    
    if png_path and os.path.exists(png_path):
        # Try to open the image with the default viewer
        try:
            print(f"Opening receipt image: {png_path}")
            if os.name == 'nt':  # Windows
                os.startfile(png_path)
            elif os.name == 'posix':  # macOS or Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', png_path])
                else:  # Linux
                    subprocess.call(['xdg-open', png_path])
        except Exception as e:
            print(f"Could not open image automatically: {str(e)}")
            print(f"Please open {png_path} manually.")

if __name__ == "__main__":
    main()