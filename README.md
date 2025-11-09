# IPSC Stage Creator

A Django-based web application for designing IPSC (International Practical Shooting Confederation) stages with drag-and-drop functionality.

## Features

- Interactive drag-and-drop stage designer
- Define custom stage dimensions
- Add and position stage items (targets, barriers, shooting boxes, etc.)
- Automatic ammunition counting
- Save and manage multiple stages
- Responsive design

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Sync dependencies and create virtual environment:
```bash
uv sync
```

3. Run migrations:
```bash
uv run python manage.py migrate
```

4. Create a superuser:
```bash
uv run python manage.py createsuperuser
```

5. Run the development server:
```bash
uv run python manage.py runserver
```

6. Open your browser to http://localhost:8000

### Alternative: Using pip

If you prefer using pip:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Usage

1. Click "Create New Stage" to start designing
2. Set the stage dimensions
3. Drag and drop items onto the stage
4. Save your stage design
5. View ammunition count for your stage

## Future Features

- AI-powered stage design suggestions based on available items and constraints
- Stage difficulty calculator
- Export stage designs as PDF
- Share stages with other users
