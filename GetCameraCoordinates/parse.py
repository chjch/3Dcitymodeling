import io
import json
    
def parseAndRead(ifh: io.TextIOBase, ofh: io.TextIOBase, origin_x: float, origin_y: float, origin_z, file_type:str):
    line = ifh.readline()
    accumulator = ''
    while line:
        abc = line.strip()
        accumulator += abc
        if abc == '}':
            # print("use", accumulator, '"')
            json_data = json.loads(accumulator)
            img_name = json_data["image_id"]
            x_pos = json_data["camera_pos_x"] - origin_x
            y_pos = json_data["camera_pos_y"] - origin_y
            z_pos = json_data["camera_z"] - origin_z
            print(f'{img_name}.{file_type}', x_pos, y_pos, z_pos, file=ofh)

            accumulator = ''
        line = ifh.readline()
    return

if __name__ == '__main__':
    use_x, use_y, use_z = 368500, 3280000, 40
    ext = 'jpeg'
    with open('./Architecture Building.txt', 'rt') as input_fh:
        with open('./out.txt', 'wt') as output_fh:
            parseAndRead(input_fh, output_fh, use_x, use_y, use_z, ext)