import rospy
import torch

class TL:
    # Size of control vector
    NCTRL = 2

    def __init__(self, params, logger, dtype):
        self.logger = logger
        self.params = params
        self.dtype  = dtype

        self.reset()

    def reset(self):
        self.K = self.params.get_int("K", default=62)
        self.T = self.params.get_int("T", default=15)

        self.min_delta = self.params.get_float("traj_gen/min_delta", default=-0.34)
        self.max_delta = self.params.get_float("traj_gen/max_delta", default=0.34)

        desired_speed = self.params.get_float("traj_gen/desired_speed", default=1.0)
        step_size = (self.max_delta - self.min_delta) / (self.K - 1)
        deltas = torch.arange(
            self.min_delta,
            self.max_delta + step_size,
            step_size)

        # The controls for TL are precomputed, and don't change
        self.ctrls = self.dtype(self.K, self.T, self.NCTRL)
        self.ctrls[:, :, 0] = desired_speed
        for t in range(self.T):
            self.ctrls[:, t, 1] = deltas


    def get_control_trajectories(self):
        '''
          Returns (K, T, NCTRL) vector of controls
            ([:, :, 0] is the desired speed, [:, :, 1] is the control delta)
        '''
        return self.ctrls

    def generate_control(self, controls, costs):
        '''
        Inputs
            controls (K, T, NCTRL tensor): Returned by get_controls
            costs (K, 1) cost to take a path

        Returns
            (T, NCTRL tensor) the lowest cost path
        '''
        assert controls.size() == (self.K, self.T, 2)
        assert costs.size() == (self.K,)
        _, idx = torch.min(costs, 0)
        return controls[idx]