# import the necessary packages
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
from plantcv import plantcv as pcv
import csv
import os
import xlsxwriter
from statistics import mean

def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

'''
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="path to the input image")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])
'''

def processImage(imagelocation,outputexcel,outputcsv):


    # load the image, convert it to grayscale, and blur it slightly
    image = cv2.imread(imagelocation)
    # file name without the filename extensions
    filename = os.path.splitext(imagelocation)[0]


    # make folder using filename to hold results
    if not os.path.exists(filename):
        os.makedirs(filename)

    # resize large images
    if image.shape[0] > image.shape[1] and image.shape[0] > 2000:
        resize_height = 2000
        resize_width = int(2000*image.shape[1]/image.shape[0])
        image = cv2.resize(image, (resize_width, resize_height),
                           interpolation=cv2.INTER_AREA)
        #print('Resized to ', image.shape)
    elif image.shape[1] >= image.shape[0] and image.shape[0] > 2000:
        resize_height = int(2000*image.shape[0]/image.shape[1])
        resize_width = 2000
        image = cv2.resize(image, (resize_width, resize_height),
                           interpolation=cv2.INTER_AREA)
        #print('Resized to ', image.shape)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    # canny edge detection, then close for gaps
    edged = cv2.Canny(gray, 50, 150)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)
    # find contours 
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # sort contours
    (cnts, _) = contours.sort_contours(cnts)

    maxA = -1
    maxB = -1
    biggestSquare = None
    # loop over each contour
    for c in cnts:
        # if the contour is not sufficiently large, ignore it
        if cv2.contourArea(c) < 100:
            continue
        # compute the rotated bounding box of the contour
        orig = image.copy()
        box = cv2.minAreaRect(c)
        box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
        box = np.array(box, dtype="int")
        
        box = perspective.order_points(box)

        # get corners of box, then compute midpoints for box sizes
        (tl, tr, br, bl) = box
        (tltrX, tltrY) = midpoint(tl, tr)
        (blbrX, blbrY) = midpoint(bl, br)
        (tlblX, tlblY) = midpoint(tl, bl)
        (trbrX, trbrY) = midpoint(tr, br)
        # compute Euclidean distance between midpoints
        dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
        dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
        # compute the size of the object
        xMax = orig.shape[1]
        yMax = orig.shape[0]
        if dA*dB > maxA*maxB: # and 0 <= tl[0] < xMax and 0 <= tl[1] < yMax and 0 <= tr[0] < xMax and 0 <= tr[1] < yMax and 0 <= bl[0] < xMax and 0 <= bl[1] < yMax and 0 <= br[0] < xMax and 0 <= br[1] < yMax:
            biggestSquare = c
            maxA = dA
            maxB = dB


    c = biggestSquare
    # compute the rotated bounding box of the contour
    orig = image.copy()
    box = cv2.minAreaRect(c)
    box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
    box = np.array(box, dtype="int")
    box = perspective.order_points(box)
    (tl, tr, br, bl) = box
    pts = np.array([tl, tr, br, bl], dtype="float32")
    # apply the four point tranform to obtain just the tray as an image
    warped = four_point_transform(orig, pts)

    # Crop the image to eliminate tray border as it creates a lot of noise
    height = warped.shape[0]
    width = warped.shape[1]
    warped = pcv.crop(img=warped, x = int(width*0.05), y = int(height*0.05), h = int(height*0.9), w = int(width*0.9))
    warpname = filename + "/warp.jpg"
    cv2.imwrite(warpname, warped)


    #IMAGE PROCESSING
    low_green = np.array([25, 52, 72])
    high_green = np.array([110, 255, 255])

    imgHSV = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(imgHSV, low_green, high_green)
    mask = pcv.dilate(gray_img=mask, ksize=5, i=2)
    mask = pcv.erode(gray_img=mask, ksize=5, i=2)
    mask = 255-mask
    gray_img = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    threshold_otsu_light  = pcv.threshold.otsu(gray_img=gray_img, max_value=255, object_type="light")
    res = cv2.bitwise_and(threshold_otsu_light, threshold_otsu_light, mask=mask)
    #cv2.imwrite("img.jpg", res)

    kernel = np.ones((10, 3), np.uint8)
    img = cv2.dilate(res, kernel, 1)
    img = cv2.erode(img, kernel, 1)

    img = pcv.erode(gray_img=img, ksize=3, i=1)
    img = pcv.dilate(gray_img=img, ksize=3, i=1)

    # divide threshold and gray image into four quadrants
    crop_height_mid = int(img.shape[0]/2)
    crop_width_mid = int(img.shape[1]/2)
    quadrants = [(img[:crop_height_mid, :crop_width_mid], gray_img[:crop_height_mid, :crop_width_mid]),
                        (img[:crop_height_mid, crop_width_mid:], gray_img[:crop_height_mid, crop_width_mid:]),
                        (img[crop_height_mid:, :crop_width_mid], gray_img[crop_height_mid:, :crop_width_mid]),
                        (img[crop_height_mid:, crop_width_mid:], gray_img[crop_height_mid:, crop_width_mid:])]

    # output list
    ids = []
    lengths_calib = []
    # skeletonize and get lengths for each quadrant
    for i, (img, gray_img) in enumerate(quadrants):
        skeleton = pcv.morphology.skeletonize(img)

        _, seg_img, edge_objects = pcv.morphology.prune(skel_img=skeleton, size=30, mask=gray_img)

        edgename = filename + "/edge.jpg_" + str(i) + ".jpg"
        cv2.imwrite(edgename, seg_img)

        real_edges = []
        for j, edge_object in enumerate(edge_objects):
            # use formula PlantCV uses to calculate plant length to remove plants below 1 pixel long (errors)
            if(float(cv2.arcLength(edge_objects[j], False) / 2) > 1):
                real_edges.append(edge_object)
        edge_objects = real_edges
        #leaf_obj, stem_obj = pcv.morphology.segment_sort(skel_img=skeleton, objects=edge_objects)
        segmented_img, labeled_img = pcv.morphology.segment_id(skel_img=skeleton,
                                                            objects=edge_objects, mask = gray_img)

        lengths_img = pcv.morphology.segment_path_length(segmented_img=segmented_img,
                                                            objects=edge_objects)

        idname = filename + "/ids_" + str(i) + ".jpg"
        cv2.imwrite(idname, labeled_img)

        lengthname = filename + "/lengths_" + str(i) + ".jpg"
        cv2.imwrite(lengthname, lengths_img)

        path_lengths = pcv.outputs.observations['default']['segment_path_length']['value']
        ids.append(pcv.outputs.observations['default']['segment_path_length']['label'])
        #pcv.outputs.save_results(filename='results.txt', outformat="json")

        # calibrate the pixel lengths to actual measurements, using the height/width of the square
        # tray as 90mm (5% of 100mm off from each side)
        new_height = warped.shape[0]
        lengths_calib.append([j * 90/new_height for j in path_lengths])

    # match ids to lengths
    result = list(zip(ids, lengths_calib))
    # Write results in an excel file
    if outputexcel:

        workbook = xlsxwriter.Workbook(filename + "/results.xlsx")
        worksheet = workbook.add_worksheet()

        for i, (ids, lengths_calib) in enumerate(result):
            try:
                average = mean(lengths_calib)
            except:
                average = "No data"
            worksheet.write(0,12+i,average)
            
            for row_num, data in enumerate(ids):
                worksheet.write(row_num, i*3, data)
            
            for row_num, data in enumerate(lengths_calib):
                worksheet.write(row_num, i*3+1, data)

        workbook.close()



    # Write results in a csv file
    if outputcsv:
        csvname = filename + "/results.csv"
        with open(csvname, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            
            maxsize = 1
            maxsizes = []
            for (ids, lengths_calib) in result:
                maxsizes.append(len(ids))
                if len(ids) > maxsize:
                    maxsize = len(ids)

            try:
                set1average = mean(result[0][1])
            except:
                set1average = "No data"
                
            try:
                set2average = mean(result[1][1])
            except:
                set2average = "No data"
                
            try:
                set3average = mean(result[2][1])
            except:
                set3average = "No data"
                
            try:
                set4average = mean(result[3][1])
            except:
                set4average = "No data"

            for index in range(maxsize):
                if index < maxsizes[0]:
                    set1id = result[0][0][index]
                    set1lengths = result[0][1][index]
                else:
                    set1id = ''
                    set1lengths = ''

                if index < maxsizes[1]:
                    set2id = result[1][0][index]
                    set2lengths = result[1][1][index]
                else:
                    set2id = ''
                    set2lengths = ''

                if index < maxsizes[2]:
                    set3id = result[2][0][index]
                    set3lengths = result[2][1][index]
                else:
                    set3id = ''
                    set3lengths = ''

                if index < maxsizes[3]:
                    set4id = result[3][0][index]
                    set4lengths = result[3][1][index]
                else:
                    set4id = ''
                    set4lengths = ''
                
                if index == 0:
                    writer.writerow((set1id,set1lengths,'',set2id,set2lengths,'',set3id,set3lengths,'',set4id,set4lengths,'',set1average,set2average,set3average,set4average))
                else:
                    writer.writerow((set1id,set1lengths,'',set2id,set2lengths,'',set3id,set3lengths,'',set4id,set4lengths))


            '''
            for (ids, lengths_calib) in result:
                # write the ids of each plant
                writer.writerow(ids)

                # write the calibrated lengths
                writer.writerow(lengths_calib)
            '''

