from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

import random

HALF_HEALTH = 5
HEALER_RATIO = 1.5

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        team = rc.get_ally_team()
        ally_castle_id = -1
        ally_castle = None

        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                ally_castle_id = rc.get_id_from_building(building)[1]
                ally_castle = building
                break
        
        ally_units = rc.get_units(team)

        enemy = rc.get_enemy_team()
        enemy_castle_id = -1

        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle_id = rc.get_id_from_building(building)[1]
                break

        enemy_castle = rc.get_building_from_id(enemy_castle_id)
        if enemy_castle is None: 
            return
        
        enemy_units = rc.get_units(enemy)
        #enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_dying = [enemy_unit for enemy_unit in enemy_units if enemy_unit.health < HALF_HEALTH]
        if enemy_units_dying != []:
            enemy_units_dying.sort(key=lambda enemy_unit: enemy_unit.health)
        
        warriors = [u for u in ally_units if u.type == UnitType.WARRIOR]
        warrior_ids = [u.id for u in ally_units if u.type == UnitType.WARRIOR]
        # healers = [u for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        healer_ids = [u.id for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        num_warriors = len(warrior_ids)
        num_healers = len(healer_ids)

        spawn_type = UnitType.WARRIOR
        if rc.get_turn() >= 4 and num_warriors > HEALER_RATIO * num_healers:
            spawn_type = UnitType.LAND_HEALER_1
        
        unit_ids_ordered = warrior_ids + healer_ids
        
        # loop through all the units
        for unit_id in unit_ids_ordered:
            unit = rc.get_unit_from_id(unit_id)

            if unit.type == UnitType.WARRIOR:
                
                # if castle still stands and can attack castle, attack castle
                # else, find and attack enemy_dying_unit
                if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                    rc.unit_attack_building(unit_id, enemy_castle_id)
                else:
                    for i in range(min(3, len(enemy_units_dying))):
                        target_unit = enemy_units_dying[i]
                        target_unit_health = target_unit.health
                        if rc.can_unit_attack_unit(unit_id, target_unit.id):
                            rc.unit_attack_unit(unit_id, target_unit.id)
                        if target_unit_health <= UnitType.WARRIOR.damage:
                            enemy_units_dying.pop(i)

                # keep one in castle
                
                
                
                #if rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x, ally_castle.y) <= 2:
                if len(rc.sense_units_within_radius(team, ally_castle.x, ally_castle.y, 2)) <= 15:
                    possible_dirs = rc.unit_possible_move_directions(unit.id)
                    pd = []
                    for i in range(len(possible_dirs)):
                        dir = possible_dirs[i]
                        new_x, new_y = rc.new_location(unit.x, unit.y, dir)
                        if rc.get_chebyshev_distance(new_x, new_y, ally_castle.x, ally_castle.y) <= 2:
                            pd.append(dir)
                            break
                    for dir in pd:
                        if rc.can_move_unit_in_direction(unit.id, dir):
                            rc.move_unit_in_direction(unit.id, dir)
                            continue
                
                
                
                #if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < spawn_type.cost:
                #    continue
                if unit is None:
                    return

                target_object = enemy_castle
                if rc.get_chebyshev_distance(unit.x, unit.y, target_object.x, target_object.y) > 2:
                    targets = sorted(enemy_units, key=lambda u: u.health)
                    for target in targets:
                        if rc.get_chebyshev_distance(unit.x, unit.y, target.x, target.y) <= 3:
                            target_object = target
                            break
                
                
                # if can move towards target, move towards target
            
                possible_move_dirs = rc.unit_possible_move_directions(unit.id)
                possible_move_dirs.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        target_object.x,
                        target_object.y,
                    )
                )
                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY
                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)    
                    
            
            elif unit.type == UnitType.LAND_HEALER_1:
                
                # if can heal, then heal
                healing_seq = sorted(warriors, key=lambda warrior: warrior.health)
                for i in range(min(3, len(healing_seq))):
                    target_warrior = healing_seq[i]               
                    target_dist = rc.get_chebyshev_distance(unit.x, unit.y, target_warrior.x, target_warrior.y)
                    if target_dist <= UnitType.LAND_HEALER_1.attack_range:
                        if rc.can_heal_unit(unit.id, target_warrior.id):
                            rc.heal_unit(unit.id, target_warrior.id)
                            
                
                
                if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < spawn_type.cost:
                    healing_targets = rc.sense_units_within_radius(team, unit.x, unit.y, unit.attack_range)
                    if len(healing_targets) > 0:
                        target = healing_targets[0]
                    else:
                        target = unit
                    if rc.can_heal_unit(unit.id, target.id):
                        rc.heal_unit(unit.id, target.id)
                        continue
                if unit is None:
                    return
                
                # move towards target
                healing_seq = sorted(warriors, key=lambda warrior: warrior.health)
                target_warrior = healing_seq[0]
                if rc.get_chebyshev_distance(unit.x, unit.y, target_warrior.x, target_warrior.y) > 5 and len(healing_seq) > 1:
                    for w in healing_seq[1:]:
                        if rc.get_chebyshev_distance(unit.x, unit.y, w.x, w.y) <= 5:
                            target_warrior = w
                            break
                
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                possible_move_dirs.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        target_warrior.x,
                        target_warrior.y,
                    )
                )
                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                
                
                healing_targets = rc.sense_units_within_radius(team, unit.x, unit.y, unit.attack_range)
                if len(healing_targets) > 0:
                    target = healing_targets[0]
                else:
                    target = unit
                if rc.can_heal_unit(unit.id, target.id):
                    rc.heal_unit(unit.id, target.id)
        

        if rc.can_spawn_unit(spawn_type, ally_castle_id):
            rc.spawn_unit(spawn_type, ally_castle_id)
            
        
