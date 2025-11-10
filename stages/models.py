from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class Stage(models.Model):
    """
    Represents an IPSC stage design
    """
    BULLET_TRAP_CHOICES = [
        ('north', 'North (Downrange)'),
        ('south', 'South (Uprange)'),
        ('east', 'East (Right)'),
        ('west', 'West (Left)'),
        ('north-east', 'North-East (Corner)'),
        ('north-west', 'North-West (Corner)'),
        ('south-east', 'South-East (Corner)'),
        ('south-west', 'South-West (Corner)'),
        ('east-west', 'East-West (Both Sides)'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    width = models.FloatField(
        validators=[MinValueValidator(1.0)],
        help_text="Stage width in meters"
    )
    height = models.FloatField(
        validators=[MinValueValidator(1.0)],
        help_text="Stage length (depth) in meters"
    )
    bullet_trap_sides = models.CharField(
        max_length=20,
        choices=BULLET_TRAP_CHOICES,
        default='north',
        help_text="Where bullet traps are positioned on the stage"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stages',
        null=True,
        blank=True
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Make this stage visible to all users"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def length(self):
        """Alias for height field - using 'length' for better shooting stage terminology"""
        return self.height

    def get_total_ammo_count(self):
        """
        Calculate total ammunition needed for this stage
        """
        total = 0
        for item in self.items.all():
            total += item.get_ammo_count()
        return total

    def get_item_summary(self):
        """
        Get a summary of items on this stage
        """
        summary = {}
        for item in self.items.all():
            item_type = item.get_item_type_display()
            if item_type in summary:
                summary[item_type] += 1
            else:
                summary[item_type] = 1
        return summary

    def calculate_difficulty(self):
        """
        Calculate comprehensive difficulty metrics for this stage.
        Returns a dictionary with difficulty score and analysis.
        """
        items = self.items.all()

        # Count different item types
        paper_targets = items.filter(item_type='paper_target').count()
        steel_targets = items.filter(item_type='steel_target').count()
        poppers = items.filter(item_type='popper').count()
        plate_racks = items.filter(item_type='plate_rack').count()
        no_shoots = items.filter(item_type='no_shoot').count()
        barriers = items.filter(item_type='barrier').count()
        walls = items.filter(item_type='wall').count()
        shooting_boxes = items.filter(item_type='shooting_box').count()

        total_scoring_targets = paper_targets + steel_targets + poppers + (plate_racks * 5)
        total_obstacles = barriers + walls

        # Calculate base difficulty score (0-100)
        score = 0
        factors = []

        # Factor 1: Number of targets (0-30 points)
        target_score = min(30, total_scoring_targets * 1.5)
        score += target_score
        if total_scoring_targets > 0:
            factors.append(f"{total_scoring_targets} scoring targets (+{target_score:.0f})")

        # Factor 2: No-shoot targets (0-20 points)
        no_shoot_score = min(20, no_shoots * 4)
        score += no_shoot_score
        if no_shoots > 0:
            factors.append(f"{no_shoots} no-shoot targets (+{no_shoot_score:.0f})")

        # Factor 3: Obstacles complexity (0-15 points)
        obstacle_score = min(15, total_obstacles * 2.5)
        score += obstacle_score
        if total_obstacles > 0:
            factors.append(f"{total_obstacles} obstacles (+{obstacle_score:.0f})")

        # Factor 4: Multiple shooting positions (0-15 points)
        shooting_position_score = 0
        if shooting_boxes > 1:
            shooting_position_score = min(15, (shooting_boxes - 1) * 5)
            score += shooting_position_score
            factors.append(f"{shooting_boxes} shooting positions (+{shooting_position_score:.0f})")

        # Factor 5: Stage size complexity (0-10 points)
        stage_area = self.width * self.height
        size_score = 0
        if stage_area > 150:
            size_score = min(10, (stage_area - 150) / 20)
            score += size_score
            factors.append(f"Large stage area ({stage_area:.0f}m²) (+{size_score:.0f})")

        # Factor 6: Target variety (0-10 points)
        target_types = sum([
            1 if paper_targets > 0 else 0,
            1 if steel_targets > 0 else 0,
            1 if poppers > 0 else 0,
            1 if plate_racks > 0 else 0
        ])
        variety_score = target_types * 2.5
        score += variety_score
        if target_types > 1:
            factors.append(f"{target_types} target types (+{variety_score:.0f})")

        # Determine difficulty level
        if score < 25:
            level = "Easy"
            color = "#27ae60"
        elif score < 50:
            level = "Medium"
            color = "#f39c12"
        elif score < 75:
            level = "Hard"
            color = "#e67e22"
        else:
            level = "Very Hard"
            color = "#e74c3c"

        # IPSC Compliance checks
        compliance_issues = []
        compliance_warnings = []

        total_ammo = self.get_total_ammo_count()

        # IPSC rules: minimum 12 rounds, maximum 32 rounds for a standard stage
        if total_ammo < 12:
            compliance_issues.append(f"Too few rounds ({total_ammo}). IPSC minimum is 12.")
        elif total_ammo > 32:
            compliance_warnings.append(f"High round count ({total_ammo}). Standard IPSC maximum is 32.")

        # Minimum 8 scoring targets
        if total_scoring_targets < 8:
            compliance_issues.append(f"Too few scoring targets ({total_scoring_targets}). IPSC minimum is 8.")

        # At least 2 different types of targets recommended
        if target_types < 2:
            compliance_warnings.append("Consider using at least 2 different target types for variety.")

        # No-shoot ratio warning
        if no_shoots > 0 and total_scoring_targets > 0:
            no_shoot_ratio = no_shoots / total_scoring_targets
            if no_shoot_ratio > 0.5:
                compliance_warnings.append(f"High no-shoot ratio ({no_shoot_ratio:.1%}). Consider reducing no-shoots.")

        # Start position check
        start_positions = items.filter(item_type='start_position').count()
        if start_positions == 0:
            compliance_issues.append("No start position defined.")
        elif start_positions > 1:
            compliance_warnings.append("Multiple start positions defined.")

        is_compliant = len(compliance_issues) == 0

        return {
            'score': round(score, 1),
            'level': level,
            'color': color,
            'factors': factors,
            'is_compliant': is_compliant,
            'compliance_issues': compliance_issues,
            'compliance_warnings': compliance_warnings,
            'total_ammo': total_ammo,
            'total_targets': total_scoring_targets,
            'stats': {
                'paper_targets': paper_targets,
                'steel_targets': steel_targets,
                'poppers': poppers,
                'plate_racks': plate_racks,
                'no_shoots': no_shoots,
                'obstacles': total_obstacles,
                'shooting_positions': shooting_boxes,
                'stage_area': round(stage_area, 1),
            }
        }


class StageItem(models.Model):
    """
    Represents an item placed on an IPSC stage
    """
    ITEM_TYPES = [
        ('paper_target', 'Paper Target'),
        ('steel_target', 'Steel Target'),
        ('popper', 'Popper'),
        ('plate_rack', 'Plate Rack'),
        ('no_shoot', 'No Shoot Target'),
        ('barrier', 'Barrier'),
        ('wall', 'Wall'),
        ('shooting_box', 'Shooting Box'),
        ('start_position', 'Start Position'),
        ('table', 'Table'),
        ('barrel', 'Barrel'),
        ('door', 'Door'),
        ('window', 'Window'),
    ]

    # Default ammo requirements for different target types
    AMMO_REQUIREMENTS = {
        'paper_target': 2,  # Typically 2 rounds per paper target
        'steel_target': 1,
        'popper': 1,
        'plate_rack': 5,    # Typically 5 plates
        'no_shoot': 0,
        'barrier': 0,
        'wall': 0,
        'shooting_box': 0,
        'start_position': 0,
        'table': 0,
        'barrel': 0,
        'door': 0,
        'window': 0,
    }

    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES)
    position_x = models.FloatField(help_text="X position in meters")
    position_y = models.FloatField(help_text="Y position in meters")
    rotation = models.FloatField(default=0, help_text="Rotation in degrees")
    width = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.1)],
        help_text="Item width in meters"
    )
    height = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.1)],
        help_text="Item height in meters"
    )
    custom_ammo_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Override default ammo count for this item"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.get_item_type_display()} on {self.stage.name}"

    def get_ammo_count(self):
        """
        Get the ammunition count for this item
        """
        if self.custom_ammo_count is not None:
            return self.custom_ammo_count
        return self.AMMO_REQUIREMENTS.get(self.item_type, 0)

    def to_dict(self):
        """
        Convert to dictionary for JSON serialization
        """
        return {
            'id': self.id,
            'item_type': self.item_type,
            'item_type_display': self.get_item_type_display(),
            'position_x': self.position_x,
            'position_y': self.position_y,
            'rotation': self.rotation,
            'width': self.width,
            'height': self.height,
            'custom_ammo_count': self.custom_ammo_count,
            'ammo_count': self.get_ammo_count(),
            'notes': self.notes,
        }
