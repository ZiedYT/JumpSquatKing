import os
import shutil 
from threading import Thread
import mediapipe as mp
from pathlib import Path

def installer(path):
    os.system("pyinstaller "+path)

if(os.path.isdir("dist")):
    shutil.rmtree("dist")

installer("JumpSquatKing.spec")

shutil.copy("logo.png", "dist/JumpSquatKing/logo.png")
shutil.copy("dist/JumpSquatKing/JumpSquatKing.exe", "dist/JumpSquatKing/JumpSquatKing_console.exe")


mpPath = Path(mp.__file__).parent.absolute()
print(mpPath)
if(os.path.isdir("dist/JumpSquatKing/mediapipe")):
    shutil.rmtree("dist/JumpSquatKing/mediapipe")
shutil.copytree(mpPath,"dist/JumpSquatKing/mediapipe")

shutil.make_archive("dist/JumpSquatKing", 'zip', "dist/JumpSquatKing")