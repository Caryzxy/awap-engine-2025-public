from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

HEALER_RATIO = 3
CATAPULT_SIZE_LIMIT = 5
LARGE_DISTANCE = 25
SUPERLARGE_DISTANCE = 35
import random

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.token = 0
        self.radius = 5

    def play_turn_catapult(self, rc: RobotController):
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
        enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_dying = [enemy_unit for (enemy_unit, enemy_unit_health) in zip(enemy_units, enemy_units_health) if enemy_unit_health < UnitType.CATAPULT.damage]

        catapult_ids = [u.id for u in ally_units if u.type == UnitType.CATAPULT]
        healer_ids = [u.id for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        num_catapults = len(catapult_ids)
        num_healers = len(healer_ids)

        spawn_type = UnitType.CATAPULT

        unit_ids_ordered = healer_ids + catapult_ids
        
        # loop through all the units
        for unit_id in unit_ids_ordered:
            unit = rc.get_unit_from_id(unit_id)

            if unit.type == UnitType.CATAPULT:

                # find and kill dying enemy units
                for i in range(len(enemy_units_dying)):
                    enemy_unit = enemy_units_dying[i]
                    if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                        rc.unit_attack_unit(unit.id, enemy_unit.id)
                        enemy_units_dying.pop(i)
                        break

                # if castle still stands and can attack castle, attack castle
                if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                    rc.unit_attack_building(unit_id, enemy_castle_id)
                else:
                    for enemy_unit in enemy_units:
                        if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                            rc.unit_attack_unit(unit.id, enemy_unit.id)
                            break
                

                # keep one in castle
                if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < spawn_type.cost:
                    continue          

                if unit is None:
                    return
                
                # if can move towards castle, move towards castle
            
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                possible_move_dirs.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        enemy_castle.x,
                        enemy_castle.y,
                    )
                )
                # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])

                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
            
            elif unit.type == UnitType.LAND_HEALER_1:
                # if can move towards castle, move towards castle
            
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                possible_move_dirs.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        enemy_castle.x,
                        enemy_castle.y,
                    )
                )
                # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])

                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                
                for ally_unit in ally_units:
                    if rc.can_heal_unit(unit.id, ally_unit.id) and ally_unit.health < 7:
                        rc.heal_unit(unit.id, ally_unit.id)
                        break
                for ally_unit in ally_units:
                    if rc.can_heal_unit(unit.id, ally_unit.id) and ally_unit.health < 10:
                        rc.heal_unit(unit.id, ally_unit.id)
                        break
        

        if rc.can_spawn_unit(spawn_type, ally_castle_id):
            rc.spawn_unit(spawn_type, ally_castle_id)

    def play_turn_short_distance(self, rc: RobotController):
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

        if len(ally_buildings) <= 2:

            if rc.get_balance(team) >= BuildingType.FARM_1.cost:
                while True:
                    x = random.randint(min(ally_castle.x, enemy_castle.x), max(ally_castle.x, enemy_castle.x))
                    y = random.randint(min(ally_castle.y, enemy_castle.y), max(ally_castle.y, enemy_castle.y))
                    if rc.can_build_building(BuildingType.FARM_1, x, y):
                        rc.build_building(BuildingType.FARM_1,x, y)
                        break
        
            if (len(rc.sense_buildings_within_radius(enemy, ally_castle.x, ally_castle.y, 20)) < 1 and len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 25)) < 1) or (len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 10)) < 1 and len(rc.get_units(team)) >=30):
                if rc.get_balance(team) < BuildingType.FARM_1.cost:
                    return
        

        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle_id = rc.get_id_from_building(building)[1]
                break

        enemy_castle = rc.get_building_from_id(enemy_castle_id)
        if enemy_castle == None or ally_castle == None: 
            return
        
        enemy_units = rc.get_units(enemy)
        enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_dying = [enemy_unit for (enemy_unit, enemy_unit_health) in zip(enemy_units, enemy_units_health) if enemy_unit_health < UnitType.WARRIOR.damage]

        sort_index = sorted(range(len(enemy_units_health)), key=lambda k: [k])
        sorted_enemy_units = [enemy_units[i] for i in sort_index]
        
        spawn_type = UnitType.WARRIOR

        if (len(ally_units) > HEALER_RATIO * (sum(1 for u in ally_units if u.type == UnitType.LAND_HEALER_1)+1)):
            spawn_type = UnitType.LAND_HEALER_1
        elif len(rc.get_buildings(team)) >2:
            spawn_type = UnitType.SWORDSMAN
            
            # loop through all the units
        for unit_id in rc.get_unit_ids(team):
            unit = rc.get_unit_from_id(unit_id)

            if unit is None:
                return

            
            if unit.type == UnitType.WARRIOR or unit.type == UnitType.SWORDSMAN or unit.type == UnitType.KNIGHT:
                
                for i in range(len(enemy_units_dying)):
                    enemy_unit = enemy_units_dying[i]
                    if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                        rc.unit_attack_unit(unit.id, enemy_unit.id)
                        enemy_units_dying.pop(i)
                        break
                
                if rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x, ally_castle.y) <= 1:
                    if rc.get_balance(team) < spawn_type.cost:
                        continue
                # for (dx, dy) in [(-1, -1), (-1, 0), (0, -1), (-1, 1), (1, -1), (0, 1), (1, 0), (1,1)]:
                #     if rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x+dx, ally_castle.y+dy) == 1:
                #         best_dir = Direction(-dx, -dy)
                #         if rc.can_move_unit_in_direction(unit_id, best_dir):
                #             rc.move_unit_in_direction(unit_id, best_dir)
                            
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                pd = []
                for dir in possible_move_dirs:
                    newx, newy = rc.new_location(unit.x, unit.y, dir)
                    if (len(rc.sense_units_within_radius(team, newx, newy, 1)) >= 1) or (len(rc.sense_buildings_within_radius(team, newx, newy, 2)) >= 1):
                            pd.append(dir)
                pd.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        enemy_castle.x,
                        enemy_castle.y,
                    )
                )
                    # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                    # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])
                if len(pd) > 0:
                    best_dir = pd[0] #least chebyshev dist direction
                else:
                    best_dir = Direction.STAY

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                
                if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                    rc.unit_attack_building(unit_id, enemy_castle_id)
                else:
                    if enemy_units != None:
                        for enemy_unit in sorted_enemy_units:
                            if enemy_unit.defense < unit.health:
                                if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                                    rc.unit_attack_unit(unit_id, enemy_unit.id)
            
            elif unit.type == UnitType.LAND_HEALER_1 or unit.type == UnitType.LAND_HEALER_2:

                for ally_unit in ally_units:
                    if rc.can_heal_unit(unit.id, ally_unit.id) and ally_unit.health <= 7:
                        rc.heal_unit(unit.id, ally_unit.id)
                        break

                if rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x, ally_castle.y) <= 1:
                    if rc.get_balance(team) < spawn_type.cost:
                        continue
                # for (dx, dy) in [(-1, -1), (-1, 0), (0, -1), (-1, 1), (1, -1), (0, 1), (1, 0), (1,1)]:
                #     if rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x+dx, ally_castle.y+dy) == 1:
                #         best_dir = Direction(-dx, -dy)
                #         if rc.can_move_unit_in_direction(unit_id, best_dir):
                #             rc.move_unit_in_direction(unit_id, best_dir)
                            
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                pd = []
                for dir in possible_move_dirs:
                    newx, newy = rc.new_location(unit.x, unit.y, dir)
                    if (len(rc.sense_units_within_radius(team, newx, newy, 1)) >= 1) or (len(rc.sense_buildings_within_radius(team, newx, newy, 2)) >= 1):
                            pd.append(dir)
                pd.sort(
                    key=lambda dir: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, dir),
                        enemy_castle.x,
                        enemy_castle.y,
                    )
                )
                    # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                    # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])
                if len(pd) > 0:
                    best_dir = pd[0] #least chebyshev dist direction
                else:
                    best_dir = Direction.STAY

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                    
                    # if can move towards castle, move towards castle
                
                    # hitable_units = rc.sense_units_within_radius(enemy, unit.x, unit.y, 2)
                    # if len(hitable_units) >=1:
                    #     hitable_units_health = [u.health for u in hitable_units]
                    #     sort_index = sorted(range(len(hitable_units_health)), key=lambda k: [k])
                    #     hitable_unit = hitable_units[sort_index[0]]

                    #     possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                    #     pd = []
                    #     for dir in possible_move_dirs:
                    #         newx, newy = rc.new_location(unit.x, unit.y, dir)
                    #         if (rc.sense_units_within_radius(team, newx, newy, 1)):
                    #             pd.append(dir)
                    #     pd.sort(
                    #         key=lambda dir: rc.get_chebyshev_distance(
                    #             *rc.new_location(unit.x, unit.y, dir),
                    #             hitable_unit.x,
                    #             hitable_unit.y,
                    #         )
                    #     )
                    #     if (len(pd) > 0) and rc.can_move_unit_in_direction(unit_id, pd[0]):
                    #         best_dir = pd[0]

                    # else:
            
            if rc.can_spawn_unit(spawn_type, ally_castle_id):
                rc.spawn_unit(spawn_type, ally_castle_id)
        if rc.can_spawn_unit(spawn_type, ally_castle_id):
                rc.spawn_unit(spawn_type, ally_castle_id)

    def play_turn_long_distance(self, rc: RobotController):
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
        if enemy_castle == None or ally_castle == None: 
            return
        
        if len(ally_buildings) <= 2:

            if rc.get_balance(team) >= BuildingType.FARM_1.cost:
                while True:
                    x = random.randint(min(ally_castle.x, enemy_castle.x), max(ally_castle.x, enemy_castle.x))
                    y = random.randint(min(ally_castle.y, enemy_castle.y), max(ally_castle.y, enemy_castle.y))
                    if rc.can_build_building(BuildingType.FARM_1, x, y):
                        rc.build_building(BuildingType.FARM_1,x, y)
                        break
        
            if (len(rc.sense_buildings_within_radius(enemy, ally_castle.x, ally_castle.y, 20)) < 1 and len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 25)) < 1) or (len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 10)) < 1 and len(rc.get_units(team)) >=30):
                if rc.get_balance(team) < BuildingType.FARM_1.cost:
                    return
            
        enemy_units = rc.get_units(enemy)
        enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_dying = [enemy_unit for (enemy_unit, enemy_unit_health) in zip(enemy_units, enemy_units_health) if enemy_unit_health < UnitType.WARRIOR.damage]

        for e in enemy_units:
            if e.type == UnitType.KNIGHT:
                self.token = 1
                break

        warrior_ids = [u.id for u in ally_units if u.type == UnitType.WARRIOR]
        swordsman_ids = [u.id for u in ally_units if u.type == UnitType.SWORDSMAN]
        healer_ids = [u.id for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        num_warriors = len(warrior_ids)
        num_healers = len(healer_ids)
        num_swordsmans = len(swordsman_ids)

        num_swordsmans = len(swordsman_ids)
        
        spawn_type = UnitType.WARRIOR
        if (num_warriors+num_swordsmans > HEALER_RATIO * num_healers):
            spawn_type = UnitType.LAND_HEALER_1
        elif len(rc.get_buildings(team)) >2 or self.token == 1:
            spawn_type = UnitType.SWORDSMAN

        unit_ids_ordered =  warrior_ids + swordsman_ids + healer_ids
            
            # loop through all the units
        for unit_id in unit_ids_ordered:
            unit = rc.get_unit_from_id(unit_id)

            if unit.type == UnitType.WARRIOR or unit.type == UnitType.SWORDSMAN:

                    # find and kill dying enemy units

                    # keep one in castle
                if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < spawn_type.cost:
                    continue          

                if unit is None:
                    return
                    
                    # if can move towards castle, move towards castle
                for i in range(len(enemy_units_dying)):
                    enemy_unit = enemy_units_dying[i]
                    if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                        rc.unit_attack_unit(unit_id, enemy_unit.id)
                        enemy_units_dying.pop(i)
                        break

                    # if castle still stands and can attack castle, attack castle
                if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                    rc.unit_attack_building(unit_id, enemy_castle_id)
                else:
                    if enemy_units != None:
                        for enemy_unit in enemy_units:
                            if enemy_unit.defense < unit.health:
                                if rc.can_unit_attack_unit(unit_id, enemy_unit.id):
                                    rc.unit_attack_unit(unit_id, enemy_unit.id)

                if len(rc.sense_units_within_radius(enemy, unit.x, unit.y, 1)) >= 1:
                    best_dir = Direction.STAY
                else:
                        possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                        pd = []
                        for dir in possible_move_dirs:
                            newx, newy = rc.new_location(unit.x, unit.y, dir)
                            if (rc.sense_units_within_radius(team, newx, newy, 1)):
                                pd.append(dir)
                        pd.sort(
                            key=lambda dir: rc.get_chebyshev_distance(
                                *rc.new_location(unit.x, unit.y, dir),
                                enemy_castle.x,
                                enemy_castle.y,
                            )
                        )
                        if (len(pd) > 0) and rc.can_move_unit_in_direction(unit_id, pd[0]):
                            best_dir = pd[0]

                    # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                    # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                
            elif unit.type == UnitType.LAND_HEALER_1:
                    # if can move towards castle, move towards castle
                    
                healable_units = rc.sense_units_within_radius(team, unit.x, unit.y, 3)
                if healable_units != None and len(healable_units) >= 1:

                    healable_unit = [u for u in healable_units if u.type == UnitType.WARRIOR]
                    if healable_unit is None or len(healable_unit) == 0:
                        healable_unit = healable_units[0]
                    else:
                        healable_unit = healable_unit[0]

                    possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                    possible_move_dirs.sort(
                        key=lambda dir: rc.get_chebyshev_distance(
                            *rc.new_location(unit.x, unit.y, dir),
                            healable_unit.x,
                            healable_unit.y,
                        )
                    )
                else:
                    possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                    possible_move_dirs.sort(
                        key=lambda dir: rc.get_chebyshev_distance(
                            *rc.new_location(unit.x, unit.y, dir),
                            enemy_castle.x,
                            enemy_castle.y,
                        )
                    )
                    # moves_and_dist_to_castle = {dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y) for dir in possible_move_dirs}
                    # moves_and_dist_to_castle = sorted(moves_and_dist_to_castle.items(), key=lambda item: item[1])

                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else possible_move_dirs[-1] #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)
                    
                for ally_unit in ally_units:
                    if rc.can_heal_unit(unit.id, ally_unit.id) and ally_unit.health <= 5:
                        rc.heal_unit(unit.id, ally_unit.id)
                        break

        for unit_id in healer_ids:
            for ally_unit in ally_units:
                if rc.can_heal_unit(unit.id, ally_unit.id) and ally_unit.health < 10:
                    rc.heal_unit(unit.id, ally_unit.id)
                    break
            
        if rc.can_spawn_unit(spawn_type, ally_castle_id):
            rc.spawn_unit(spawn_type, ally_castle_id)

    def play_turn_super_long(self, rc:RobotController):
        ally = rc.get_ally_team()
        ally_units = rc.get_units(ally)
        ally_buildings = rc.get_buildings(ally)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                ally_castle = building
                break
        
        enemy = rc.get_enemy_team()
        enemy_units = rc.get_units(enemy)
        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle = building
                break
        
        if enemy_castle is None:
            return
        
        knights = [u for u in ally_units if u.type == UnitType.KNIGHT]
        knight_ids = [u.id for u in ally_units if u.type == UnitType.KNIGHT]
        # healers = [u for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        healer_ids = [u.id for u in ally_units if u.type == UnitType.LAND_HEALER_1]
        num_knights = len(knight_ids)
        num_healers = len(healer_ids)
        
        spawn_type = UnitType.KNIGHT
        if rc.get_turn() >= 4 and num_knights > HEALER_RATIO * num_healers:
            spawn_type = UnitType.LAND_HEALER_1
        
        
        # move if spawn available
        
        if rc.get_balance(ally) >= spawn_type.cost:
            units_dist = sorted(ally_units, key=lambda u: rc.get_chebyshev_distance(u.x, u.y, ally_castle.x, ally_castle.y), reverse=True)
            for r in range(1, self.radius):
                for i in range(len(units_dist)):
                    unit = units_dist[i]
                    dist = rc.get_chebyshev_distance(unit.x, unit.y, ally_castle.x, ally_castle.y)
                    if dist < r:
                        possible_dirs = rc.unit_possible_move_directions(unit.id)
                        possible_dirs.sort(
                            key=lambda dir: rc.get_chebyshev_distance(
                                *rc.new_location(unit.x, unit.y, dir),
                                ally_castle.x,
                                ally_castle.y,
                            ), reverse=True
                        )
                        for dir in possible_dirs:
                            if rc.can_move_unit_in_direction(unit.id, dir):
                                rc.move_unit_in_direction(unit.id,dir)
                                break
                if rc.can_spawn_unit(spawn_type, ally_castle.id):
                    rc.spawn_unit(spawn_type, ally_castle.id)
                    break
                    
        
        # farm if rich
        
        if rc.get_balance(ally) >= BuildingType.FARM_1.cost:
            while True:
                new_x = random.randint(min(ally_castle.x, enemy_castle.x), max(ally_castle.x, enemy_castle.x))
                new_y = random.randint(min(ally_castle.y, enemy_castle.y), max(ally_castle.y, enemy_castle.y))
                if rc.can_build_building(BuildingType.FARM_1, new_x, new_y):
                    rc.build_building(BuildingType.FARM_1, new_x, new_y)
                    break
    
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
        if enemy_castle == None or ally_castle == None: 
            return
        
        if (rc.get_chebyshev_distance(ally_castle.x, ally_castle.y, enemy_castle.x, enemy_castle.y) < CATAPULT_SIZE_LIMIT):
            self.play_turn_catapult(rc)
            return
        elif (rc.get_chebyshev_distance(ally_castle.x, ally_castle.y, enemy_castle.x, enemy_castle.y) >= SUPERLARGE_DISTANCE) or not self.map.is_tile_type(ally_castle.x-1,ally_castle.y, Tile.GRASS) or not self.map.is_tile_type(ally_castle.x,ally_castle.y-1, Tile.GRASS) or not self.map.is_tile_type(ally_castle.x,ally_castle.y+1, Tile.GRASS) or not self.map.is_tile_type(ally_castle.x+1,ally_castle.y, Tile.GRASS):
                self.play_turn_super_long(rc)
        elif (rc.get_chebyshev_distance(ally_castle.x, ally_castle.y, enemy_castle.x, enemy_castle.y) >= LARGE_DISTANCE) and (rc.get_chebyshev_distance(ally_castle.x, ally_castle.y, enemy_castle.x, enemy_castle.y) < SUPERLARGE_DISTANCE):
            if len(rc.get_buildings(team)) <= 2:
                self.play_turn_long_distance(rc)
            else:
                self.play_turn_short_distance(rc)

        else:
            self.play_turn_short_distance(rc)