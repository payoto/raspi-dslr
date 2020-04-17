from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import signal
import os
import subprocess
import argparse
# Kill the gphoto process that starts
# whenever we turn on the camera or
# reboot the raspberry pi

def killGphoto2Process():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    # Search for the process we want to kill
    for line in out.splitlines():
        if b'gvfsd-gphoto2' in line:
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


def createSaveFolder(save_location):
    try:
        os.makedirs(save_location)
    except:
        print("Failed to create new directory.")
    os.chdir(save_location)


def captureImages(folder=camera_base_store + camera_subfolder, delay=3):
    gp(triggerCommand)
    sleep(delay)
    gp(downloadCommand(folder))
    gp(clearFolder(folder))


def renameFiles(ID, shot_time):
    for filename in os.listdir("."):
        if len(filename) < 13:
            if filename.endswith(".JPG"):
                os.rename(filename, (shot_time + ID + ".JPG"))
                print(f"Renamed the {filename}")
            elif filename.endswith(".NEF"):
                os.rename(filename, (shot_time + ID + ".NEF"))
                print(f"Renamed the {filename}")


def main():
    parser = argparse.ArgumentParser(description='Control a time lapse.')
    parser.add_argument('-H', '--hours', type=float, default=12.0,
                        help='the duration of the timelapse in hours')
    parser.add_argument('-P', '--period', default=30.0, type=float,
                        help='Period in seconds between pictures')
    parser.add_argument('-d', '--directory', default="PiShots",
                        type=str, help='Name of the output directory')
    parser.add_argument('--maxexposure', default=2.0,
                        type=float, help='Maximum mexposure in seconds')

    args = parser.parse_args()
    
    if args.period < args.maxexposure:
        ArgumentError(
        f"--maxexposure ({args.maxexposure}) cannot be above the period" 
        + f" ({args.period})")
    
    killGphoto2Process()
    num_pictures = int(args.hours*3600 / args.period)

    shot_date = datetime.now().strftime("%Y-%m-%d")
    shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    folder_name = args.directory + '-' + shot_date
    save_location = "./timelapses/" + folder_name
    camera_save_location = camera_base_store + camera_subfolder
    
    createSaveFolder(save_location)
    gp(clearFolder(camera_save_location))
    for i in range(num_pictures):
        start_time = datetime.now()
        captureImages(folder=camera_save_location,delay=args.maxexposure)
        renameFiles(args.directory, shot_time)
        sleep(max(0.0,
        args.period - (datetime.now() - start_time).total_seconds()))


if __name__ == '__main__':
    main()
