import markdown
from pathlib import Path
import subprocess
import sys

def convert_md_to_pdf():
    """Convert REVISION_RESPONSE.md to PDF using available tools."""
    
    # File paths
    md_file = Path(r"c:\Users\Jack0\GitHub\Air-quality-insight-Uzbekistan\Research_paper\npj_urban_sustainability\REVISION_RESPONSE.md")
    html_file = Path(r"c:\Users\Jack0\GitHub\Air-quality-insight-Uzbekistan\Research_paper\npj_urban_sustainability\REVISION_RESPONSE.html")
    pdf_file = Path(r"c:\Users\Jack0\GitHub\Air-quality-insight-Uzbekistan\Research_paper\npj_urban_sustainability\REVISION_RESPONSE_npjUS.pdf")
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML with extensions
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # Add professional styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Revision Response - npj Urban Sustainability</title>
        <style>
            @page {{
                size: letter;
                margin: 1in;
            }}
            body {{
                font-family: 'Times New Roman', Times, serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #000;
                max-width: 8.5in;
                margin: 0 auto;
            }}
            h1 {{
                font-size: 18pt;
                font-weight: bold;
                margin-top: 24pt;
                margin-bottom: 12pt;
                page-break-after: avoid;
            }}
            h2 {{
                font-size: 14pt;
                font-weight: bold;
                margin-top: 18pt;
                margin-bottom: 10pt;
                page-break-after: avoid;
            }}
            h3 {{
                font-size: 12pt;
                font-weight: bold;
                margin-top: 12pt;
                margin-bottom: 8pt;
                page-break-after: avoid;
            }}
            p {{
                margin-bottom: 10pt;
                text-align: justify;
            }}
            ul, ol {{
                margin-bottom: 10pt;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12pt 0;
                page-break-inside: avoid;
            }}
            th {{
                background-color: #f0f0f0;
                border: 1px solid #000;
                padding: 8pt;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                border: 1px solid #000;
                padding: 8pt;
                text-align: left;
            }}
            blockquote {{
                margin: 12pt 0;
                padding-left: 16pt;
                border-left: 4pt solid #ccc;
                font-style: italic;
                color: #555;
            }}
            code {{
                font-family: 'Courier New', monospace;
                background-color: #f5f5f5;
                padding: 2pt 4pt;
                border-radius: 3pt;
            }}
            hr {{
                border: none;
                border-top: 2pt solid #000;
                margin: 18pt 0;
            }}
            .checkmark {{
                color: #0c0;
                font-weight: bold;
            }}
            @media print {{
                body {{
                    font-size: 11pt;
                }}
                h1, h2, h3 {{
                    page-break-after: avoid;
                }}
                table {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    print(f"✅ HTML file created: {html_file}")
    
    # Try weasyprint first
    try:
        from weasyprint import HTML
        HTML(filename=str(html_file)).write_pdf(str(pdf_file))
        print(f"✅ PDF created successfully using WeasyPrint: {pdf_file}")
        return True
    except ImportError:
        print("⚠️ WeasyPrint not installed. Trying alternative methods...")
    except Exception as e:
        print(f"⚠️ WeasyPrint error: {e}")
    
    # Try pdfkit
    try:
        import pdfkit
        pdfkit.from_file(str(html_file), str(pdf_file))
        print(f"✅ PDF created successfully using pdfkit: {pdf_file}")
        return True
    except ImportError:
        print("⚠️ pdfkit not installed. Trying alternative methods...")
    except Exception as e:
        print(f"⚠️ pdfkit error: {e}")
    
    # Try using Microsoft Edge browser (available on Windows)
    try:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if Path(edge_path).exists():
            subprocess.run([
                edge_path,
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + str(pdf_file),
                str(html_file)
            ], check=True)
            print(f"✅ PDF created successfully using Microsoft Edge: {pdf_file}")
            return True
        else:
            print("⚠️ Microsoft Edge not found at expected location")
    except Exception as e:
        print(f"⚠️ Edge browser error: {e}")
    
    # If all else fails, provide instructions
    print("\n❌ Unable to generate PDF automatically.")
    print(f"\n📄 HTML file has been created: {html_file}")
    print("\nTo create PDF manually:")
    print("1. Open REVISION_RESPONSE.html in your browser")
    print("2. Press Ctrl+P (Print)")
    print("3. Select 'Save as PDF' as the printer")
    print(f"4. Save as: {pdf_file}")
    print("\nOR install one of these:")
    print("  pip install weasyprint")
    print("  pip install pdfkit")
    
    return False

if __name__ == "__main__":
    try:
        success = convert_md_to_pdf()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
