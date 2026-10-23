from comfy_api.latest import ComfyExtension

from .nodes import AssetImage, LoadAssetImage, AssetMaster, LoadAssetMaster, AssetExport, PixalViewSet
from .nodes import ModelBudget, PrepareView, FinishPreparation, AssetScale, VerifiedModelLoRA
from .nodes import AssetDraft, LoadAssetDraft, AssetGuide, SourceFOV
from .nodes import SDXLCheckpoint, SDXLModelLoRA
from . import routes

WEB_DIRECTORY = "./web"


class AssetWorkshopExtension(ComfyExtension):
    async def get_node_list(self):
        return [AssetImage, LoadAssetImage, AssetMaster, LoadAssetMaster, AssetExport,
                PixalViewSet, ModelBudget, PrepareView, FinishPreparation, AssetScale, VerifiedModelLoRA,
                AssetDraft, LoadAssetDraft, AssetGuide, SourceFOV, SDXLCheckpoint, SDXLModelLoRA]


async def comfy_entrypoint():
    return AssetWorkshopExtension()
