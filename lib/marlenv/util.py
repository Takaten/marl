import os
import numpy as np

class Recorder:
    def __init__(self):
        pass

    def begin_episode(self, record_path, episode):
        raise NotImplementedError

    def record(self, data):
        raise NotImplementedError

    def end_epidose(self):
        raise NotImplementedError

class GoldmineRecorder(Recorder):
    def __init__(self, agent_num):
        self.agent_num = agent_num

    def begin_episode(self, record_path, episode):
        path = record_path + '/episode{:06d}'.format(episode)
        if not os.path.exists(path):
            os.makedirs(path)
        self.task_fp = open(path + '/task.log', 'w')
        self.agent_fp = []
        for i in range(self.agent_num):
            name = path + '/agent{:03d}.log'.format(i)
            self.agent_fp.append(open(name, 'w'))

    def record(self, data):
        for d in data['task']:
            self.task_fp.write(','.join(map(str, d)) + '\n')
        for agfp, d in zip(self.agent_fp, data['agent']):
            agfp.write(','.join(map(str, d)) + '\n')

    def end_episode(self):
        self.task_fp.close()
        for f in self.agent_fp:
            f.close()
