import json
import os

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from src.app.chatbot import *
from werkzeug.utils import secure_filename

# Define the routes Blueprint
route_blueprint = Blueprint('routes', __name__)

# Configure upload folder
UPLOADS_FOLDER = 'uploads'
if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)
route_blueprint.config = {'UPLOAD_FOLDER': UPLOADS_FOLDER}

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define the /documents endpoint
@route_blueprint.route('/documents', methods=['GET'])
def list_documents():
    return jsonify({"documents": list(chatbot.documents.keys())})

@route_blueprint.route('/links', methods=['GET'])
def list_links():
    print("Received request for /links")
    return jsonify({"links": list(chatbot.links.keys())})

# Define the /upload endpoint
@route_blueprint.route('/document_upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(route_blueprint.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from the file
        try:
            content = chatbot.extract_text_from_file(filepath)
            chatbot.documents[filename] = content
            
            # Create a file message with metadata
            response_data = {
                "message": "File uploaded successfully",
                "content": content,
                "metadata": {
                    "fileName": filename,
                    "fileType": file.content_type,
                    "fileSize": os.path.getsize(filepath)
                }
            }
            print("Sending response:", response_data)  # Debug log
            return jsonify(response_data), 200
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "File type not allowed"}), 400

# Define the /link_upload endpoint
@route_blueprint.route('/link_upload', methods=['POST'])
async def crawl():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        url = data.get('url')
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # Extract and store link data
        link_data = await chatbot.extract_data_from_web_page(url)
        
        # Return the link data
        return jsonify({
            "message": "Link processed successfully",
            "link": {
                "id": link_data['url'],
                "title": link_data['title'],
                "description": link_data['description'],
                "image": link_data.get('image'),  # Include the image URL
                "timestamp": link_data['timestamp']
            }
        }), 200
    except Exception as e:
        logger.error(f"Error processing link: {e}")
        return jsonify({"error": str(e)}), 500

@route_blueprint.route('/link_delete', methods=['POST'])
def delete_link():
    data = request.get_json()
    link_id = data.get('id')
    if not link_id:
        return jsonify({"error": "No link ID provided"}), 400

    try:
        # Delete link directory
        link_dir = os.path.join(route_blueprint.config['LINKS_FOLDER'], link_id)
        if os.path.exists(link_dir):
            import shutil
            shutil.rmtree(link_dir)
        
        # Remove from memory
        if link_id in chatbot.links:
            del chatbot.links[link_id]
        
        return jsonify({"message": "Link deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting link: {e}")
        return jsonify({"error": str(e)}), 500

@route_blueprint.route('/link_content', methods=['POST'])
def get_link_content():
    data = request.get_json()
    link_id = data.get('id')
    if not link_id:
        return jsonify({"error": "No link ID provided"}), 400

    try:
        # Get link directory
        link_dir = os.path.join(route_blueprint.config['LINKS_FOLDER'], link_id)
        if not os.path.exists(link_dir):
            return jsonify({"error": "Link not found"}), 404

        # Read metadata
        metadata_path = os.path.join(link_dir, 'meta.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Read content
        content_path = os.path.join(link_dir, 'content.txt')
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            "metadata": metadata,
            "content": content
        }), 200
    except Exception as e:
        logger.error(f"Error getting link content: {e}")
        return jsonify({"error": str(e)}), 500
    
# Define the /chat endpoint
@route_blueprint.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message')
    conversation_id = data.get('conversation_id')
    document_name = data.get('document')
    link = data.get('link')
    
    if not user_input:
        return jsonify({'response': 'Error: Empty input'}), 400
    elif len(user_input) > 512:
        return jsonify({'response': 'Error: Input too long'}), 400
    elif not isinstance(user_input, str):
        return jsonify({'response': 'Error: Invalid input type'}), 400
    elif user_input.lower() == '/bye':
        formatted_inquiry = f"Am trying to say goodbye to you. Please wish me well."
        simple_response = chatbot.get_simple_response(formatted_inquiry)
        return jsonify({'response': simple_response})
        exit()
    elif data.get('reasoning'):
        try:
            simple_response = chatbot.get_simple_response(user_input)
            deepseek_input = f"Our client is requesting about this: {simple_response}"
            reasoned_response = chatbot.get_reasoned_response(deepseek_input)
            deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"
            final_response = chatbot.get_simple_response(deepseek_output)
            return jsonify({'response': final_response})
        except Exception as e:
            return jsonify({'response': f'Error: {e}'}), 500
    elif document_name:
        if document_name in chatbot.documents:
            try:
                doc_content = chatbot.documents[document_name]
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}"
                print(combined_input)
                response = chatbot.get_simple_response(combined_input)
                return jsonify({'response': response})
            except Exception as e:
                return jsonify({'response': f'Error: {e}'}), 500
        else:
            return jsonify({'response': 'Error: Document not found'}), 404
    elif data.get('reasoning') and document_name:
        if document_name in chatbot.documents:
            try:
                doc_content = chatbot.documents[document_name]
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}"
                deepseek_input = f"Our client is requesting about this: {combined_input}"
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"
                final_response = chatbot.get_simple_response(deepseek_output)
                return jsonify({'response': final_response})
            except Exception as e:
                return jsonify({'response': f'Error: {e}'}), 500
        else:
            return jsonify({'response': 'Error: Document not found'}), 404
    elif link:
        if link in chatbot.links:
            try:
                link_content = chatbot.links[link]
                combined_input = f"{user_input}\n\nLink Content:\n{link_content}"
                response = chatbot.get_simple_response(combined_input)
                return jsonify({'response': response})
            except Exception as e:
                return jsonify({'response': f'Error: {e}'}), 500
        else:
            return jsonify({'response': 'Error: Link not found'}), 404
    elif data.get('reasoning') and link:
        if link in chatbot.links:
            try:
                link_content = chatbot.links[link]
                combined_input = f"{user_input}\n\nLink Content:\n{link_content}"
                deepseek_input = f"Our client is requesting about this: {combined_input}"
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"
                final_response = chatbot.get_simple_response(deepseek_output)
                return jsonify({'response': final_response})
            except Exception as e:
                return jsonify({'response': f'Error: {e}'}), 500
        else:
            return jsonify({'response': 'Error: Link not found'}), 404
    elif data.get('reasoning') and document_name and link:
        if document_name in chatbot.documents and link in chatbot.links:
            try:
                doc_content = chatbot.documents[document_name]
                link_content = chatbot.links[link]
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}\n\nLink Content:\n{link_content}"
                deepseek_input = f"Our client is requesting about this: {combined_input}"
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"
                final_response = chatbot.get_simple_response(deepseek_output)
                return jsonify({'response': final_response})
            except Exception as e:
                return jsonify({'response': f'Error: {e}'}), 500
        else:
            return jsonify({'response': 'Error: Document or link not found'}), 404
    else:
        try:
            simple_response = chatbot.get_simple_response(user_input)
            return jsonify({'response': simple_response})
        except Exception as e:
            return jsonify({'response': f'Error: {e}'}), 500