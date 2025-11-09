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

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Open your browser to http://localhost:8000

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
