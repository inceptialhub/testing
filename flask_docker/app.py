import logging
from flask import Flask, request, jsonify
import os
import face_recognition
import shutil
import json

app = Flask(__name__)

# Define base folder paths (for Docker compatibility)
BASE_DIR = os.getenv("BASE_DIR", "/app")
BULK_FOLDER = os.path.join(BASE_DIR, "bulk")
SINGLE_FOLDER = os.path.join(BASE_DIR, "single")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

# Ensure the folders exist
os.makedirs(BULK_FOLDER, exist_ok=True)
os.makedirs(SINGLE_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Setup logger
LOG_FILE = "api_logbook.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Logs also appear in the console
    ]
)
logger = logging.getLogger(__name__)

# Example usage of the logger
logger.info("Logger initialized successfully.")

@app.route('/upload_and_match', methods=['POST'])
def upload_and_match():
    logger.info("Received request at /upload_and_match endpoint.")

    if 'file' not in request.files or 'json_data' not in request.form:
        logger.warning("File or JSON data missing in the request.")
        return jsonify({"error": "File and JSON data are required"}), 400

    file = request.files['file']
    json_data = request.form['json_data']

    if file.filename == '':
        logger.warning("No file selected.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type. Only .jpg, .jpeg, and .png are allowed."}), 400

    # Parse JSON data to get specific photo names and IDs
    try:
        photo_data = json.loads(json_data)
        selected_photos = {item['name']: item['id'] for item in photo_data}  # Map names to IDs
        logger.info(f"Parsed JSON data successfully: {selected_photos}")
    except (json.JSONDecodeError, KeyError):
        logger.error("Invalid JSON data provided.")
        return jsonify({"error": "Invalid JSON data. Each entry must include 'name' and 'id' fields."}), 400

    # Save the uploaded file
    single_image_path = os.path.join(SINGLE_FOLDER, file.filename)
    try:
        file.save(single_image_path)
        logger.info(f"File saved at {single_image_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        return jsonify({"error": f"Failed to save uploaded file: {str(e)}"}), 500

    # Load and encode the uploaded image
    try:
        single_image = face_recognition.load_image_file(single_image_path)
        single_encodings = face_recognition.face_encodings(single_image)
    except Exception as e:
        logger.error(f"Failed to process the uploaded image: {e}")
        return jsonify({"error": f"Failed to process the uploaded image: {str(e)}"}), 500

    if not single_encodings:
        logger.warning("No face detected in the uploaded image.")
        return jsonify({"error": "No face detected in the uploaded image"}), 400

    results = []
    tolerance = 0.5  # Lower tolerance for stricter matching
    distance_threshold = 0.4  # Additional threshold for face distance

    # Iterate through selected photos for face matching
    for image_file, image_id in selected_photos.items():
        bulk_image_path = os.path.join(BULK_FOLDER, image_file)
        if not os.path.exists(bulk_image_path):
            logger.warning(f"Bulk image not found: {bulk_image_path}")
            continue

        try:
            bulk_image = face_recognition.load_image_file(bulk_image_path)
            bulk_encodings = face_recognition.face_encodings(bulk_image)
        except Exception as e:
            logger.warning(f"Error processing bulk image {bulk_image_path}: {e}")
            continue

        if not bulk_encodings:
            logger.warning(f"No faces detected in bulk image: {bulk_image_path}")
            continue

        for i, single_encoding in enumerate(single_encodings):
            for j, bulk_encoding in enumerate(bulk_encodings):
                match = face_recognition.compare_faces([bulk_encoding], single_encoding, tolerance=tolerance)
                distance = face_recognition.face_distance([bulk_encoding], single_encoding)[0]

                if match[0] and distance < distance_threshold:
                    confidence = max(0, (1.0 - distance)) * 100
                    results.append({
                        "uploaded_face_index": i,
                        "matched_face_index_in_bulk": j,
                        "matched_file": image_file,
                        "matched_id": image_id,
                        "confidence": f"{confidence:.2f} %",
                        "face_distance": distance
                    })
                    logger.info(f"Match found: {results[-1]}")

    # Move the uploaded image to the processed folder
    try:
        processed_image_path = os.path.join(PROCESSED_FOLDER, file.filename)
        shutil.move(single_image_path, processed_image_path)
        logger.info(f"File moved to processed folder: {processed_image_path}")
    except Exception as e:
        logger.error(f"Failed to move processed image: {e}")
        return jsonify({"error": f"Failed to move processed image: {str(e)}"}), 500

    if results:
        logger.info(f"Matching completed successfully for file: {file.filename}")
        return jsonify({
            "message": "Success! Matches found.",
            "matches": results,
            "uploaded_file": file.filename
        })

    logger.info(f"No matches found for file: {file.filename}")
    return jsonify({
        "message": "No match found",
        "uploaded_file": file.filename
    })

if __name__ == '__main__':
    logger.info("Starting Flask app on port 5008")
    app.run(debug=True, host='0.0.0.0', port=5008)

# import logging
# from flask import Flask, request, jsonify
# import os
# import face_recognition
# import shutil
# import json

# app = Flask(__name__)

# # Define paths for bulk, single, and processed folders
# BULK_FOLDER = "/Users/aditya/Downloads/bulk"
# SINGLE_FOLDER = "/Users/aditya/Downloads/single"
# PROCESSED_FOLDER = "/Users/aditya/Downloads/PROCESSED"

# # Ensure the folders exist
# os.makedirs(BULK_FOLDER, exist_ok=True)
# os.makedirs(SINGLE_FOLDER, exist_ok=True)
# os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# # Setup logger
# LOG_FILE = "api_logbook.log"
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
#     handlers=[
#         logging.FileHandler(LOG_FILE),
#         logging.StreamHandler()  # Logs also appear in the console
#     ]
# )
# logger = logging.getLogger(__name__)



# from logging.handlers import TimedRotatingFileHandler

# # Create a logger
# logger = logging.getLogger("DatewiseLogger")
# logger.setLevel(logging.DEBUG)  # Set the logging level

# # Create a TimedRotatingFileHandler
# log_handler = TimedRotatingFileHandler(
#     filename="app.log",  # Base filename
#     when="midnight",     # Rotate the log at midnight
#     interval=1,          # Rotate every day
#     backupCount=7        # Keep logs for the last 7 days
# )
# log_handler.suffix = "%Y-%m-%d"  # Add the date to the log file name
# log_handler.setLevel(logging.DEBUG)

# # Create a formatter and add it to the handler
# formatter = logging.Formatter("%(asctime)s - %(levelname)s:%(lineno)d - %(message)s")

# log_handler.setFormatter(formatter)

# # Add the handler to the logger
# logger.addHandler(log_handler)

# # Example usage of the logger
# logger.info("This is an info log entry.")
# logger.error("This is an error log entry.")

# @app.route('/upload_and_match', methods=['POST'])
# def upload_and_match():
#     logger.info("Received request at /upload_and_match endpoint.")
    
#     if 'file' not in request.files or 'json_data' not in request.form:
#         logger.warning("File or JSON data missing in the request.")
#         return jsonify({"error": "File and JSON data are required"}), 400

#     file = request.files['file']
#     json_data = request.form['json_data']

#     if file.filename == '':
#         logger.warning("No file selected.")
#         return jsonify({"error": "No selected file"}), 400

#     if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
#         logger.warning(f"Invalid file type: {file.filename}")
#         return jsonify({"error": "Invalid file type. Only .jpg, .jpeg, and .png are allowed."}), 400

#     # Parse JSON data to get specific photo names and IDs
#     try:
#         photo_data = json.loads(json_data)
#         selected_photos = {item['name']: item['id'] for item in photo_data}  # Map names to IDs
#         logger.info(f"Parsed JSON data successfully: {selected_photos}")
#     except (json.JSONDecodeError, KeyError):
#         logger.error("Invalid JSON data provided.")
#         return jsonify({"error": "Invalid JSON data. Each entry must include 'name' and 'id' fields."}), 400

#     single_image_path = os.path.join(SINGLE_FOLDER, file.filename)
#     file.save(single_image_path)
#     logger.info(f"File saved at {single_image_path}")

#     single_image = face_recognition.load_image_file(single_image_path)
#     single_encodings = face_recognition.face_encodings(single_image)

#     if not single_encodings:
#         logger.warning("No face detected in the uploaded image.")
#         return jsonify({"error": "No face detected in the uploaded image"}), 400

#     results = []
#     tolerance = 0.5  # Lower tolerance for stricter matching
#     distance_threshold = 0.4  # Additional threshold for face distance

#     for image_file, image_id in selected_photos.items():
#         bulk_image_path = os.path.join(BULK_FOLDER, image_file)
        
#         if not os.path.exists(bulk_image_path):
#             logger.warning(f"Bulk image not found: {bulk_image_path}")
#             continue
        
#         bulk_image = face_recognition.load_image_file(bulk_image_path)
#         bulk_encodings = face_recognition.face_encodings(bulk_image)

#         if not bulk_encodings:
#             logger.warning(f"No faces detected in bulk image: {bulk_image_path}")
#             continue

#         for i, single_encoding in enumerate(single_encodings):
#             for j, bulk_encoding in enumerate(bulk_encodings):
#                 match = face_recognition.compare_faces([bulk_encoding], single_encoding, tolerance=tolerance)
#                 distance = face_recognition.face_distance([bulk_encoding], single_encoding)[0]
                
#                 if match[0] and distance < distance_threshold:
#                     confidence = max(0, (1.0 - distance)) * 100
#                     results.append({
#                         "uploaded_face_index": i,
#                         "matched_face_index_in_bulk": j,
#                         "matched_file": image_file,
#                         "matched_id": image_id,
#                         "confidence": f"{confidence:.2f} %",
#                         "face_distance": distance
#                     })
#                     logger.info(f"Match found: {results[-1]}")

#     processed_image_path = os.path.join(PROCESSED_FOLDER, file.filename)
#     shutil.move(single_image_path, processed_image_path)
#     logger.info(f"File moved to processed folder: {processed_image_path}")

#     if results:
#         logger.info(f"Matching completed successfully for file: {file.filename}")
#         return jsonify({
#             "message": "Success! Matches found.",
#             "matches": results,
#             "uploaded_file": file.filename
#         })

#     logger.info(f"No matches found for file: {file.filename}")
#     return jsonify({
#         "message": "No match found",
#         "uploaded_file": file.filename
#     })

# if __name__ == '__main__':
#     logger.info("Starting Flask app on port 5008")
#     app.run(debug=True,host='0.0.0.0', port=5008)
