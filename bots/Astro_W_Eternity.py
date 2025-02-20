from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

HEALER_RATIO = 3
CATAPULT_SIZE_LIMIT = 5

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

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

        if rc.get_balance(team) >= BuildingType.FARM_1.cost:
            bp = rc.get_buildings(team)[-1]
            dirx = 1 if (ally_castle.x-bp.x) > 0 else -1
            diry = 1 if (ally_castle.y - bp.y) > 0 else -1
            for (x, y) in [(-dirx, -diry), (-dirx, 0), (0, -diry), (-dirx, diry), (dirx, -diry), (0, diry), (dirx, 0), (dirx, diry)]:
                if rc.can_build_building(BuildingType.FARM_1, x+bp.x, y+bp.y):
                    rc.build_building(BuildingType.FARM_1, bp.x+x, bp.y+y)
        
        if (len(rc.sense_buildings_within_radius(enemy, ally_castle.x, ally_castle.y, 25)) < 1 and len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 25)) < 1) or (len(rc.sense_units_within_radius(enemy, ally_castle.x, ally_castle.y, 10)) < 1 and len(rc.get_units(team)) >=30):
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
        
        if (rc.get_chebyshev_distance(ally_castle.x, ally_castle.y, enemy_castle.x, enemy_castle.y) < CATAPULT_SIZE_LIMIT):
            self.play_turn_catapult(rc)
            return
            
        enemy_units = rc.get_units(enemy)
        enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_dying = [enemy_unit for (enemy_unit, enemy_unit_health) in zip(enemy_units, enemy_units_health) if enemy_unit_health < UnitType.WARRIOR.damage]

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
        elif len(rc.get_buildings(team)) >2:
            spawn_type = UnitType.SWORDSMAN

        unit_ids_ordered =  warrior_ids + swordsman_ids + healer_ids
            
            # loop through all the units
        for unit_id in unit_ids_ordered:
            unit = rc.get_unit_from_id(unit_id)

            if unit.type == UnitType.WARRIOR or unit.type == UnitType.SWORDSMAN:

                    # find and kill dying enemy units

                    # keep one in castle
                # if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < spawn_type.cost:
                #     continue          

                if unit is None:
                    return
                    
                    # if can move towards castle, move towards castle
                
                if len(rc.sense_units_within_radius(enemy, unit.x, unit.y, 1)) >= 1:
                    best_dir = Direction.STAY
                else:

                    hitable_units = rc.sense_units_within_radius(enemy, unit.x, unit.y, 2)
                    if len(hitable_units) >=1:
                        hitable_unit = hitable_units[0]

                        possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                        possible_move_dirs.sort(
                            key=lambda dir: rc.get_chebyshev_distance(
                                *rc.new_location(unit.x, unit.y, dir),
                                hitable_unit.x,
                                hitable_unit.y,
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

                    best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)

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