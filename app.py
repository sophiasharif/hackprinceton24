from flask import Flask, render_template, Response, jsonify
import cv2
import logging
import os
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

camera = None
current_model = None

# Initialize models
def initialize_models():
    global current_model
    try:
        from models.main import trash1, trash2, fruits
        current_model = trash1
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")

initialize_models()

def get_camera():
    global camera
    if camera is None:
        logger.info("Attempting to open camera 1...")
        camera = cv2.VideoCapture(1)
        if not camera.isOpened():
            logger.info("Camera 1 failed, trying camera 0...")
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                logger.error("Failed to open any camera!")
                return None
            else:
                logger.info("Successfully opened camera 0")
        else:
            logger.info("Successfully opened camera 1")
        
        # Set camera resolution to 1280x720 (720p)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return camera

def generate_frames():
    camera = get_camera()
    if camera is None:
        return
        
    while True:
        try:
            success, frame = camera.read()
            if not success:
                logger.error("Failed to read frame")
                break
            else:
                frame = cv2.flip(frame, 1)  # Mirror the frame
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.error("Failed to encode frame")
                    continue
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            logger.error(f"Error in generate_frames: {str(e)}")
            break

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    camera = get_camera()
    if camera is None:
        return "Camera not available", 500
        
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/classify')
def classify_frame():
    global current_model
    if current_model is None:
        return jsonify({"error": "Model not initialized"})
        
    camera = get_camera()
    if camera is None:
        return jsonify({"error": "Camera not available"})
        
    success, frame = camera.read()
    if success:
        frame = cv2.flip(frame, 1)  # Mirror the frame
        try:
            # Generate timestamp for unique filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            image_path = os.path.join('images', f'capture_{timestamp}.jpg')
            
            # Save the frame as JPEG
            cv2.imwrite(image_path, frame)
            
            # Perform classification
            result = current_model.classify(frame, return_all=True)
            if not result:
                return jsonify({"error": "No classification results"})
            
            # Ensure results are sorted by confidence descending
            result_sorted = sorted(result, key=lambda x: x[2], reverse=True)
            top_result = result_sorted[0]
            category, label, score = top_result
            category_name = str(category).split('.')[-1]
            return jsonify({
                "category": category_name,
                "label": label,
                "confidence": f"{score:.2%}",
                "image_saved": image_path
            })
        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            return jsonify({"error": f"Classification error: {str(e)}"})
    return jsonify({"error": "Failed to capture frame"})

@app.route('/switch_model/<model_name>')
def switch_model(model_name):
    global current_model
    try:
        from models.main import trash1, trash2, fruits
        models = {
            'trash1': trash1,
            'trash2': trash2,
            'fruits': fruits
        }
        if model_name in models:
            current_model = models[model_name]
            logger.info(f"Switched to model: {model_name}")
            return jsonify({"success": True, "message": f"Switched to model: {model_name}"})
        else:
            return jsonify({"success": False, "error": "Model not found"})
    except Exception as e:
        logger.error(f"Error switching model: {str(e)}")
        return jsonify({"error": str(e)})
    
if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5001)
