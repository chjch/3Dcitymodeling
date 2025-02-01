import tkinter as tk
import tkinter.simpledialog as tksd
import tkinter.messagebox as tkmb
import urllib.request
import urllib.parse
import urllib.error
import os
import random
import json


# Following code modified from Gemini with prompt 'tkinter simpledialog change width'
class TokenEnter(tksd.Dialog):
    def body(self, parent):
        font = ("Times", 15)

        self.mainFrame = tk.Frame(parent)
        self.mainFrame.pack(expand=True, fill='both')

        tk.Label(self.mainFrame, text='Username:', font=font).grid(row=0, column=0)
        self.userNameEnt = tk.Entry(self.mainFrame, width=20, font=font)
        self.userNameEnt.grid(row=0, column=1, sticky='ew')

        tk.Label(self.mainFrame, text='Password:', font=font).grid(row=1, column=0)
        self.password = tk.Entry(self.mainFrame, width=20, show='*', font=font)  # Set the width here
        self.password.grid(row=1, column=1)
        self.error = False
        return self

    def apply(self):
        # Make call
        baseUrl = 'https://api.vexcelgroup.com/v2/auth/login'
        toEncode = {'username': self.userNameEnt.get(), 'password': self.password.get()}
        # https://stackoverflow.com/questions/36484184/python-make-a-post-request-using-python-3-urllib
        data = urllib.parse.urlencode(toEncode).encode()
        req =  urllib.request.Request(baseUrl, data=data) # this will make the method "POST"
        req.add_header('Content-Type', 'application/json')
        req.add_header('accept', 'application/json')
        try:
            with urllib.request.urlopen(baseUrl, data=data) as resp:
                if resp.status != 200:
                    self.result = '204 Error: No content available'
                    self.error = True
                obj = json.loads(resp.read())
                self.result = obj["token"]
        except urllib.error.HTTPError as err:
            self.result = 'HTTP Error: ' + err.reason
            self.error = True
        except urllib.error.URLError as err:
            self.result = 'URL Error: Unknown cause'
            self.error = True


class VexcelGetter(tk.Frame):
    def __init__(self, parent, tkn, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.__baseUrl = r'https://api.vexcelgroup.com/v2/oriented/extract?layer=urban'
        entLabs = {"wkt": ("WKT", "POINT(-82.347763 29.643984)"), 
                   "imgName": ("Image Name", "2024~us-fl-gainesville-2024~images~N_20241026_152951_49_3893BD830CA5ADC_rgb"), 
                   "imgType": ("Image Type", "oblique-north"), 
                   "minDay": ("Min Day", "2023-03-26"), "down": ("Down Sample", "4"), 
                   "bbw": ("BBox Width", "200"), "bbh": ("BBox Height", "200"), 
                   "crop": ("Crop", "clip-trimmed"), "ftype": ("Format", "jpeg")}
        self.ents: dict[str, tk.Entry] = dict()
        self.__token = tkn
        font = ("Times", 15)
        useRow = 0
        for entKey, entLab in entLabs.items():
            # https://www.geeksforgeeks.org/how-to-set-the-default-text-of-tkinter-entry-widget/
            lab = tk.Label(self, text=entLab[0], font=font)
            lab.grid(row=useRow, column=0)
            ent = tk.Entry(self, width=50, font=font)
            ent.grid(row=useRow, column=1)
            ent.insert(0, entLab[1])
            useRow += 1
            self.ents[entKey] = ent
        
        subFrame = tk.Frame(self)
        subFrame.grid(row=useRow, columnspan=2)
        useRow += 1

        btn1 = tk.Button(subFrame, text="Image by Name", command=self.handleImgByName, font=font)
        btn2 = tk.Button(subFrame, text="Images by Location", command=self.handleGetAllImgsByLoc, font=font)
        btn3 = tk.Button(subFrame, text="Image by Type", command=self.handleImgByType, font=font)
        btn1.pack(side='left', anchor='center')
        btn2.pack(side='left', anchor='center')
        btn3.pack(side='left', anchor='center')

        self.batchLab = tk.Label(self, text='Batch progress', font=font)
        self.batchLab.grid(row=useRow, columnspan=2)
    
    def reportError(self, msg):
        tkmb.showerror("Error", msg)
    
    def getImageName(self):
        return self.ents['imgName'].get()
    
    # @staticmethod
    # def isFloat(pot:str):
    #     # https://stackoverflow.com/questions/22789392/str-isdecimal-and-str-isdigit-difference-example
    #     pt_pos = pot.find('.')
    #     if pt_pos == -1:
    #         return pot.isdecimal()
    #     return (pot[:pt_pos].isdecimal() or pot[0] == '-' and pot[1:pt_pos].isdecimal()) and pot[pt_pos + 1:].isdecimal()

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
    
    def getWKT(self):
        wkt = self.ents['wkt'].get().strip()
        if not len(wkt) > 0:
            self.reportError("WKT may not be empty for this call type.")
            return ""
        return wkt

    def getSharedValues(self):
        minDay = self.ents['minDay'].get().strip()
        if not self.isDay(minDay):
            self.reportError("Problem with date.")
            return ("-1",)
        bboxWidth = self.ents["bbw"].get().strip()
        bboxHeight = self.ents["bbh"].get().strip()
        if not self.isNaturalItg(bboxWidth) or not self.isNaturalItg(bboxHeight):
            self.reportError("Problem with bounding box width and/or height.")
            return ("-1",)
        downsample = self.ents["down"].get().strip()
        if not self.isNaturalItg(downsample, includeZero=True):
            self.reportError("Problem with down sample integer.")
            return ("-1",)
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
    
    def handleImgByName(self):
        img_name = self.getImageName().strip()
        if len(img_name) < 1:
            self.reportError('Image name field must not be empty.')
            return
        
        wkt = self.getWKT()
        if wkt == "":
            return
        
        others = self.getSharedValues()
        if others[0] == '-1':
            return

        url = self.makeGetImgUrl(img_name, '', wkt, *others)
        if self.makeImgRequest(url, img_name + '.' + others[-1]):
            tkmb.showinfo("Success", f"Successfully wrote to '{img_name}.{others[-1]}'")

    def handleImgByType(self):
        img_type = self.ents['imgType'].get().strip()
        if len(img_type) < 1:
            self.reportError('Image type field must not be empty.')
            return
        
        wkt = self.ents['wkt'].get().strip()
        if len(wkt) < 1:
            self.reportError('WKT field must not be empty.')
            return
        
        others = self.getSharedValues()
        if others[0] == '-1':
            return

        url = self.makeGetImgUrl('', img_type, wkt, *others)
        if self.makeImgRequest(url, img_type + '.' + others[-1]):
            tkmb.showinfo("Success", f"Successfully wrote to '{img_type}.{others[-1]}'")

    

    def handleGetAllImgsByLoc(self):
        wkt = self.getWKT()
        if wkt == '':
            return

        others = self.getSharedValues()
        if others[0] == '-1':
            return
        minDay = others[0]
        ftype = others[-1]

        url = self.makeGetImageJSONUrl(wkt, minDay)
        jsonObj = self.makeJSONRequest(url)
        if not jsonObj:
            return
        actImgs = jsonObj['features']
        if len(actImgs) < 1:
            tkmb.showinfo("Success", "No images found.")
        # Make a folder
        folderName = ''
        while True:
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
                self.batchLab.config(text=f'Quit at {idx + 1} of {numImgs}')
                return
            self.batchLab.config(text=f'{idx + 1} of {numImgs}')
            self.batchLab.update()
        self.batchLab.config(text=f'Finished process')
        self.batchLab.update()
        tkmb.showinfo("Success", f"Successfully wrote {numImgs} images to {folderName}")

def main_func():
    root = tk.Tk()
    root.withdraw()

    ctr = 0
    while True:
        dg = TokenEnter(root, title="My Dialog")
        if dg.error:
            ctr += 1
            if ctr < 5:
                tkmb.showerror('Error', dg.result)
            else:
                tkmb.showerror('Stop', f'Attempted {ctr} times. Halting program.')
                return
        else:
            break
    if dg.result is None:
        return

    root.wm_deiconify()
    tk.Label(root, text="Quick Caller", font=("times", 36)).pack(side='top', anchor='center')
    
    vg = VexcelGetter(root, dg.result)
    vg.pack()
    
    tk.mainloop()

if __name__ == '__main__':
    main_func()