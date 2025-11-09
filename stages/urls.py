from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),

    # Stage views
    path('', views.stage_list, name='stage_list'),
    path('create/', views.stage_create, name='stage_create'),
    path('<int:pk>/', views.stage_detail, name='stage_detail'),
    path('<int:pk>/edit/', views.stage_edit, name='stage_edit'),
    path('<int:pk>/delete/', views.stage_delete, name='stage_delete'),
    path('<int:pk>/designer/', views.stage_designer, name='stage_designer'),

    # API endpoints
    path('api/<int:stage_pk>/items/', views.api_get_items, name='api_get_items'),
    path('api/<int:stage_pk>/items/add/', views.api_add_item, name='api_add_item'),
    path('api/items/<int:item_pk>/update/', views.api_update_item, name='api_update_item'),
    path('api/items/<int:item_pk>/delete/', views.api_delete_item, name='api_delete_item'),
]
