ARRANGE_FLOWERS_TASK_PLAN = {
    'desired_task': 'Arrange Flowers',
    'steps': [
        {
            'is_start': True,
            'checkpoints': [
                {'instruction': 'Open 1/2 bag of flower food', 'blip_prompt': 'Is half a bag of flower food opened?'},
                {'instruction': 'Pour the flower food into the vase', 'blip_prompt': 'Is the flower food being poured into the vase?'}
            ],
            'step_check_prompts': ['Is the flower food in the vase?'],
            'content': 'Pour flower food into the vase.'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Measure 16oz of water', 'blip_prompt': 'Is 16oz of water being measured?'},
                {'instruction': 'Pour the water into the vase', 'blip_prompt': 'Is the water being poured into the vase with flower food?'}
            ],
            'step_check_prompts': ['Is the vase filled with 16oz of water and flower food?'],
            'content': 'Pour water to the vase'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Use the scissors to trim leaves below the waterline to prevent decay', 'blip_prompt': 'Are the leaves being trimmed with scissors?'}
            ],
            'step_check_prompts': ['Have the leaves below the waterline been removed?'],
            'content': 'Trim leaves'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Cut 2-3 inches off the stems with scissors at 45 degree angle', 'blip_prompt': 'Are the flower stems being cut by 2-3 inches?'},
            ],
            'step_check_prompts': ['Have the stems been trimmed?'],
            'content': 'Trim stems'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Arrange the flowers neatly in the vase', 'blip_prompt': 'Are the flowers being arranged neatly?'},
            ],
            'step_check_prompts': ['Are the flowers neatly arranged and properly submerged?'],
            'content': 'Arrange the flowers'
        }
    ],
    'objects': ['Vase', 'Flower food', 'Scissors', 'Water', 'Flowers','Measure cup']
}