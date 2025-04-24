from dataclasses import dataclass, field



@dataclass
class FuzzyState:
    UNSTARTED = "UNSTARTED"
    REACHED = "REACHED"
    FINISHED = "FINISHED"
    
    value: any  # The actual value (could be index, ID, etc.)
    confidence: float  # Confidence level (0.0 to 1.0)
    permanent: bool = False  # If True, the value is locked and won't be updated
    threshold: float = 0.5  # Threshold for locking the value
    finish_threshold: float = 0.2
    state: str = field(default=UNSTARTED)

    
    def update_confidence(self, new_confidence):
        """
        Update the confidence of the state. If the confidence exceeds the threshold,
        lock the state as permanent.
        """
        if not self.permanent:
            self.confidence = new_confidence
            if new_confidence >= self.threshold:
                self.permanent = True  # Lock the value as permanent
                self.state = FuzzyState.REACHED
            
        else:
            if new_confidence < self.finish_threshold and self.state == FuzzyState.REACHED:
                self.state = FuzzyState.FINISHED
            
            

    def is_permanent(self):
        """
        Check if the state is permanent.
        """
        return self.permanent

    def get_confident_prediction(self):
        return self.permanent
    
    def is_done(self):
        return self.state == FuzzyState.FINISHED
    
    def is_processing(self):
        return self.state == FuzzyState.REACHED
    
    def force_set_state(self, new_state):
        if new_state == FuzzyState.FINISHED:
            self.state = FuzzyState.FINISHED
            self.permanent = True
            self.confidence = self.finish_threshold - 0.01
        elif new_state == FuzzyState.REACHED:
            self.state = FuzzyState.REACHED
            self.permanent = True
            self.confidence = 1.0
        else:
            self.state = FuzzyState.UNSTARTED
            self.permanent = False
            self.confidence = 0.0
        return self.state