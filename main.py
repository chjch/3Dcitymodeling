import tkinter as tk
import tkinter.simpledialog as tksd
import tkinter.messagebox as tkmb
import urllib.request
import urllib.error
import os
import random
import json


# Following code modified from Gemini with prompt 'tkinter simpledialog change width'
class TokenEnter(tksd.Dialog):
    def body(self, master):
        self.entry = tk.Entry(master, width=50, show='*')  # Set the width here
        self.entry.pack()
        return self.entry

    def apply(self):
        self.result = self.entry.get()


class VexcelGetter(tk.Frame):
    def __init__(self, master, tkn, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.__baseUrl = r'https://api.vexcelgroup.com/v2/oriented/extract?layer=urban'
        entLabs = {"lat": ("Latitude", "29.643984"), "lng": ("Longitude", "-82.347763"), 
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
    
    @staticmethod
    def isFloat(pot:str):
        # https://stackoverflow.com/questions/22789392/str-isdecimal-and-str-isdigit-difference-example
        pt_pos = pot.find('.')
        if pt_pos == -1:
            return pot.isdecimal()
        return (pot[:pt_pos].isdecimal() or pot[0] == '-' and pot[1:pt_pos].isdecimal()) and pot[pt_pos + 1:].isdecimal()

    @staticmethod
    def isPosItg(pot:str):
        if len(pot) == 0:
            return True
        try:
            intg = int(pot)
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
        lng = self.ents['lng'].get().strip()
        lat = self.ents['lat'].get().strip()
        if not self.isFloat(lng) or not self.isFloat(lat) or len(lng) == 0 or len(lat) == 0:
            self.reportError("Invalid longitude and/or latitude.")
            return ("-1",)
        minDay = self.ents['minDay'].get().strip()
        if not self.isDay(minDay):
            self.reportError("Problem with date.")
            return ("-1",)
        bboxWidth = self.ents["bbw"].get().strip()
        bboxHeight = self.ents["bbh"].get().strip()
        if not self.isPosItg(bboxWidth) or not self.isPosItg(bboxHeight):
            self.reportError("Problem with bounding box width and/or height.")
            return ("-1",)
        downsample = self.ents["down"].get().strip()
        if not self.isPosItg(downsample):
            self.reportError("Problem with down sample integer.")
            return ("-1",)
        crop_type = self.ents["crop"].get().strip()
        img_format = self.ents["ftype"].get().strip()
        
        return (lng, lat, minDay, downsample, bboxWidth, bboxHeight, crop_type, img_format)
    
    def makeGetImageJSONUrl(self, lng, lat, minDay):
        url = r'https://api.vexcelgroup.com/v2/oriented/query?'
        url += rf'&wkt=POINT%20%28{lng}%20{lat}%29'
        url += r'&spatial-operation=intersect'
        if len(minDay) > 0:
            url += rf'&min-capture-date={minDay}T00%3A00%3A00&metadata-format=JSON'
        url += r'&bands=RGB&include=image-name'
        url += r'&order-by=layer-asc%2C%20collection-last-capture-date-desc%2C%20image-center-distance-asc'
        url += rf'&token={self.__token}'
        return url

    def makeGetImgUrl(self, img_name, img_type, lng, lat, minDay:str, downsample, bboxWidth, bboxHeight, crop_type, img_format):
        # TODO: Check if min day is in YYYY-MM-DD format
        
        useUrl = r'https://api.vexcelgroup.com/v2/oriented/extract?layer=urban'                                  # base url
        if len(lng) > 0 and len(lat) > 0:
            useUrl += rf'&wkt=POINT%20%28{lng}%20{lat}%29'                                                           # point

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
        
        others = self.getSharedValues()
        if others[0] == '-1':
            return

        url = self.makeGetImgUrl(img_name, '', *others)
        if self.makeImgRequest(url, img_name + '.' + others[-1]):
            tkmb.showinfo("Success", f"Successfully wrote to '{img_name}.{others[-1]}'")

    def handleImgByType(self):
        img_type = self.ents['imgType'].get().strip()
        if len(img_type) < 1:
            self.reportError('Image type field must not be empty.')
            return
        
        others = self.getSharedValues()
        if others[0] == '-1':
            return

        url = self.makeGetImgUrl('', img_type, *others)
        if self.makeImgRequest(url, img_type + '.' + others[-1]):
            tkmb.showinfo("Success", f"Successfully wrote to '{img_type}.{others[-1]}'")

    

    def handleGetAllImgsByLoc(self):        
        others = self.getSharedValues()
        if others[0] == '-1':
            return
        
        lng = others[0]
        lat = others[1]
        minDay = others[2]
        ftype = others[-1]

        url = self.makeGetImageJSONUrl(lng, lat, minDay)
        jsonObj = self.makeJSONRequest(url)
        if not jsonObj:
            return
        actImgs = jsonObj['features']
        if len(actImgs) < 1:
            tkmb.showinfo("Success", "No images found.")
        # Make a folder
        folderName = ''
        while True:
            folderName = f'./ImagesLat{lat}Lng{lng}R{random.randint(1,100000)}'
            try:

                os.mkdir(folderName)
            except FileExistsError:
                continue
            break

        numImgs = len(actImgs)
        for idx, img in enumerate(actImgs):
            name = img['properties']['image-name']
            url = self.makeGetImgUrl(name, '', *others)
            if not self.makeImgRequest(url, folderName + '/' + name + '.' + ftype):
                self.batchLab.config(text=f'Quit at {idx + 1} of {numImgs}')
                return
            self.batchLab.config(text=f'{idx + 1} of {numImgs}')
            self.batchLab.update()
        self.batchLab.config(text=f'Finished process')
        self.batchLab.update()
        tkmb.showinfo("Success", f"Successfully wrote {numImgs} images to {folderName}")
            
if __name__ == '__main__':   
    root = tk.Tk()
    root.withdraw()

    dg = TokenEnter(root, title="My Dialog")

    root.wm_deiconify()
    tk.Label(root, text="Quick Caller", font=("times", 36)).pack(side='top', anchor='center')
    
    vg = VexcelGetter(root, dg.result)
    vg.pack()
    
    tk.mainloop()
