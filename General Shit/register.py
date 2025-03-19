import base64
#import dlib
import numpy as np
import time, cv2, json, random, os
# from PIL import Image
import face_recognition


FrameDimension = {'W': 1920, 'H': 1080}
# todo get screen dimensions from config 

VisionDevice = None


FaceAlignMask = ((FrameDimension['W'] // 2, FrameDimension['H'] // 2) , 120, 160)
'''
face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("./models/shape_predictor_81_face_landmarks.dat")
'''

def StructureLandmarkAligned(point):
    x,y = point
    center_x, center_y = FaceAlignMask[0]
    a = FaceAlignMask[1]
    b = FaceAlignMask[2]
    return ((x - center_x) ** 2) / (a ** 2) + ((y - center_y) ** 2) / (b ** 2) <= 1


def UpdateMask():
    global FaceAlignMask
    FaceAlignMask = ((FrameDimension['W'] // 2, FrameDimension['H'] // 2) , 120, 160)


async def ProcessVisionFrame(image, websocket, response):
    global progress_value
    face_landmarks = face_recognition.face_landmarks(image)
    
    ''' __image = image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)'''
    if FaceAlignMask:
        cv2.ellipse(image, FaceAlignMask[0], (FaceAlignMask[1], FaceAlignMask[2]), 0, 0, 360, (48, 10, 5), 2)

    '''for face in faces:
        landmarks = shape_predictor(gray, face)
        face_landmark_aligned_with_mask = all([StructureLandmarkAligned(landmarks.part(i).x, landmarks.part(i).y) for i in range(81)])

        if face_landmark_aligned_with_mask:
            points = []
            k = random.randint(0, 80)
            for i in range(81):
                x, y = landmarks.part(i).x, landmarks.part(i).y
                points.append((x,y))
                # cv2.circle(image, (x, y), 2, (0, 0, 255), -1)
                cv2.circle(image, (x, y), 2, (255, 93, 93), -1, 1)'''
                
                # cv2.line(image, (x, y), (random.choice(points)[0], random.choice(points)[1]), (255, 93, 93), 1)

                # cv2.line(image, (random.choice(points)[0], random.choice(points)[1]), (random.choice(points)[0], random.choice(points)[1]), (255, 93, 93), 1)
                # if len(points) >= 80:
                #     cv2.line(image, (random.choice(points[0]), random.choice(points[1])), (points[k][0], points[k][1]), (255, 93, 93), 1)
                # k = random.choice(points)
                # cv2.line(image, (x, y), (k[0], k[1]), (255, 93, 93), 1)
                
                # if len(points) >= 80:
                #     cv2.line(image, (x, y), (points[k][0], points[k][1]), (255, 93, 93), 1)
                # cv2.circle(image, (x, y), 3, (48, 10, 5), -1)
                # image_tk = convert_cv_to_tk(image)

    for landmark in face_landmarks:
        for facial_feature in landmark.values():
            for point in facial_feature:
                cv2.circle(image, point, 2, (255, 93, 93), -1, 1)

    _, img_encoded = cv2.imencode('.jpg', image)
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')
    await websocket.send(json.dumps({'Action': {'Response': response}, 'Transfer': {'Code': '25', 'VisionFeedStream': img_base64}}))

VisionSight = False

async def VisionFeed(websocket, response, directory):
    global VisionSight, progress_value, registered_faces, VisionDevice
    progress_value = 0
    VisionSight = True
    Frames = []
    # cap = cv2.VideoCapture(0)
    cap = cv2.VideoCapture(VisionDevice['Index'])
    if cap is not None and cap.isOpened():
        frame_cnt = 0
        while VisionSight:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            await ProcessVisionFrame(display_frame, websocket, response)

            frame_cnt += 1
            #raw_frame = frame.copy()
            if frame_cnt % 3 == 0:
                await RegisterVisionID(frame, display_frame, websocket, directory)
            '''Frames.append(frame)
            if len(Frames) > 7:
                Frames = Frames[-7:]
            await ProcessVisionFrame(frame, websocket, response)
            match_found = any(list(np.array_equal(frame, prev_frame) for prev_frame in Frames[:-1]))
            # print(list(np.array_equal(frame, prev_frame) for prev_frame in Frames[:-1]))
            # print(any(list(np.array_equal(frame, prev_frame) for prev_frame in Frames[:-1])))
            # print(all(list(np.array_equal(frame, prev_frame) for prev_frame in Frames[:-1])))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)
            if match_found and len(faces) > 0:
                await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'Move Your Face for complete structure modeling'}}))
            else:
                await RegisterVisionID(raw_frame, frame, websocket, directory)'''
    else:
        await websocket.send(json.dumps({'Action': {'Response': 'VisionDeviceError'}, 'Transfer': {'Code': '25', 'Reason' : 'Camera not found'}}))
    cap.release()
    cv2.destroyAllWindows()


Structure_ReferenceDataCollection_MAX_Limit = 10
VisionID_StructureCriteriaFulfill = []


async def RegisterVisionID(raw_frame, display_frame, websocket, Directory):
    global VisionSight, VisionID_StructureCriteriaFulfill
    '''gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)'''
    rgb_frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
    face_location = face_recognition.face_locations(rgb_frame)
    face_landmarks = face_recognition.face_landmarks(rgb_frame)
    if len(face_location) == 1:
        '''face = faces[0]
        landmarks = shape_predictor(gray, face)'''
        landmarks = face_landmarks[0]
        top, right, bottom, left = face_location[0]

        all_points = []
        for facial_feature in landmarks.values():  
                all_points.extend(facial_feature)

        face_landmark_aligned_with_mask = all([StructureLandmarkAligned(point) for point in all_points])
        if face_landmark_aligned_with_mask:
            margin = {'Y': 40, 'X': 5}
            VisionID_StructureFrame = raw_frame[
                max(0, top - margin['Y']):min(raw_frame.shape[0], bottom + margin['Y']),
                max(0, left - margin['X']):min(raw_frame.shape[1], right + margin['X'])
            ]

            VisionID_StructureCriteriaFulfill.append((VisionID_StructureFrame, landmarks))
            progress_value = int((len(VisionID_StructureCriteriaFulfill) /Structure_ReferenceDataCollection_MAX_Limit) * 100)

            await websocket.send(json.dumps({'Action': {'Response': 'VisionIDRegisterProgress'}, 'Transfer': {'Code': '25', 'Percentage': progress_value}}))
            if progress_value >= 100:
                VisionSight = False
                SaveStructureFrame(Directory)
                VisionID_StructureCriteriaFulfill.clear()
                await websocket.send(json.dumps({'Action': {'Response': 'VisionIDRegisterComplete'}, 'Transfer': {'Code': '25', 'Registration': True}}))
            if progress_value < 50:
                await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'Move your face slowly to left for complete structure modeling'}}))
            else:
                await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'Move your face slowly to right for complete structure modeling'}}))
        else:
            await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'Face not Aligned with the mark'}}))
    elif len(face_location) > 1:
        await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'Multiple Faces Detected!'}}))
    elif len(face_location) == 0:
        await websocket.send(json.dumps({'Action': {'Response': 'VisionRegisterInstruction'}, 'Transfer': {'Code': '25', 'Instruction': 'No  Face Detected!'}}))
        

def SaveStructureFrame(Directory):
    global VisionID_StructureCriteriaFulfill
    #SessionTimeStamp = time.strftime("%Y%m%d-%H%M%S")

    os.makedirs(Directory, exist_ok=True)
    parent_dir = os.path.dirname(Directory)
    os.makedirs(parent_dir, exist_ok=True)

    all_encodings = []
    for i, (face_image, _) in  enumerate(VisionID_StructureCriteriaFulfill):
        filename = os.path.join(parent_dir, f"FacialStructure_{i}.png")
        # filename = f"user/UserFacialFeatureReg_{SessionTimeStamp}/UserStructure_{i}.png"   
        
        if face_image is not None and face_image.size > 0:
            try:
                # Save original BGR image
                #cv2.imwrite(filename, face_image)
                
                # Convert to RGB for face_recognition
                rgb_frame = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(rgb_frame)
                
                if encodings:
                    all_encodings.append(encodings[0])
            except cv2.error as e:
                print(f"Error processing image {i}: {str(e)}")
                continue

        if all_encodings:
            mean_encoding = np.mean(all_encodings, axis=0)
            np.save(os.path.join(Directory, "face_encoding.npy"), mean_encoding)
        
    VisionID_StructureCriteriaFulfill.clear()



async def VisionDeviceSetup(Vision, websocket, response):
    global VisionDevice
    VisionDevice = Vision
    cap = cv2.VideoCapture(Vision['Index'])
    _VisionDevice = {'FrameHeight': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), 'FrameWidth': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 'Name': Vision['Name'], '_Index': Vision['Index'], 'ID': Vision['VisionID']}

    FrameDimension['W'] = _VisionDevice['FrameWidth']
    FrameDimension['H'] = _VisionDevice['FrameHeight']
    UpdateMask()

    await websocket.send(json.dumps({'Action': {'Response': response}, 'Transfer': {'Code': '25', 'VisionDevice': _VisionDevice}}))


