# -*- coding: utf-8 -*-
"""Car Speed Estimator - Frame-by-Frame Control Version"""

# This version provides enhanced frame-by-frame control
# Import required libraries

import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import*

model=YOLO('yolov8n.pt')

vi=cv2.VideoCapture('highway_mini.mp4')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
              'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

tracker=Tracker()
count=0

import time
down = {}
up = {}
counter_down = []
counter_up = []

print("=== FRAME-BY-FRAME VIDEO CONTROL ===")
print("Controls:")
print("  SPACEBAR - Next frame")
print("  'p' - Play/Pause (auto-advance)")
print("  'r' - Reset to beginning")
print("  ESC - Exit")
print("=====================================")

auto_play = False
current_frame = 0
total_frames = int(vi.get(cv2.CAP_PROP_FRAME_COUNT))

while True:
  ret,frame=vi.read()
  if not ret:
    print("End of video reached. Press 'r' to restart or ESC to exit.")
    key = cv2.waitKey(0) & 0xFF
    if key == ord('r'):  # Reset video
        vi.set(cv2.CAP_PROP_POS_FRAMES, 0)
        current_frame = 0
        count = 0
        down.clear()
        up.clear()
        counter_down.clear()
        counter_up.clear()
        continue
    elif key == 27:  # ESC
        break
    else:
        continue
        
  count+=1
  current_frame = int(vi.get(cv2.CAP_PROP_POS_FRAMES))
  frame=cv2.resize(frame,(1020,500))

  results=model.predict(frame)
  print(f"Frame {current_frame}/{total_frames}: {results[0].boxes.data.shape}") # prints the shape of the detected bounding boxes
  a=results[0].boxes.data
  a=a.detach().cpu().numpy()
  px=pd.DataFrame(a).astype("float")
  #print(px)
  list = []

  for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
            list.append([x1, y1, x2, y2])
  bbox_id=tracker.update(list)
  for bbox in bbox_id:
    x3,y3,x4,y4,id=bbox
    cx=int(x3+x4)//2
    cy=int(y3+y4)//2
    red_line_y=198
    blue_line_y=268
    offset = 7

    if red_line_y<(cy+offset) and red_line_y > (cy-offset):
           down[id]=time.time()   # current time when vehichle touch the first line
    if id in down:

           if blue_line_y<(cy+offset) and blue_line_y > (cy-offset):
             elapsed_time=time.time() - down[id]  # current time when vehicle touch the second line. Also we a re minusing the previous time ( current time of line 1)
             if counter_down.count(id)==0:
                counter_down.append(id)
                distance = 100 # meters
                a_speed_ms = distance / elapsed_time
                a_speed_kh = a_speed_ms * 3.6  # this will give kilometers per hour for each vehicle. This is the condition for going downside
                cv2.circle(frame,(cx,cy),4,(0,0,255),-1)
                cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)  # Draw bounding box
                cv2.putText(frame,str(id),(x3,y3),cv2.FONT_HERSHEY_COMPLEX,0.6,(255,255,255),1)
                cv2.putText(frame,str(int(a_speed_kh))+'Km/h',(x4,y4 ),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,255,255),2)


        #####going UP blue line#####
    if blue_line_y<(cy+offset) and blue_line_y > (cy-offset):
           up[id]=time.time()
    if id in up:

           if red_line_y<(cy+offset) and red_line_y > (cy-offset):
             elapsed1_time=time.time() - up[id]
             # formula of speed= distance/time
             if counter_up.count(id)==0:
                counter_up.append(id)
                distance1 = 100 # meters  (Distance between the 2 lines is 10 meters )
                a_speed_ms1 = distance1 / elapsed1_time
                a_speed_kh1 = a_speed_ms1 * 3.6
                cv2.circle(frame,(cx,cy),4,(0,0,255),-1)
                cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)  # Draw bounding box
                cv2.putText(frame,str(id),(x3,y3),cv2.FONT_HERSHEY_COMPLEX,0.6,(255,255,255),1)
                cv2.putText(frame,str(int(a_speed_kh1))+'Km/h',(x4,y4),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,255,255),2)


    text_color = (255,255,255)  # white color for text
    red_color = (0, 0, 255)  # (B, G, R)
    blue_color = (255, 0, 0)  # (B, G, R)
    green_color = (0, 255, 0)  # (B, G, R)

    cv2.line(frame,(172,198),(774,198),red_color,3)  #  starting cordinates and end of line cordinates
    cv2.putText(frame,('red line'),(172,198),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

    cv2.line(frame,(8,268),(927,268),blue_color,3)  # seconde line
    cv2.putText(frame,('blue line'),(8,268),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

    cv2.putText(frame, ('Going Down - ' + str(len(counter_down))), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    cv2.putText(frame, ('Going Up - ' + str(len(counter_up))), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Add frame counter
    cv2.putText(frame, f'Frame: {current_frame}/{total_frames}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Add play mode indicator
    mode_text = "AUTO" if auto_play else "MANUAL"
    cv2.putText(frame, f'Mode: {mode_text}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

  cv2.imshow('Car Speed Estimation - Frame Control', frame)
  
  # Enhanced frame control
  wait_time = 100 if auto_play else 0  # Auto-play with 100ms delay, or wait for key
  key = cv2.waitKey(wait_time) & 0xFF
  
  if key == 27:  # ESC key to exit
     break
  elif key == ord(' '):  # SPACEBAR - next frame (always works)
     continue
  elif key == ord('p'):  # 'p' - toggle play/pause
     auto_play = not auto_play
     print(f"Mode changed to: {'AUTO-PLAY' if auto_play else 'MANUAL (frame-by-frame)'}")
  elif key == ord('r'):  # 'r' - restart video
     vi.set(cv2.CAP_PROP_POS_FRAMES, 0)
     current_frame = 0
     count = 0
     down.clear()
     up.clear()
     counter_down.clear()
     counter_up.clear()
     print("Video restarted")

vi.release()
cv2.destroyAllWindows()
