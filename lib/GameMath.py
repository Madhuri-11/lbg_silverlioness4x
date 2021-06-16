"""
Filename: GameMath.py
Description: This file contains configuration for the Game designed and developed as per Game Document
All kind of variable and method declaration are performed here
created date : 07/04/21
# author: Anish Sharma
# Ref math : Silver Lioness 4x 96.15% for Konami.xlsx

"""
# imported RequestError python file  in order to check invalid data request from frontEnd
from games.libs.server.RequestError import RequestError


class GameMath:
    def __init__(self):
        # supported game RTP's
        self.rtp = {
            "96": 0.9615
        }

        self.sd = 5.89

        self.variant = None

        self.version = "2.2"

        self.reel_layout = [4, 4, 4, 4, 4]

        self.base_cost = 40

        self.ways = 1024

        self.wilds = [0,13]

        self.paytable = {
            "0":  [0, 0,    0,      0,    0],
            "1":  [0, 1.25, 3.75,   5,    6.25],
            "2":  [0, 0.5,  2,      3.75, 5],
            "3":  [0, 0.5,  2,      3.75, 5],
            "4":  [0, 0.25, 1,      2.5,  3.5],
            "5":  [0, 0.25, 1,      2.5,  3.5],
            "6":  [0, 0,    0.25,   1.25, 3.25],
            "7":  [0, 0,    0.25,   1.25, 3.25],
            "8":  [0, 0,    0.125,  1,    2.75],
            "9":  [0, 0,    0.125,  1,    2.75],
            "10": [0, 0,    0.125,  0.5,  2.5],
            "11": [0, 0,    0.125, 0.5,   2.5],
            "13": [0, 0,    0,      0,    0],
            "15": [0, 0,    0,      0,      0],
            "16": [0, 0,    0,      0,      0],
            "17": [0, 0,    0,      0,      0],

        }
        # scatter
        self.scatters = {
            "12": {
                "base": {
                    "min": 3,
                    "trigger": "freespin",
                    "pay": [0, 0, 2, 10, 20],
                }
                ,
                "freespin": {
                    "min": 2,
                    "trigger": "freespin",
                    "pay": [0, 0, 2, 10, 20]
                }
            }
        }

        # free spin count
        self.freespins = {
            "base": {
                "spins": [8, 15, 20],
            }
            ,
            "freespin": {
                "spins": [5, 8, 15, 20]
            }
        }
        self.wild_sym_lst = {
            2:15, # multiplier associated with the symbol id as per client request
            3:16,
            4:17
        }
        # free spin multiplier ( Reel id mapped with possible available multipliers)
        self.freespin_multiplier = {
            '1': [
                [1, 2],
                [1, 4],
            ],
            '2': [
                [1, 2],
                [1, 3]
            ],
            '3': [
                [1, 2],
                [1, 3]
            ],

        }

        self.reels = {
            "base": {
                "96": [
                    [
                        1, 1, 1, 10, 7, 10, 2, 6, 7, 10, 3, 10, 6, 7, 4, 10, 8, 6, 2, 6, 11, 10, 5, 9, 10, 6, 3, 6,
                        11, 10, 5, 11, 11, 11, 12, 6, 11, 6, 5, 6, 10, 1, 1, 1, 10, 7, 10, 2, 6, 7, 10, 3, 10, 6, 7,
                        4, 10, 8, 6, 2, 6, 11, 10, 5, 9, 10, 6, 3, 6, 11, 10, 5, 11, 11, 5, 6, 11, 6, 5, 6, 10
                    ],
                    [
                        0, 9, 8, 9, 4, 9, 8, 1, 8, 7, 8, 12, 4, 11, 9, 8, 3, 9, 1, 8, 11, 4, 9, 4, 8, 2, 11, 10, 11, 3,
                        11,
                        8, 9, 4, 6, 8, 9, 0, 9, 8, 9, 4, 9, 8, 1, 4, 8, 7, 12, 5, 8, 9, 8, 4, 9, 1, 8, 10, 4, 11, 4, 8,
                        2,
                        11, 9, 11, 3, 11, 8, 9, 4, 6, 8, 9],
                    [
                        0, 10, 10, 8, 2, 9, 5, 5, 10, 3, 8, 2, 2, 9, 5, 10, 4, 6, 10, 8, 4, 4, 7, 10, 12, 8, 2, 6, 10,
                        11,
                        1, 10, 5, 8, 10, 0, 10, 10, 8, 2, 9, 5, 5, 10, 3, 8, 2, 2, 10, 5, 10, 4, 6, 10, 8, 4, 4, 7, 10,
                        8,
                        2, 6, 10, 11, 1, 10, 5, 8, 10],
                    [
                        0, 9, 7, 7, 3, 9, 3, 7, 4, 9, 9, 12, 8, 3, 3, 9, 10, 7, 1, 9, 1, 6, 3, 9, 1, 7, 5, 9, 7, 2, 7,
                        5,
                        7, 3, 11, 9, 5, 5, 7, 9, 0, 9, 7, 7, 3, 9, 3, 7, 4, 9, 9, 8, 3, 3, 9, 10, 7, 1, 9, 1, 11, 3, 9,
                        1,
                        7, 5, 9, 7, 2, 7, 5, 7, 3, 11, 9, 5, 5, 7, 9],
                    [
                        1, 11, 7, 2, 8, 11, 3, 9, 6, 4, 7, 6, 5, 11, 4, 8, 7, 1, 10, 11, 2, 8, 3, 6, 12, 6, 4, 11, 12,
                        8,
                        3, 6, 11, 12, 11, 3, 7, 6, 12, 11, 2, 6, 4, 6]
                ]
            },

            "freespin":{
                "96": [
                [
                    7, 8, 9, 7, 8, 1, 9, 8, 7, 7, 9, 2, 7, 9, 12, 9, 8, 7, 1, 8, 7, 9, 5, 9, 8, 10, 1, 9, 7, 9, 8, 1, 9, 7,
                 9, 8, 9, 9, 1,
                 7, 3, 8, 7, 11, 4, 9, 11, 8, 9, 1, 7, 8, 6, 8, 9, 1, 7, 8, 7, 7, 8, 1, 9, 7, 8, 7, 8, 1, 9, 8, 2, 8, 9,
                 9, 2, 2, 7, 9,
                 7, 1, 7, 8, 9, 1, 7, 8, 7, 7, 8, 1, 9, 7, 12, 8, 9, 8, 7, 8, 1, 9, 8, ],
                [
                    3, 3, 5, 10, 5, 7, 3, 6, 11, 8, 2, 8, 5, 5, 10, 12, 6, 5, 8, 6, 5, 10, 13, 6, 5, 5, 10, 6, 6, 5, 10, 6,
                 5, 10, 5, 10,
                 12, 6, 10, 10, 5, 6, 10, 10, 6, 5, 10, 10, 6, 10, 5, 10, 13, 6, 5, 11, 5, 6, 10, 6, 3, 2, 6, 10, 6, 10,
                 5, 6, 10, 6,
                 10, 4, 10, 6, 6, 1, 1, 9, 6, 3, 1, ],
                [
                    11, 4, 10, 11, 13, 10, 10, 4, 11, 10, 11, 4, 10, 9, 10, 12, 10, 8, 4, 10, 4, 10, 11, 9, 1, 8, 10, 10,
                 4, 11, 10, 11, 4,
                 10, 9, 10, 9, 12, 10, 8, 4, 10, 4, 10, 4, 4, 8, 10, 10, 4, 10, 9, 13, 10, 11, 4, 10, 4, 4, 11, 10, 11,
                 4, 11, 10, 12,
                 4, 8, 8, 9, 3, 11, 7, 4, 11, 13, 9, 11, 4, 11, 9, 5, 6, 11, 10, 4, 11, 9, 11, 1, 11, 1, 10, 9, 11, 4,
                 10, 11, 11, 2,
                 10, 4, 11, 12, 3, 4, 11, 9, 10, 4, 9, 11, ],
                [
                    11, 7, 11, 12, 11, 11, 8, 11, 11, 10, 10, 13, 11, 5, 4, 3, 11, 11, 3, 12, 11, 3, 3, 11, 11, 10, 10, 11,
                 13, 10, 10, 11,
                 3, 6, 10, 11, 11, 6, 9, 13, 11, 6, 6, 10, 11, 6, 13, 6, 6, 10, 10, 6, 10, 6, 6, 6, 11, 3, 7, 2, 8, 1,
                 1, 10, 6, 10, 8,
                 7, 10, 8, 1, 1, 10, 8, 10, 7, 1, 1, 10, 7, 10, ],
                [
                    5, 6, 3, 4, 5, 10, 4, 6, 5, 4, 4, 6, 6, 4, 5, 4, 3, 4, 5, 4, 3, 12, 4, 3, 3, 3, 5, 4, 3, 3, 5, 5, 4, 3,
                 1, 1, 5, 6, 4,
                 3, 5, 5, 4, 3, 5, 4, 3, 5, 5, 4, 6, 5, 11, 4, 3, 5, 12, 5, 3, 5, 9, 4, 5, 5, 4, 5, 3, 7, 1, 1, 1, 6, 5,
                 3, 1, 1, 1, 3,
                 1, 1, 1, 2, 1, 1, 5, 8, 1, 1, 3, 5, 6, 1, 1, 3, 4, 5, ]]
            }
        }

    def set_variant(self, variant):
        if self.rtp.get(variant) is None:
            raise RequestError("Invalid Variant")

        self.variant = variant

    def get_paytable(self):
        return self.paytable

    def get_reels(self, state):
        """
        get reels for playable variant and state
        :param state:
        :return:
        """
        return self.reels[state][self.variant]


    def get_num_ways(self):
        return self.ways

    def get_base_cost(self):
        return self.base_cost

    def get_rtp(self, variant=None):
        if variant is None:
            variant = self.variant

        return self.rtp[variant], self.sd

    def get_wilds(self):
        return self.wilds

    def get_scatter(self, game_type):
        """
        function to get the scatter properties
        :return:
        """
        return {"12": self.scatters["12"][game_type]}

    def get_scatter_pays(self, game_type, index):
        """
        function to get the number of credits that will be paid based on the number of scatter symbols occured
        :param index:
        :return:
        """
        return self.scatters["12"][game_type]["pay"][index]

    def get_spins(self, game_type, scatter_count):
        """
        function to get the number of freespins earned for the respective scatter counts
        :param scatter_count:
        :return:
        """
        spin_index = scatter_count - self.scatters["12"][game_type]["min"]

        return self.freespins[game_type]["spins"][spin_index]

    def get_reel_layout(self):
        """
        function to get the layout of the reel [3x5] or [3x3]
        :return:
        """
        return self.reel_layout

    def get_start_matrix(self):
        start_matrix = []
        offset = 0
        for reel in range(len(self.reels["base"][self.variant])):
            start_matrix.append([])
            for symbol in range(self.reel_layout[reel]):  # 0, 1, 2, 3
                start_matrix[reel].append(self.reels["base"][self.variant][reel][symbol + offset])
            offset += 1
        return start_matrix

    def get_freespin_start_matrix(self):
        start_matrix = []
        offset = 0
        for reel in range(len(self.reels["freespin"][self.variant])):
            start_matrix.append([])
            for symbol in range(self.reel_layout[reel]):
                start_matrix[reel].append(self.reels["freespin"][self.variant][reel][symbol + offset])
            offset += 1
        return start_matrix

    def get_all_variants(self):
        return list(self.rtp.keys())

    def get_freespin_reel_multiplier(self, reelid):
        """
        function to get freespin multiplier
        :return:
        """
        return self.freespin_multiplier[str(reelid)]

    def get_full_start_matrix(self):
        """
        function to get the complete matrices (inner,outer,index)
        :param state:
        :return:
        """
        reels = self.reels["base"][self.variant]
        start_matrix = []
        start_outer_matrix = []
        start_indices = [0, 0, 0, 0, 0]

        for reel in range(len(reels)):
            start_matrix.append([])
            start_outer_matrix.append([])
            start_outer_matrix[reel].append(reels[reel][len(reels[reel]) - 1])
            start_outer_matrix[reel].append(reels[reel][self.reel_layout[reel]])
            for symbol in range(self.reel_layout[reel]):
                start_matrix[reel].append(reels[reel][symbol])

        full_start_dictionary = {"inner": start_matrix, "outer": start_outer_matrix, "index": start_indices}
        return full_start_dictionary