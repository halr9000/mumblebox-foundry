---
license: openrail
datasets:
- gvecchio/MatSynth
language:
- en
library_name: diffusers
pipeline_tag: text-to-image
tags:
- material
- pbr
- svbrdf
- 3d
- texture
inference: false
---

# StableMaterials

**StableMaterials** is a diffusion-based model designed for generating photorealistic physical-based rendering (PBR) materials. This model integrates semi-supervised learning with Latent Diffusion Models (LDMs) to produce high-resolution, tileable material maps from text or image prompts. StableMaterials can infer both diffuse (Basecolor) and specular (Roughness, Metallic) properties, as well as the material mesostructure (Height, Normal). 🌟

For more details, visit the [project page](https://gvecchio.com/stablematerials/) or read the full paper on [arXiv](https://arxiv.org/abs/2406.09293).

<center>
    <img src="https://gvecchio.com/stablematerials/static/images/teaser.jpg" style="border-radius:10px;">
</center>

⚠️ This repo contains the weight and the pipeline code for the **base model** in both the LDM and LCM verisons. The refiner model, along with its pipeline and the inpainting pipeline, will be released shortly.

## Model Architecture

<center>
    <img src="https://gvecchio.com/stablematerials/static/images/architecture.png" style="border-radius:10px;">
</center>

### 🧩 Base Model 
The base model generates low-resolution (512x512) material maps using a compression VAE (Variational Autoencoder) followed by a latent diffusion process. The architecture is based on the MatFuse adaptation of the LDM paradigm, optimized for material map generation with a focus on diversity and high visual fidelity. 🖼️

### 🔑 Key Features
- **Semi-Supervised Learning**: The model is trained using both annotated and unannotated data, leveraging adversarial training to distill knowledge from large-scale pretrained image generation models. 📚
- **Knowledge Distillation**: Incorporates unannotated texture samples generated using the SDXL model into the training process, bridging the gap between different data distributions. 🌐
- **Latent Consistency**: Employs a latent consistency model to facilitate fast generation, reducing the inference steps required to produce high-quality outputs. ⚡
- **Feature Rolling**: Introduces a novel tileability technique by rolling feature maps for each convolutional and attention layer in the U-Net architecture. 🎢

## Intended Use

StableMaterials is designed for generating high-quality, realistic PBR materials for applications in computer graphics, such as video game development, architectural visualization, and digital content creation. The model supports both text and image-based prompting, allowing for versatile and intuitive material generation. 🕹️🏛️📸

## 🧑‍💻 Usage

To generate materials using the StableMaterials base model, use the following code snippet:

### Standard model

```python
from diffusers import DiffusionPipeline
from diffusers.utils import load_image

# Load pipeline enabling the execution of custom code
pipe = DiffusionPipeline.from_pretrained(
    "gvecchio/StableMaterials", 
    trust_remote_code=True, 
    torch_dtype=torch.float16
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
pipe = pipe.to(device)

# Text prompt example
material = pipe(
  prompt="Old rusty metal bars with peeling paint",
  guidance_scale=10.0,
  tileable=True,
  num_images_per_prompt=1,
  num_inference_steps=50,
).images[0]

# Image prompt example
material = pipe(
  prompt=load_image("path/to/input_image.jpg"),
  guidance_scale=10.0,
  tileable=True,
  num_images_per_prompt=1,
  num_inference_steps=50,
).images[0]

# The output will include basecolor, normal, height, roughness, and metallic maps
basecolor = material.basecolor
normal = material.normal
height = material.height
roughness = material.roughness
metallic = material.metallic
```

### Consistency model

```python
from diffusers import DiffusionPipeline, LCMScheduler, UNet2DConditionModel
from diffusers.utils import load_image

# Load LCM distilled unet
unet = UNet2DConditionModel.from_pretrained(
    "gvecchio/StableMaterials",
    subfolder="unet_lcm",
    torch_dtype=torch.float16,
)

# Load pipeline enabling the execution of custom code
pipe = DiffusionPipeline.from_pretrained(
    "gvecchio/StableMaterials", 
    trust_remote_code=True, 
    unet=unet,
    torch_dtype=torch.float16
)

# Replace scheduler with LCM scheduler
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
pipe = pipe.to(device)

# Text prompt example
material = pipe(
  prompt="Old rusty metal bars with peeling paint",
  guidance_scale=10.0,
  tileable=True,
  num_images_per_prompt=1,
  num_inference_steps=4, # LCM enables fast generation in as few as 4 steps
).images[0]

# Image prompt example
material = pipe(
  prompt=load_image("path/to/input_image.jpg"),
  guidance_scale=10.0,
  tileable=True,
  num_images_per_prompt=1,
  num_inference_steps=4,
).images[0]

# The output will include basecolor, normal, height, roughness, and metallic maps
basecolor = material.basecolor
normal = material.normal
height = material.height
roughness = material.roughness
metallic = material.metallic
```

## 🗂️ Training Data

The model is trained on a combined dataset from MatSynth and Deschaintre et al., including 6,198 unique PBR materials. It also incorporates 4,000 texture-text pairs generated from the SDXL model using various prompts. 🔍

## 🔧 Limitations

While StableMaterials shows robust performance, it has some limitations:
- It may struggle with complex prompts describing intricate spatial relationships. 🧩
- It may not accurately represent highly detailed patterns or figures. 🎨
- It occasionally generates incorrect reflectance properties for certain material types. ✨

Future updates aim to address these limitations by incorporating more diverse training prompts and improving the model's handling of complex textures.


## 📖 Citation 

If you use this model in your research, please cite the following paper:

```
@article{vecchio2024stablematerials,
  title={StableMaterials: Enhancing Diversity in Material Generation via Semi-Supervised Learning},
  author={Vecchio, Giuseppe},
  journal={arXiv preprint arXiv:2406.09293},
  year={2024}
}
```