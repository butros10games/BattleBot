import tkinter as tk
from src.client.video import VideoWindow


def main():
    # create a window
    window = tk.Tk()
    # set the window title
    window.title("Battlebot GUI")
    # load the videostream from raspberry pi (this is defined in the video.py file as an separate window)
    video = VideoWindow()
    # set the window size
    window.geometry("1200x800")
    # run the window
    window.mainloop()


if __name__ == "__main__":
    main()
