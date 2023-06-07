"Module that runs the user interface for the plant measurement application."

import base64
import io
import os

import PySimpleGUI as sg
from PIL import Image

import img_processing_final
from logo import LOGO_BIN

import set_known_length as skl
import app_logger

# Constants
CSV = "csv"
EXCEL = "excel"
FILES_LIST = "-FILE-LIST-"
FOLDER = "-FOLDER-"
IMAGE_WIDTH = 300
LOGO_FILE = "logo.png"
OUTPUT = "output"
PREVIEWS = "previews"
PREVIEW_INFO = "preview_info"
SELECT_ALL = "Select All"
UNSELECT_ALL = "Unselect All"
TOGGLE_PREVIEWS = "Toggle Previews"


class Application:
    """An application class that handles the PySimpleGUI instance that manages the application."""

    def __init__(self):
        self.preview_shown = True
        self.shown_files = []
        self.all_files = []
        self.values = {}
        self.window = self._setup()

    def _setup(self):
        # Column for displaying the list of files in current folder
        file_list_column = [
            [
                sg.Text("Image Folder"),
                sg.In(size=(None, 1), expand_x=True, enable_events=True, key=FOLDER),
                sg.FolderBrowse(),
            ],
            [
                sg.Listbox(
                    values=[], enable_events=True, key=FILES_LIST, select_mode="multiple", expand_x=True, expand_y=True
                )
            ],
            [sg.Button(SELECT_ALL), sg.Button(UNSELECT_ALL)],
        ]

        # Column to show the image previews of all currently selected images
        image_viewer_column = [
            [sg.Text("Image Previews:"), sg.Text("Shown", key=PREVIEW_INFO), sg.Button(TOGGLE_PREVIEWS)],
            [
                sg.Column(
                    [],
                    size=(IMAGE_WIDTH, None),
                    scrollable=True,
                    vertical_scroll_only=True,
                    key=PREVIEWS,
                    expand_x=True,
                    expand_y=True,
                    element_justification="center",
                )
            ],
        ]

        # Output button with checkboxes to select what type of output
        output_column = [
            [sg.Checkbox("Excel Output", default=False, enable_events=True, key=EXCEL)],
            [sg.Checkbox("CSV Output", default=False, enable_events=True, key=CSV)],
            [sg.OK(OUTPUT, disabled=True)],
        ]

        menu_def = ['&Option', ['&Set known length']], ['&Help',['&About']]
        # The full layout of the application
        layout = [
            [sg.Menu(menu_def, background_color='lightsteelblue',text_color='navy', disabled_text_color='yellow', font='Verdana', pad=(10,10))],
            [
                sg.vtop(sg.Column(file_list_column, expand_x=True, expand_y=True), expand_x=True, expand_y=True),
                sg.VSeperator(),
                sg.vtop(sg.Column(image_viewer_column, expand_x=True, expand_y=True), expand_y=True),
                sg.VSeperator(),
                sg.Column(
                    output_column, expand_x=True, expand_y=True
                ),  # we should remove both expand_x and expand_y or one of them, it looks better on maximizing
            ]
        ]

        # Create a new application window, using the app icon
        window = sg.Window(
            "Image Viewer",
            layout,
            size=(800, 350),
            icon=base64.b64encode(LOGO_BIN),
            resizable=True,
            finalize=True,
        )

        # To set minimum size for application
        window.TKroot.minsize(850, 400)

        # Return the configured application window
        return window

    def _output_selected(self):
        # Returns if at least one output has been selected.
        return self.values.get(CSV) or self.values.get(EXCEL)

    def _hide_images(self):
        # Hides all images
        for file_name in self.shown_files:
            self._hide_image(file_name)

        # Updates window
        self.window[PREVIEWS].Widget.update()
        self.window[PREVIEWS].contents_changed()
        self.window.refresh()

    def _hide_image(self, file_name):
        self.window[f"img_{file_name}"].update(visible=False)
        self.window[f"img_{file_name}"].hide_row()
        self.window[f"name_{file_name}"].update(visible=False)
        self.window[f"name_{file_name}"].hide_row()

    def _show_images(self, files, folder_name):
        # Hides all current images, then shows the wanted images
        self._hide_images()
        for file_name in files:
            self._show_image(file_name, folder_name)

        # Updates window
        self.window[PREVIEWS].Widget.update()
        self.window[PREVIEWS].contents_changed()
        self.window.refresh()

    def _show_image(self, file_name, folder_name):
        # If not previosuly shown, load the image in, create a thumbnail and add it to the preview pane
        if file_name not in self.shown_files:
            image = Image.open(os.path.join(folder_name, file_name))
            image.thumbnail((IMAGE_WIDTH, 2 * IMAGE_WIDTH))
            bio = io.BytesIO()
            image.save(bio, format="PNG")
            self.window.extend_layout(
                self.window[PREVIEWS],
                [[sg.Image(bio.getvalue(), key=f"img_{file_name}", pad=(0, 0))]],
            )
            self.window.extend_layout(self.window[PREVIEWS], [[sg.Text(file_name + "\n\n", key=f"name_{file_name}")]])
            self.shown_files.append(file_name)

            # Hide to update text centering in column
            self._hide_image(file_name)

        # Shows the images
        self.window[f"img_{file_name}"].update(visible=True)
        self.window[f"img_{file_name}"].unhide_row()
        self.window[f"name_{file_name}"].update(visible=True)
        self.window[f"name_{file_name}"].unhide_row()

    def _event_loop(self):
        """The event loop that handles the logic of the appliaction.
        Events are generated and handled as required.

        Returns:
            bool: True if continue, False if break
        """

        # Get next event and values, if None return as application is closing
        event, self.values = self.window.read()
        if not self.values:
            return False
        files = self.values.get(FILES_LIST)

        # Break application loop if application is closed
        if event in ("Exit", sg.WIN_CLOSED):
            return False

        # When a folder is selected, get all image file names
        if event == FOLDER:
            folder = self.values[FOLDER]
            try:
                file_list = os.listdir(folder)
            except FileNotFoundError:
                file_list = []

            self.all_files = [f for f in file_list if f.lower().endswith((".png", ".gif", ".jpeg", ".jpg", ".tiff"))]
            self.window[FILES_LIST].update(self.all_files)

        # A new image files was selected or unselected
        elif event == FILES_LIST:
            # Set output button status depending on if any images are selected
            if files and self._output_selected():
                self.window[OUTPUT].update(disabled=False)
            else:
                self.window[OUTPUT].update(disabled=True)

            # Show images if previews are currently enabled
            if self.preview_shown:
                self._show_images(files, self.values[FOLDER])

        # Toggle the visibility of preview images
        elif event == TOGGLE_PREVIEWS:
            self.preview_shown = not self.preview_shown
            if not self.preview_shown:
                self._hide_images()
                self.window[PREVIEW_INFO].update(value="Hidden")
            else:
                self._show_images(self.values[FILES_LIST], self.values[FOLDER])
                self.window[PREVIEW_INFO].update(value="Shown")

        elif event == SELECT_ALL:
            self.window[FILES_LIST].set_value(self.all_files)
            if self.preview_shown:
                self._show_images(self.all_files, self.values[FOLDER])

        elif event == UNSELECT_ALL:
            self.window[FILES_LIST].set_value([])
            if self.preview_shown:
                self._show_images([], self.values[FOLDER])

        # More conditions to ensure that output checkbox is only enabled when files and output type are selected
        elif event in (CSV, EXCEL):
            if len(files) > 0 and self._output_selected():
                self.window[OUTPUT].update(disabled=False)
            else:
                self.window[OUTPUT].update(disabled=True)

        # The output button has been pressed and at least one out was selected
        elif event == OUTPUT and self._output_selected():
            # Call _process_image for each selected image
            for index, file in enumerate(files):
                filepath = os.path.join(self.values[FOLDER], file)

                img_processing_final.processImage(filepath, self.values[EXCEL], self.values[CSV])
                sg.one_line_progress_meter("Progress", index, len(files))

            # Close application if something was output
            if files:
                return False
        elif event == 'Set known length':
            sklw = skl.ExtraWindows()
            sklw.get_popup_menu()
        
        elif event == 'About':
            self.window.disappear()
            sg.popup('About this program', 'It is used to measure the stem of a plant',
            'Product details: \nVersion: 1.0 \nResources: [github link]',  grab_anywhere=True, keep_on_top=True)
            self.window.reappear()

        return True
    
    def block_focus(self, window):
        for key in window.key_dict:    # Remove dash box of all Buttons
            element = window[key]
            if isinstance(element, sg.Button):
                element.block_focus()

    def run(self):
        """Runs the application. Closes the winodw once finished."""

        while self._event_loop():
            pass
        self.window.close()


# Create the application and run it
if __name__ == "__main__":
    app = Application()
    app.run()
