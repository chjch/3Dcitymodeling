import numpy as np
import cv2
from PIL import Image, ImageDraw

import sys
sys.path.append('../GetCameraCoordinates')

from exifExtractor import get_xml_data_from_file

# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=how+to+crop+an+image+pil+python
# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=create+a+perspective+transform+matrix+in+opencv+python
# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=concatenate+numpy+arrays+by+column
# Intro to OpenCV: https://stackoverflow.com/questions/14830698/transform-point-position-in-trapezoid-to-rectangle-position
# OpenCV sources:
#  * https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html
#  * https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html#gaf73673a7e8e18ec6963e3774e6a94b87
#  * https://docs.opencv.org/4.x/d2/de8/group__core__array.html#gad327659ac03e5fd6894b90025e6900a7
# Aya, jjv-liu at https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 for importing
# Making white box: https://www.youtube.com/watch?v=5QR-dG68eNE


# Pixel bounding box

def get_transformed_pts(perspective_mat: np.ndarray, two_d_pt_mat: np.ndarray):
    extended_pt_mat = np.concatenate((two_d_pt_mat.T, np.ones((1, two_d_pt_mat.shape[0]))), axis=0)
    extended_trans_pt_mat = perspective_mat @ extended_pt_mat
    adjusted_pts = extended_trans_pt_mat[:2,:] / extended_trans_pt_mat[2:,:]
    return adjusted_pts.T

def points_to_bbox(point_mat: np.ndarray):
    minims = point_mat.min(axis=0)
    maxims = point_mat.max(axis=0)
    return (int(minims[0]), int(minims[1]), int(maxims[0]), int(maxims[1]))

def wkt_to_pts(strung_wkt: str, strip_last=True, adjust_lng=83, adjust_lat=-29):
    '''
    Convert a wkt polygon to np array. Can optionally ignore last point (useful for bounding boxes).
    Also can add adjust_lng and adjust_lat to longitude and latitude
    '''
    first_paren = strung_wkt.find('(')
    if first_paren == -1 or strung_wkt[:first_paren].strip() != 'POLYGON':
        raise SyntaxError("Not valid WKT string or not POLYGON")
    # Otherwise, will assume all is okay

    # Split into points
    strung_pts = strung_wkt[first_paren + 2: -2].split(',')

    # Make Numpy array. Size will be length of points, potentially minus 1 if ignoring last point
    out_shape = (len(strung_pts) - 1, 2) if strip_last else (len(strung_pts), 2)
    out_pts = np.zeros(out_shape, dtype=np.float32)

    # Go through and do conversions
    for idx, strung in enumerate(strung_pts[:out_shape[0]]):
        split = strung.strip().split(' ')
        out_pts[idx][0] = float(split[0]) + adjust_lng
        out_pts[idx][1] = float(split[1]) + adjust_lat 
    
    return out_pts
    
def make_perspective_matrix(geo_pts: np.ndarray, pixel_pts: np.ndarray):
    return cv2.getPerspectiveTransform(geo_pts, pixel_pts)

def get_pixel_bbox(bbox_data : str | tuple[int]):
    if isinstance(bbox_data, str):
        bbox_data = tuple(int(coord) for coord in bbox_data.split(','))
    return np.array([
        [bbox_data[0], bbox_data[1]], 
        [bbox_data[2], bbox_data[1]], 
        [bbox_data[2], bbox_data[3]], 
        [bbox_data[0], bbox_data[3]]
    ], np.float32)


def get_bboxes(wkt_array: np.ndarray, image_name: str):
    # Gets, in order, picture geometry bbox array, picture pixel bbox array, and transformed wkt bbox condensed
    # condensed means (x0, y0, x1, y1)

    # Get the geometry and pixel bounding boxes (assuming they line up exactly)
    all_data = get_xml_data_from_file(image_name)
    geo_bnd_box = wkt_to_pts(all_data['geometry'])
    pixel_bnd_box = get_pixel_bbox(all_data['pixel-bbox'])

    # Make the perspective matrix and get the transformed bbox
    perspectiveMatrix = make_perspective_matrix(geo_bnd_box, pixel_bnd_box)
    transformed_wkt_bnd_box = points_to_bbox(get_transformed_pts(perspectiveMatrix, wkt_array))

    return geo_bnd_box, pixel_bnd_box, transformed_wkt_bnd_box 

def crop_image(wkt_array: np.ndarray, image_name: str):
    '''
    Crop the image.
    Parameters:
    * wkt_array: wkt string as an adjusted numpy array. Omit the loop point (though shouldn't cause issues)
    * image_name: Name of image
    '''
    # Get the transformed wkt bounding box
    _, _, new_bbox = get_bboxes(wkt_array, image_name)

    # Crop the image
    with Image.open(image_name) as img:
        cropped_img = img.crop(new_bbox)
        cropped_img.save(image_name[:image_name.rfind('.')] + "_cropped.jpeg")

def make_mask(wkt_array: np.ndarray, image_name: str):
    _, image_pixel_bbox, trans_wkt_pixel_bbox = get_bboxes(wkt_array, image_name)
    # Create a new black image
    full_width, full_height = int(image_pixel_bbox[2][0]), int(image_pixel_bbox[2][1])
    img = Image.new('1', (full_width, full_height))

    # Add white square (see YouTube source)
    draw = ImageDraw.Draw(img)
    draw.rectangle(trans_wkt_pixel_bbox, 'white')
    img.save(img_name[:img_name.rfind('.')] + '_mask.jpeg')
    

if __name__ == '__main__':
    img_name = "MalachowskyEast1.jpeg"

    # Set up the cropping wkt
    mala_wkt = 'POLYGON ((-82.34839486935482 29.644256291665307, -82.348401674093097 29.643813201012254, -82.347120059355348 29.643797220022378, -82.347113254617071 29.644240310745761, -82.34839486935482 29.644256291665307))'
    mala_box_pnts = wkt_to_pts(mala_wkt)
    # crop_image(mala_box_pnts, img_name)
    make_mask(mala_box_pnts, img_name)
