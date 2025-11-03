import math
import random
from idlelib.outwin import file_line_pats
from math import floor

from game_message import *


class Point:
    def __init__(self, position: Position):
        self.x = position.x
        self.y = position.y

    def to_pos(self):
        return Position(self.x, self.y)


    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


class Bot:
    def __init__(self):
        print("Initializing your super mega duper bot")
        self.links = set()

    def get_next_move(self, game_message: TeamGameState):
        actions = []
        remaining_biomass = game_message.maximumNumberOfBiomassPerTurn

        for couple in self.links:
            colony1 = self.get_col_at(game_message,couple[0].to_pos())
            colony2 = self.get_col_at(game_message, couple[1].to_pos())
            actions.extend(self.remove_superficial(game_message, colony1, colony2))

        i=0
        while remaining_biomass > 0 and i < len(self.get_sorted_colonies(game_message)):
            most_val = self.get_sorted_colonies(game_message)[i]
            closest = self.closest(game_message, most_val.position)[0]
            actions_to_add, used = self.link(game_message, most_val, closest, remaining_biomass)
            remaining_biomass -= used
            actions.extend(actions_to_add)
            i += 1

        print(game_message)
        return actions

    # NOT WORKING
    def remove_superficial(self, game_message: TeamGameState, colony1: Colony, colony2: Colony):
        path = self.path(colony1.position, colony2.position)
        maximum_link_value = min(colony2.nutrients, colony1.nutrients)
        current_link_value = self.get_path_value(game_message, path)
        to_remove = current_link_value - maximum_link_value
        if to_remove > 0:
            actions = {}
            for position in path:
                key = (position.x, position.y)
                actions[key] = to_remove
            return [RemoveBiomassAction(value, Position(key[0], key[1])) for key, value in actions.items()]
        else:
            return []

    def get_col_at(self,game_message : TeamGameState, position: Position):
        for colony in game_message.map.colonies:
            if colony.position == position:
                return colony
        return None

    def get_sorted_colonies(self, game_message: TeamGameState, future_steps: int = 5, future_weight=0.9):
        return sorted(game_message.map.colonies,
                      key=lambda colony: colony.nutrients + future_weight * sum(colony.futureNutrients[:future_steps])
                      , reverse=True)

    def link(self, game_message: TeamGameState, colony1: Colony, colony2: Colony, remaining_biomass) -> (
            list[Action], int):

        path = self.path(colony1.position, colony2.position)
        maximum_link_value = min(colony2.futureNutrients[0], colony1.futureNutrients[0])
        current_link_value = self.get_path_value(game_message, path)

        to_add = maximum_link_value - current_link_value
        given_thingy = remaining_biomass

        path_value_to_add = min((given_thingy // len(path), to_add))
        added = path_value_to_add * len(path)
        actions = {}
        for position in path:
            key = (position.x, position.y)
            actions[key] = path_value_to_add
        self.links.add((Point(colony1.position), Point(colony2.position)))
        return ([AddBiomassAction(value, Position(key[0], key[1])) for key, value in actions.items()], added)



    def get_path_value(self, game_message: TeamGameState, path: list[Position]) -> float:
        value = 0
        for position in path:
            value += game_message.map.biomass[position.x][position.y]
        return value / len(path)

    def path(self, start: Position, end: Position):
        positions = []

        # Move along x
        step_x = 1 if end.x > start.x else -1
        for x in range(start.x + step_x, end.x + step_x, step_x):
            positions.append(Position(x, start.y))

        # Move along y
        step_y = 1 if end.y > start.y else -1
        for y in range(start.y + step_y, end.y + step_y, step_y):
            positions.append(Position(end.x, y))
        positions.remove(end)
        return positions

    def closest(self, game_message: TeamGameState, start: Position) -> list[Colony]:
        closest = []
        close = math.inf
        for colony in game_message.map.colonies:
            dist = abs(start.x - colony.position.x) + abs(start.y - colony.position.y)
            if dist < close and dist != 0:
                close = dist
                closest.clear()
                closest.append(colony)
            elif dist == close and dist != 0:
                closest.append(colony)
        return closest
