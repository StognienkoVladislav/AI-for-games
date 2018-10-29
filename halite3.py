#!/usr/bin/env python3
# Python 3.6

import hlt

from hlt import constants

from hlt.positionals import Direction

import random
import numpy
import logging

game = hlt.Game()

game.ready("TwisharBot")

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ship_states = {}

while True:

    game.update_frame()

    me = game.me
    game_map = game.game_map

    command_queue = []

    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

    position_choices = []
    flag = True

    for ship in me.get_ships():

        if ship.id not in ship_states:
            ship_states[ship.id] = "collecting"
        position_options = ship.position.get_surrounding_cardinals() + [ship.position]
        # {(0,1): (14, 52)}
        position_dict = {}

        # {(0, 1): 512}
        halite_dict = {}

        if game.turn_number == 250 and len(me.get_dropoffs()) < 1 and me.halite_amount > 5000 and flag:
            mean_position = round(numpy.mean(
                [game_map.calculate_distance(me.shipyard.position, ship.position) for ship in me.get_ships()]))
            ship_distance = game_map.calculate_distance(me.shipyard.position, ship.position)
            if int(mean_position) - int(ship_distance) < 1:
                ship_states[ship.id] = "drop_off"
                command_queue.append(ship.make_dropoff())
                flag = False

        for n, direction in enumerate(direction_order):
            position_dict[direction] = position_options[n]

        for direction in position_dict:
            position = position_dict[direction]
            halite_amount = game_map[position].halite_amount

            if position_dict[direction] not in position_choices:

                if direction == Direction.Still:
                    halite_dict[direction] = halite_amount * 3
                else:
                    halite_dict[direction] = halite_amount

        if ship_states[ship.id] == "depositing":
            positions_for_depositing = {}
            positions = me.get_dropoffs()
            positions.append(me.shipyard)
            for pos in positions:
                positions_for_depositing[game_map.calculate_distance(pos.position, ship.position)] = pos.position

            pos_optimal = min(positions_for_depositing)

            move = game_map.naive_navigate(ship, positions_for_depositing[pos_optimal])
            position_choices.append(position_dict[move])
            command_queue.append(ship.move(move))

            if move == Direction.Still:
                ship_states[ship.id] = "collecting"

        elif ship_states[ship.id] == "collecting":
            directional_choice = max(halite_dict, key=halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            command_queue.append(ship.move(game_map.naive_navigate(ship, position_dict[directional_choice])))

            if ship.halite_amount > constants.MAX_HALITE * 0.95 and not game_map[me.shipyard].is_occupied:
                check_occupied = me.get_dropoffs()
                ship_states[ship.id] = "depositing"
                if len(check_occupied) > 1 and not game_map[check_occupied[0]].is_occupied:
                    ship_states[ship.id] = "depositing"
                elif len(check_occupied) > 1:
                    ship_states[ship.id] = "collecting"

    if game.turn_number <= 200:
        if game_map.height < 48:
            ships_per_map = 15
        else:
            ships_per_map = 25
    else:
        ships_per_map = 10

    if len(me.get_ships()) < ships_per_map:
        if game.turn_number <= 100 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())

        elif game.turn_number <= 180 and me.halite_amount >= constants.SHIP_COST * 2 and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())

        elif me.halite_amount >= constants.SHIP_COST * 8 and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)

