from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.troop_format = [UnitType.WARRIOR, UnitType.LAND_HEALER_1]
        self.spawn_order = 0
        self.troop = []
        self.army = []
        self.army_list = []
    
    def play_turn(self, rc: RobotController):

        #find the main castle
        team = rc.get_ally_team()
        ally_castle_id = -1
        ally_castle = None

        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                ally_castle_id = rc.get_id_from_building(building)[1]
                ally_castle = building
                break

        #find the enemy castle
        enemy = rc.get_enemy_team()
        enemy_castle_id = -1

        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle_id = rc.get_id_from_building(building)[1]
                break
        
        #if no enemy castle, return
        enemy_castle = rc.get_building_from_id(enemy_castle_id)
        if enemy_castle is None: 
            return
        
        #find all enemy units
        enemy_units = rc.get_units(enemy)
        enemy_units_health = [enemy_unit.health for enemy_unit in enemy_units]
        enemy_units_location = [[enemy_unit.x, enemy_unit.y] for enemy_unit in enemy_units]

        
        
        # loop through all the units
        for unit_id in rc.get_unit_ids(team):
            unit = rc.get_unit_from_id(unit_id)

                # if castle still stands and can attack castle, attack castle
                if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                    rc.unit_attack_building(unit_id, enemy_castle_id)

                # keep one in castle
                if (unit.x, unit.y) == (ally_castle.x, ally_castle.y) and rc.get_balance(team) < UnitType.CATAPULT.cost:
                    continue          
                
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
        

        if rc.can_spawn_unit(self.troop_format[self.spawn_order], ally_castle_id):
            rc.spawn_unit(self.troop_format[self.spawn_order], ally_castle_id)
            self.troop.append( rc.get_unit_ids(team)[-1])
            self.spawn_order+=1
            if self.spawn_order == len(self.troop_format)-1:
                self.spawn_order = 0
                self.army.append(self.troop)
                self.troop = []
        if len(self.army) ==3:
            self.army_list.append(self.army)
            self.army = []
                
            
        
