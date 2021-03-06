import os
import numpy as np
import tensorflow as tf
from keras.models import Model, load_model
from keras.layers import Input, Conv2D, Dense, Flatten, Lambda, concatenate, MaxPooling2D
from keras.optimizers import RMSprop
from keras.utils import multi_gpu_model
from keras import backend as K

from agent.agent import Agent
from agent.util import Memory

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)
K.set_session(sess)

class CentralizedDQN(Agent):
    def __init__(self, action_space, observation_space, agent_num, memory_size,
                 batch_size, learning_rate, gamma, target_update):
        # parameters
        self.action_space      = action_space
        self.observation_space = observation_space
        self.agent_num         = agent_num
        self.memory_size       = memory_size
        self.batch_size        = batch_size
        self.learning_rate     = learning_rate
        self.gamma             = gamma
        self.target_update     = target_update

        # variables
        self.train_cnt = 0
        self.memory = Memory(memory_size)

        self.target_network = self._get_model()
        self.eval_network   = self._get_model()

    def _get_model(self):
        obs_in = Input(shape=self.observation_space, dtype='float32')
        x = Conv2D(32, kernel_size=8, strides=4, padding='same', activation='relu')(obs_in)
        x = Conv2D(64, kernel_size=4, strides=2, padding='same', activation='relu')(x)
        x = Conv2D(64, kernel_size=3, strides=1, padding='same', activation='relu')(x)
        x = Flatten()(x)
        x = Dense(512, activation='relu')(x)
        q_vals = Dense(self.action_space ** self.agent_num)(x)

        model = Model(inputs=obs_in, outputs=q_vals)
        optimizer = RMSprop(lr=self.learning_rate)

        try:
            model = multi_gpu_model(model, gpus=None)
        except:
            pass

        model.compile(loss='mean_squared_error', optimizer=optimizer)

        return model

    def get_action(self, obs, eps):
        if eps < np.random.uniform(0, 1):
            q_vals = self.eval_network.predict(np.expand_dims(obs, axis=0), batch_size=1)
            max_q = np.argmax(q_vals)
            actions = []
            for i in range(self.agent_num):
                actions.append(max_q % self.action_space)
                max_q //= self.action_space
        else:
            actions = np.random.randint(self.action_space, size=self.agent_num)

        return actions

    def train(self):
        batch_obs, batch_action, batch_reward, batch_nobs = self.memory.sample(self.batch_size)
        batch_target = self._calc_target(batch_obs, batch_action, batch_reward, batch_nobs)
        loss = self.eval_network.train_on_batch(batch_obs, batch_target)

        self.train_cnt += 1
        if self.train_cnt % self.target_update == 0:
            self._update_target()

        return loss

    def _calc_target(self, batch_obs, batch_action, batch_reward, batch_nobs):
        target_q_vals = self.target_network.predict(batch_nobs, batch_size=self.batch_size)
        eval_q_vals = self.eval_network.predict(batch_nobs, batch_size=self.batch_size)

        targets = self.target_network.predict(batch_obs, batch_size=self.batch_size)

        next_val = target_q_vals[np.arange(self.batch_size), np.argmax(eval_q_vals, axis=1)]
        next_val = batch_reward.sum(axis=1) + self.gamma * next_val

        mul = np.array([x ** self.action_space for x in range(self.agent_num)])
        joint_action = (batch_action * mul).sum(axis=1)

        targets[np.arange(self.batch_size), joint_action] = next_val

        return targets

    def _update_target(self):
        self.target_network.set_weights(self.eval_network.get_weights())

    def save(self, path, episode):
        if not os.path.exists(path):
            os.makedirs(path)
        self.target_network.save(path + '/target_network_{:06d}'.format(episode) + '.h5')
        self.eval_network.save(path + '/eval_network_{:06d}'.format(episode) + '.h5')

    def load(self, path, episode):
        self.target_network = load_model(path + '/target_network_{:06d}'.format(episode) + '.h5')
        self.eval_network = load_model(path + '/eval_network_{:06d}'.format(episode) + '.h5')
