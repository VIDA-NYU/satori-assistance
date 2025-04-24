CLEAN_ROOM_TASK_PLAN = {
    'desired_task': 'Clean Room',
    'steps': [
        {
            'is_start': True,
            'checkpoints': [
                {'instruction': 'Connect the mop poles', 'blip_prompt': 'Are the Swiffer mop poles connected?'},
                {'instruction': 'Wrap the pad around the mop head', 'blip_prompt': 'Is the pad wrapped around the mop head?'}
            ],
            'step_check_prompts': ['Is the Swiffer mop fully assembled?'],
            'content': 'Assemble the mop'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Connect the duster handle to the duster head', 'blip_prompt': 'Is the duster handle attached to the duster head?'},
                {'instruction': 'Slide the handle into the duster all the way to the top', 'blip_prompt': 'Is the handle fully inserted into the duster?'}
            ],
            'step_check_prompts': ['Are the duster fully connected?'],
            'content': 'Assemble the Swiffer duster'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Sweep the mop across the floor and use the duster', 'blip_prompt': 'Are the mop and duster being used to clean?'},
            ],
            'step_check_prompts': ['Has the duster and mop been used to clean?'],
            'content': 'Mop the floor thoroughly. Dust the desk thoroughly. Be careful with fragile items.'
        },
    ],
    'objects': ['Swiffer mop', 'Mop poles', 'Mop head', 'Mop pads', 'Duster', 'Duster handle', 'Desk', 'Floor']
}