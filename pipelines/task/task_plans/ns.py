CONNECT_SWITCH_TASK_PLAN = {
    'desired_task': 'Connect Switch',
    'steps': [
        {
            'is_start': True,
            'checkpoints': [
                {'instruction': 'Connect HDMI port to the switch dock', 'blip_prompt': 'Is the HDMI cable connected to the switch dock?'},
                {'instruction': 'Connect the power cable to the switch dock and AC outlet', 'blip_prompt': 'Is the power cable plugged into the switch dock and AC outlet?'}
            ],
            'step_check_prompts': ['Is the HDMI cable and power cable properly connected to the switch dock?'],
            'content': 'Connect the HDMI cable between the monitor and the switch dock. Connect the power cable to the switch dock and an AC outlet'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Insert the Switch into the dock securely', 'blip_prompt': 'Is the Switch securely inserted into the dock?'}
            ],
            'step_check_prompts': ['Is the Switch properly docked?'],
            'content': 'Insert the Switch into the dock'
        },
        {
            'is_start': False,
            'checkpoints': [
                {'instruction': 'Press the power button to turn on the monitor', 'blip_prompt': 'Is the monitor powering on?'},
                {'instruction': 'Press the power button to turn on the Switch', 'blip_prompt': 'Is the Switch powering on and displaying on the monitor?'}
            ],
            'step_check_prompts': ['Is the Switch powered on and displaying on the monitor?'],
            'content': 'Power on the monitor and the Switch'
        },
    ],
    'objects': ['HDMI cable', 'Power cable', 'Monitor', 'Switch dock', 'Switch', 'AC outlet']
}