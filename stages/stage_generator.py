"""
AI-powered stage design generator for IPSC stages
"""
import random
import math
from .models import StageItem


class StageGenerator:
    """
    Generates IPSC stage designs based on constraints and difficulty levels

    Stage Layout Philosophy:
    - Bullet traps are positioned on 1-3 sides of the stage
    - Start position is in the safe zone (opposite bullet traps)
    - Targets face toward the safe zone with bullet traps behind them
    - Stage flow creates a logical path through the course
    """

    def __init__(self, width, height, difficulty='medium', bullet_trap_sides='north'):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.items = []
        self.occupied_areas = []

        # Parse bullet trap configuration from string
        # Convert hyphenated format to list: 'north-east' -> ['north', 'east']
        if '-' in bullet_trap_sides:
            self.bullet_trap_sides = bullet_trap_sides.split('-')
        else:
            self.bullet_trap_sides = [bullet_trap_sides]

        # Define safe zone (where shooters will be positioned)
        self.safe_zone = self._define_safe_zone()

        # Define target zones (where targets should be placed)
        self.target_zones = self._define_target_zones()

    def _define_safe_zone(self):
        """
        Define the safe zone where shooters will be positioned
        Returns dict with boundaries
        """
        buffer = 2.0  # Safety buffer from edges

        # Safe zone is opposite from bullet traps
        if 'north' in self.bullet_trap_sides and 'south' not in self.bullet_trap_sides:
            # Shooters at south, targets at north
            return {
                'x_min': buffer,
                'x_max': self.width - buffer,
                'y_min': 0,
                'y_max': self.height * 0.25,  # Southern quarter
                'primary_direction': 'north'  # Shooting northward
            }
        elif 'south' in self.bullet_trap_sides and 'north' not in self.bullet_trap_sides:
            return {
                'x_min': buffer,
                'x_max': self.width - buffer,
                'y_min': self.height * 0.75,
                'y_max': self.height,
                'primary_direction': 'south'
            }
        elif 'east' in self.bullet_trap_sides and 'west' not in self.bullet_trap_sides:
            return {
                'x_min': 0,
                'x_max': self.width * 0.25,
                'y_min': buffer,
                'y_max': self.height - buffer,
                'primary_direction': 'east'
            }
        elif 'west' in self.bullet_trap_sides and 'east' not in self.bullet_trap_sides:
            return {
                'x_min': self.width * 0.75,
                'x_max': self.width,
                'y_min': buffer,
                'y_max': self.height - buffer,
                'primary_direction': 'west'
            }
        else:
            # Corner configurations (e.g., north + east)
            return {
                'x_min': buffer,
                'x_max': self.width * 0.3,
                'y_min': buffer,
                'y_max': self.height * 0.3,
                'primary_direction': 'northeast' if 'north' in self.bullet_trap_sides else 'southeast'
            }

    def _define_target_zones(self):
        """
        Define zones where targets should be placed (near bullet traps)
        Returns list of zone dicts
        """
        zones = []
        buffer = 2.0

        # Create zones near each bullet trap
        if 'north' in self.bullet_trap_sides:
            zones.append({
                'name': 'north_zone',
                'x_min': buffer,
                'x_max': self.width - buffer,
                'y_min': self.height * 0.6,
                'y_max': self.height - buffer,
                'facing': 180  # Face south toward shooters
            })

        if 'south' in self.bullet_trap_sides:
            zones.append({
                'name': 'south_zone',
                'x_min': buffer,
                'x_max': self.width - buffer,
                'y_min': buffer,
                'y_max': self.height * 0.4,
                'facing': 0  # Face north toward shooters
            })

        if 'east' in self.bullet_trap_sides:
            zones.append({
                'name': 'east_zone',
                'x_min': self.width * 0.6,
                'x_max': self.width - buffer,
                'y_min': buffer,
                'y_max': self.height - buffer,
                'facing': 270  # Face west toward shooters
            })

        if 'west' in self.bullet_trap_sides:
            zones.append({
                'name': 'west_zone',
                'x_min': buffer,
                'x_max': self.width * 0.4,
                'y_min': buffer,
                'y_max': self.height - buffer,
                'facing': 90  # Face east toward shooters
            })

        return zones

    def generate(self, available_items=None):
        """
        Generate a complete stage design with proper bullet trap awareness

        Args:
            available_items: Dict of {item_type: quantity} or None for auto-generation

        Returns:
            List of item configurations
        """
        if available_items is None:
            available_items = self._get_default_items()

        # Clear previous generation
        self.items = []
        self.occupied_areas = []

        # Step 1: Place start position in safe zone
        self._place_start_position()

        # Step 2: Place shooting boxes in safe zone or along the path
        if available_items.get('shooting_box', 0) > 0:
            self._place_shooting_boxes(available_items['shooting_box'])

        # Step 3: Place barriers and walls for cover (between safe zone and targets)
        self._place_obstacles(available_items)

        # Step 4: Place targets in target zones facing shooters
        self._place_targets(available_items)

        # Step 5: Add no-shoot targets near shooting targets
        if available_items.get('no_shoot', 0) > 0:
            self._place_no_shoots(available_items['no_shoot'])

        # Step 6: Add props (tables, barrels, etc.)
        self._place_props(available_items)

        return self.items

    def _get_default_items(self):
        """Get default item quantities based on difficulty"""
        difficulty_configs = {
            'easy': {
                'paper_target': 6,
                'steel_target': 3,
                'popper': 2,
                'barrier': 2,
                'wall': 1,
                'shooting_box': 1,
                'start_position': 1,
                'table': 1,
            },
            'medium': {
                'paper_target': 10,
                'steel_target': 5,
                'popper': 3,
                'plate_rack': 1,
                'no_shoot': 2,
                'barrier': 3,
                'wall': 2,
                'shooting_box': 2,
                'start_position': 1,
                'table': 1,
                'barrel': 2,
            },
            'hard': {
                'paper_target': 14,
                'steel_target': 8,
                'popper': 5,
                'plate_rack': 2,
                'no_shoot': 4,
                'barrier': 5,
                'wall': 3,
                'door': 1,
                'window': 1,
                'shooting_box': 3,
                'start_position': 1,
                'table': 2,
                'barrel': 3,
            }
        }
        return difficulty_configs.get(self.difficulty, difficulty_configs['medium'])

    def _place_start_position(self):
        """Place the start position in the safe zone"""
        # Place in safe zone, away from targets
        safe = self.safe_zone
        x = random.uniform(safe['x_min'] + 0.5, safe['x_max'] - 0.5)
        y = random.uniform(safe['y_min'] + 0.5, safe['y_max'] - 0.5)

        # Ensure minimum coordinates
        x = max(1.0, x)
        y = max(1.0, y)

        item = {
            'item_type': 'start_position',
            'position_x': x,
            'position_y': y,
            'rotation': 0,
            'width': 1.0,
            'height': 1.0,
        }
        self.items.append(item)
        self._mark_occupied(x, y, 1.0, 1.0)

    def _place_shooting_boxes(self, count):
        """Place shooting boxes in safe zone or along the path"""
        # First shooting box in safe zone
        # Additional boxes create a path through the stage
        safe = self.safe_zone

        for i in range(count):
            if i == 0:
                # First box in safe zone
                x = random.uniform(safe['x_min'] + 1, safe['x_max'] - 1)
                y = random.uniform(safe['y_min'] + 1, safe['y_max'] - 1)
            else:
                # Additional boxes create a path
                # Place them between safe zone and target zones
                mid_x = self.width / 2
                mid_y = self.height / 2
                x = mid_x + random.uniform(-2, 2)
                y = mid_y + random.uniform(-2, 2)

            # Try to find a free position nearby if this one is occupied
            for attempt in range(10):
                if self._is_area_free(x, y, 1.0, 1.0):
                    # Determine rotation based on primary shooting direction
                    facing = self._calculate_facing_angle(x, y)

                    item = {
                        'item_type': 'shooting_box',
                        'position_x': x,
                        'position_y': y,
                        'rotation': facing,
                        'width': 1.0,
                        'height': 1.0,
                    }
                    self.items.append(item)
                    self._mark_occupied(x, y, 1.0, 1.0)
                    break
                else:
                    x += random.uniform(-1, 1)
                    y += random.uniform(-1, 1)

    def _place_obstacles(self, available_items):
        """Place barriers and walls for cover and complexity"""
        # Barriers
        barrier_count = available_items.get('barrier', 0)
        for _ in range(barrier_count):
            x, y = self._find_free_position(1.5, 1.2, min_distance=2.0)
            if x is not None:
                item = {
                    'item_type': 'barrier',
                    'position_x': x,
                    'position_y': y,
                    'rotation': random.choice([0, 45, 90, 135, 180]),
                    'width': 1.5,
                    'height': 1.2,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 1.5, 1.2)

        # Walls
        wall_count = available_items.get('wall', 0)
        for _ in range(wall_count):
            x, y = self._find_free_position(2.0, 1.5, min_distance=2.5)
            if x is not None:
                item = {
                    'item_type': 'wall',
                    'position_x': x,
                    'position_y': y,
                    'rotation': random.choice([0, 90]),
                    'width': 2.0,
                    'height': 1.5,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 2.0, 1.5)

        # Doors
        door_count = available_items.get('door', 0)
        for _ in range(door_count):
            x, y = self._find_free_position(1.0, 2.0, min_distance=2.0)
            if x is not None:
                item = {
                    'item_type': 'door',
                    'position_x': x,
                    'position_y': y,
                    'rotation': 0,
                    'width': 1.0,
                    'height': 2.0,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 1.0, 2.0)

    def _place_targets(self, available_items):
        """Place shooting targets in target zones facing the safe zone"""
        # Distribute targets across available target zones
        all_targets = []

        # Collect all target types and counts
        target_types = [
            ('paper_target', 0.5, 0.8, available_items.get('paper_target', 0)),
            ('steel_target', 0.3, 0.3, available_items.get('steel_target', 0)),
            ('popper', 0.4, 0.6, available_items.get('popper', 0)),
            ('plate_rack', 1.0, 0.5, available_items.get('plate_rack', 0)),
        ]

        # Place targets in target zones
        for target_type, width, height, count in target_types:
            for _ in range(count):
                # Choose a random target zone
                zone = random.choice(self.target_zones) if self.target_zones else None

                if zone:
                    # Place in this zone
                    x = random.uniform(zone['x_min'], zone['x_max'] - width)
                    y = random.uniform(zone['y_min'], zone['y_max'] - height)

                    # Try to find a free position
                    for attempt in range(20):
                        if self._is_area_free(x, y, width, height):
                            # Calculate facing toward safe zone with some variation
                            facing = zone['facing'] + random.randint(-15, 15)

                            item = {
                                'item_type': target_type,
                                'position_x': x,
                                'position_y': y,
                                'rotation': facing,
                                'width': width,
                                'height': height,
                            }
                            self.items.append(item)
                            self._mark_occupied(x, y, width, height)
                            break
                        else:
                            # Try another position in this zone
                            x = random.uniform(zone['x_min'], zone['x_max'] - width)
                            y = random.uniform(zone['y_min'], zone['y_max'] - height)
                else:
                    # Fallback: place anywhere (shouldn't happen with proper zones)
                    x, y = self._find_free_position(width, height, min_distance=1.0)
                    if x is not None:
                        facing = self._calculate_facing_angle(x, y)
                        item = {
                            'item_type': target_type,
                            'position_x': x,
                            'position_y': y,
                            'rotation': facing,
                            'width': width,
                            'height': height,
                        }
                        self.items.append(item)
                        self._mark_occupied(x, y, width, height)

    def _place_no_shoots(self, count):
        """Place no-shoot targets near paper targets"""
        paper_targets = [item for item in self.items if item['item_type'] == 'paper_target']

        placed = 0
        for paper in paper_targets[:count]:
            if placed >= count:
                break

            # Try to place near this paper target
            offset_x = random.choice([-0.8, 0.8])
            offset_y = random.choice([-0.5, 0.5])

            x = paper['position_x'] + offset_x
            y = paper['position_y'] + offset_y

            if self._is_area_free(x, y, 0.5, 0.8):
                item = {
                    'item_type': 'no_shoot',
                    'position_x': x,
                    'position_y': y,
                    'rotation': random.randint(-10, 10),
                    'width': 0.5,
                    'height': 0.8,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 0.5, 0.8)
                placed += 1

    def _place_props(self, available_items):
        """Place props like tables, barrels, windows"""
        # Tables
        table_count = available_items.get('table', 0)
        for _ in range(table_count):
            x, y = self._find_free_position(1.5, 0.8, min_distance=1.5)
            if x is not None:
                item = {
                    'item_type': 'table',
                    'position_x': x,
                    'position_y': y,
                    'rotation': random.choice([0, 90]),
                    'width': 1.5,
                    'height': 0.8,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 1.5, 0.8)

        # Barrels
        barrel_count = available_items.get('barrel', 0)
        for _ in range(barrel_count):
            x, y = self._find_free_position(0.6, 0.6, min_distance=1.0)
            if x is not None:
                item = {
                    'item_type': 'barrel',
                    'position_x': x,
                    'position_y': y,
                    'rotation': 0,
                    'width': 0.6,
                    'height': 0.6,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 0.6, 0.6)

        # Windows
        window_count = available_items.get('window', 0)
        for _ in range(window_count):
            x, y = self._find_free_position(1.0, 1.0, min_distance=1.5)
            if x is not None:
                item = {
                    'item_type': 'window',
                    'position_x': x,
                    'position_y': y,
                    'rotation': 0,
                    'width': 1.0,
                    'height': 1.0,
                }
                self.items.append(item)
                self._mark_occupied(x, y, 1.0, 1.0)

    def _find_free_position(self, width, height, min_distance=1.0, max_attempts=50):
        """Find a free position for an item with given dimensions"""
        for _ in range(max_attempts):
            x = random.uniform(1, self.width - width - 1)
            y = random.uniform(2, self.height - height - 1)

            if self._is_area_free(x, y, width, height, min_distance):
                return (x, y)

        return (None, None)

    def _is_area_free(self, x, y, width, height, buffer=0.5):
        """Check if an area is free from other items"""
        # Check bounds
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            return False

        # Check against occupied areas
        for ox, oy, ow, oh in self.occupied_areas:
            # Check if rectangles overlap with buffer
            if not (x + width + buffer < ox or
                    x > ox + ow + buffer or
                    y + height + buffer < oy or
                    y > oy + oh + buffer):
                return False

        return True

    def _mark_occupied(self, x, y, width, height):
        """Mark an area as occupied"""
        self.occupied_areas.append((x, y, width, height))

    def _calculate_facing_angle(self, x, y):
        """
        Calculate the angle an item should face based on its position
        relative to the safe zone (so it faces toward shooters)
        """
        safe = self.safe_zone

        # Calculate center of safe zone
        safe_center_x = (safe['x_min'] + safe['x_max']) / 2
        safe_center_y = (safe['y_min'] + safe['y_max']) / 2

        # Calculate angle from item to safe zone center
        dx = safe_center_x - x
        dy = safe_center_y - y

        # Convert to degrees (0 = east, 90 = north, 180 = west, 270 = south)
        angle = math.degrees(math.atan2(dy, dx))

        # Adjust to our coordinate system (0 = north, 90 = east, etc.)
        # and add 90 degrees so targets face the direction
        facing = (90 - angle) % 360

        return int(facing)

    def calculate_difficulty_score(self):
        """Calculate a difficulty score for the generated stage"""
        score = 0

        # Count different target types
        target_count = sum(1 for item in self.items if 'target' in item['item_type'])
        score += target_count * 2

        # No-shoots increase difficulty
        no_shoot_count = sum(1 for item in self.items if item['item_type'] == 'no_shoot')
        score += no_shoot_count * 5

        # Obstacles add complexity
        obstacle_count = sum(1 for item in self.items
                           if item['item_type'] in ['barrier', 'wall', 'door'])
        score += obstacle_count * 3

        # Shooting positions add variety
        box_count = sum(1 for item in self.items if item['item_type'] == 'shooting_box')
        score += box_count * 4

        # Stage size factor
        size_factor = (self.width * self.height) / 100
        score *= size_factor

        return round(score, 1)
