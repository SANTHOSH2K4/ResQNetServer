from django.urls import path
from .views import AdminUserRegistrationView, AdminVerifierLoginView, AdminUserListView, AdminUserDetailView,AdminUserUpdateStatusView, serve_pdf, AdminUserSummaryView, RevokeAdminPrivilegesView, AdminGroupsListView, AdminTodosView
from .views import (
    AdminGroupsCreateView, AdminGroupsUpdateView,
    TodoTitleCreateView, TodoTitleUpdateView,
    SubTaskCreateView, SubTaskUpdateView,
)

urlpatterns = [
    path('admin-registration/', AdminUserRegistrationView.as_view(), name='admin-registration'),
    path('admin-verifier-login/', AdminVerifierLoginView.as_view(), name='admin-verifier-login'),
    path('admin-users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin-user-summary/<int:pk>/', AdminUserSummaryView.as_view(), name='admin-user-summary'),
    path('admin-users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin-users/<int:pk>/update-status/', AdminUserUpdateStatusView.as_view(), name='admin-user-update-status'),
    path("uploads/<str:file_path>", serve_pdf, name="serve_pdf"),
    path('revoke-admin/<int:pk>/', RevokeAdminPrivilegesView.as_view(), name='revoke-admin'),
    path('admin-groups/<int:admin_id>/', AdminGroupsListView.as_view(), name='admin-groups-list'),
    path('admin-todos/<int:admin_id>/', AdminTodosView.as_view(), name='admin-todos'),
     path('admin-group-create/', AdminGroupsCreateView.as_view(), name='admin-groups-create'),
    path('admin-group-update/<int:pk>/update/', AdminGroupsUpdateView.as_view(), name='admin-groups-update'),
    path('todo-titles/', TodoTitleCreateView.as_view(), name='todo-titles-create'),
    path('todo-titles/<int:pk>/update/', TodoTitleUpdateView.as_view(), name='todo-titles-update'),    
    path('subtasks/', SubTaskCreateView.as_view(), name='subtasks-create'),
    path('subtasks/<int:pk>/update/', SubTaskUpdateView.as_view(), name='subtasks-update'),
]