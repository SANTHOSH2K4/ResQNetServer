from django.urls import path
from .views import AdminUserRegistrationView, AdminVerifierLoginView, AdminUserListView, AdminUserDetailView,AdminUserUpdateStatusView, serve_pdf, AdminUserSummaryView, RevokeAdminPrivilegesView, AdminGroupsListView, AdminTodosView
from .views import (
    AdminGroupsCreateView, AdminGroupsUpdateView,
    TodoTitleCreateView, TodoTitleUpdateView,
    SubTaskCreateView, SubTaskUpdateView,
    send_otp, verify_otp,
    GeneralUserRegistrationView,
    GroupListView, CreateGroupView,
    CreateVolunteerRequestView,ApproveVolunteerView,
    SendMessageView, trend_extractor_view,
    trend_summarizer_view,fetch_all_todos,create_or_update_todo,delete_todo_or_subtask,create_subtask,hazlebot_view,update_subtask
)

urlpatterns = [
    path('admin-registration/', AdminUserRegistrationView.as_view(), name='admin-registration'),
    path('api/general-register/', GeneralUserRegistrationView.as_view(), name='general_register'),
    path('api/volunteer_request/', CreateVolunteerRequestView.as_view(), name='volunteer_request'),
    path('api/approve_volunteer/', ApproveVolunteerView.as_view(), name='ApproveVolunteerView'),   
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
    path('api/send_otp/', send_otp, name='send_otp'),
    path('api/verify_otp/', verify_otp, name='verify_otp'),
    path('api/groups/', GroupListView.as_view(), name='group_list'),
    path('api/create_group/', CreateGroupView.as_view(), name='create_group'),
    path('api/send_message/', SendMessageView.as_view(), name='send_message'),
    path('api/trend-extractor/', trend_extractor_view, name='trend_extractor_api'),
    path('api/trend-summarizer/', trend_summarizer_view, name='trend_summarizer_api'),
     path('todos/', fetch_all_todos, name='fetch_all_todos'),
    path('todos/manage/', create_or_update_todo, name='create_or_update_todo'),
    path('todos/delete/', delete_todo_or_subtask, name='delete_todo_or_subtask'),
     path('subtasks/create/', create_subtask, name='create_subtask'),
     path('api/hazlebot/',hazlebot_view,name='hazlebot_view'),
      path('todos/', fetch_all_todos, name='fetch_all_todos'),
    path('todos/manage/', create_or_update_todo, name='create_or_update_todo'),
    path('todos/delete/', delete_todo_or_subtask, name='delete_todo_or_subtask'),
     path('subtasks/create/', create_subtask, name='create_subtask'),
     path('subtasks/update/', update_subtask, name='update_subtask'),



]