# For exifread, Gemini via https://www.google.com/search?client=firefox-b-1-d&q=how+to+extract+exif+data+in+python
# https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image also viewed for PIL
# For xmp: 
#  * https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.getxmp
#  * https://stackoverflow.com/questions/6822693/read-image-xmp-data-in-python#:~:text=As%20of%20PIL%208.2.%200%2C%20this%20can,does%20require%20defusedxml%20to%20be%20installed%20though.
#  * Gemini via extract xmpmeta from jpegg
# import PIL.JpegImagePlugin
# import exifread
# import pprint
# Got final used idea from Gemini and stack overflow question about getting xmp data
import os
import json

use_origin = (368500, 3280000, 40)

def picture_info_to_file(out_file_name: str, xmp_data: list[dict[str:str|float]]):
    out_str = json.dumps(xmp_data)
    out_str = out_str.replace(', "', ',\n"')
    out_str = out_str.replace('}, ', '\n},\n')
    with open(out_file_name, 'wt') as ofh:
        ofh.write(out_str)

def cam_pos_to_file(out_file_name: str, xmp_data: list[dict[str:str|float]], origin: tuple[float,float,float],  out_file_type:str = 'jpeg'):
    with open(out_file_name, 'wt') as ofh:
        for file_info in xmp_data:
            name = file_info['image-name'] + '.' + out_file_type
            use_x = file_info['camera-pos-x'] - origin[0]
            use_y = file_info['camera-pos-y'] - origin[1]
            use_z = file_info['camera-pos-z'] - origin[2]
            print(f'{name} {use_x} {use_y} {use_z}', file=ofh)


def bytes_to_float_or_str(as_bytes: bytes) -> float | str:
    if as_bytes.count(b'.') != 1:
        return as_bytes.decode()
    try:
        return float(as_bytes)
    except ValueError:
        return as_bytes.decode()

def extract_wanted_data(xml_data: bytes, property: bytes, property_prefix: bytes, out_type: type, default):
    start_tag = b'<' + property_prefix + b':' + property + b'>'
    stop_tag = b'</' + property_prefix + b':' + property + b'>'
    start = xml_data.find(start_tag)
    stop = xml_data.find(stop_tag)
    if start == -1 or stop == -1:
        return default
    start = start + len(start_tag)
    return out_type(xml_data[start:stop])

def extract_all_tags_with_prefix(xml_data: bytes, prefix: bytes = b'Vexcel'):
    out_data = dict()
    prefix = prefix + b':'
    prefix_pos = xml_data.find(prefix)
    while prefix_pos > -1:
        start_pos = prefix_pos + len(prefix)
        end_tag = xml_data.find(b'>', start_pos)
        end_data = xml_data.find(b'<', end_tag)
        end_end_tag = xml_data.find(b'>', end_data)
        tag = xml_data[start_pos:end_tag]
        value = xml_data[end_tag + 1: end_data]
        # Assuming utf-8
        out_data[tag.decode()] = bytes_to_float_or_str(value)
        prefix_pos = xml_data.find(prefix, end_end_tag)
    return out_data

def get_xml_data_from_file(in_file_name: str):
    with open(in_file_name, 'rb') as fh:
        raw_data = fh.read(3000)
        # print(raw_data)
        start_tag = b'<?xml'
        stop_tag = b'</x:xmpmeta>'
        start = raw_data.find(start_tag)
        stop = raw_data.find(stop_tag)
        if start == -1 or stop == -1:
            pass
        stop = stop + len(stop_tag)
        xmp_meta = raw_data[start:stop]
        data = extract_all_tags_with_prefix(xmp_meta)
        # pprint.pprint(data)
        return data



if __name__ == '__main__':
    # image_name = './ArchImages/2024~us-fl-gainesville-2024~images~E_20241026_160055_49_3893BD844B468B1_rgb.jpeg'
    # get_xml_data_from_file(image_name)
    full_file_data = []
    plain_folder_name = 'ArchImages'
    folder_name = f'./{plain_folder_name}/'
    for item in os.scandir(folder_name):
        if item.is_file():
            rp_pos = item.name.rfind('.')
            if rp_pos != -1:
                if item.name[rp_pos + 1:] in ('jpeg', 'jpg'):
                    file_data = get_xml_data_from_file(item.path)
                    full_file_data.append(file_data)
    
    cam_pos_file_name = f'{plain_folder_name}_camera_pos.txt'
    full_info_file_name = folder_name + 'picture_data.txt'
    cam_pos_to_file(cam_pos_file_name, full_file_data, use_origin)
    picture_info_to_file(full_info_file_name, full_file_data)
    
    