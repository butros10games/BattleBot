import os
import sys

import cv2 as cv

print("Current working directory:", os.getcwd())

# Load the image using the relative path
img = cv.imread("Python/tests/starry_night.jpg")

# Check if the image was loaded successfully
if img is None:
    sys.exit("Could not read the image.")

# Display the image
cv.imshow("Display window", img)
k = cv.waitKey(0)

# Save the image if the key 's' is pressed
if k == ord("s"):
    cv.imwrite("starry_night.png", img)

# Close the window if any key is pressed
if k != -1:
    cv.destroyAllWindows()
