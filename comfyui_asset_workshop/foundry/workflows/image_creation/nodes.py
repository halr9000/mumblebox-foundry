"""Native image I/O boundary for the independent creation workflow."""
import json
from pathlib import Path
import folder_paths
import numpy as np
import torch
from PIL import Image, ImageOps
from ...artifacts import owned_path,digest
from .library import identifier


class FoundryLoadCreationImage:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'filename':('STRING',),'sha256':('STRING',)}}
    RETURN_TYPES=('IMAGE','MASK');FUNCTION='load';CATEGORY='Mumblebox Foundry/Images'

    @classmethod
    def path(cls,filename):
        output=filename.endswith(' [output]')
        name=filename[:-9] if output else filename
        root=Path(folder_paths.get_output_directory() if output else folder_paths.get_input_directory())
        return owned_path(root,root/name)

    @classmethod
    def IS_CHANGED(cls,filename,sha256):return digest(cls.path(filename))

    def load(self,filename,sha256):
        path=self.path(filename)
        if not sha256 or digest(path)!=sha256:raise ValueError('The queued reference image changed. Reopen its latest revision.')
        with Image.open(path) as source:
            image=ImageOps.exif_transpose(source).convert('RGBA')
            pixels=torch.from_numpy(np.asarray(image,dtype=np.float32).copy()/255)[None]
        return pixels[...,:3],1-pixels[...,3]


class FoundrySaveCreationImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'image':('IMAGE',),'creation_id':('STRING',),'attempt_id':('STRING',),'recipe':('STRING',)},
                'optional':{f'report{i}':('STRING',{'forceInput':True}) for i in range(1,9)}}
    RETURN_TYPES=('IMAGE',);FUNCTION='save';CATEGORY='Mumblebox Foundry/Images';OUTPUT_NODE=True

    def save(self,image,creation_id,attempt_id,recipe,**reports):
        from ....nodes import save_png
        root=Path(folder_paths.get_output_directory())
        relative=Path('foundry-images')/identifier(creation_id)/(identifier(attempt_id)+'.png')
        path=owned_path(root,root/relative)
        if path.exists():raise ValueError('This generation already has a saved output; recover it instead of overwriting it.')
        details=json.loads(recipe)
        details['lora_validation']=[json.loads(value) for value in reports.values()]
        save_png(image,path,details)
        entry={'filename':path.name,'subfolder':relative.parent.as_posix(),'type':'output'}
        return {'ui':{'images':[entry],'creation_provenance':[details]},'result':(image,)}


NODE_CLASS_MAPPINGS={cls.__name__:cls for cls in (FoundryLoadCreationImage,FoundrySaveCreationImage)}
