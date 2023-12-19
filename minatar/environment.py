################################################################################################################
# Authors:                                                                                                     #
# Kenny Young (kjyoung@ualberta.ca)                                                                            #
# Tian Tian (ttian@ualberta.ca)                                                                                #
################################################################################################################
from importlib import import_module
import numpy as np

from gym.spaces import Discrete, Box
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#####################################################################################################################
# Environment
#
# Wrapper for all the specific game environments. Imports the environment specified by the user and then acts as a
# minimal interface. Also defines code for displaying the environment for a human user. 
#
#####################################################################################################################
class Environment:
    def __init__(self, env_name, sticky_action_prob = 0.1, difficulty_ramping = True, random_seed = None):
        env_module = import_module('minatar.environments.'+env_name)
        self.random = np.random.RandomState(random_seed)
        self.env_name = env_name
        self.env = env_module.Env(ramping = difficulty_ramping, random_state = self.random)
        self.n_channels = self.env.state_shape()[2]
        self.sticky_action_prob = sticky_action_prob
        self.last_action = 0
        self.visualized = False
        self.closed = False

        self.action_space = Discrete(self.num_actions())
        self.observation_space = Box(low=0, high=1, shape=(len(self.env.channels), 10, 10),dtype=bool)
        #self.observation_space = Box(low=0, high=1, shape=(10,10,len(self.env.channels)),dtype=bool)
        self.reward_range = (-float("inf"), float("inf"))
        self.metadata = {"render.modes": []}

    # Wrapper for env.act
    def act(self, a):
        if(self.random.rand()<self.sticky_action_prob):
            a = self.last_action
        self.last_action = a
        return self.env.act(a)

    # Wrapper for env.state
    def state(self):
        return self.get_state(self.env.state())

    # Wrapper for env.reset
    def reset(self):
        #return self.get_state(self.env.reset())
        return self.env.reset()

    # Wrapper for env.state_shape
    def state_shape(self):
        return self.env.state_shape()

    # All MinAtar environments have 6 actions
    def num_actions(self):
        return 6

    # Name of the MinAtar game associated with this environment
    def game_name(self):
        return self.env_name

    # Wrapper for env.minimal_action_set
    def minimal_action_set(self):
        return self.env.minimal_action_set()

    # Display the current environment state for time milliseconds using matplotlib
    def display_state(self, time=50):
        if(not self.visualized):
            global plt
            global colors
            global sns
            mpl = __import__('matplotlib.pyplot', globals(), locals())
            plt = mpl.pyplot
            mpl = __import__('matplotlib.colors', globals(), locals())
            colors = mpl.colors
            sns = __import__('seaborn', globals(), locals())
            self.cmap = sns.color_palette("cubehelix", self.n_channels)
            self.cmap.insert(0,(0,0,0))
            self.cmap=colors.ListedColormap(self.cmap)
            bounds = [i for i in range(self.n_channels+2)]
            self.norm = colors.BoundaryNorm(bounds, self.n_channels+1)
            _, self.ax = plt.subplots(1,1)
            plt.show(block=False)
            self.visualized = True
        if(self.closed):
            _, self.ax = plt.subplots(1,1)
            plt.show(block=False)
            self.closed = False
        state = self.env.state()
        numerical_state = np.amax(state*np.reshape(np.arange(self.n_channels)+1,(1,1,-1)),2)+0.5
        self.ax.imshow(numerical_state, cmap=self.cmap, norm=self.norm, interpolation='none')
        plt.pause(time/1000)
        plt.cla()

    def close_display(self):
        plt.close()
        self.closed = True

    # @0821 Ho
    @property
    def unwrapped(self):
        return self

    def seed(self, random_seed):
        self.random = np.random.RandomState(random_seed)

    def close(self):
        pass

    def get_state(self, s):
        return torch.tensor(s).permute(2, 0, 1).float()
        #return torch.tensor(s).permute(2, 0, 1).unsqueeze(0).float()
        #return (torch.tensor(s, device=device).permute(2, 0, 1)).unsqueeze(0).float()

    def step(self, action):
        reward, done = self.act(action)
        #next_state = self.get_state(self.state())
        next_state = self.state()

        #return next_state, torch.tensor([[reward]], device=device).float(), torch.tensor([[done]], device=device), {}
        #return next_state, torch.tensor([[reward]]).float(), torch.tensor([[done]]), {}
        return next_state, reward, done, {}

    #Define action space & observation space