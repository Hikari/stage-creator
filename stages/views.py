from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Stage, StageItem
import json


def stage_list(request):
    """
    Display list of all stages
    """
    stages = Stage.objects.all()
    return render(request, 'stages/stage_list.html', {'stages': stages})


def stage_detail(request, pk):
    """
    Display stage details with all items
    """
    stage = get_object_or_404(Stage, pk=pk)
    items = stage.items.all()
    return render(request, 'stages/stage_detail.html', {
        'stage': stage,
        'items': items,
        'total_ammo': stage.get_total_ammo_count(),
        'item_summary': stage.get_item_summary(),
    })


def stage_create(request):
    """
    Create a new stage
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        width = float(request.POST.get('width', 10))
        height = float(request.POST.get('height', 10))

        stage = Stage.objects.create(
            name=name,
            description=description,
            width=width,
            height=height,
            created_by=request.user if request.user.is_authenticated else None
        )
        messages.success(request, f'Stage "{stage.name}" created successfully!')
        return redirect('stage_designer', pk=stage.pk)

    return render(request, 'stages/stage_create.html')


def stage_designer(request, pk):
    """
    Interactive stage designer view
    """
    stage = get_object_or_404(Stage, pk=pk)
    items = stage.items.all()

    # Get available item types
    item_types = StageItem.ITEM_TYPES

    return render(request, 'stages/stage_designer.html', {
        'stage': stage,
        'items': items,
        'item_types': item_types,
        'item_types_json': json.dumps(item_types),
    })


def stage_edit(request, pk):
    """
    Edit stage details
    """
    stage = get_object_or_404(Stage, pk=pk)

    if request.method == 'POST':
        stage.name = request.POST.get('name', stage.name)
        stage.description = request.POST.get('description', stage.description)
        stage.width = float(request.POST.get('width', stage.width))
        stage.height = float(request.POST.get('height', stage.height))
        stage.save()
        messages.success(request, f'Stage "{stage.name}" updated successfully!')
        return redirect('stage_detail', pk=stage.pk)

    return render(request, 'stages/stage_edit.html', {'stage': stage})


def stage_delete(request, pk):
    """
    Delete a stage
    """
    stage = get_object_or_404(Stage, pk=pk)

    if request.method == 'POST':
        stage_name = stage.name
        stage.delete()
        messages.success(request, f'Stage "{stage_name}" deleted successfully!')
        return redirect('stage_list')

    return render(request, 'stages/stage_delete.html', {'stage': stage})


# API Views for AJAX operations

@csrf_exempt
@require_http_methods(["POST"])
def api_add_item(request, stage_pk):
    """
    API endpoint to add an item to a stage
    """
    try:
        stage = get_object_or_404(Stage, pk=stage_pk)
        data = json.loads(request.body)

        item = StageItem.objects.create(
            stage=stage,
            item_type=data.get('item_type'),
            position_x=float(data.get('position_x', 0)),
            position_y=float(data.get('position_y', 0)),
            rotation=float(data.get('rotation', 0)),
            width=float(data.get('width', 0.5)),
            height=float(data.get('height', 0.5)),
            custom_ammo_count=data.get('custom_ammo_count'),
            notes=data.get('notes', ''),
        )

        return JsonResponse({
            'success': True,
            'item': item.to_dict(),
            'total_ammo': stage.get_total_ammo_count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_item(request, item_pk):
    """
    API endpoint to update an item's position/properties
    """
    try:
        item = get_object_or_404(StageItem, pk=item_pk)
        data = json.loads(request.body)

        if 'position_x' in data:
            item.position_x = float(data['position_x'])
        if 'position_y' in data:
            item.position_y = float(data['position_y'])
        if 'rotation' in data:
            item.rotation = float(data['rotation'])
        if 'width' in data:
            item.width = float(data['width'])
        if 'height' in data:
            item.height = float(data['height'])
        if 'custom_ammo_count' in data:
            item.custom_ammo_count = data['custom_ammo_count']
        if 'notes' in data:
            item.notes = data['notes']

        item.save()

        return JsonResponse({
            'success': True,
            'item': item.to_dict(),
            'total_ammo': item.stage.get_total_ammo_count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_item(request, item_pk):
    """
    API endpoint to delete an item
    """
    try:
        item = get_object_or_404(StageItem, pk=item_pk)
        stage = item.stage
        item.delete()

        return JsonResponse({
            'success': True,
            'total_ammo': stage.get_total_ammo_count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_get_items(request, stage_pk):
    """
    API endpoint to get all items for a stage
    """
    try:
        stage = get_object_or_404(Stage, pk=stage_pk)
        items = [item.to_dict() for item in stage.items.all()]

        return JsonResponse({
            'success': True,
            'items': items,
            'total_ammo': stage.get_total_ammo_count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
