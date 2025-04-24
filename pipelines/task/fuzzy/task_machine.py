import numpy as np
from collections import deque
from .state import FuzzyState
import imageio


class FuzzyTaskMachine:
    def __init__(self, task_schema, window_size=4, threshold=0.6, alpha=0.2, allow_self_step_change=True):
        self.task_schema = task_schema
        for i, step in enumerate(self.task_schema['steps']):
            step['step_index'] = i
            self.task_schema['steps'][i] = step 
        self.steps = {i: step for i, step in enumerate(task_schema['steps'])}  # Step by index
        self.window_size = window_size
        self.alpha = alpha

        # Initialize states using FuzzyState
        self.current_step_state = FuzzyState(value=None, confidence=1.0, threshold=threshold)  # Current step
        self.current_checkpoint_states = {}  # Manage checkpoint states as FuzzyState instances
        self.current_step_index = 0
        # Initialize buffers for each checkpoint within the current step
        self.checkpoint_buffers = {}  # Buffers for each checkpoint
        self.in_step_buffer = deque(maxlen=self.window_size)  
        self.setup_initial_state()
        self.initialized = False
        self.allow_self_step_change = allow_self_step_change
        self.in_transition = False
        self.task_state = "UNSTARTED" # Possible options: "IN_STEP", "IN_TRANSITION", "DETACHED", "FINISHED" , "UNSTARTED", "INITIAL_TRANSITION"

    def print_states(self):
        print("step states:", self.current_step_state)
        print("ckpt states:", self.current_checkpoint_states)

    def setup_initial_state(self):
        # Initialize step and checkpoint states
        for i, step in enumerate(self.task_schema['steps']):
            if step['is_start']:
                self.current_step_state.value = True
                self.initialize_checkpoints(i)
                break

    def initialize_checkpoints(self, step_index):
        """
        Initialize checkpoints for the given step.
        """
        if step_index in self.steps:
            step = self.steps[step_index]
            self.current_checkpoint_states = {
                idx: FuzzyState(value="checkpoint-{}".format(idx), confidence=0.0, threshold=0.45)  # Set threshold for checkpoint permanence
                for idx in range(len(step['checkpoints']))
            }
            self.checkpoint_buffers = {
                idx: deque(maxlen=self.window_size) for idx in range(len(step['checkpoints']))
            }

    def add_frame(self, frame_data):
        """
        Add a frame's data to the buffer for all checkpoints in the current step.
        frame_data format: {
            "checkpoint_predictions": [True, False, ...],  # Predictions for each checkpoint
            "in_step": number  # Index for the step
        }
        """
        # Ensure the frame is for the current step
        # if frame_data["in_step"] == self.current_step_state.value:
            # Add frame data to each checkpoint buffer
        for idx, prediction in enumerate(frame_data['checkpoint_predictions']):
            if idx in self.checkpoint_buffers:
                self.checkpoint_buffers[idx].append({'checkpoint_reached': prediction['value'] * prediction['confidence']})
                
        in_step_pred = frame_data.get('in_step', {"value": 0, "confidence": 0})
        self.in_step_buffer.append(in_step_pred['value'] * in_step_pred['confidence'])
        
    def calculate_checkpoint_confidence(self, checkpoint_index):
        """
        Calculate the confidence for a given checkpoint based on the buffer of frames.
        Considers both the ratio of True/False values and the number of frames.
        """
        buffer = self.checkpoint_buffers[checkpoint_index]
        frame_count = len(buffer)
        if frame_count == 0:
            return 0.0  # No frames to base confidence on

        # Calculate the True/False ratio for checkpoint reached
        true_count_checkpoint = sum(1 for frame in buffer if frame['checkpoint_reached'])
        ratio_checkpoint = true_count_checkpoint / frame_count
        if buffer[-1]['checkpoint_reached'] > 0.999:
            return 1.
        # Calculate the confidence considering both the ratio and the number of frames
        confidence_checkpoint = ratio_checkpoint * (1 - np.exp(-self.alpha * frame_count))
        return confidence_checkpoint

    def update_checkpoint_confidences(self):
        """
        Update confidences for all checkpoints in the current step.
        """
        for checkpoint_index, fuzzy_state in self.current_checkpoint_states.items():
            if not fuzzy_state.is_permanent():  # Only update if not permanent
                confidence = self.calculate_checkpoint_confidence(checkpoint_index)
                fuzzy_state.update_confidence(confidence)

    def calculate_step_confidence(self):
        """
        Calculate the confidence that the current step is not finished.
        This is based on the 'in_step_buffer' values and the number of frames used.
        """
        frame_count = len(self.in_step_buffer)
        if frame_count == 0:
            return 0.0  # No frames to base confidence on

        # Calculate the mean of in_step_prediction values
        mean_in_step_prediction = np.mean(self.in_step_buffer)

        # Calculate the confidence considering both the mean prediction and the number of frames
        confidence_not_finished = mean_in_step_prediction * (1 - np.exp(-self.alpha * frame_count))

        # Ensure confidence is within the range [0, 1]
        confidence_not_finished = max(0.0, min(confidence_not_finished, 1.0))
        
        if self.in_step_buffer[-1] > 0.999:
            confidence_not_finished = 1.
        
        return confidence_not_finished

 
    def update_checkpoint_confidences(self):
        """
        Update confidences for all checkpoints in the current step.
        """
        for checkpoint_index, fuzzy_state in self.current_checkpoint_states.items():
            # if not fuzzy_state.is_permanent():  # Only update if not permanent
            confidence = self.calculate_checkpoint_confidence(checkpoint_index)
            fuzzy_state.update_confidence(confidence)

    def get_current_step_desc(self):
        return self.task_schema[self.current_step_index]['content']
    
    # def calculate_step_confidence(self):
    #     """
    #     Calculate the confidence that the current step is not finished.
    #     This is based on the confidence that each checkpoint within the step is not reached.
    #     """
    #     if not self.current_checkpoint_states:
    #         return 0.0

    #     # Compute confidence that the step is not finished as 1 - average confidence of checkpoints reached
    #     total_confidence_reached = np.mean([
    #         checkpoint.confidence for checkpoint in self.current_checkpoint_states.values()
    #     ])
    #     confidence_not_finished = 1 - total_confidence_reached
    #     return confidence_not_finished

    def update_step_state(self):
        """
        Update the state of the current step based on checkpoint confidences.
        """
        self.update_checkpoint_confidences()  # Update checkpoint states first
        step_confidence = self.calculate_step_confidence()
        self.current_step_state.update_confidence(step_confidence)
        # step_change = self.get_next_step()
        step_change = self.finish_step()
        self.print_states()
        return {
            "step_change": step_change
        }

    def test_step_finish(self):
        n_checkpoint_reached = 0
        last_reached = False
        for checkpoint_i, checkpoint_state in self.current_checkpoint_states.items():
            if checkpoint_state.is_done():
                n_checkpoint_reached += 1
                last_reached = True
            else:
                last_reached = False
        # print(n_checkpoint_reached, len(list(self.current_checkpoint_states.keys())), last_reached, self.current_step_state.is_done())
        if self.current_step_state.is_done():
            for checkpoint_i, checkpoint_state in self.current_checkpoint_states.items():
                checkpoint_state.force_set_state(FuzzyState.FINISHED)
        return (n_checkpoint_reached / len(list(self.current_checkpoint_states.keys())) > 0.8 and last_reached) or self.current_step_state.is_done()
    
    def validate_next_step(self):
        if not self.is_initialized_and_first_transitioned():
            return True, 0
        current_step_index = self.current_step_index
        next_step_index = current_step_index + 1
        if next_step_index == len(self.task_schema['steps']):
            return False, current_step_index
        else:
            return True, next_step_index
    
    def finish_step(self, force=False):
        if self.current_step_index == len(self.task_schema['steps']) - 1:
            return False
        if (self.test_step_finish() and self.allow_self_step_change) or force:
            # print("====================================")
            # print("")
            # print("Step finished !!!")
            # print("")
            # print("Transiting to next step !!!")
            # print("====================================")
            # self.in_transition = True
            self.task_state = "IN_TRANSITION"
            return True
        elif self.task_state == "IN_TRANSITION":
            return True 
        else:
            return False
    def finish_transition(self, force=False):
        print()
        print()
        print("GOING TO FINISH!!", self.task_state)
        if self.task_state == "IN_TRANSITION" or self.task_state == "INITIAL_TRANSITION":
            flag, next_step_index = self.validate_next_step()
            print("ft", flag, next_step_index)
            if flag:
                self.current_step_state = FuzzyState(value='step-{}'.format(next_step_index), confidence=0., threshold=self.current_step_state.threshold)  # Reset confidence for new step
                self.initialize_checkpoints(next_step_index)  # Initialize checkpoints for the new step
                self.current_step_index = next_step_index
                print("Finish transition !!!", self.current_step_index)
                # self.in_transition = False
                self.task_state = "IN_STEP"
            return True
        return False
    
    def decline_next_step(self):
        self.task_state = "DETACHED"
    
    def reset_step_state(self):
        self.current_step_state = FuzzyState(value='step-{}'.format(self.current_step_index), confidence=0., threshold=self.current_step_state.threshold)
        self.initialize_checkpoints(self.current_step_index)
    
    
    def get_next_step(self, force=False):
        """
        Determine if the current step is finished and get the next step if so.
        """
        
        if (self.test_step_finish() and self.allow_self_step_change) or force:
            
            print("====================================")
            print("")
            print("Step finished !!!")
            print("")
            print("Go to next step !!!")
            print("====================================")
            # Transition to the next step if the step is permanent or the confidence that the step is not finished is below the threshold
            current_step_index = self.current_step_index
            next_step_index = current_step_index + 1
            if next_step_index == len(self.task_schema['steps']):
                return False 
            # Initialize checkpoints for the new step
            self.current_step_state = FuzzyState(value=True, confidence=0., threshold=self.current_step_state.threshold)  # Reset confidence for new step
            self.initialize_checkpoints(next_step_index) 
            self.current_step_index = next_step_index
            print("Go to next step !!!", self.current_step_index)
            return True 
        return False 

    def is_task_complete(self):
        """
        Define task completion condition.
        """
        return self.current_step_state.value is None


    def save_frames_to_gif(self, frames, output_path, fps=10):
        """
        Save a series of frames to a GIF file.

        Args:
            frames (np.ndarray): NumPy array of shape [len, height, width, channel].
            output_path (str): Path to save the output GIF file.
            fps (int): Frames per second for the GIF.
        """
        # Convert NumPy array to list of images
        frames_list = [frame for frame in frames]

        # Save frames as GIF
        imageio.mimsave(output_path, frames_list, format='GIF', fps=fps)

    def initialize(self):
        if self.task_state == "UNSTARTED":
            self.task_state = "INITIAL_TRANSITION"
        # self.task_state = "IN_STEP"
        self.initialized = True
    
    def is_initialized(self):
        return self.task_state != "UNSTARTED"

    def is_initialized_and_first_transitioned(self):
        return self.task_state not in ["UNSTARTED", "INITIAL_TRANSITION"]
    
    def get_next_action(self):
        if not self.initialized:
            return self.task_schema['steps'][self.current_step_index]
        elif self.current_step_index < len(self.task_schema['steps']) - 1:
            return self.task_schema['steps'][self.current_step_index + 1]
        else:
            return {
                "checkpoints": [],
                "content": "finished"
            }
    def get_next_action_id(self):
        if not self.is_initialized_and_first_transitioned():
            return self.current_step_index
        elif self.current_step_index < len(self.task_schema['steps']) - 1:
            return self.current_step_index + 1
        else:
            return self.current_step_index
    def get_current_step_id(self):
        return self.current_step_index
    
    def get_current_step(self):
        return self.task_schema['steps'][self.current_step_index]
    
    def force_set_checkpoint_state(self, checkpoint_id, force_state):
        self.current_checkpoint_states[checkpoint_id].force_set_state(force_state)
    
    def force_go_prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.current_step_state = FuzzyState(value='step-{}'.format(self.current_step_index), confidence=0., threshold=self.current_step_state.threshold)
            self.initialize_checkpoints(self.current_step_index)
            return True
        return False
    
    def get_guidance_step_index(self):
        return self.get_next_action_id()
        if self.task_state == "IN_TRANSITION":
            return self.get_next_action_id()
        return self.current_step_index    
    def is_in_step(self):
        return self.task_state == "IN_STEP"
    
    def is_in_transitioning(self):
        return False
        return self.task_state == "IN_TRANSITION" or self.task_state == "INITIAL_TRANSITION"