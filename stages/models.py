from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class Stage(models.Model):
    """
    Represents an IPSC stage design
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    width = models.FloatField(
        validators=[MinValueValidator(1.0)],
        help_text="Stage width in meters"
    )
    height = models.FloatField(
        validators=[MinValueValidator(1.0)],
        help_text="Stage height in meters"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stages',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

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
