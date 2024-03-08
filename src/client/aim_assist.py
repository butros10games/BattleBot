# Importing all modules
import cv2
import numpy as np

class AimAssist:
    steering_angle = 180
    camera_angle = 66
    # Specifying upper and lower ranges of color to detect in hsv (Hue, Saturation, Value) format
    lower = np.array([15, 180, 120])
    upper = np.array([35, 255, 255])  # (These ranges will detect Yellow)

    # Capturing webcam footage
    webcam_video = cv2.VideoCapture(0)

    while True:
        # full_video = GetFrame()
        success, full_video = webcam_video.read()  # Reading webcam footage

        # Choose video format
        # video = full_video[:, :full_video.shape[1] // 2, :]  # Crop the input video to its left half (For 2 cameras stitched together)
        video = full_video # For full camera feed (if you have 2 cameras without merging the overlap it wont track correctly)

        img = cv2.cvtColor(video, cv2.COLOR_BGR2HSV)  # Converting BGR image to HSV format

        mask = cv2.inRange(img, lower, upper)  # Masking the image to find the set color

        mask_contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Finding contours in the mask image

        # Finding the biggest contour
        biggest_contour = max(mask_contours, key=cv2.contourArea, default=None)

        # Drawing the biggest contour
        if biggest_contour is not None and cv2.contourArea(biggest_contour) > 500:
            x, y, w, h = cv2.boundingRect(biggest_contour)

            # Calculate the position relative to the center of the cropped video
            position_ratio = (x + w / 2) / video.shape[1]  # assuming width is the horizontal dimension

            # Adjusting the red channel based on position
            roi_width = int(video.shape[1] * 0.05)  # 5% of the full video width

            if position_ratio < 0.5: # Check position ratio
                side = slice(None, roi_width) # Set side to the left
            else:
                side = slice(-roi_width, None) # Set side to the right

            red_channel = video[:, side, 2] # Set a red bar to whatever side needed

            position_ratio = position_ratio - 0.5  # Shifting the position ratio to be centered at 0
            if position_ratio < 0:
                position_ratio = -position_ratio  # Making position ratio positive

            video[:, side, 2] = np.clip(video[:, side, 2] + int(255 * position_ratio), 0, 255)  # Displaying a red transparency effect based on distance from center

            print(position_ratio)
            cv2.rectangle(video, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Drawing rectangle with adjusted color

        cv2.imshow("mask image", mask)  # Displaying mask image
        cv2.imshow("window", video)  # Displaying cropped webcam image with adjusted redness
        #send steering data
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam_video.release()
    cv2.destroyAllWindows()
