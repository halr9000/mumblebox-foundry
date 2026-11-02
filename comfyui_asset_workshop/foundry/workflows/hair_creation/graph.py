"""Native HairDeck templates, with a durable Foundry checkpoint at their boundary."""
import json


def generate(record, variant):
    c = record['config']
    return {
        '70000': {'class_type': 'FoundryLoadCreationImage', 'inputs': {'filename': c['image'], 'sha256': record['source_sha256']}},
        '70001': {'class_type': 'HairDeckLoader', 'inputs': {**c['checkpoints'], 'resources': 'hairdeck'}},
        '70002': {'class_type': 'HairDeckGenerate', 'inputs': {'model': ['70001', 0], 'image': '',
                    'external_image': ['70000', 0], 'transparent_mask': ['70000', 1],
                    'seed': c['seed']+variant, 'steps': c['steps'], 'cfg': c['cfg'], 'generate_bones': c['bones']}},
        '70003': {'class_type': 'FoundryHairCheckpoint', 'inputs': {'result': ['70002', 0], 'creation_id': record['id'], 'variant': variant}}
    }


def export(record, checkpoint):
    return {'70004': {'class_type': 'FoundryHairExport', 'inputs': {'checkpoint': checkpoint,
              'options': json.dumps(record['config'], ensure_ascii=False)}}}
