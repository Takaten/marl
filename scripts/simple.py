from hyperdash import Experiment
from agent.trainer import Trainer
from agent.util import EpsilonExponentialDecay
from marlenv.goldmine.basic import Goldmine
from marlenv.util import GoldmineRecorder
from agent.deepq.simple_dqn import SimpleDQN

name = 'simple'
exp = Experiment(name)

agent_num = 6
task_num = 4
env = Goldmine(agent_num, task_num)
env.seed(0)

params = {
    'name'              : name,
    'episodes'          : 40000,
    'steps'             : 200,
    'no_op_episodes'    : 100,
    'epsilon'           : EpsilonExponentialDecay(init=1.0, rate=0.9998),
    'train_every'       : 1,
    'save_model_every'  : 1000,
    'is_centralized'    : False,

    'agent_num'         : agent_num,
    'env'               : env,
    'action_space'      : env.action_space,
    'observation_space' : env.observation_space,
    'preprocess'        : None,
    'recorder'          : GoldmineRecorder(agent_num),

    'agent': [
        SimpleDQN(
            action_space      = env.action_space,
            observation_space = env.observation_space,
            memory_size       = 10000,
            batch_size        = 32,
            learning_rate     = 0.0002,
            gamma             = 0.99,
            target_update     = 200,
            use_dueling       = False
        ) for _ in range(agent_num)
    ],

    'hyperdash': exp
}

trainer = Trainer(**params)
trainer.train()

exp.end()
