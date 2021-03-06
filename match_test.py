import torch
from model import ResNet, ResidualBlock, load_model
import random
import numpy as np

from Simulator import Simulator as sim
from utils import coordinates_to_plane, best_shot_parm, get_score
from tqdm import trange, tqdm

import time
from multiprocessing import Pool, freeze_support, RLock

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-M", '--model_file_name', default="zero_final_0")
parser.add_argument("-OP", '--opponent_model_file_name', default=None)
parser.add_argument("-O", '--order', default=0, type=int)


def match(args):
    num_of_game, n, model_file_name, order, opponent = args
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = ResNet(ResidualBlock, [2, 2, 2, 2]).to(device)

    # model_file_name = "zero_final_0"
    load_model(model, model_file_name)

    if opponent is not None:
        model2 = ResNet(ResidualBlock, [2, 2, 2, 2]).to(device)
        load_model(model2, opponent)

    # num_of_game = 1000
    num_of_win = 0
    # order = 0
    p_bar = trange(num_of_game, position=n)
    for i in p_bar:
        state = np.zeros((1, 32))
        for turn in range(8):
            if turn % 2 == order:
                state_plane = coordinates_to_plane(state, turn, order).to(device)

                prob, _ = model(state_plane)
                action = best_shot_parm(prob)
            elif opponent is not None:
                state_plane = coordinates_to_plane(state, turn, (order+1) % 2).to(device)

                prob, _ = model2(state_plane)
                action = best_shot_parm(prob)
            else:
                # action = (2.375, 4.88, random.randint(0, 1))
                action = (random.random() * 4.75, random.random() * 11.28, random.randint(0, 1))

            state = sim.simulate(state, turn, action[0], action[1], action[2], 0.145)[0]
        if get_score(state, order) > 0:
            num_of_win += 1
        p_bar.set_description("%.3f" % (num_of_win/(i+1)))

    return num_of_win / num_of_game


if __name__ == "__main__":
    # 1000: 35.8 -> 20.6
    # '4' is best in my computer
    n_times = 4

    args = parser.parse_args()

    freeze_support()
    s = time.time()

    ns = [[250, x+1, args.model_file_name, args.order, args.opponent_model_file_name] for x in range(4)]
    p = Pool(len(ns), initializer=tqdm.set_lock, initargs=(RLock(),))
    results = p.map(match, ns)
    p.close()
    p.join()

    print("\n" * n_times)
    print(results)
    print("%.3f %%" % (sum(results)/len(results)))
    print("total elapsed time: %.3f" % (time.time() - s))
