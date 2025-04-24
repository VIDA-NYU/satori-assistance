COFFEE_TASK_PLAN = {
    'desired_task': 'Brewing Pour-Over Coffee', 
    'steps': [
        {'is_start': True, 
        'checkpoints': [
            {'instruction': 'Measure 11g of coffee beans with a scale', 'blip_prompt': 'Do you see coffee beans on a scale?'}
            ], 
            'step_check_prompts': ['Are there coffee beans visible on a scale?'], 
            'content': 'Measure coffee beans using a scale'
        }, 
        {'is_start': False, 
        'checkpoints': [
            {'instruction': 'Put the beans into the grinder', 'blip_prompt': 'Are the coffee beans inside the grinder?'}, 
            {'instruction': 'Grind until they become coffee powder', 'blip_prompt': 'Is the user grinding the coffee with the grinder?'}
            ], 
            'step_check_prompts': ['Is a grinder being used or visible?', 'Is coffee powder visible?'], 
            'content': 'Grind the coffee beans into powder'
        },
        {'is_start': False, 
        'checkpoints': [
            {'instruction': 'Open a cone-like coffee filter and place it in the brewer', 'blip_prompt': 'Is the filter placed inside the brewer?'}],
            'step_check_prompts': ['Is the coffee filter placed inside the brewer?'], 
            'content': 'Open a coffee filter and place it in the brewer'
        }, 
        {'is_start': False, 
        'checkpoints': [
            {'instruction': 'Place the brewer on the cup', 'blip_prompt': 'Is the brewer placed on top of a cup?'}, 
            {'instruction': 'Pour enough water into the filter to wet it', 'blip_prompt': 'Is water visible in the filter?'}, 
            {'instruction': 'Remove any papery residue', 'blip_prompt': 'Is the filter free of residue?'}], 
            'step_check_prompts': ['Is the brewer on top of a cup?', 'Is water being poured into the filter?'], 
            'content': 'Place the brewer on the cup and wet the filter'
            }, 
        {'is_start': False, 
        'checkpoints': [{'instruction': 'Place the coffee powder into the filter', 'blip_prompt': 'Is the coffee powder added to the filter?'}, 
        {'instruction': 'Put the cup and brewer on the scale', 'blip_prompt': 'Is the cup and brewer on the scale?'}, 
        {'instruction': 'Set the scale to zero', 'blip_prompt': 'Is the scale reading zero?'}], 
        'step_check_prompts': ['Is the coffee powder in the filter?'], 
        'content': 'Add coffee powder to the filter, set up the scale'
        },
        {'is_start': False, 
        'checkpoints': [ 
        {'instruction': 'Pour water in a circular motion over the coffee grounds until the scale shows 50g', 'blip_prompt': 'Does the scale display 50g?'}, 
        {'instruction': 'Wait until the timer reaches 30 seconds', 'blip_prompt': 'Has the timer reached 30 seconds?'}], 
        'step_check_prompts': ['Is water being poured over the coffee?'], 
        'content': 'Pour water into coffee ground'
        }], 'objects': ['Coffee Beans', 'Scale', 'Grinder', 'Cone-like Coffee Filter', 'Brewer', 'Cup', 'Water', 'Towel or Cloth', 'Timer']}