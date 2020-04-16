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


clearCommand = ["--folder", "/store_00020001/DCIM/100CANON",
                "--delete-all-files", "-R"]
triggerCommand = ["--trigger-capture"]
downloadCommand = ["--get-all-files"]


def createSaveFolder(save_location):
    try:
        os.makedirs(save_location)
    except:
        print("Failed to create new directory.")
    os.chdir(save_location)


def captureImages(delay=3):
    gp(triggerCommand)
    sleep(delay)
    gp(downloadCommand)
    gp(clearCommand)


def renameFiles(ID, shot_time):
    for filename in os.listdir("."):
        if len(filename) < 13:
            if filename.endswith(".JPG"):
                os.rename(filename, (shot_time + ID + ".JPG"))
                print("Renamed the JPG")
            elif filename.endswith(".CR2"):
                os.rename(filename, (shot_time + ID + ".CR2"))
                print("Renamed the CR2")


def main():
    parser = argparse.ArgumentParser(description='Control a time lapse.')
    parser.add_argument('-H', '--hours', type=float, default=12.0,
                        help='the duration of the timelapse in hours')
    parser.add_argument('-P', '--period', default=30.0, type=float,
                        help='Period in seconds between pictures')
    parser.add_argument('-d', '--directory', default="PiShots",
                        type=str, help='Name of the output directory')

    args = parser.parse_args()
    killGphoto2Process()
    gp(clearCommand)
    num_pictures = int(args.hours*3600 / args.period)

    shot_date = datetime.now().strftime("%Y-%m-%d")
    shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    folder_name = args.directory + shot_date
    save_location = "~/gphoto/images/" + folder_name
    createSaveFolder(save_location)
    for i in range(num_pictures):
        captureImages(args.period)
        renameFiles(args.directory, shot_time)


if __name__ == '__main__':
    main()
