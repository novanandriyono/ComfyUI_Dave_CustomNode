# Made by Davemane42#0042 for ComfyUI
# 02/04/2023

import torch
from nodes import MAX_RESOLUTION

class MultiAreaConditioning:
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning0": ("CONDITIONING", ),
                "conditioning1": ("CONDITIONING", )
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }
    


    RETURN_TYPES = ("CONDITIONING", "INT", "INT")
    RETURN_NAMES = (None, "resolutionX", "resolutionY")
    FUNCTION = "doStuff"
    CATEGORY = "Davemane42"

    def doStuff(self, extra_pnginfo, unique_id, **kwargs):

        c = []
        values = []
        resolutionX = 512
        resolutionY = 512

        for node in extra_pnginfo["workflow"]["nodes"]:
            if node["id"] == int(unique_id):
                values = node["properties"]["values"]
                resolutionX = node["properties"]["width"]
                resolutionY = node["properties"]["height"]
                break
        k = 0
        for arg in kwargs:
            if k > len(values): break;
            if not torch.is_tensor(kwargs[arg][0][0]): continue;
            
            x, y = values[k][0], values[k][1]
            w, h = values[k][2], values[k][3]

            # If fullscreen
            if (x == 0 and y == 0 and w == resolutionX and h == resolutionY):
                for t in kwargs[arg]:
                    c.append(t)
                k += 1
                continue
            
            if x+w > resolutionX:
                w = max(0, resolutionX-x)
            
            if y+h > resolutionY:
                h = max(0, resolutionY-y)

            if w == 0 or h == 0: continue;

            for t in kwargs[arg]:
                n = [t[0], t[1].copy()]
                n[1]['area'] = (h // 8, w // 8, y // 8, x // 8)
                n[1]['strength'] = values[k][4]
                n[1]['min_sigma'] = 0.0
                n[1]['max_sigma'] = 99.0
                
                c.append(n)
            
            k += 1
            
        
        return (c, resolutionX, resolutionY)

class MultiAreaConditioningV2:
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning0": ("CONDITIONING", ),
                "conditioning1": ("CONDITIONING", )
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("CONDITIONING", "INT", "INT")
    RETURN_NAMES = (None, "resolutionX", "resolutionY")
    FUNCTION = "doStuff"
    CATEGORY = "Davemane42"

    def doStuff(self, extra_pnginfo, unique_id, **kwargs):

        c = []
        values = []
        resolutionX = 512
        resolutionY = 512

        for node in extra_pnginfo["workflow"]["nodes"]:
            if node["id"] == int(unique_id):
                values = node["properties"]["values"]
                resolutionX = node["properties"]["width"]
                resolutionY = node["properties"]["height"]
                break
        k = 0
        for arg in kwargs:
            if k > len(values): break;
            if not torch.is_tensor(kwargs[arg][0][0]): continue;
            
            x, y = values[k][0], values[k][1]
            w, h = values[k][2], values[k][3]

            # If fullscreen
            if (x == 0 and y == 0 and w == resolutionX and h == resolutionY):
                for t in kwargs[arg]:
                    c.append(t)
                k += 1
                continue
            
            if x+w > resolutionX:
                w = max(0, resolutionX-x)
            
            if y+h > resolutionY:
                h = max(0, resolutionY-y)

            if w == 0 or h == 0: continue;

            for t in kwargs[arg]:
                n = [t[0], t[1].copy()]
                n[1]['area'] = (h // 8, w // 8, y // 8, x // 8)
                n[1]['strength'] = values[k][4]
                n[1]['min_sigma'] = 0.0
                n[1]['max_sigma'] = 99.0
                
                shape_type = 0
                if len(values[k]) > 5:
                    shape_type = values[k][5]
                
                rotation = 0
                if len(values[k]) > 6:
                    rotation = values[k][6]
                
                if shape_type > 0 or rotation != 0:
                    mask = torch.zeros((resolutionY, resolutionX), dtype=torch.float32)
                    grid_y, grid_x = torch.meshgrid(torch.arange(resolutionY), torch.arange(resolutionX), indexing='ij')
                    
                    center_x = x + w / 2.0
                    center_y = y + h / 2.0

                    if rotation != 0:
                        import math
                        angle = math.radians(rotation)
                        cos_a = math.cos(angle)
                        sin_a = math.sin(angle)
                        
                        dx = grid_x - center_x
                        dy = grid_y - center_y
                        rot_x = cos_a * dx + sin_a * dy + center_x
                        rot_y = -sin_a * dx + cos_a * dy + center_y
                    else:
                        rot_x = grid_x
                        rot_y = grid_y

                    if shape_type == 1: # circle/oval
                        radius_x = w / 2.0
                        radius_y = h / 2.0
                        dist = ((rot_x - center_x) ** 2) / (radius_x ** 2 + 1e-8) + ((rot_y - center_y) ** 2) / (radius_y ** 2 + 1e-8)
                        mask[dist <= 1.0] = 1.0
                    elif shape_type == 2: # triangle
                        in_bottom = rot_y <= y + h
                        in_top = rot_y >= y
                        in_left = (rot_y - y) >= (h / (w / 2.0 + 1e-8)) * (center_x - rot_x)
                        in_right = (rot_y - y) >= (h / (w / 2.0 + 1e-8)) * (rot_x - center_x)
                        mask[in_bottom & in_top & in_left & in_right] = 1.0
                    else: # rectangle
                        in_bottom = rot_y <= y + h
                        in_top = rot_y >= y
                        in_left = rot_x >= x
                        in_right = rot_x <= x + w
                        mask[in_bottom & in_top & in_left & in_right] = 1.0
                    
                    n[1]['mask'] = mask.unsqueeze(0)
                    n[1]['set_area_to_bounds'] = False
                
                c.append(n)
            
            k += 1
            
        return (c, resolutionX, resolutionY)

class ConditioningUpscale():
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "conditioning": ("CONDITIONING", ),
                "scalar": ("INT", {"default": 2, "min": 1, "max": 100, "step": 0.5}),
            },
        }
    
    RETURN_TYPES = ("CONDITIONING",)
    CATEGORY = "Davemane42"

    FUNCTION = 'upscale'

    def upscale(self, conditioning, scalar):
        c = []
        for t in conditioning:

            n = [t[0], t[1].copy()]
            if 'area' in n[1]:
                
                n[1]['area'] = tuple(map(lambda x: ((x*scalar + 7) >> 3) << 3, n[1]['area']))

            if 'mask' in n[1]:
                import torch.nn.functional as F
                mask = n[1]['mask']
                mask = F.interpolate(mask.unsqueeze(0), scale_factor=scalar, mode="bilinear", align_corners=False).squeeze(0)
                n[1]['mask'] = mask

            c.append(n)

        return (c, )
    
class ConditioningStretch():
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "conditioning": ("CONDITIONING", ),
                "resolutionX": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 64}),
                "resolutionY": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 64}),
                "newWidth": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 64}),
                "newHeight": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 64}),
                #"scalar": ("INT", {"default": 2, "min": 1, "max": 100, "step": 0.5}),
            },
        }
    
    RETURN_TYPES = ("CONDITIONING",)
    CATEGORY = "Davemane42"

    FUNCTION = 'upscale'

    def upscale(self, conditioning, resolutionX, resolutionY, newWidth, newHeight, scalar=1):
        c = []
        for t in conditioning:

            n = [t[0], t[1].copy()]
            if 'area' in n[1]:

                newWidth *= scalar
                newHeight *= scalar
                
                #n[1]['area'] = tuple(map(lambda x: ((x*scalar + 32) >> 6) << 6, n[1]['area']))
                x = ((n[1]['area'][3]*8)*newWidth/resolutionX) // 8
                y = ((n[1]['area'][2]*8)*newHeight/resolutionY) // 8
                w = ((n[1]['area'][1]*8)*newWidth/resolutionX) // 8
                h = ((n[1]['area'][0]*8)*newHeight/resolutionY) // 8

                n[1]['area'] = tuple(map(lambda x: (((int(x) + 7) >> 3) << 3), [h, w, y, x]))

            if 'mask' in n[1]:
                import torch.nn.functional as F
                mask = n[1]['mask']
                mask = F.interpolate(mask.unsqueeze(0), size=(newHeight, newWidth), mode="bilinear", align_corners=False).squeeze(0)
                n[1]['mask'] = mask

            c.append(n)

        return (c, )

class ConditioningDebug():
    def __init__(self) -> None:
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "conditioning": ("CONDITIONING", ),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "debug"

    OUTPUT_NODE = True

    CATEGORY = "Davemane42"

    def debug(self, conditioning):
        print("\nDebug")
        for i, t in enumerate(conditioning):
            print(f"{i}:")
            if "area" in t[1]:
                print(f"\tx{t[1]['area'][3]*8} y{t[1]['area'][2]*8} \n\tw{t[1]['area'][1]*8} h{t[1]['area'][0]*8} \n\tstrength: {t[1]['strength']}")
            else:
                print(f"\tFullscreen")

        return (None, )

