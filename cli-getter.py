import urllib.request
import urllib.parse
import urllib.error
import os
import random
import json
import sys


class VexcelGetter(tk.Frame):
    def __init__(self, parent, tkn, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.__baseUrl = r'https://api.vexcelgroup.com/v2/oriented/extract?layer=urban'
    
    @staticmethod
    def isNaturalItg(pot:str, includeZero=False):
        if len(pot) == 0:
            return True
        try:
            intg = int(pot)
            if includeZero:
                return intg >= 0
            return intg > 0
        except ValueError:
            return False
    
    @staticmethod
    def isDay(pot:str):
        if len(pot) < 0:
            return True
        if len(pot) != len("0000-00-00"):
            return False
        if pot[4] != '-' or pot[7] != '-' or  not pot[:4].isdecimal() or not pot[5:7].isdecimal() or not pot[8:].isdecimal():
            return False
        year = int(pot[:4])
        month = int(pot[5:7])
        day = int(pot[8:])
        
        if month > 12 or month < 1:
            return False
        if year < 1901:
            return False
        if day < 1:
            return False
        if month in (1, 3, 5, 7, 8, 10, 12) and day > 31:
            return False
        elif month in (4, 6, 9, 11) and day > 30:
            return False
        elif month == 2 and year % 4 == 0 and day > 29:
            return False
        elif month == 2 and day > 28:
            return False
        return True
    

    def getSharedValues(self):
        minDay = self.ents['minDay'].get().strip()
        bboxWidth = self.ents["bbw"].get().strip()
        bboxHeight = self.ents["bbh"].get().strip()
        downsample = self.ents["down"].get().strip()
        crop_type = self.ents["crop"].get().strip()
        img_format = self.ents["ftype"].get().strip()
        
        return (minDay, downsample, bboxWidth, bboxHeight, crop_type, img_format)
    
    def makeGetImageJSONUrl(self, wkt, minDay):
        url = r'https://api.vexcelgroup.com/v2/oriented/query?'
        url += rf'&' + urllib.parse.urlencode([('wkt', wkt)])
        # url += r'&spatial-operation=intersect'
        url += r'&spatial-operation=covers-wkt'
        if len(minDay) > 0:
            url += rf'&min-capture-date={minDay}T00%3A00%3A00&metadata-format=JSON'
        url += r'&bands=RGB&include=image-name'
        url += r'&order-by=layer-asc%2C%20collection-last-capture-date-desc%2C%20image-center-distance-asc'
        url += rf'&token={self.__token}'
        return url

    def makeGetImgUrl(self, img_name, img_type, wkt, minDay:str, downsample, bboxWidth, bboxHeight, crop_type, img_format):
        # TODO: Check if min day is in YYYY-MM-DD format
        
        useUrl = r'https://api.vexcelgroup.com/v2/oriented/extract?layer=urban'                                  # base url
        if len(wkt) > 0:
            # url_wkt = urllib.parse.urlencode([('wkt', f'POINT ({lng} {lat})')], encoding='utf-8')
            url_wkt = urllib.parse.urlencode([('wkt', wkt)], encoding='utf-8')
            # useUrl += rf'&wkt=POINT%20%28{lng}%20{lat}%29'                                                           # point
            useUrl += '&' + url_wkt

        if len(img_name) > 0:
            useUrl += rf'&image-name={img_name}'
        if len(img_type) > 0:
            useUrl += rf'&product-type={img_type}'
        useUrl += r'&order-by=layer-asc%2C%20collection-last-capture-date-desc%2C%20image-center-distance-asc'   # layer info
        if len(minDay) > 0:
            useUrl += rf'&min-capture-date={minDay}%2000%3A00%3A00'                                                 # minimum capture date
        if len(downsample) > 0:
            useUrl += rf'&downsample={downsample}'                                                                   # take 1 of so many pixels
        useUrl += rf'&bbox-dimensions={bboxWidth}%2C{bboxHeight}'                                                # bbox
        useUrl += r'&rotation=natural'
        if len(crop_type) > 0:
            useUrl += rf'&crop={crop_type}'
        useUrl += r'&attribution=false'
        if len(img_format) > 0:
            useUrl += rf'&image-format={img_format}'
        useUrl += rf'&token={self.__token}'
        return useUrl
    
    # Saw something similar by LarsaSolidor at https://stackoverflow.com/questions/47516722/urllib-request-ssl-connection-python-3
    # https://security.stackexchange.com/questions/245590/is-adding-a-default-context-to-pythons-urllib-necessary-security-wise-and-is-i
    def makeImgRequest(self, url, fileName):
        try:
            with urllib.request.urlopen(url) as req:
                with open(fileName, 'wb') as imgFileOut:
                    imgFileOut.write(req.read())
        except urllib.error.HTTPError as err:
            self.reportError("HTTP Error: " + err.reason)
            return False
        except urllib.error.URLError as err:
            self.reportError("Unknown URL Error")
            return False
        return True
    
    def makeJSONRequest(self, url):
        try:
            with urllib.request.urlopen(url) as req:
                obj = json.loads(req.read())
                return obj
        except urllib.error.HTTPError as err:
            self.reportError("HTTP Error: " + err.reason)
            return False
        except urllib.error.URLError as err:
            self.reportError("Unknown URL Error")
            return False
        return True

    def handleGetAllImgsByLoc(self, wkt, minDay, downsample, bboxWidth, bboxHeight, crop_type, ftype):
        others = (minDay, downsample, bboxWidth, bboxHeight, crop_type, ftype)
        if others[0] == '-1':
            return

        url = self.makeGetImageJSONUrl(wkt, minDay)
        jsonObj = self.makeJSONRequest(url)
        if not jsonObj:
            return
        actImgs = jsonObj['features']
        if len(actImgs) < 1:
            print("No images found.")
            return
        
        # Make a folder
        folderName = ''
        while True:
            # TODO: Get the location name from file
            simp = wkt.replace(' ', '').replace(',', '~')
            folderName = f'./ImagesWKT{simp[:50]}R{random.randint(1,100000)}'
            try:
                os.mkdir(folderName)
            except FileExistsError:
                continue
            break

        numImgs = len(actImgs)
        for idx, img in enumerate(actImgs):
            name = img['properties']['image-name']
            url = self.makeGetImgUrl(name, '',wkt, *others)
            if not self.makeImgRequest(url, folderName + '/' + name + '.' + ftype):
                print(f'Quit at {idx + 1} of {numImgs}')
                return
        print(f"Successfully wrote {numImgs} images to {folderName}")

def main_func():
    # TODO: Get actual token
    token = ''
    
    vg = VexcelGetter(token)
    
    # TODO: Add code that goes through and gets the appropriate results

if __name__ == '__main__':
    # Ask for password and username, or for token (better)
    # Ask for trim wkt or clip wkt
    # Need to gather
    # token, wkts, minDay, downsample, bboxWidth, bboxHeight, crop_type, ftype
    # May also need downsample
    main_func()