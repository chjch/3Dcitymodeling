import sys
sys.path.append('./MakeMask/')
sys.path.append('./GetCameraCoordinates/')

import os
import shutil
from translator2 import crop_image, make_mask, wkt_to_pts
from exifExtractor import cam_pos_to_file, get_xml_data_from_file, use_origin

# Relative imports: Aya and jjv-liu https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
# shutil: Swati and ruohola https://stackoverflow.com/questions/123198/how-do-i-copy-a-file

def rename_in_cwd():
    change_map = dict()
    for record in os.scandir():
        if record.is_file():
            dot_pos = record.name.rfind('.')
            if record.name[dot_pos:] == '.jpeg':
                use_name = get_xml_data_from_file(record.name)['image-name'] + '.jpeg'
                if use_name != record.name:
                    change_map[record.name] = use_name
    
    for from_file_name, to_file_name in change_map.items():
        shutil.move(from_file_name, to_file_name)

def make_masks_and_crops(wkt_array, src_dir='', tgt_dir_masks='', tgt_dir_crops=''):
    ctr = 0
    for record in os.scandir(src_dir):
        if record.is_dir():
            continue
        if record.name[record.name.rfind('.'):] == '.jpeg':
            make_mask(wkt_array, record.name, src_dir, tgt_dir_masks)
            crop_image(wkt_array, record.name, src_dir, tgt_dir_crops)
            ctr += 1
            if ctr % 10 == 0:
                print(f"Masks and cropped {ctr} images so far")
    print("Done with masks and crops.")

def create_camera_position_for_folder(from_folder: str, full_out_name: str, origin: tuple[int, int, int]):
    accumulated_data = []
    for record in os.scandir(from_folder):
        if record.is_dir():
            continue
        if record.name[record.name.rfind('.'):] == '.jpeg':
            accumulated_data.append(get_xml_data_from_file(record.path))
    cam_pos_to_file(full_out_name, accumulated_data, origin, 'jpeg')


if __name__ == '__main__':
    base_folder = './MalachowskyEntire/'
    imagesSubdir = 'Images/'

    # Set up the cropping wkt
    mala_wkt = 'POLYGON ((-82.34839486935482 29.644256291665307, -82.348401674093097 29.643813201012254, -82.347120059355348 29.643797220022378, -82.347113254617071 29.644240310745761, -82.34839486935482 29.644256291665307))'
    mala_box_pnts = wkt_to_pts(mala_wkt)

    # Go to appropriate folder
    os.chdir(base_folder + imagesSubdir)

    # Rename the files so that they are as recorded in the file
    rename_in_cwd()

    # Go back to parent directory and make folders for mask and crops
    mask_dir_name, crop_dir_name = './masks/', './cropped_images/'
    os.chdir('..')
    try:
        os.mkdir(mask_dir_name)
    except FileExistsError:
        pass
    try:
        os.mkdir(crop_dir_name)
    except FileExistsError:
        pass

    # Now, make the masks and crops
    make_masks_and_crops(mala_box_pnts, './' + imagesSubdir, mask_dir_name, crop_dir_name)

    # Finally, make the georeference file
    cam_pos_file_name = 'camera_positions.txt'
    create_camera_position_for_folder('./' + imagesSubdir, cam_pos_file_name, use_origin)
    print("Done")
    
    


