import io
import struct

use_origin = (368500, 3280000, 40)

class RGBVertex:
    def __init__(self, stream: io.BufferedReader=None):
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0
        self.nx: float = 0.0
        self.nx: float = 0.0
        self.ny: float = 0.0
        self.red: int = 0
        self.green: int = 0
        self.blue: int = 0

        if stream is not None:
            self.read_from_stream(stream)

    
    def read_from_stream(self, stream: io.BufferedReader):
        self.x = struct.unpack('f', stream.read(4))[0]
        self.y = struct.unpack('f', stream.read(4))[0]
        self.z = struct.unpack('f', stream.read(4))[0]
        # self.nx = struct.unpack('f', stream.read(4))[0]
        # self.ny = struct.unpack('f', stream.read(4))[0]
        # self.nz = struct.unpack('f', stream.read(4))[0]
        self.red = struct.unpack('c', stream.read(1))[0]
        self.green = struct.unpack('c', stream.read(1))[0]
        self.blue = struct.unpack('c', stream.read(1))[0]
    
    def write_to_stream(self, stream: io.BufferedWriter):
        stream.write(struct.pack('f', self.x))
        stream.write(struct.pack('f', self.y))
        stream.write(struct.pack('f', self.z))
        # stream.write(struct.pack('f', self.nx))
        # stream.write(struct.pack('f', self.ny))
        # stream.write(struct.pack('f', self.nz))
        stream.write(struct.pack('i', self.red))
        stream.write(struct.pack('i', self.green))
        stream.write(struct.pack('i', self.blue))


with open('output.ply', 'rb') as ifh:
    # TODO: May want to handle format of big endian (easy to do in Python)
    ln = ifh.readline().strip()
    if ln != b'ply':
        print("Error: Not a ply file")

    num_in_vxs = 0
    while ln != b'end_header':
        print(ln)
        if ln.startswith(b'element vertex '):
            vxs = ln.split(b' ')[2]
            num_in_vxs = int(vxs)
            print(num_in_vxs)

        ln = ifh.readline().strip()
    min_x = 1e20
    max_x = 1e-20
    min_y = 1e20
    max_y = 1e-20
    for i in range(num_in_vxs):
        try:
            newVx = RGBVertex(ifh)

            if newVx.x > max_x:
                max_x = newVx.x
            if newVx.x < min_x:
                min_x = newVx.x
            if newVx.y > max_y:
                max_y = newVx.y
            if newVx.y < min_y:
                min_y = newVx.y
        except struct.error as e:
            print("Error at: ", i)
            raise e
        
    print(f'({min_x}, {min_y}), ({max_x}, {max_y})')
    act_min_x = min_x + use_origin[0]
    act_max_x = max_x + use_origin[0]
    act_min_y = min_y + use_origin[1]
    act_max_y = max_y + use_origin[1]
    print(f'POLYGON(({act_min_x} {act_min_y}, {act_min_x} {act_max_y}, {act_max_x} {act_max_y}, {act_max_x} {act_min_y}))')
    print(min_y, max_y)
    print(ln)