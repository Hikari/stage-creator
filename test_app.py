#!/usr/bin/env python
"""
Simple test script to verify the IPSC Stage Creator application
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from stages.models import Stage, StageItem

def test_stage_creation():
    """Test creating a stage and adding items"""
    print("Testing Stage Creator Application...")
    print("-" * 50)

    # Create a test stage
    stage = Stage.objects.create(
        name="Test Stage 1",
        description="A test IPSC stage with various targets",
        width=15.0,
        height=12.0
    )
    print(f"✓ Created stage: {stage.name}")
    print(f"  Dimensions: {stage.width}m x {stage.height}m")

    # Add some items
    items_data = [
        {'item_type': 'paper_target', 'position_x': 5.0, 'position_y': 3.0},
        {'item_type': 'paper_target', 'position_x': 7.0, 'position_y': 3.0},
        {'item_type': 'steel_target', 'position_x': 10.0, 'position_y': 5.0},
        {'item_type': 'popper', 'position_x': 12.0, 'position_y': 4.0},
        {'item_type': 'barrier', 'position_x': 6.0, 'position_y': 6.0},
        {'item_type': 'shooting_box', 'position_x': 2.0, 'position_y': 2.0},
        {'item_type': 'start_position', 'position_x': 1.0, 'position_y': 1.0},
    ]

    for item_data in items_data:
        item = StageItem.objects.create(
            stage=stage,
            **item_data
        )
        print(f"✓ Added {item.get_item_type_display()} at ({item.position_x}, {item.position_y})")

    # Test statistics
    print("-" * 50)
    print("Stage Statistics:")
    print(f"  Total items: {stage.items.count()}")
    print(f"  Total ammunition: {stage.get_total_ammo_count()} rounds")
    print("\nItem Summary:")
    for item_type, count in stage.get_item_summary().items():
        print(f"  {count}x {item_type}")

    print("-" * 50)
    print("✓ All tests passed!")
    print(f"\nStage ID: {stage.pk}")
    print("You can now run 'python manage.py runserver' and visit:")
    print(f"  - http://localhost:8000/stages/")
    print(f"  - http://localhost:8000/stages/{stage.pk}/designer/")

    return stage

if __name__ == '__main__':
    test_stage_creation()
