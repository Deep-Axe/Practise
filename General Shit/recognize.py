import base64
#import dlib
import numpy as np
import cv2, json, os #random, time
import face_recognition
from vision.spoof_detection import SpoofDetector
import datetime
import glob
import sys, os, threading
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

VisionSight = False
VisionDevice = None

async def set_user_key(key):
    """Set the user key for authentication broadcasting"""
    RecognizeFrame.user_key = key
    
async def set_system_log(log_function):
    """Set the system log function for authentication broadcasting"""
    RecognizeFrame.system_log = log_function

FrameDimension = {'W': 1920, 'H': 1080}
frame_buffer = []
FRAME_BUFFER_SIZE = 5
CONFIDENCE_THRESHOLD = 0.65
spoof_detector = SpoofDetector()

def broadcast_authentication(user_key, system_log):
    """Broadcasts authentication status without causing circular imports"""
    try:
        # Import only here when needed, not at the module level
        from Network import NetworkAuth
        
        # Broadcast authentication status in a background thread
        broadcast_thread = threading.Thread(
            target=NetworkAuth.network_auth.broadcast_auth_status,
            args=(user_key,),
            daemon=True
        )
        broadcast_thread.start()
        system_log("Vision authentication broadcast sent to network")
    except Exception as e:
        print(f"Error broadcasting vision authentication: {e}")

# http://dlib.net/files/shape_predictor_81_face_landmarks.dat.bz2
# https://github.com/codeniko/shape_predictor_81_face_landmarks/blob/master/shape_predictor_81_face_landmarks.dat

# http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

#shape_predictor = dlib.shape_predictor("./models/shape_predictor_81_face_landmarks.dat")


'''def UpdateMask():
    global FaceAlignMask
    FaceAlignMask = ((FrameDimension['W'] // 2, FrameDimension['H'] // 2) , 120, 160)

c = 100'''

def load_reference_embeddings(directory):
    embeddings = []
    try:
        primary_path = os.path.join(directory, 'face_encoding.npy')
        if os.path.exists(primary_path):
            embeddings.append(np.load(primary_path))
        else:
            print(f"Primary face encoding not found at {primary_path}")
            return None
        
        recognize_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), directory, 'recognize_encodings')
        if os.path.exists(recognize_dir):
            encoding_files = glob.glob(os.path.join(recognize_dir, 'encoding_*.npy'))
            encoding_files.sort(key=os.path.getctime, reverse=True)
            for encoding_file in encoding_files[:4]:
                embeddings.append(np.load(encoding_file))

    except Exception as e:
        print(f"Error loading embeddings: {e}")
    return embeddings if embeddings else None

async def RecognizeFrame(frame, directory, websocket, response):
    '''
    frame - current video feed frame
    directory - directory containing the frames as reference for recognition
    '''
    global frame_buffer, VisionSight
    if not hasattr(RecognizeFrame, 'ref_embeddings'):
        RecognizeFrame.ref_embeddings = load_reference_embeddings(directory)

        if RecognizeFrame.ref_embeddings is None:
            await websocket.send(json.dumps({
                'Action': {'Response': 'VisionAuth_Error'}, 
                'Transfer': {
                    'Code': '25', 
                    'Error': 'No reference face encoding found'
                }
            }))
            VisionSight = False
            return
        

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame) 
    if len(face_locations) == 1:
        top, right, bottom, left = face_locations[0]
        face_region = frame[top:bottom, left:right]
        #cv2.imwrite("debug_face.jpg", face_region)
        is_real,spoof_confidence = spoof_detector.detect_spoof(face_region)
                  
        if is_real == False:
            #print(f"Is real: {is_real}, type: {type(is_real)}, Confidence: {spoof_confidence}")
            try:
                auth_message = {
                    'Action': {'Response': 'AuthenticationState'},
                    'Transfer': {
                        'Code': '25', 
                        'AuthType': 'Vision', 
                        'Authentication': False,
                        'Spoof_Confidence': spoof_confidence
                    }
                }
                await websocket.send(json.dumps(auth_message))
                #print(f"Sent authentication false message: {auth_message}")
                spoof_detector.reset_buffer()
                VisionSight = False
                return            
            except Exception as e:
                print(f"Error sending authentication false message: {e}")
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if face_encodings:
            current_encoding = face_encodings[0]
            frame_buffer.append(current_encoding)
            if len(frame_buffer) > FRAME_BUFFER_SIZE:
                frame_buffer.pop(0)
            
            if len(frame_buffer) == FRAME_BUFFER_SIZE:
                frame_confidences = []
                for encoding in frame_buffer:
                    encoding_confidences = []
                    for ref_encoding in RecognizeFrame.ref_embeddings:
                        distance = face_recognition.face_distance([ref_encoding], encoding)[0]
                        confidence = 1 - distance
                        encoding_confidences.append(confidence)
                    
                    frame_confidences.append(np.mean(encoding_confidences))

                mean_confidence = float(np.mean(frame_confidences))
                if mean_confidence > CONFIDENCE_THRESHOLD:
                    save_frame_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), directory, 'AuthImage')
                    os.makedirs(save_frame_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    frame_path = os.path.join(save_frame_dir, f'auth_frame_{timestamp}.jpg')
                    top, right, bottom, left = face_locations[0]
                    '''face_image = frame[top:bottom, left:right]
                    cv2.imwrite(frame_path, face_image)
                    print(f"Saved authenticated face frame to: {frame_path}")'''''

                    save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), directory, 'recognize_encodings')
                    #print(save_dir)
                    os.makedirs(save_dir, exist_ok=True)
                    encoding_files = glob.glob(os.path.join(save_dir, 'encoding_*.npy'))
                    encoding_files.sort(key=os.path.getctime, reverse=True)
                    existing_encodings = len(glob.glob(os.path.join(save_dir, 'encoding_*.npy')))

                    if existing_encodings >= 4:
                        best_confidence = 0
                        closest_encoding = None
                        closest_file = None

                        
                        for enc_file in encoding_files[:4]:
                            ref_encoding = np.load(enc_file)
                            distance = face_recognition.face_distance([ref_encoding], current_encoding)[0]
                            confidence = 1 - distance
                            if confidence > best_confidence:
                                best_confidence = confidence
                                closest_encoding = ref_encoding
                                closest_file = enc_file
                        
                        if best_confidence > (CONFIDENCE_THRESHOLD * 1.1):
                            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                            new_file = os.path.join(os.path.dirname(closest_file), f'encoding_{timestamp}.npy')                            
                            weighted_encoding = (0.8 * closest_encoding) + (0.2 * current_encoding)
                            os.remove(closest_file)
                            np.save(new_file, weighted_encoding)
                            '''print(f"Updated encoding {os.path.basename(closest_file)} -> {os.path.basename(new_file)}")
                            print(f"Confidence: {best_confidence:.3f}")'''

                    else:
                        primary_distance = face_recognition.face_distance([RecognizeFrame.ref_embeddings[0]], current_encoding)[0]
                        primary_confidence = 1 - primary_distance
                        
                        if primary_confidence > (CONFIDENCE_THRESHOLD * 1.05):
                            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                            encoding_path = os.path.join(save_dir, f'encoding_{timestamp}.npy')
                            np.save(encoding_path, current_encoding)
                            '''print(f"Adding new encoding with confidence {primary_confidence:.3f}")
                            print(f"Created new file: encoding_{timestamp}.npy")'''

                    await websocket.send(json.dumps({
                        'Action': {'Response': 'AuthenticationState'}, 
                        'Transfer': {
                            'Code': '25', 
                            'AuthType': 'Vision', 
                            'Authentication': True,
                            'Confidence': mean_confidence
                        }
                    }))
                    await websocket.send(json.dumps({
                        'Action': {'Response': 'AuthenticationState'}, 
                        'Transfer': {
                            'Code': '25', 
                            'AuthType': 'Vision', 
                            'Authentication': True,
                            'Confidence': mean_confidence
                        }
                    }))
                    
                    if hasattr(RecognizeFrame, 'user_key') and RecognizeFrame.user_key:
                        broadcast_authentication(
                            RecognizeFrame.user_key,
                            lambda msg: print(f"[Vision] {msg}")
                        )
                    VisionSight = False
                    return
    '''image = frame
    c -= 1
    if c <= 0:
        await websocket.send(json.dumps({'Action': {'Response': 'AuthenticationState'}, 'Transfer': {'Code': '25', 'AuthType': 'Vision', 'Authentication': True}}))
        VisionSight = False
    else:
        # recognize the face'''
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')
    await websocket.send(json.dumps({
        'Action': {'Response': 'VisionAuth_Instruction'},
         'Transfer': {'Code': '25', 'Instruction': 'Vision ID Running!'}
    }))
    await websocket.send(json.dumps({
        'Action': {'Response': response},
        'Transfer': {'Code': '25', 'VisionFeedStream': img_base64}
    }))


async def VisionFeed(websocket, response, directory):
    global VisionSight, VisionDevice, c
    c = 100
    VisionSight = True
    cap = cv2.VideoCapture(VisionDevice['Index'])
    if cap is not None and cap.isOpened():
        while VisionSight:
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            raw_frame = frame.copy()
            await RecognizeFrame(raw_frame, directory, websocket, response)
    else:
        await websocket.send(json.dumps({'Action': {'Response': 'VisionDeviceError'}, 'Transfer': {'Code': '25', 'Reason' : 'Camera not found'}}))
    cap.release()
    cv2.destroyAllWindows()


async def VisionDeviceSetup(Vision, websocket, response):
    global VisionDevice
    VisionDevice = Vision
    cap = cv2.VideoCapture(Vision['Index'])
    FrameDimension['H'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    FrameDimension['W'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    _VisionDevice = {
        'FrameHeight': FrameDimension['H'],
        'FrameWidth': FrameDimension['W'],
        'Name': Vision['Name'],
        '_Index': Vision['Index'],
        'ID': Vision['VisionID']
    }

    await websocket.send(json.dumps({
        'Action': {'Response': response}, 
        'Transfer': {'Code': '25', 'VisionDevice': _VisionDevice}
    }))







