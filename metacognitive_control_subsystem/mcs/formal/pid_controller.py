"""
A Proportional-Integral-Derivative (PID) controller.

This module provides a PID controller implementation, a crucial component for
stabilizing the dual variable (Lagrange multiplier) updates in the primal-dual
optimization algorithm. As highlighted in the TDD, a standard integral-only
controller is prone to oscillation and overshoot, which is unacceptable in a
safety-critical system. This PID controller ensures smooth and reliable
convergence to the constraint boundaries.
"""

class PIDController:
    """
    Implements a PID controller for stabilizing a control variable.
    """

    def __init__(self, kp: float, ki: float, kd: float, set_point: float = 0.0):
        """
        Initializes the PID controller.

        Args:
            kp (float): The proportional gain.
            ki (float): The integral gain.
            kd (float): The derivative gain.
            set_point (float): The target value for the system. In the R2A2
                             context, this is the constraint budget 'd_k', so the
                             error is calculated relative to it. Defaults to 0.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.set_point = set_point

        self._previous_error = 0.0
        self._integral = 0.0

    def update(self, process_variable: float) -> float:
        """
        Calculates the control output based on the current process variable.

        Args:
            process_variable (float): The current measured value of the system.
                                      In the R2A2 context, this is the estimated
                                      cost Q_C_k(s, a).

        Returns:
            float: The control output, which will be used to adjust the
                   Lagrange multiplier.
        """
        error = process_variable - self.set_point

        # Proportional term
        p_term = self.kp * error

        # Integral term
        self._integral += error
        i_term = self.ki * self._integral

        # Derivative term
        derivative = error - self._previous_error
        d_term = self.kd * derivative

        # Update state for next iteration
        self._previous_error = error

        # The control output is the sum of the three terms
        return p_term + i_term + d_term

    def reset(self):
        """
        Resets the controller's internal state (integral and previous error).
        """
        self._previous_error = 0.0
        self._integral = 0.0