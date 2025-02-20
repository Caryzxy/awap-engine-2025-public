from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        
        self.troop_format = [UnitType.SWORDSMAN, UnitType.LAND_HEALER_1]
        self.spawn_order = 0
        self.routes = []  # Stores multiple paths from ally castle to enemy castle
        self.direction_lists = []
        self.unit_assignments = {}  # {unit_id: route_index}
        self.waiting_pairs = {}  # {warrior_id: healer_id}
        self.visited_count = {}  # Tracks the number of times each tile is used in a route
        
        
        


    def find_all_routes(self, rc: RobotController):
        """Finds multiple paths from ally castle to enemy castle using greedy movement based on Chebyshev distance."""
        
        map_data = rc.get_map()
        team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        start = map_data.castle_locs[team]
        goal = map_data.castle_locs[enemy_team]
        
        width, height = map_data.width, map_data.height
        directions = [
            Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT,
            Direction.UP_LEFT, Direction.UP_RIGHT, Direction.DOWN_LEFT, Direction.DOWN_RIGHT
        ]

        def copy_map():
            return [[map_data.tiles[x][y] for y in range(height)] for x in range(width)]

        def bfs_path(allowed_map):
            """Finds the shortest path using BFS while prioritizing tiles visited the least."""
            queue = [(start, [], [])]
            visited = set()
            visited.add(start)
            
            while queue:
                queue.sort(key=lambda item: self.visited_count.get(item[0], 0))  # Prioritize least visited path
                current, path, direction_list = queue.pop(0)
                x, y = current
                
                if (x, y) == goal:
                    path = [start] + path
                    direction_list = [None] + direction_list
                    return path, direction_list
                
                for d in directions:
                    nx, ny = x + d.dx, y + d.dy
                    if map_data.in_bounds(nx, ny) and allowed_map[nx][ny] in {Tile.GRASS, Tile.BRIDGE} and (nx, ny) not in visited:
                        queue.append(((nx, ny), path + [(nx, ny)], direction_list + [d]))
                        visited.add((nx, ny))            
            return None, None  # No valid path found
        
        allowed_map = copy_map()
        self.routes = []
        echo = 0
        while True and echo <50:
            route, direction_list = bfs_path(allowed_map)
            echo +=1
            print(echo)
            if not route:
                break
            self.routes.append(route)
            self.direction_lists.append(direction_list)
            for x, y in route:
                    self.visited_count[(x, y)] = self.visited_count.get((x, y), 0) + 1  # Increment visit count
            
            

    def assign_units_to_routes(self, rc: RobotController):
        """Assigns warriors and healers to paths, ensuring they attack obstacles, attack enemy castle, and heal allies."""
        team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        self.enemy_castle_id = -1
        self.enemy_castle = None
        enemy_buildings = rc.get_buildings(enemy_team)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                self.enemy_castle_id = rc.get_id_from_building(building)[1]
                self.enemy_castle = building
                break
        
        if not self.routes:
            self.find_all_routes(rc)
            print("all routes found")
        
        unit_ids = rc.get_unit_ids(team)
        if not unit_ids:
            rc.spawn_unit(UnitType.SWORDSMAN, self.ally_castle_id)
            print("no problem here")
            return
        
        last_unit_id = unit_ids[-1]  # Last spawned unit
        last_unit = rc.get_unit_from_id(last_unit_id)
        
        
        if last_unit_id not in self.unit_assignments:
            route_index = len(self.unit_assignments) % len(self.routes)
            self.unit_assignments[last_unit_id] = route_index
            
            if last_unit.type == UnitType.SWORDSMAN:
                self.waiting_pairs[last_unit_id] = None  # This Warrior will wait for a Healer
            elif last_unit.type == UnitType.LAND_HEALER_1:
                if len(unit_ids) >= 2:
                    last_warrior_id = unit_ids[-2]  # The unit before the healer
                    
                    self.waiting_pairs[last_warrior_id] = last_unit_id
                    self.unit_assignments[last_unit_id] = self.unit_assignments[last_warrior_id]

        for warrior_id, healer_id in self.waiting_pairs.items():
            #First, check if anyone is dead
            warrior_dead = False
            healer_dead = False
            if  not warrior_id in rc.get_unit_ids(team) and warrior_id in self.unit_assignments:
                    warrior_dead = True
            if  not healer_id in rc.get_unit_ids(team) and healer_id in self.unit_assignments:
                    healer_dead = True
            
            if warrior_dead == False and warrior_id != None:
                warrior_pos = (rc.get_unit_from_id(warrior_id).x, rc.get_unit_from_id(warrior_id).y)
            if healer_dead == False and healer_id != None:
                healer_pos = (rc.get_unit_from_id(healer_id).x, rc.get_unit_from_id(healer_id).y)

            path_index = self.unit_assignments[warrior_id]
            direction_list = self.direction_lists[path_index]
            path = self.routes[path_index]
            

            if healer_id is None and not healer_dead:
                # Check if we can spawn a healer, and if so, move the warrior forward to make space
                healer_spawn_possible = rc.get_balance(team) >=3
                if healer_spawn_possible:
                    if not warrior_dead:
                        warrior_next = direction_list[min(path.index(warrior_pos) + 1, len(direction_list) - 1)]
                    if rc.can_move_unit_in_direction(warrior_id, warrior_next):
                        rc.move_unit_in_direction(warrior_id, warrior_next)
                        #("warrior leave the castle")
                        rc.spawn_unit(UnitType.LAND_HEALER_1, self.ally_castle_id)  # Spawn healer in the now freed space
                        #print("healer spawned")
                continue
            
            
            # Warrior attacks enemy main castle if in range
            
            if not healer_dead and self.enemy_castle and rc.can_unit_attack_building(warrior_id, self.enemy_castle_id):
                if rc.can_unit_attack_building(warrior_id, self.enemy_castle.id):
                    rc.unit_attack_building(warrior_id, self.enemy_castle.id)
            
            # Warrior checks if the next step is occupied by an enemy
            if not warrior_dead:
                warrior_next = path[min(path.index(warrior_pos) + 1, len(path) - 1)]
                nearby_enemies = rc.sense_units_within_radius(enemy_team, warrior_pos[0], warrior_pos[1], 1)
                nearby_buildings = rc.sense_buildings_within_radius(enemy_team, warrior_pos[0], warrior_pos[1], 1)
                enemies_in_way = [enemy for enemy in nearby_enemies + nearby_buildings if (enemy.x, enemy.y) == warrior_next]

                warrior_next = direction_list[min(path.index(warrior_pos) + 1, len(direction_list) - 1)]
                
            
                if enemies_in_way:
                    target = enemies_in_way[0]  # Attack the first enemy blocking the path
                    if isinstance(target, Unit) and rc.can_unit_attack_unit(warrior_id, target.id):
                        rc.unit_attack_unit(warrior_id, target.id)
                    elif isinstance(target, Building) and rc.can_unit_attack_building(warrior_id, target.id):
                        rc.unit_attack_building(warrior_id, target.id)

            # Healer heal the ally within the range with the lowest hp
            if not healer_dead:
                healer_next = direction_list[min(path.index(healer_pos) + 1, len(direction_list) - 1)]
                nearby_allies = rc.sense_units_within_radius(team, healer_pos[0], healer_pos[1], 2)
                ally_to_heal = min([ally for ally in nearby_allies],key=lambda ally: ally.health, default=None)
                if rc.can_heal_unit(healer_id, ally_to_heal.id):
                    rc.heal_unit(healer_id,ally_to_heal.id)
            # Move forward towards enemy castle or next step
            if not warrior_dead and not enemies_in_way and rc.can_move_unit_in_direction(warrior_id, warrior_next):
                rc.move_unit_in_direction(warrior_id, warrior_next)
            if not healer_dead and rc.can_move_unit_in_direction(healer_id, healer_next):
                rc.move_unit_in_direction(healer_id, healer_next)
            
        #check if the last unit is a healer, and get ready to spawn a warrior
        if last_unit.type == UnitType.LAND_HEALER_1:
            rc.spawn_unit(UnitType.SWORDSMAN, self.ally_castle_id)


                


    def play_turn(self, rc: RobotController):
        """Main bot logic for each turn."""
        team = rc.get_ally_team()
        self.ally_castle_id = -1
        self.ally_castle = None
        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                self.ally_castle_id = rc.get_id_from_building(building)[1]
                self.ally_castle = building
                break
        #spawn_order = [UnitType.WARRIOR, UnitType.LAND_HEALER_1]
        #current_spawn = spawn_order[len(rc.get_unit_ids(team)) % 2]
        #if rc.can_spawn_unit(current_spawn, self.ally_castle_id):
        #    rc.spawn_unit(current_spawn, self.ally_castle_id)
        #    print("A unit spawned")
        self.assign_units_to_routes(rc)
