import time
from datetime import datetime
import PySimpleGUI as sg
from logo import LOGO_BIN
import base64, io
import os, shutil
import filetype
import numpy as np
import pickle, skimage.io, codecs
from PIL import ImageGrab, Image

import app_logger

class ExtraWindows:
    
    def __init__(self):
        self._logger = app_logger.logs().get_logger(__name__)
        self.data_dir = os.makedirs(os.getcwd() + "/data/tmp", exist_ok=True)
        self._logger.info(self.data_dir)
        self.host_screen_size = ImageGrab.grab()

    def get_popup_menu(self):
        # menu_def=['&Open', ['&File', 'Fol&der','---', '!&Recent Files','C&lose']],
        #             ['&Save',['&Save File', 'Save &As','Save &Copy'  ]],
        #             ['&Edit', ['&Cut', '&Copy', '&Paste']], 
        #             ['&Tools', ['&Set known length']]
        menu_def = ['&Open', ['&File']], ['&Tools', ['&Set known length']]

        layout = [
            [sg.Menu(menu_def, background_color='lightsteelblue', text_color='navy', disabled_text_color='yellow', font='Verdana', pad=(10,10))],
        ]

        host_w, host_h = 0, 0
        app_w, app_h = 350, 20 # 500, 400 # initial width and height
        curr_app_w, curr_app_h = 0, 0 # current application with and height
        # rmw, rmh = 500, 400 # root min width and height
        # Create a new application window, using the app icon
        window = sg.Window(
            "Measure stem - Set known length",
            layout,
            size=(app_w, app_h),
            margins=(0, 0),
            icon=base64.b64encode(LOGO_BIN),
            alpha_channel=0.7,
            # right_click_menu=[[...]],
            debugger_enabled=True, # to be removed before final product
            # enable_window_config_events=True,
            # use_custom_titlebar=True,
            keep_on_top=True,
            # grab_anywhere=True, 
            resizable=True,
            finalize=True,
        )
        self._logger.info(sg.Window.get_screen_size())
        host_w, host_w = sg.Window.get_screen_size()
        # window[FILES_LIST].expand(True, True)
        # To set minimum size for application
        
        # window.TKroot.minsize(rmw, rmh)
        # window.move_to_center()
        # window.bind('<Configure>', "Configure")
      
        while True:	  
            # Get next event and values, if None return as application is closing
            event, values = window.read()
            # self._logger.info("dir(window): " + str(dir(window)))
            self._logger.info("event: " + str(event))
            self._logger.info("values: " + str(values))
            # self._logger.info("window.size: " + str(window.size))
            # curr_win_w, curr_w_h = window.size
            if not values:
                return False
            # files = values.get(FILES_LIST)

            # Break application loop if application is closed
            if event in ("Exit", sg.WIN_CLOSED):
                return False

            # When a folder is selected, get all image file names
            if event == "File":
                self.main_window()

            elif event == "Set known length":
                self._logger.info("Calling display for 'Set known length'")
                # self.SetKnownLength
                self.show_set_length_section()

    def img2ndarray(self, fpath):
        return skimage.io.imread(fpath)
    
    def nparray_to_b64str(self, input_data, reverse=False):
        # convert image in nparray to base64 string and vice versa
        if reverse is False and isinstance(input_data, np.ndarray):
            return codecs.encode(pickle.dumps(input_data, protocol=pickle.HIGHEST_PROTOCOL), "base64").decode('latin1')
        elif reverse is True and isinstance(input_data, str): 
            # this isinstance checking is only for the reversal within this method
            # otherwise a more robust checking is required
            return pickle.loads(codecs.decode(input_data.encode('latin1'), "base64"))
        else:
            self._logger.info("Input data must be of type 'numpy.ndarray' when reverse=False "
                            + "or "
                            + "Input data must be of type 'str' when reverse=True "
                            + "but " + str(type(input_data)) + " is given")

    def getImageName(self, file_location):
        filename = file_location.split('/')[-1]
        location = file_location.split('/')[0:-1]
        filename = filename.split('.')
        filename[0] += "_resized"
        filename = '.'.join(filename)
        print("filename: " + filename)
        new_path = '/'.join(location) + '/' + filename
        return new_path

    def get_fname(self, f_path): # without extension
        return f_path.split('/')[-1].split(".")[0]

    # def create_thumbnail(self, file):
    #     # put in the same place
    #     image = Image.open(file)
    
    def create_thumbnail(self, src, dst, size):
        # size should be a tuple or list of length 2
        image = Image.open(src)
        image.thumbnail(size)
        image.save(dst)

    def any_img2png_save(self, src, dst):
        # check if the image is png
        # if not png 
        image = Image.open(src)
        # original = PIL.Image.open("original.jpg")
        # image.thumbnail(image.size)
        fname = self.get_fname(src) # image name without extension
        
        # print(self.getImageName(f_path))
        if filetype.is_image(src) and image.format != "PNG":
            image.save(dst + "/{}.png".format(fname), format="png")
            # print ("not png")
        else:
            # if it's png just copy and rename
            shutil.copy(src, dst)

    def main_window(self):
        # TODO:
        # - get image size that will be use in the canvas size below (use 10% of the original image if
        # it is not greater than the host display)
        path_to_file = None
        right_click_menu = ['', ['Crop', 'Copy', 'Paste', 'Select All', 'Cut']]
        MLINE_KEY = '-MLINE-'

        layout = [
            # TODO:
            # right-click and copy file path
                    [   sg.Column([[
                            sg.Button("Select file"),
                            sg.Text(visible=False, expand_y=True, enable_events=True, 
                                tooltip="Path to selected file",
                                key='-INPUT-')
                        ]],  justification='center') 
                    #     # sg.FileBrowse(
                    #     #     key="-IN-", 
                    #     #     file_types = (('ALL Files', '*.* *'),), 
                    #     #     enable_events = True, 
                    #     #     change_submits = True, 
                    #     #     )
                    ],
                    [   sg.Column([[
                            sg.Graph(
                                canvas_size=(600, 400),
                                # graph_top_left = (0, 0), # invalid argument
                                # graph_bottom_right = (600,400), # invalid argument
                                graph_bottom_left=(0, 0),
                                graph_top_right=(600, 400),
                                key="-GRAPH-",
                                change_submits=True,  # mouse click events
                                background_color='lightblue',
                                drag_submits=True,
                                expand_x=True, 
                                expand_y=True,
                                right_click_menu=right_click_menu,
                                visible=False,
                                # enable_events=True, 
                            )

                        ]],  justification='center')
                    ],
                    [sg.Column([
                                [sg.Text(key='info', 
                                expand_x=True,
                                # This controls the initial width as others elements have visible=False
                                size=(60, 1), 
                                )
                                ]
                        ],  justification='center')
                    ],
                    [
                        sg.Column([[
                            sg.Text("Enter below the known distance or length of width you measure on the screeen"),
                        ]],  
                        key="SetKnownDistanceInfo", 
                        visible=False,
                        justification='center')
                    ],
                    [
                        sg.Column([[
                            sg.InputText(size=(10,10), key='KnownLength'), 
                            sg.Combo(['mm','cm','m', 'km'], default_value='mm', key='KnownUnit'), 
                            sg.Button("Set known distance")
                        ]],  
                        key="SetKnownDistanceSection", 
                        visible=False,
                        justification='center')
                    ],
                    # [sg.Multiline(size=(60,20), key=MLINE_KEY, right_click_menu=right_click_menu)],
        ]
        window = sg.Window("Set known length", layout, 
            # size=(600, 400),
            resizable=True,
            icon=base64.b64encode(LOGO_BIN),
            finalize=True,
            debugger_enabled=True,
            )
        
        # get the window elements for ease of use later
        select_file = window['-INPUT-']
        graph = window["-GRAPH-"] 
        setdistance_info = window["SetKnownDistanceInfo"]
        setdistance = window["SetKnownDistanceSection"]

        # can use data argument here instead of filename
        # draw_image(filename = None,  data = None, location = (None, None))
        # graph.draw_image(image_file, location=(0,400)) if image_file else None
        dragging = False
        start_point = end_point = prior_rect = None
        
        # initialization for cropping
        buf = io.BytesIO()
        curr_img = "" # numpy.ndarray
        curr_img_name = ""
        curr_img_dir = ""
        start_pt, end_pt = 0, 0
        thumnail_size = 0
        # TODO:
        # make scaling factor dynamic with, currently using 10% of the image
        scale_d_factor = 0.1 

        while True:
            event, values = window.read()
            self._logger.info("event: " + str(event))
            self._logger.info("values: " + str(values))
            # self._logger.info("key[-IN-]: " + )
            if event == sg.WIN_CLOSED:
                break  # exit


            # TODO:
            # - compare host display size and image input original size
            # - determine the thumbnail size and update the window element accordingly
            if event == "Select file":
                path_to_file = sg.popup_get_file('', multiple_files=False, no_window=True)
                curr_img_name = self.get_fname(path_to_file) # without file extension
                curr_img_dir = f"./data"
                curr_img_tbn_dir = f"{curr_img_dir}/{curr_img_name}_thumbnail.png"
               
                # # first save any input image to png, if it's png just copy
                # self.any_img2png_save(path_to_file, "./data")
                # create thumbnail from the converted or copied file
                # image = Image.open(f"./data/{fname}.png")
                curr_img = Image.open(path_to_file)
                # need make a copy as resizing or modifying affect the same memory location
                curr_img_tbn = curr_img.copy() 
                print(f"image.size before making thumbnail: {curr_img.size}")
                thumbnail_size = tuple(np.asarray(curr_img.size)*0.1) # use again in coordinate conversion
                curr_img_tbn.thumbnail(thumbnail_size)
                curr_img_tbn.save(curr_img_tbn_dir, format="png")
                print(f"image.size after making thumbnail: {curr_img_tbn.size}")

                # self.img2ndarray(path_to_file)
                # skimage.io.imsave(fname="data/resized.png", arr=self.img2ndarray(path_to_file))
                
                # image_data = self.nparray_to_b64str(self.img2ndarray(path_to_file))
                # self._logger.info("type(image_data): " + str(type(image_data)))
                if path_to_file:
                    select_file.update(visible=True)
                    buf = io.BytesIO()
                    curr_img_tbn.save(buf, format="PNG")
                    graph.draw_image(data=buf.getvalue(), location=(0,400)) if path_to_file else None
                    # graph.draw_image(curr_thumbnail_dir, location=(0,400)) if path_to_file else None
                    # graph.draw_image(data=image_data, location=(0,200)) if path_to_file else None
                    graph.update(visible=True)
                    graph.set_size(thumbnail_size)
                    graph.change_coordinates((0,0), thumbnail_size)
                    setdistance_info(visible=True)
                    setdistance(visible=True)
                    select_file.update(path_to_file)
                    # select_file.update(';'.join(path_to_file)) for multiple files
                else:
                    select_file.update('')
            if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse
                x, y = values["-GRAPH-"]
                if not dragging:
                    start_point = (x, y)
                    dragging = True
                else:
                    end_point = (x, y)
                if prior_rect:
                    graph.delete_figure(prior_rect)
                if None not in (start_point, end_point):
                    prior_rect = graph.draw_rectangle(start_point, end_point, line_color='red')

            elif event.endswith('+UP'):  # The drawing has ended because mouse up
                info = window["info"]
                # info2 = window["info2"]
                # Check of start_point and end_point are same, i.e. when a user click a point and release the mouse
                if end_point is None:
                    end_point = start_point
                info.update(value=f"selected rectangle coordiantes [{start_point} , {end_point}]")
                # info2.update(value=f"Known distance = ")
                self._logger.info("start_point: " + str(start_point))
                self._logger.info("end_point: " + str(type(end_point)))
                start_pt, end_pt = start_point, end_point # to be used in the next event e.g. cropping
                start_point, end_point = None, None  # enable grabbing a new rect
                dragging = False

            elif event == 'Crop':
                self._logger.info(f"start_point, end_point: {start_pt}, {end_pt}")
                self._logger.info(f"curr_image size (w,h): {curr_img.size}")
                self._logger.info(f"thumbnail size (w,h): {thumbnail_size}")

                # self.crop_selected_area(start_pt, end_pt, coor_origin=bottom_left)
                # coor_origin is origin of coordinate system
                # coor_origin = bottom_left for this implementation but
                # coor_origin = top_left for actual image system, so need to consider the conversion
                # start_point = end_point = (x, y) but in actual image system (y, x), need to keep in mind this as well
                
                suggested_filename = f"{curr_img_name}_cropped_{time.strftime('%Y%m%d-%H%M%S')}.png"
                saving_path = sg.popup_get_file(message='Save cropped image to...', 
                                    title = "Save cropped image to...",
                                    default_extension = ".png",
                                    # file_types = (('.png', '*.*'), ('.jpg', '.JPG'), ), 
                                    no_window=True, save_as=True,
                                    default_path=suggested_filename)
                
                # screen coordinate to image coordinate system conversion
                cropped_image = self.crop_image(curr_img, thumbnail_size, (start_pt, end_pt))
                save_format = f"{saving_path.split('.')[-1]}"
                save_format = "jpeg" if save_format.lower() == "jpg" else save_format 
                print("str(saving_path): " + str(saving_path))
                self.numpyToPil(cropped_image).save(saving_path, format=save_format)
                # self.numpyToPil(cropped_image).save(curr_img_dir + f"/{curr_img_name}_cropped.png", format="png")

            else:
                self._logger.info("unhandled event: " + str(event) + "," + str(values))
    
    def crop_image(self, base_image, ref_image_size, selected_reg):
        # base_image (width, height): original image (list of files/Pilimage or source directory) or (file or PilImage)
        # ref_image_size (width, height): Smaller or bigger version of base_image on the screen where the user select
        #                            region of interest are i.e. selected_reg
        # selected_reg: The region in ref_image that should be cropped out.
        #                coordinate of region in ref_image to map to base image,
        #                it can be one region or 
        #                list of multiple regions in a pair of tuple ((2,4), (4,6)) in (x,y) coordinate system
        # return: numpy array of the cropped image

        # TODO: Check if selected_reg is outsize the picture when maximizing as the zoom or 
        # displays size is not yet dynamic
        print("str(type(base_image)): " + str(type(base_image)))
        print("str(base_image.shape): " + str(base_image.size))
        print("str(ref_image_size): " + str(ref_image_size))
        print("str(selected_reg): " + str(selected_reg))

        col, row = selected_reg[0] # start_pt coordinate
        col_, row_ = selected_reg[1] # end_pt coordinate
        row_s = row if row > row_ else row_
        row_e = row if row < row_ else row_
        col_s = col if col < col_ else col_
        col_e = col if col > col_ else col_

        # since (0,0) is at the top left for further analysis
        # adjust the height/row values
        ref_img_h = ref_image_size[1]
        row_s = ref_img_h - row_s 
        row_e = ref_img_h - row_e 
        
        region_to_crop = [(row_s, row_e), (col_s, col_e)]
        print("region_to_crop: " + str(region_to_crop))

        scale_d_factor = round(ref_image_size[1]/base_image.size[1], 1) # both are still in (width, height) format
        print("str(scale_d_factor): " + str(scale_d_factor))
        # use scaling factor that is used to make thumbnail image to get 
        # the actual region on the original image
        # TODO: check if image is scaling up or down, then do scaling up or down accoringly 
        # currently only scaling up is used
        row_s = int(row_s * (1/scale_d_factor)) # scale_up_factor = 1/scale_d_factor
        row_e = int(row_e * (1/scale_d_factor))
        col_s = int(col_s * (1/scale_d_factor))
        col_e = int(col_e * (1/scale_d_factor))

        print(f"row_s, row_e, col_s, col_e: {row_s}, {row_e}, {col_s}, {col_e}")
        
        return self.pilToNumpy(base_image)[row_s:row_e, col_s:col_e]

    def crop_selected_area(self, sp, ep):
        print()

    def show_set_length_section(self):
        self._logger.info('')

    def pilToNumpy(self, img):
        # (height, width, channel)
        return np.array(img) 

    def numpyToPil(self, img):
        # (width, height, channel) ~ (x, y, channel)
        # good for plotting images
        return Image.fromarray(img) 

    def block_focus(self, window):
        for key in window.key_dict:    # Remove dash box of all Buttons
            element = window[key]
            if isinstance(element, sg.Button):
                element.block_focus()
    
    
