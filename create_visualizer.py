import os
import glob

def generate_html(output_dir, num_pages):
    """Создает HTML файл для визуализации JSON данных."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DOCX Block Visualizer</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 1em; box-sizing: border-box; }}
        #main-container {{ display: flex; gap: 20px; height: 95vh; }}
        #page-container {{
            position: relative;
            border: 1px solid #ccc;
            background-color: #f9f9f9;
            flex: 1;
            aspect-ratio: 210 / 297; /* A4 aspect ratio */
        }}
        #text-container {{
            flex: 1;
            border: 1px solid #ccc;
            padding: 10px;
            overflow-y: auto;
            white-space: pre-wrap; /* Respect newlines in text */
            background-color: #fff;
        }}
        #text-container span {{
            cursor: pointer;
            display: block;
            margin-bottom: 1em;
            padding: 5px;
            border-radius: 3px;
        }}
        #text-container span:hover {{
            background-color: #f0f0f0;
        }}
        .block {{
            position: absolute;
            border: 1px solid rgba(255, 0, 0, 0.7);
            background-color: rgba(255, 0, 0, 0.1);
            box-sizing: border-box;
            transition: background-color 0.2s, border-color 0.2s;
            /* For blocks with no explicit size */
            min-width: 1%; 
            min-height: 1%;
            overflow: hidden;
        }}
        .block.image {{
            border-color: rgba(0, 0, 255, 0.7);
            background-color: rgba(0, 0, 255, 0.1);
        }}
        .block.highlighted {{
            background-color: rgba(255, 255, 0, 0.5);
            border-color: #ff0;
        }}
        .block.autosized {{
            /* Make autosized blocks visible but distinct */
            width: auto !important;
            height: auto !important;
        }}
        #controls {{ display: flex; flex-direction: column; }}
    </style>
</head>
<body>
    <div id="controls">
        <h3>Page Navigator</h3>
        <select id="page-selector">
            {"".join(f'<option value="{i}">Page {i}</option>' for i in range(1, num_pages + 1))}
        </select>
    </div>
    <div id="main-container">
        <div id="page-container"></div>
        <div id="text-container"></div>
    </div>

<script>
    const pageContainer = document.getElementById('page-container');
    const textContainer = document.getElementById('text-container');
    const pageSelector = document.getElementById('page-selector');
    const totalPages = {num_pages};

    async function loadPage(pageNumber) {{
        pageContainer.innerHTML = ''; // Clear previous blocks
        textContainer.innerHTML = ''; // Clear previous text
        try {{
            const response = await fetch(`out/page_${{pageNumber}}.json`);
            if (!response.ok) {{
                pageContainer.innerText = `Could not load page_${{pageNumber}}.json`;
                return;
            }}
            const data = await response.json();
            
            data.blocks.forEach((blockData, index) => {{
                const blockId = `block-${{index}}`;

                // --- Create visual block on the left ---
                const blockDiv = document.createElement('div');
                blockDiv.className = 'block';
                blockDiv.id = `vis-${{blockId}}`;
                if (blockData.type === 'image') {{
                    blockDiv.classList.add('image');
                }}
                const rect = blockData.bounding_rect;
                blockDiv.style.left = `${{rect.x}}%`;
                blockDiv.style.top = `${{rect.y}}%`;
                blockDiv.style.width = `${{rect.width}}%`;
                blockDiv.style.height = `${{rect.height}}%`;
                if (rect.width === 0 || rect.height === 0) {{
                    blockDiv.classList.add('autosized');
                    blockDiv.innerText = blockData.text; // Show text to give it size
                }}
                pageContainer.appendChild(blockDiv);

                // --- Create text span on the right ---
                const textSpan = document.createElement('span');
                textSpan.id = `text-${{blockId}}`;
                textSpan.innerText = blockData.text || '[IMAGE]';
                textContainer.appendChild(textSpan);

                // --- Add hover events ---
                textSpan.addEventListener('mouseover', () => {{
                    document.getElementById(`vis-${{blockId}}`).classList.add('highlighted');
                }});
                textSpan.addEventListener('mouseout', () => {{
                    document.getElementById(`vis-${{blockId}}`).classList.remove('highlighted');
                }});
            }});
        }} catch (error) {{
            console.error('Error loading or parsing JSON:', error);
            pageContainer.innerText = 'Error loading page data.';
        }}
    }}

    pageSelector.addEventListener('change', (e) => {{
        loadPage(e.target.value);
    }});

    // Load the first page initially
    loadPage(1);
</script>
</body>
</html>
    """
    # Явно указываем encoding='utf-8' для надежной работы в любой ОС
    with open(os.path.join(output_dir, "visualizer.html"), "w", encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, 'out')

    if not os.path.isdir(json_dir):
        print(f"Ошибка: Директория '{json_dir}' не найдена.")
        print("Сначала запустите abbyy_docx_extractor.py для генерации JSON файлов.")
        exit(1)

    json_files = glob.glob(os.path.join(json_dir, 'page_*.json'))
    if not json_files:
        print(f"Ошибка: В директории '{json_dir}' не найдены файлы page_*.json.")
        exit(1)
        
    num_pages = len(json_files)

    generate_html(script_dir, num_pages)
    print(f"Создан/обновлен визуализатор: {os.path.join(script_dir, 'visualizer.html')}")