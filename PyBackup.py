import subprocess as subp  # Let's python open Pycharm and detect when it closes
import os  # Allows file manipulation on the pc
from pydrive.auth import GoogleAuth  # Authorizes google drive bot
from pydrive.drive import GoogleDrive  # Manipulates google drive
import unicodedata  # Converts unicode
import Tkinter as Tk  # GUI thingy

root, pycharmLoc, files = os.walk('C:\Program Files\JetBrains').next()
del root, files


def get_disk_sizes():  # Gets the file sizes of scripts in C:\Users\Colby\PycharmProjects
    disk_sizes = {}
    for folder in os.listdir('C:\Users\Colby\PycharmProjects'):
        folder_dir_temp = 'C:\Users\Colby\PycharmProjects\\' + folder
        try:
            for filename in os.listdir(folder_dir_temp):
                if '.py' not in filename:
                    pass
                elif '.pyc' in filename:
                    pass
                else:
                    # disk_sizes[file] = [file size, directory]
                    disk_sizes[filename] = [os.path.getsize(folder_dir_temp + '\\' + filename), folder_dir_temp + '\\' + filename]
        except WindowsError:  # Occurs when the selected item is not a folder
            if '.py' not in folder:
                pass
            elif '.pyc' in folder:
                pass
            else:
                disk_sizes[folder] = [os.path.getsize(folder_dir_temp), folder_dir_temp]
    return disk_sizes


def get_drive_files(update_list, update_list_check):  # Gets the files that are on Google Drive
    update_list = [update_list[q] for q in range(len(update_list)) if update_list_check[q].get() == 1]
    root.destroy()  # Stop file selection GUI
    for name in update_list:
        temp = drive.CreateFile({'id': gDriveFiles[name][2]})
        temp.GetContentFile(name)
        if name in disk_sizes:
            if 'pybackup' in name.lower():  # Makes sure not to delete PyBackup
                pass
            else:
                os.remove(disk_sizes[name][1])
            # Places the file in a known directory (i.e. it already exists on file)
            os.rename('C:\Users\Colby\PycharmProjects\PyBackup\\' + name, disk_sizes[name][1])
        else:
            # Places in the root Projects directory
            os.rename('C:\Users\Colby\PycharmProjects\PyBackup\\' + name, 'C:\Users\Colby\PycharmProjects\\' + name)

    # Run Pycharm
    global pycharm
    pycharm = subp.Popen(['C:\Program Files\JetBrains\\' + pycharmLoc[0] + '\\bin\pycharm64.exe'])


# Automatically connect to google drive using stored credentials
gauth = GoogleAuth()

gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()

gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)


# Gets the file list from google drive and the sizes

# Get a list of the current files on google drive and their last modified dates
file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format('0B14P7QJeVacJWVg5UTIyV3dRU2c')}).GetList()
gDriveFiles = {}
for filename in file_list:
    # Converts the datetime format from pydrive into time from epoch to be easier compared
    # gDriveFiles[file] = [file size, file name, file id]
    gDriveFiles[filename['title']] = [int(unicodedata.normalize('NFKD', filename['fileSize']).encode('ascii', 'ignore')), filename['title'], filename['id'],]

# Trims to only python files
gDrive_scripts = {}
for key in gDriveFiles:
    if '.py' not in gDriveFiles[key][1]:
        pass
    elif '.pyc' in gDriveFiles[key][1]:
        pass
    else:
        # Converts from unicode since pydrive reads data in unicode
        gDrive_scripts[unicodedata.normalize('NFKD', gDriveFiles[key][1]).encode('ascii', 'ignore')] = []

disk_sizes = get_disk_sizes()

updates = []
for key in gDrive_scripts:
    # If the file is not on disk, download it
    if key not in disk_sizes:
        # updates.append(gDriveFiles[key][2])
        updates.append(key)

    # If the file is in google drive and has been updated more recently than the version on disk, update it
    elif disk_sizes[key][0] != gDriveFiles[key][0]:
        # updates.append(gDriveFiles[key][2])
        updates.append(key)


# Creates a tkinter window to select which files to update
if updates:
    root = Tk.Tk()

    updateCheck = list(range(len(updates)))
    updateLabel = Tk.Label(root, text='The following files have updates:', width=30).pack()

    checkboxFrame = Tk.Frame(root)
    checkboxFrame.pack()

    for i in range(len(updates)):
        updateCheck[i] = Tk.IntVar()
        updateCheckButton = Tk.Checkbutton(checkboxFrame, text=updates[i], variable=updateCheck[i])
        updateCheckButton.select()
        updateCheckButton.grid(row=i, sticky='w')

    continueButton = Tk.Button(root, text='Update Selected Files', command=lambda: get_drive_files(updates, updateCheck))
    continueButton.pack()

    root.mainloop()
else:
    pycharm = subp.Popen(['C:\Program Files\JetBrains\\' + pycharmLoc[0] + '\\bin\pycharm64.exe'])

# Waits until pycharm closes to finish up
subp.Popen.wait(pycharm)

# Get disk sizes again in case modifications were made since opening pycharm
del disk_sizes
disk_sizes = get_disk_sizes()

# Compares the two databases and acts accordingly
for key in disk_sizes:

    # If the file is not even in google drive, upload it
    if key not in gDrive_scripts:
        try:
            filename = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": '0B14P7QJeVacJWVg5UTIyV3dRU2c'}]})
            filename.SetContentFile(disk_sizes[key][1])
            filename['title'] = key
            filename.Upload()
        except:
            print 'The file you tried to upload is empty'

    # If the file is in google drive and has a different size, update it
    elif disk_sizes[key][0] != gDriveFiles[key][0]:
        filename = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": '0B14P7QJeVacJWVg5UTIyV3dRU2c'}], 'id': gDriveFiles[key][2]})
        filename.Trash()

        filename = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": '0B14P7QJeVacJWVg5UTIyV3dRU2c'}]})
        filename.SetContentFile(disk_sizes[key][1])
        filename['title'] = key
        filename.Upload()
