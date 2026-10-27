import cv2
import argparse
# You will need to install ultralytics to use YOLOv8: pip install ultralytics
try:
    from ultralytics import YOLO
except ImportError:
    print("Please install ultralytics: pip install ultralytics")
    YOLO = None

def run_ai_surveillance(video_source=0):
    if YOLO is None:
        return

    print("Loading YOLOv8 model for Person Detection...")
    model = YOLO('yolov8n.pt') # Load a pretrained YOLOv8 nano model

    print(f"Opening video source: {video_source}")
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or error reading frame.")
            break

        # Run YOLOv8 inference on the frame
        results = model(frame, classes=[0], conf=0.5) # Class 0 is 'person' in COCO dataset

        # Visualize the results on the frame
        annotated_frame = results[0].plot()
        
        # Count detected persons for alerts
        person_count = len(results[0].boxes)
        if person_count > 0:
            cv2.putText(annotated_frame, f"ALERT: {person_count} Person(s) Detected!", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # Here you could trigger a network alert/syslog to the ERP/Admin VLAN

        # Display the frame
        cv2.imshow("VLAN AI Surveillance System", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Surveillance for VLAN Network")
    parser.add_argument('--source', default=0, help='Video source (0 for webcam, or path to video file)')
    args = parser.parse_args()
    
    source = args.source
    if str(source).isdigit():
        source = int(source)
        
    run_ai_surveillance(source)
