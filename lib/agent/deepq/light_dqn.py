from keras.models import Model
from keras.layers import Input, Conv2D, Dense, Flatten, Lambda, concatenate, MaxPooling2D
from keras.optimizers import RMSprop
from agent.deepq.simple_dqn import SimpleDQN

class LightDQN(SimpleDQN):
    def _get_model(self):
        obs_in = Input(shape=self.observation_space, dtype='float32')

        # Light network
        x = Conv2D(8, kernel_size=2, strides=1, padding='same', activation='relu')(obs_in)
        x = Conv2D(16, kernel_size=2, strides=1, padding='same', activation='relu')(x)
        x = Flatten()(x)
        x = Dense(128, activation='relu')(x)

        if self.use_dueling:
            value = Dense(1)(x)
            advantage = Dense(self.action_space, use_bias=False)(x)
            q_vals = Lambda(lambda a: a[0] + (a[1] - K.mean(a[1], keepdims=True)),
                            output_shape=(self.action_space,))([value, advantage])
        else:
            q_vals = Dense(self.action_space)(x)

        model = Model(inputs=obs_in, outputs=q_vals)
        optimizer = RMSprop(lr=self.learning_rate)
        model.compile(loss='mean_squared_error', optimizer=optimizer)

        return model
