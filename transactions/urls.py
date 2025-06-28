from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView, LogoutView


app_name = 'transactions'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('transactions/', views.TransactionListView.as_view(), name='list'),
    path('transactions/add/', views.CreateTransactionView.as_view(), name='create'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('export-transactions/', views.export_transactions, name='export'),
    
]
