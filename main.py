import os
import io
from flask import Flask, render_template, request, flash, send_file

# --- Basic Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-that-no-one-should-guess'

# --- Core Logic (Unchanged) ---
TASK_TEMPLATE = """<task><taskId>{task_id}</taskId>
<taskStatus>Pending</taskStatus><category>BUILD-ING_CREATION</category>
<taskDescription>QIL for Stuggart, asbhatka</taskDescription>
<inboundContextData><items>
      <item><key>earthCoreUrl</key><value>{earthcore_url}</value></item>
      <item><key>tileId</key><value>{tile_id}</value></item>
      <item><key>tileScheme</key><value>HERE</value></item>
      <item><key>tileKeyFormat</key><value>LONGKEY</value></item>
</items></inboundContextData>
</task>"""
XML_HEADER = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n<mockTaskList>\n<taskList>"
XML_FOOTER = "</taskList>\n</mockTaskList>"
MAX_TASKS_PER_FILE = 99
PROD_URL = "http://ecfs-buildings.3dmap.here.com/ec-proxy/"
UAT_URL = "http://ecfs-buildings-uat.3dmap.here.com/ec-proxy/"

def generate_xml_content(tile_ids_chunk, starting_task_id, earthcore_url):
    task_xml_parts = [TASK_TEMPLATE.format(
        task_id=starting_task_id + i,
        tile_id=tile_id,
        earthcore_url=earthcore_url
    ) for i, tile_id in enumerate(tile_ids_chunk)]
    
    return "\n".join([XML_HEADER, *task_xml_parts, XML_FOOTER])

# --- Flask Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    # --- POST request logic ---
    env_choice = request.form.get('environment')
    base_filename = request.form.get('base_filename').strip()
    tile_ids_raw = request.form.get('tile_ids').splitlines()
    all_tile_ids = [line.strip() for line in tile_ids_raw if line.strip()]

    # --- Input Validation ---
    if not base_filename or not all_tile_ids:
        flash('Error: Base Filename and at least one Tile ID are required.', 'error')
        return render_template('index.html')
    
    for tile_id in all_tile_ids:
        if not tile_id.isdigit():
            flash(f"Error: Invalid Tile ID '{tile_id}'. All IDs must be numbers.", 'error')
            return render_template('index.html')

    # --- File Generation Logic ---
    selected_url = PROD_URL if env_choice == "PROD" else UAT_URL
    total_tiles = len(all_tile_ids)
    
    num_files_to_be_created = (total_tiles + MAX_TASKS_PER_FILE - 1) // MAX_TASKS_PER_FILE

    if num_files_to_be_created == 1:
        # --- Single File: Send directly ---
        xml_output = generate_xml_content(all_tile_ids, 1, selected_url)
        memory_file = io.BytesIO(xml_output.encode('utf-8'))
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f'{base_filename}.txt',
            mimetype='text/plain'
        )
    else:
        # --- Multiple Files: Prepare data for the download page ---
        files_data = []
        global_task_id_counter = 1
        file_counter = 1
        for i in range(0, total_tiles, MAX_TASKS_PER_FILE):
            tile_id_chunk = all_tile_ids[i: i + MAX_TASKS_PER_FILE]
            xml_output = generate_xml_content(tile_id_chunk, global_task_id_counter, selected_url)
            
            filename = f"{base_filename}_{file_counter}.txt"
            
            files_data.append({
                'filename': filename,
                'content': xml_output
            })
            
            file_counter += 1
            global_task_id_counter += len(tile_id_chunk)
            
        # Render the download page and pass the file data to it
        return render_template('download.html', files=files_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)