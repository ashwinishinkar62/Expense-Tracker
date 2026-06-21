
from django.urls import path,include
from .views import *
urlpatterns = [
    path('',home, name="home"),
    path('register/',register,name='register'),
    path('delete-expense/<int:id>/',delete_expense, name='delete_expense'),
    path('edit-expense/<int:id>/',edit_expense, name='edit_expense'),
    path('export-csv/',export_csv,name='export_csv'),
    path('recycle-bin/',recycle_bin, name='recycle_bin'),
    path('restore-expense/<int:id>/',restore_expense,name='restore_expense'),
]
