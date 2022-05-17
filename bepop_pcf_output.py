#!/usr/bin/env python
# coding: utf-8
# zoroyoshi,18-2-22,18-8-10
import sys,struct
import inkex
from inkex.transforms import Transform
from inkex import paths

class BepopPcfOutput(inkex.OutputExtension):
    def __init__(self):
        super(BepopPcfOutput, self).__init__()
        self.arg_parser.add_argument('--myparam',
          type = str, dest = 'myparam', default = '')
        self.arg_parser.add_argument('--curlayer',
          type = inkex.Boolean, dest = 'curlayer', default = True)
        self.arg_parser.add_argument('--resize',
          type = inkex.Boolean, dest = 'resize', default = True)

    def dmesg(self,s):
        #inkex.debug(s.encode('utf-8'))
        pass
    def effect(self):
        pass
    def save(self, stream):
        self.dmesg('output')
        layer= self.document
        if self.options.curlayer:
            layer= self.svg.get_current_layer()
        #calculate bounding box first: determine line/curve/point after conveted to integer
        box= None
        for node in layer.xpath('.//svg:path', namespaces=inkex.NSS):
            m = (node.transform @ Transform([[1.0,0.0,0.0],[0.0,1.0,0.0]])).matrix
            path = paths.CubicSuperPath(paths.Path(node.get('d')))
            paths.Path(path).transform(Transform(m)).to_arrays()
            bbox = paths.Path(path).bounding_box()
            b=[bbox.x.minimum, bbox.x.maximum, bbox.y.minimum, bbox.y.maximum]
            if box==None:
                box= b
            else:
                box= [min(box[0],b[0]),max(box[1],b[1]),min(box[2],b[2]),max(box[3],b[3])]
        mag= 10.0
        if self.options.resize:
            mag= 1000/max(box[1]-box[0], box[3]-box[2])
        ofs= 0.5
        data= b''
        for node in layer.xpath('.//svg:path', namespaces=inkex.NSS):
            self.dmesg('node')
            m = (node.transform @ Transform([[1.0,0.0,0.0],[0.0,1.0,0.0]])).matrix
            path = paths.CubicSuperPath(paths.Path(node.get('d')))
            paths.Path(path).transform(Transform(m)).to_arrays()
            for elem in path:
                for cur in elem:
                    for pt in cur:
                        pt[0]= int((pt[0]-box[0])*mag+ofs)
                        pt[1]= int((pt[1]-box[2])*mag+ofs)
                data+= struct.pack('<iib', elem[0][1][0], elem[0][1][1], 6)
                self.dmesg('start %s' % str(elem[0][1]))
                for i in range(len(elem)-1):
                    cur= elem[i]
                    nex= elem[i+1]
                    if cur[1]==cur[2] and nex[0]==nex[1]:
                        if cur[1]==nex[1]:
                            self.dmesg('%d:point-%s' % (i,str(nex[1])))
                            pass #remove point
                        else:
                            self.dmesg('%d:line-%s' % (i,str(nex[1])))
                            data+= struct.pack('<iib', nex[1][0], nex[1][1], 2)
                    else:
                        self.dmesg('%d:curve-%s-%s-%s' % (i,str(cur[2]),str(nex[0]),str(nex[1])))
                        data+= struct.pack('<iib', cur[2][0], cur[2][1], 4)
                        data+= struct.pack('<iib', nex[0][0], nex[0][1], 4)
                        data+= struct.pack('<iib', nex[1][0], nex[1][1], 4)
                lastc= int(data[-1])
                if lastc==6: #no elem available
                    data= data[:-9]
                else: #end flag
                    data= data[:-1]+struct.pack('b',lastc+1)
        if sys.platform == "win32":
            import os, msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        stream.write(b'Bepop PictSign'+b'\x00'*50)
        stream.write(b'Ver.0.00'+b'\x00'*8)
        stream.write(struct.pack('<ii', int((box[1]-box[0])*mag+ofs), int((box[3]-box[2])*mag+ofs))) 
        stream.write(b'\x00'*168)
        stream.write(struct.pack('<i', len(data)//9))
        stream.write(data)
        stream.flush()

if __name__ == '__main__':
    e=BepopPcfOutput()
    e.run()
