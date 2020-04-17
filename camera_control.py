from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import signal
import re
import os
import subprocess
import argparse
import pdb
# Kill the gphoto process that starts
# whenever we turn on the camera or
# reboot the raspberry pi

def killGphoto2Process():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    # Search for the process we want to kill
    for line in out.splitlines():
        if (b'gvfs-gphoto2' in line
            or b'gphoto2' in line) :
            # Kill that process!
            pid = int(line.split(None,1)[0])
            os.kill(pid, signal.SIGKILL)

try:
    camera_base_store = re.compile(
        "/store[^'\n]*DCIM"
    ).findall(str(a.stdout))[0]
except Exception as e:
    camera_base_store = '/store_00010001/DCIM/'

camera_subfolder = "101TLAPS"

def clearFolder(folder): 
    return ["--folder", folder, "--delete-all-files", "-R"]

triggerCommand = ["--trigger-capture"]

def downloadCommand(folder): 
    return ["--folder", folder, "--get-all-files"]

def setCaptureTarget(is_disk=1):
    gp(['--set-config', f'capturetarget={is_disk}'])


def downloadImage(folder, image): 
    gp(["--folder", folder, "--get-file", image])

def createSaveFolder(save_location, max_fail = 10):
    test_save =  save_location
    fail_count = 0
    while fail_count < max_fail:
        try:
            os.makedirs(test_save)
            save_location = test_save
            break
        except:
            print(f"Failed to create new directory: {test_save}")
            fail_count += 1
            test_save = save_location + "_" + str(fail_count)
    
    os.chdir(save_location)
    print(f"Working in directory: {save_location}")
    return save_location


def triggerImages(delay=3):
    gp(triggerCommand)
    sleep(delay)

def captureImageAndDown():
    out = gp(['--capture-image-and-download'])
    try:
        img_name = re.compile(
            r"Saving file as ([^\\]*)").findall(str(out.stdout))[0]
        # print(img_name)
    except IndexError as e:
        print("Image not copied.")

def imageList(folder):
    out = gp(["--folder", folder, "--list-files"])
    return re.compile("[a-zA-Z0-9_]*.JPG").findall(str(out))

def imageDict(folder):
    image_map = {}
    for img in imageList(folder):
        image_map[img] = True
    return image_map

def renameFiles(ID, shot_time):
    exts = [".JPG", ".NEF"]
    differentiator = {}
    for ext in exts:
        differentiator[ext] = ""

    for filename in os.listdir("."):
        if len(filename) < 13:
            new_name = ID + '-' + shot_time
            for ext in exts:
                if filename.endswith(ext):
                    new_name += str(differentiator[ext]) + ext
                    os.rename(filename, new_name)
                    print(f"Renamed {filename} to {new_name}")
                    try:
                        differentiator[ext] += 1
                    except:
                        differentiator[ext] = 1


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Control a time lapse.')
    parser.add_argument('-H', '--hours', type=float, default=12.0,
                        help='the duration of the timelapse in hours')
    parser.add_argument('-P', '--period', default=30.0, type=float,
                        help='Period in seconds between pictures')
    parser.add_argument('-f', '--folder', default="PiShots",
                        type=str, help='Name of the output directory')
    parser.add_argument('--maxexposure', default=3.0,
                        type=float, help='Maximum mexposure in seconds')
    parser.add_argument('--nodownload', action='store_true',
                        help='Use to disable downloading of images' +
                        'automatically added when period < 4.5')

    args = parser.parse_args()
    
    if args.period < 4.5:
        args.nodownload = True
    
    if args.period < args.maxexposure:
        args.maxexposure = args.period * 0.5
        
    shot_date = datetime.now().strftime("%Y-%m-%d")
    folder_name = args.folder + '-' + shot_date
    run_name = folder_name.split('/')[-1]
    save_location = "./timelapses/" + folder_name
    camera_save_location = camera_base_store + camera_subfolder
    
    # Prepare camera access
    killGphoto2Process()
    setCaptureTarget(is_disk=1)
    save_location = createSaveFolder(save_location)
    
    images_to_keep_on_camera = imageDict(camera_save_location)
    
    # Start loop
    num_pictures = int(args.hours*3600 / args.period)
    print(f"Capturing {num_pictures} pictures")
    for i in range(num_pictures):
        print(f"Capturing picture {i+1} of {num_pictures}")
        start_time = datetime.now()

        if args.nodownload:
            triggerImages(delay=args.maxexposure)
        else:
            captureImageAndDown()
            shot_time = datetime.now().strftime("%H:%M:%S")
            renameFiles(run_name, shot_time)
        sleep(max(0.001,
        args.period - (datetime.now() - start_time).total_seconds()))

    if args.nodownload:
        images_to_keep_on_camera
        
        imageList(camera_save_location)
        new_images = [img for img in imageList(camera_save_location) 
            if not img in images_to_keep_on_camera]
        for i, img in enumerate(new_images):
            print(f"Downloading {img} ({i+1} / {num_pictures}) ...", end=" ")
            downloadImage(camera_save_location, img)
            print(f"Done!")

if __name__ == '__main__':
    main()
    
