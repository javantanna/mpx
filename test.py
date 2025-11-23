# from scenedetect import detect, ContentDetector

# def get_scene_cuts(video_path):
#     # Returns list of [Start Time, End Time] for every scene
#     scene_list = detect(video_path, ContentDetector())
#     return [(s[0].get_seconds(), s[1].get_seconds()) for s in scene_list]



# if __name__ == "__main__":
#     print(get_scene_cuts("/Users/javantanna/Code/mp5/Jug Jug Jiyo Beta _ Ek Nanha Sa Beta _ Latest Birthday Song For Son _ Lofi _ Vicky D Parekh.mp4"))


import cv2

print(cv2.CV_64F)
