from src.app.chatbot import *
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json

# Define the routes Blueprint
route_blueprint = Blueprint('routes', __name__)

# Define the /documents endpoint
@route_blueprint.route('/documents', methods=['GET'])                                                           # Define the /documents endpoint
def list_documents():                                                                               # Define the list_documents function
    return jsonify({"documents": list(chatbot.documents.keys())})                                   # Return the list of uploaded documents

@route_blueprint.route('/links', methods=['GET'])
def list_links():
    print("Received request for /links")
    return jsonify({"links": list(chatbot.links.keys())})

# Define the /upload endpoint
@route_blueprint.route('/document_upload', methods=['POST'])                                                             # Define the /upload endpoint
def upload_file():                                                                                  # Define the upload_file function
    if 'file' not in request.files:                                                                 # Check if the request contains a file part
        return jsonify({"error": "No file part"}), 400                                              # Return an error response if no file part is found
    file = request.files['file']                                                                    # Get the file from the request
    if file.filename == '':                                                                         # Check if the file name is empty
        return jsonify({"error": "No selected file"}), 400                                          # Return an error response if no file is selected
    if file and allowed_file(file.filename):                                                        # Check if the file is allowed
        filename = secure_filename(file.filename)                                                   # Secure the filename
        filepath = os.path.join(route_blueprint.config['UPLOAD_FOLDER'], filename)                              # Get the file path
        file.save(filepath)                                                                         # Save the file to the specified path
        chatbot.documents[filename] = chatbot.extract_text_from_file(filepath)                      # Extract text from the file and store it in the documents dictionary
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 200        # Return a success response
    return jsonify({"error": "File type not allowed"}), 400                                         # Return an error response if the file type is not allowed

# Define the /link_upload endpoint
@route_blueprint.route('/link_upload', methods=['POST'])
def crawl():
    data = request.get_json()
    urls = data.get('urls')
    if not urls:
        return jsonify({"response": "Error: Empty input"}), 400

    # Call the web crawler API here and return the result
    try:
        response = chatbot.extract_data_from_web_page(urls)
        if response:
            # Generate a safe filename
            filename = secure_filename(f"{urls}.json")
            filepath = os.path.join(route_blueprint.config['LINKS_FOLDER'], filename)
            # Save the response to a file
            with open(filepath, 'w') as file:
                json.dump(response, file)
            chatbot.links[filename] = response
            return jsonify({"response": response}), 200
        else:
            return jsonify({"response": "Error: Unable to extract data"}), 500
    except Exception as e:
        return jsonify({"response": f"Error: {e}"}), 500

@route_blueprint.route('/link_content', methods=['POST'])
def get_link_content():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"response": "Error: No filename provided"}), 400

    filepath = os.path.join(route_blueprint.config['LINKS_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({"response": "Error: File not found"}), 404

    try:
        with open(filepath, 'r') as file:
            content = json.load(file)
        return jsonify({"response": content}), 200
    except Exception as e:
        return jsonify({"response": f"Error: {e}"}), 500
    
# Define the /chat endpoint
@route_blueprint.route('/chat', methods=['POST'])                                                               # Define the /chat endpoint
def chat():                                                                                         # Define the chat function
    data = request.get_json()                                                                       # Get the JSON data from the request
    user_input = data.get('message')                                                                # Get the user input from the JSON data
    document_name = data.get('document')                                                            # Get the document name from the JSON data                                                                       # Get the link from the JSON data
    link = data.get('link')
    
    if not user_input:                                                                              # Check if the user input is empty
        return jsonify({'response': 'Error: Empty input'})                                          # Return an error response if the input is empty
    elif len(user_input) > 512:                                                                     # Check if the user input is too long
        return jsonify({'response': 'Error: Input too long'})                                       # Return an error response if the input is too long
    elif not isinstance(user_input, str):                                                           # Check if the user input is not a string
        return jsonify({'response': 'Error: Invalid input type'})                                   # Return an error response if the input is not a string
    elif user_input.lower() == '/bye':                                                              # Check if the user input is '/bye'
        formatted_inquiry = f"Am trying to say goodbye to you. Please wish me well."                # Format the user input
        simple_response = chatbot.get_simple_response(formatted_inquiry)                            # Generate a simple response
        return jsonify({'response': simple_response})                                               # Return the simple response
        exit()
    elif data.get('reasoning'):                                                                     # Check if the reasoning flag is set
        try:                                                                                        # Try to process the deepseek request
            simple_response = chatbot.get_simple_response(user_input)                               # Generate a simple response
            deepseek_input = f"Our client is requesting about this: {simple_response}"              # Format the deepseek input
            reasoned_response = chatbot.get_reasoned_response(deepseek_input)                       # Generate a reasoned response
            deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"        # Format the deepseek output
            final_response = chatbot.get_simple_response(deepseek_output)                           # Generate a simple response
            return jsonify({'response': final_response})                                            # Return the final response
        except Exception as e:                                                                      # Handle exceptions
            return jsonify({'response': f'Error: {e}'})                                             # Return an error response
    elif document_name:                                                                             # Check if a document name is provided
        if document_name in chatbot.documents:                                                      # Check if the document exists in the documents dictionary
            try:
                doc_content = chatbot.documents[document_name]                                          # Get the content of the document
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}"                    # Combine the user input and document content
                print(combined_input)
                response = chatbot.get_simple_response(combined_input)                                  # Generate a simple response
                return jsonify({'response': response})                                                  # Return the response
            except Exception as e:                                                                      # Handle exceptions
                return jsonify({'response': f'Error: {e}'})                                             # Return an error response
        else:                                                                                       # If the document does not exist
            return jsonify({'response': 'Error: Document not found'})                               # Return an error response
    elif data.get('reasoning') and document_name:
        if document_name in chatbot.documents:                                                      # Check if the document exists in the documents dictionary
            try:
                doc_content = chatbot.documents[document_name]                                          # Get the content of the document
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}"                    # Combine the user input and document content
                deepseek_input = f"Our client is requesting about this: {combined_input}"                # Format the deepseek input
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)                       # Generate a reasoned response
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"        # Format the deepseek output
                final_response = chatbot.get_simple_response(deepseek_output)                           # Generate a simple response
                return jsonify({'response': final_response})                                            # Return the final response
            except Exception as e:                                                                      # Handle exceptions
                return jsonify({'response': f'Error: {e}'})                                             # Return an error response
        else:                                                                                       # If the document does not exist
            return jsonify({'response': 'Error: Document not found'})                               # Return an error response
    elif link:
        if link in chatbot.links:                                                                   # Check if the link exists in the links dictionary
            try:
                link_content = chatbot.links[link]                                                       # Get the content of the link
                combined_input = f"{user_input}\n\nLink Content:\n{link_content}"                        # Combine the user input and link content
                response = chatbot.get_simple_response(combined_input)                                   # Generate a simple response
                return jsonify({'response': response})                                                   # Return the response
            except Exception as e:                                                                      # Handle exceptions
                return jsonify({'response': f'Error: {e}'})                                             # Return an error response
        else:                                                                                       # If the link does not exist
            return jsonify({'response': 'Error: Link not found'})                                     # Return an error response
    elif data.get('reasoning') and link:
        if link in chatbot.links:                                                                   # Check if the link exists in the links dictionary
            try:
                link_content = chatbot.links[link]                                                       # Get the content of the link
                combined_input = f"{user_input}\n\nLink Content:\n{link_content}"                        # Combine the user input and link content
                deepseek_input = f"Our client is requesting about this: {combined_input}"                # Format the deepseek input
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)                       # Generate a reasoned response
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"        # Format the deepseek output
                final_response = chatbot.get_simple_response(deepseek_output)                           # Generate a simple response
                return jsonify({'response': final_response})                                            # Return the final response
            except Exception as e:                                                                      # Handle exceptions
                return jsonify({'response': f'Error: {e}'})                                             # Return an error response
        else:                                                                                       # If the link does not exist
            return jsonify({'response': 'Error: Link not found'})                                     # Return an error response
    elif data.get('reasoning') and document_name and link:
        if document_name in chatbot.documents and link in chatbot.links:                              # Check if the document and link exist
            try:
                doc_content = chatbot.documents[document_name]                                          # Get the content of the document
                link_content = chatbot.links[link]                                                       # Get the content of the link
                combined_input = f"{user_input}\n\nDocument Content:\n{doc_content}\n\nLink Content:\n{link_content}" # Combine the user input, document content, and link content
                deepseek_input = f"Our client is requesting about this: {combined_input}"                # Format the deepseek input
                reasoned_response = chatbot.get_reasoned_response(deepseek_input)                       # Generate a reasoned response
                deepseek_output = f"Here is the relevant reasoned response: {reasoned_response}"        # Format the deepseek output
                final_response = chatbot.get_simple_response(deepseek_output)                           # Generate a simple response
                return jsonify({'response': final_response})                                            # Return the final response
            except Exception as e:                                                                      # Handle exceptions
                return jsonify({'response': f'Error: {e}'})                                             # Return an error response
        else:                                                                                       # If the document or link does not exist
            return jsonify({'response': 'Error: Document or link not found'})                        # Return an error responseected
    else:                                                                                           # If none of the above conditions are met
        try:
            simple_response = chatbot.get_simple_response(user_input)                                   # Generate a simple response
            return jsonify({'response': simple_response})                                               # Return the simple response
        except Exception as e:                                                                      # Handle exceptions
            return jsonify({'response': f'Error: {e}'})                                                 # Return an error response