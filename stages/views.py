from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Stage, StageItem
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
import json


def stage_list(request):
    """
    Display list of all public stages and user's own stages
    """
    if request.user.is_authenticated:
        # Show public stages and user's own stages (both public and private)
        stages = Stage.objects.filter(
            Q(is_public=True) | Q(created_by=request.user)
        ).distinct()
    else:
        # Show only public stages for anonymous users
        stages = Stage.objects.filter(is_public=True)

    return render(request, 'stages/stage_list.html', {'stages': stages})


def stage_detail(request, pk):
    """
    Display stage details with all items
    """
    stage = get_object_or_404(Stage, pk=pk)

    # Check if user has permission to view this stage
    if not stage.is_public:
        if not request.user.is_authenticated or stage.created_by != request.user:
            messages.error(request, 'You do not have permission to view this private stage.')
            return redirect('stage_list')

    items = stage.items.all()
    difficulty = stage.calculate_difficulty()
    return render(request, 'stages/stage_detail.html', {
        'stage': stage,
        'items': items,
        'total_ammo': stage.get_total_ammo_count(),
        'item_summary': stage.get_item_summary(),
        'difficulty': difficulty,
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
        is_public = request.POST.get('is_public') == 'on'

        stage = Stage.objects.create(
            name=name,
            description=description,
            width=width,
            height=height,
            is_public=is_public,
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


# Authentication Views

def user_register(request):
    """
    User registration view
    """
    if request.user.is_authenticated:
        return redirect('stage_list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('stage_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'stages/register.html', {'form': form})


def user_login(request):
    """
    User login view
    """
    if request.user.is_authenticated:
        return redirect('stage_list')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'stage_list')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()

    return render(request, 'stages/login.html', {'form': form})


def user_logout(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('stage_list')


@login_required
def user_profile(request):
    """
    User profile view
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)

    # Get user's stages
    user_stages = Stage.objects.filter(created_by=request.user)

    return render(request, 'stages/profile.html', {
        'form': form,
        'user_stages': user_stages,
    })


# Export and Sharing Views

def stage_export_pdf(request, pk):
    """
    Export stage as PDF
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from django.http import HttpResponse
    import io

    stage = get_object_or_404(Stage, pk=pk)

    # Check permission
    if not stage.is_public:
        if not request.user.is_authenticated or stage.created_by != request.user:
            messages.error(request, 'You do not have permission to export this private stage.')
            return redirect('stage_list')

    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(1*inch, height - 1*inch, stage.name)

    # Metadata
    p.setFont("Helvetica", 12)
    y_position = height - 1.5*inch

    if stage.description:
        p.drawString(1*inch, y_position, f"Description: {stage.description}")
        y_position -= 0.3*inch

    p.drawString(1*inch, y_position, f"Dimensions: {stage.width}m x {stage.height}m")
    y_position -= 0.3*inch
    p.drawString(1*inch, y_position, f"Total Ammunition: {stage.get_total_ammo_count()} rounds")
    y_position -= 0.3*inch
    p.drawString(1*inch, y_position, f"Created: {stage.created_at.strftime('%Y-%m-%d')}")
    y_position -= 0.5*inch

    # Item Summary
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, y_position, "Item Summary:")
    y_position -= 0.3*inch

    p.setFont("Helvetica", 11)
    item_summary = stage.get_item_summary()
    for item_type, count in item_summary.items():
        p.drawString(1.2*inch, y_position, f"• {count}x {item_type}")
        y_position -= 0.25*inch

    y_position -= 0.3*inch

    # Stage Layout (simplified top-down view)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, y_position, "Stage Layout:")
    y_position -= 0.4*inch

    # Draw stage boundary
    scale = 30  # pixels per meter
    stage_width_px = min(stage.width * scale, 6*inch)
    stage_height_px = min(stage.height * scale, 4*inch)

    p.setStrokeColor(colors.black)
    p.setLineWidth(2)
    p.rect(1*inch, y_position - stage_height_px, stage_width_px, stage_height_px)

    # Draw grid
    p.setStrokeColor(colors.lightgrey)
    p.setLineWidth(0.5)
    for i in range(int(stage.width) + 1):
        x = 1*inch + (i * scale)
        p.line(x, y_position - stage_height_px, x, y_position)
    for i in range(int(stage.height) + 1):
        y = y_position - (i * scale)
        p.line(1*inch, y, 1*inch + stage_width_px, y)

    # Draw items
    items = stage.items.all()
    for item in items:
        x = 1*inch + (item.position_x * scale)
        y = y_position - (item.position_y * scale)
        w = item.width * scale
        h = item.height * scale

        # Color based on item type
        if 'target' in item.item_type:
            p.setFillColor(colors.red)
        elif 'barrier' in item.item_type or 'wall' in item.item_type:
            p.setFillColor(colors.brown)
        elif 'shooting_box' in item.item_type or 'start' in item.item_type:
            p.setFillColor(colors.green)
        else:
            p.setFillColor(colors.grey)

        p.setStrokeColor(colors.black)
        p.setLineWidth(1)
        p.rect(x, y - h, w, h, fill=1, stroke=1)

        # Label
        p.setFillColor(colors.white)
        p.setFont("Helvetica", 6)
        label = item.get_item_type_display()[:8]
        p.drawString(x + 2, y - h + 2, label)

    # Footer
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.grey)
    p.drawString(1*inch, 0.5*inch, f"Generated by IPSC Stage Creator - {stage.created_at.strftime('%Y-%m-%d')}")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{stage.name.replace(" ", "_")}_stage.pdf"'
    return response


def stage_export_json(request, pk):
    """
    Export stage as JSON
    """
    stage = get_object_or_404(Stage, pk=pk)

    # Check permission
    if not stage.is_public:
        if not request.user.is_authenticated or stage.created_by != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)

    items = stage.items.all()

    data = {
        'name': stage.name,
        'description': stage.description,
        'width': stage.width,
        'height': stage.height,
        'created_at': stage.created_at.isoformat(),
        'items': [item.to_dict() for item in items],
        'total_ammo': stage.get_total_ammo_count(),
        'item_summary': stage.get_item_summary(),
    }

    response = JsonResponse(data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="{stage.name.replace(" ", "_")}_stage.json"'
    return response


def stage_import_json(request):
    """
    Import stage from JSON
    """
    if request.method == 'POST' and request.FILES.get('json_file'):
        try:
            json_file = request.FILES['json_file']
            data = json.loads(json_file.read().decode('utf-8'))

            # Create stage
            stage = Stage.objects.create(
                name=data.get('name', 'Imported Stage'),
                description=data.get('description', ''),
                width=data.get('width', 10),
                height=data.get('height', 10),
                created_by=request.user if request.user.is_authenticated else None,
                is_public=False  # Imported stages are private by default
            )

            # Create items
            for item_data in data.get('items', []):
                StageItem.objects.create(
                    stage=stage,
                    item_type=item_data['item_type'],
                    position_x=item_data['position_x'],
                    position_y=item_data['position_y'],
                    rotation=item_data.get('rotation', 0),
                    width=item_data.get('width', 0.5),
                    height=item_data.get('height', 0.5),
                    custom_ammo_count=item_data.get('custom_ammo_count'),
                    notes=item_data.get('notes', ''),
                )

            messages.success(request, f'Stage "{stage.name}" imported successfully!')
            return redirect('stage_designer', pk=stage.pk)

        except Exception as e:
            messages.error(request, f'Error importing stage: {str(e)}')
            return redirect('stage_list')

    return render(request, 'stages/stage_import.html')


def stage_print_view(request, pk):
    """
    Print-friendly view of stage
    """
    stage = get_object_or_404(Stage, pk=pk)

    # Check permission
    if not stage.is_public:
        if not request.user.is_authenticated or stage.created_by != request.user:
            messages.error(request, 'You do not have permission to view this private stage.')
            return redirect('stage_list')

    items = stage.items.all()
    return render(request, 'stages/stage_print.html', {
        'stage': stage,
        'items': items,
        'total_ammo': stage.get_total_ammo_count(),
        'item_summary': stage.get_item_summary(),
    })


# AI-Powered Stage Generation Views

def stage_generate_ai(request):
    """
    AI stage generation interface
    """
    if request.method == 'POST':
        from .stage_generator import StageGenerator

        name = request.POST.get('name', 'AI Generated Stage')
        description = request.POST.get('description', '')
        width = float(request.POST.get('width', 15))
        height = float(request.POST.get('height', 12))
        difficulty = request.POST.get('difficulty', 'medium')
        is_public = request.POST.get('is_public') == 'on'

        # Create stage
        stage = Stage.objects.create(
            name=name,
            description=description,
            width=width,
            height=height,
            is_public=is_public,
            created_by=request.user if request.user.is_authenticated else None
        )

        # Generate items
        generator = StageGenerator(width, height, difficulty)
        items_data = generator.generate()

        # Create items
        for item_data in items_data:
            StageItem.objects.create(
                stage=stage,
                **item_data
            )

        messages.success(request, f'AI-generated stage "{stage.name}" created successfully with {len(items_data)} items!')
        return redirect('stage_designer', pk=stage.pk)

    return render(request, 'stages/stage_generate.html', {
        'item_types': StageItem.ITEM_TYPES,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_items(request, stage_pk):
    """
    API endpoint to generate items for an existing stage
    """
    from .stage_generator import StageGenerator

    try:
        stage = get_object_or_404(Stage, pk=stage_pk)

        # Check permission
        if request.user.is_authenticated and stage.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        difficulty = data.get('difficulty', 'medium')
        available_items = data.get('available_items', None)
        clear_existing = data.get('clear_existing', False)

        # Clear existing items if requested
        if clear_existing:
            stage.items.all().delete()

        # Generate items
        generator = StageGenerator(stage.width, stage.height, difficulty)
        items_data = generator.generate(available_items)

        # Create items
        created_items = []
        for item_data in items_data:
            item = StageItem.objects.create(
                stage=stage,
                **item_data
            )
            created_items.append(item.to_dict())

        return JsonResponse({
            'success': True,
            'items': created_items,
            'total_ammo': stage.get_total_ammo_count(),
            'difficulty_score': generator.calculate_difficulty_score(),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
