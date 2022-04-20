# Jump Squat King by ZiedYT

A program that serves as a "mod" for the game jumpking, that uses your cam inorder to play the game

## How To Use It
- Try to have no light sources behind you visible in the camera.
- Go to main/JumpSquatKing.exe and run it as administrator
-  ![N|topic](https://i.imgur.com/lPFAHrZ.png)
- Use the eyes coordinate for a better detection, make sure that you are close enough for your eyes to be visible. If enabled: 
    - the program only accepts the faces where the eyes are visible, to remove false detections.
    - if no face got detected (eg slighty outside the camera, or not in frontfal view) the program uses the coordinates of the detected eyes if found.
- Use the drop down menu to select your camera. You may have to wait if you choose a camera with high resolution.
- Use the flip checkBox to flip the input from the camera.
- Click the rotate button to rotate the camera.
- Set the pixel count you want to use. This represents the resolution of your camera. The higher the number, the better the tracking quality is and more computing power is needed. Use lower numbers if you encounter lag. 
- Tracking boxes can be shown using the checkbox. There is 4 fields:
    - one that presses the right arrow(if you are in the left size even if you are squatting)
    - one that presses the left arrow (if you are in the left size even if you are squatting)
    - one that presses the spacebar (if you are squatting, even if you are in the left or right side, you don't have to be in the middle)
    - one that releases all the keys. 
- You can change the size and position of the fields by changing the idle box position and size.
- When all your settings are ready, open jumpking, click start tracking inorder to start using the program.
- Also shout me out if you can, this makes me motivated to make open source stuff for everyone to use. 
- If you encounter any bugs feel feel to message me on twitter.
- If you are interested in the code, it's in the first folder.
