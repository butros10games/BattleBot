# Importing all modules
import cv2
import numpy as np

# Specifying upper and lower ranges of color to detect in hsv format
lower = np.array([15, 180, 120])
upper = np.array([35, 255, 255])  # (These ranges will detect Yellow)

# Capturing webcam footage
webcam_video = cv2.VideoCapture(0)

while True:
    success, full_video = webcam_video.read()  # Reading webcam footage

    # Crop the input video to its left half
    # video = full_video[:, :full_video.shape[1] // 2, :]
    video = full_video

    img = cv2.cvtColor(video, cv2.COLOR_BGR2HSV)  # Converting BGR image to HSV format

    mask = cv2.inRange(img, lower, upper)  # Masking the image to find our color

    mask_contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Finding contours in the mask image

    # Finding position of all contours
    if len(mask_contours) != 0:
        for mask_contour in mask_contours:
            if cv2.contourArea(mask_contour) > 500:
                x, y, w, h = cv2.boundingRect(mask_contour)

                # Calculate the position relative to the center of the cropped video
                position_ratio = (x + w / 2) / video.shape[1] # assuming width is the horizontal dimension

                # Adjusting the red channel based on position
                roi_width = int(video.shape[1] * 0.05)  # 5% of the full video width

                if position_ratio < 0.5:
                    side = slice(None, roi_width)
                else:
                    side = slice(-roi_width, None)

                red_channel = video[ :, side, 2]

                position_ratio = position_ratio - 0.5  # Shifting the position ratio to be centered at 0
                if position_ratio < 0:
                    position_ratio = -position_ratio # Making position ratio positive

                video[:, side, 2] = np.clip(video[:, side, 2] + int(255 * position_ratio), 0, 255) #Displaying a red transparancy effect based on distance from center

                print(position_ratio)
                cv2.rectangle(video, (x, y), (x + w, y + h), (0, 0, 255), 3)  # drawing rectangle with adjusted color

    cv2.imshow("mask image", mask)  # Displaying mask image
    cv2.imshow("window", video)  # Displaying cropped webcam image with adjusted redness

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
webcam_video.release()
cv2.destroyAllWindows() 