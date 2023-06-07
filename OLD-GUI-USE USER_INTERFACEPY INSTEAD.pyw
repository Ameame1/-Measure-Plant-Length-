# img_viewer.py

import base64
import csv
import io
import os
import os.path

import PySimpleGUI as sg
import xlsxwriter
from PIL import Image
import img_processing_final

# function to process file -- UPDATE WITH ACTUAL PROCESSING FUNCTION
def processFile(filename):
    print("Processing " + filename)


# First the window layout in 2 columns

file_list_column = [
    [
        sg.Text("Image Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[],
            enable_events=True,
            size=(45, 30),
            key="-FILE LIST-",
            select_mode="multiple",
        )
    ],
]

# For now will only show the name of the file that was chosen
#
image_viewer_column = [
    [
        sg.Text("Image Previews:"),
        sg.Text("Shown", key="preview_info"),
        sg.Button("Toggle Previews"),
    ],
    [
        sg.Column(
            [],
            size=(300, 1000),
            scrollable=True,
            vertical_scroll_only=True,
            key="previews",
        )
    ],
]

# Checkboxes to select what type of output
outputColumn = [
    [sg.Checkbox("Excel Output", default=False, enable_events=True, key="EXCEL")],
    [sg.Checkbox("CSV Output", default=False, enable_events=True, key="CSV")],
    [sg.OK("output", disabled=True)],
]

# ----- Full layout -----
layout = [
    [
        sg.vtop(sg.Column(file_list_column), expand_x=True, expand_y=True),
        sg.VSeperator(),
        sg.vtop(
            sg.Column(image_viewer_column, pad=(0, 0)), expand_x=True, expand_y=True
        ),
        sg.VSeperator(),
        sg.Column(outputColumn, expand_x=True, expand_y=True),
    ]
]

with open("logo.png", "rb") as img_file:
    window = sg.Window(
        "Image Viewer",
        layout,
        size=(800, 350),
        icon=base64.b64encode(img_file.read()),
        resizable=True,
        finalize=True,
    )

preview_shown = True
fnames = []
shown_files = []
files = []
filename = ""

# To enable event for window resizing
window.bind("<Configure>", "Configure")

## Found an easier way to do minimum size
window.TKroot.minsize(850, 400)


def hide_images():
    for file in shown_files:
        window[f"img_{file}"].update(visible=False)
        window[f"img_{file}"].hide_row()
        window[f"name_{file}"].update(visible=False)
        window[f"name_{file}"].hide_row()

    window["previews"].Widget.update()
    window["previews"].contents_changed()
    window.refresh()


def show_images():
    hide_images()
    for file in files:
        if file in shown_files:
            window[f"img_{file}"].update(visible=True)
            window[f"img_{file}"].unhide_row()
            window[f"name_{file}"].update(visible=True)
            window[f"name_{file}"].unhide_row()
        else:
            image = Image.open(os.path.join(values["-FOLDER-"], file))
            image.thumbnail((300, 400))
            bio = io.BytesIO()
            image.save(bio, format="PNG")
            window.extend_layout(
                window["previews"],
                [[sg.Image(bio.getvalue(), key=f"img_{file}", pad=(0, 0))]],
            )
            window.extend_layout(
                window["previews"], [[sg.Text(file, key=f"name_{file}", pad=(0, 0))]]
            )
            shown_files.append(file)

    window["previews"].Widget.update()
    window["previews"].contents_changed()
    window.refresh()


while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    ## EVENT FOR WINDOW RESIZING -- MIGHT NEED IN THE FUTURE-- ENFORCE A MINIMUM SIZE??
    if event == "Configure":
        continue
        # my_windows_size  = window.Size
        # print(my_windows_size)

    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".png", ".gif", ".jpeg", ".jpg", ".tiff"))
        ]
        window["-FILE LIST-"].update(fnames)

    elif event == "-FILE LIST-":  # A file was chosen from the listbox
        try:
            files = values["-FILE LIST-"]

            ## SET output button disabled based on whether there are files selected
            if len(files) > 0 and (values["CSV"] or values["EXCEL"]):
                window["output"].update(disabled=False)
            else:
                window["output"].update(disabled=True)

            if preview_shown:
                show_images()

        except:
            pass

    if event == "Toggle Previews":
        preview_shown = not preview_shown
        if not preview_shown:
            hide_images()
            window["preview_info"].update(value="Hidden")
        else:
            show_images()
            window["preview_info"].update(value="Shown")

    ## More conditions to ensure that output checkbox is only enabled when files AND output type are selected
    if event == "CSV" or event == "EXCEL":
        if len(files) > 0 and (values["CSV"] or values["EXCEL"]):
            window["output"].update(disabled=False)
        else:
            window["output"].update(disabled=True)

    if event == "output":

        outputsomething = False

        i = 0
        for file in files:

            filepath = os.path.join(values["-FOLDER-"], file)
            filename = os.path.splitext(filepath)[0]
            # Filename has some weird problem - need to change \ to /
            filepath = filepath.replace("\\","/")

            # Final check that at least one type of output has been selected
            if(values["EXCEL"] or values["CSV"]):
                img_processing_final.processImage(filepath,values["EXCEL"],values["CSV"])

                outputsomething = True
            i += 1
            sg.one_line_progress_meter('Progress', i, len(files))



        if outputsomething:
            break
            


window.close()
