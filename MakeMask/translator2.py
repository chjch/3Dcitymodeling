import numpy as np
import cv2
from PIL import Image

# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=how+to+crop+an+image+pil+python
# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=create+a+perspective+transform+matrix+in+opencv+python
# Gemini via https://www.google.com/search?client=firefox-b-1-d&q=concatenate+numpy+arrays+by+column
# Intro to OpenCV: https://stackoverflow.com/questions/14830698/transform-point-position-in-trapezoid-to-rectangle-position
# OpenCV sources:
#  * https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html
#  * https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html#gaf73673a7e8e18ec6963e3774e6a94b87
#  * https://docs.opencv.org/4.x/d2/de8/group__core__array.html#gad327659ac03e5fd6894b90025e6900a7


image_name = '2023~us_fl_gainesville_2023~images~E_20230329_154948_52_3893BD827C938F8_rgb'
original_image_name = 'oblique/21307_lvl02_oblique_backward.jpg'
original_shot_name = '21307_Lvl02_Oblique_Backward'
capture_date = '2023_03_29 15:49:48.0'
camera_pos_x = 367800.5072
camera_pos_y = 3280010.3069
camera_pos_z = 1693.00244140625
ground_z = 34.0461540222168
omega = -0.00531388824027168
phi = -0.7849689088686691
kappa = -1.5821114131544343
image_center = 'POINT (-82.34859766 29.64312294)'
geometry = 'POLYGON ((-82.34228866 29.64853174, -82.34203534 29.63770632, -82.35327423 29.63915002, -82.35342425 29.64702842, -82.34228866 29.64853174))'
flight_line_id = '1'
collection = 'us_fl_gainesville_2023'
pretty_name = 'us_fl_gainesville_2023'
layer = 'urban'
min_gsd = 0.06109885419550084
max_gsd = 0.07340499683758596
product_type = 'oblique_east'
utm_zone = '17N'
focal_length = 123.38
pp0_x = 0.0
pp0_y = 0.0
k0 = 0.0
k1 = 0.0
k2 = 0.0
k3 = 0.0
p1 = 0.0
p2 = 0.0
raster_size_width = 14144
raster_size_height = 10560
pixel_size = 0.00376
b1 = 0.0
b2 = 0.0
camera_technology = 'UltraCam_Osprey_4.1_f120'
band = 'rgb'
pixel_bbox = (0,0,14144,10560)


# Have origin at POINT(-82 29)
geo_bnd_box = np.array([
    [1-0.34228866, 0.64853174], 
    [1-0.34203534, 0.63770632],
    [1-0.35327423, 0.63915002],
    [1-0.35342425, 0.64702842]
], np.float32)


# Pixel bounding box
pixel_bnd_box = np.array([
    [pixel_bbox[0], pixel_bbox[1]],
    [pixel_bbox[2], pixel_bbox[1]],
    [pixel_bbox[2], pixel_bbox[3]],
    [pixel_bbox[0], pixel_bbox[3]]
], np.float32)

def get_transformed_pts(perspective_mat: np.ndarray, two_d_pt_mat: np.ndarray):
    extended_pt_mat = np.concatenate((two_d_pt_mat.T, np.ones((1, two_d_pt_mat.shape[0]))), axis=0)
    extended_trans_pt_mat = perspective_mat @ extended_pt_mat
    adjusted_pts = extended_trans_pt_mat[:2,:] / extended_trans_pt_mat[2:,:]
    return adjusted_pts.T

def points_to_bbox(point_mat: np.ndarray):
    minims = point_mat.min(axis=0)
    maxims = point_mat.max(axis=0)
    return (int(minims[0]), int(minims[1]), int(maxims[0]), int(maxims[1]))
 
mala_box_pnts = np.array([
    [1-0.34839486935482,  0.644256291665307], 
    [1-0.348401674093097, 0.643813201012254], 
    [1-0.347120059355348, 0.643797220022378], 
    [1-0.347113254617071, 0.644240310745761]
])

def make_perspective_matrix(geo_pts: np.ndarray, pixel_pts: np.ndarray):
    return cv2.getPerspectiveTransform(geo_pts, pixel_pts)
perspectiveMatrix = make_perspective_matrix(geo_bnd_box, pixel_bnd_box)
print(type(perspectiveMatrix))
print(perspectiveMatrix)

pin_loc = np.array([1-0.34770920083035, 0.64404509457797, 1.0])
pix_pin_loc = perspectiveMatrix @ pin_loc
int_pix_pin_loc = (int(pix_pin_loc[0] / pix_pin_loc[2]), int(pix_pin_loc[1] / pix_pin_loc[2]))
print(pix_pin_loc)
print(int_pix_pin_loc)

new_bbox = points_to_bbox(get_transformed_pts(perspectiveMatrix, mala_box_pnts))


# # Open the image
img = Image.open("MalachowskyEast1.jpeg")

# # Define the cropping box
# rad = 200
# crop_box = (int_pix_pin_loc[0] - rad, int_pix_pin_loc[1]- rad, int_pix_pin_loc[0] + rad, int_pix_pin_loc[1] + rad)
# cropped_img = img.crop(crop_box)
# cropped_img.save("cropped_image_2.jpeg")
cropped_img = img.crop(new_bbox)
cropped_img.save("cropped_image_2.jpeg")
