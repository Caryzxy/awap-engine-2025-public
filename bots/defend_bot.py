from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.formation = None
        self.spawn_order = 0
        self.defensive_assignments = {}
        
    #evaluate the map, find the defensive layer we need. It shouold be 
    #centered around the ally castle. It should form a 7x7 max defence
    #The center will be the castle, then 2 layers of healer 2 and a 
    #layer of knights. Return a list of 48 units to be generated.
    #In case of some of the spot shouold not be able to access(mountain,
    #water, out of bounday, etc), put a None at that index in the list,
    #otherwise give a tuple of what should be the unit type and what should
    #be the coordinate to go for that unit.
    def generate_defensive_formation(self, rc: RobotController):
        """Creates a 7x7 defensive formation around the ally castle, prioritizing the outer layer first."""
            
        if not self.ally_castle:
            return None  # No castle found, return nothing

        castle_x, castle_y = self.ally_castle.x, self.ally_castle.y
        formation = []
        map_data = rc.get_map()

        # Define the layers: Outer layer (Knights), Inner layers (Healer 2)
        layer_order = [
            (UnitType.KNIGHT, 3),  # Outer layer
            (UnitType.LAND_HEALER_1, 2),  # Middle layer
            (UnitType.LAND_HEALER_1, 1)  # Inner layer
        ]

        # Generate the positions for each layer in the correct order
        for unit_type, layer_distance in layer_order:
            for dx in range(-layer_distance, layer_distance + 1):
                for dy in range(-layer_distance, layer_distance + 1):
                    if abs(dx) == layer_distance or abs(dy) == layer_distance:  # Ensure it's the outer part of this layer
                        new_x, new_y = castle_x + dx, castle_y + dy

                        # Check if the position is within bounds and not obstructed
                        if map_data.in_bounds(new_x, new_y) and map_data.tiles[new_x][new_y] not in {Tile.MOUNTAIN, Tile.WATER}:
                            formation.append((unit_type, (new_x, new_y)))
                        else:
                            formation.append(None)  # Unplaceable position

        return formation

    #Now I need a function to loop through the strategy and all the units we have
    #It go through the defence formation. spawn one in order if possible.
    #It then go through all units.
    #For knights, it moves one step to its assigned location
    #For Healer, it loves one step to the assiged location and heal the lowest health
    #ally in range
    def execute_defensive_strategy(self, rc: RobotController):
        """Executes the defensive strategy by spawning units and moving them to their assigned positions."""

        # Get team information
        team = rc.get_ally_team()

        # Spawn units in order if possible
        if self.spawn_order < len(self.formation):
            unit_info = self.formation[self.spawn_order]
            print(len(self.formation))
            print(self.spawn_order)
            if unit_info is not None:
                unit_type, target_position = unit_info
                print(unit_type)
                if rc.can_spawn_unit(unit_type, self.ally_castle_id):
                    rc.spawn_unit(unit_type, self.ally_castle_id)
                    unit_id = rc.get_unit_ids(team)[-1]
                    self.defensive_assignments[unit_id] = target_position  # Assign the unit to its position
                    self.spawn_order += 1
            else:
                self.spawn_order += 1 
        # Loop through all ally units
        unit_ids = rc.get_unit_ids(team)

        for unit_id in unit_ids:
            unit = rc.get_unit_from_id(unit_id)

            if unit_id not in self.defensive_assignments:
                continue  # Ignore units that are not part of the defensive formation
            
            target_x, target_y = self.defensive_assignments[unit_id]

            # Move unit toward its assigned position
            if (unit.x, unit.y) != (target_x, target_y):
                possible_moves = rc.unit_possible_move_directions(unit_id)
                possible_moves.sort(
                    key=lambda d: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, d),
                        target_x,
                        target_y
                    )
                )

                if possible_moves:
                    best_move = possible_moves[0]
                    if rc.can_move_unit_in_direction(unit_id, best_move):
                        rc.move_unit_in_direction(unit_id, best_move)

            # If it's a healer, heal the lowest-health ally in range
            if unit.type == UnitType.LAND_HEALER_2:
                nearby_allies = rc.sense_units_within_radius(team, unit.x, unit.y, 2)
                if nearby_allies:
                    lowest_health_ally = min(nearby_allies, key=lambda ally: ally.health)
                    if rc.can_unit_heal(unit_id, lowest_health_ally.id):
                        rc.unit_heal(unit_id, lowest_health_ally.id)


    def play_turn(self, rc: RobotController):
        """Main bot logic for each turn."""
        #finds ally castle
        team = rc.get_ally_team()
        self.ally_castle_id = -1
        self.ally_castle = None
        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                self.ally_castle_id = rc.get_id_from_building(building)[1]
                self.ally_castle = building
                break
        #if didn't have the strategy yet, find one
        if self.formation == None:
            self.formation = self.generate_defensive_formation(rc)
        
        self.execute_defensive_strategy(rc)

        
