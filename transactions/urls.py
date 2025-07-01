from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')


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
    path('budget-alerts/', views.budget_alerts, name='budget-alerts'),
    path('budgets/', views.BudgetLimitListView.as_view(), name='budget-list'),
    path('budgets/add/', views.BudgetLimitCreateView.as_view(), name='budget-add'),
    path('budgets/<int:pk>/edit/', views.BudgetLimitUpdateView.as_view(), name='budget-edit'),
    path('budgets/<int:pk>/delete/', views.BudgetLimitDeleteView.as_view(), name='budget-delete'),
    path('api/', include(router.urls)),
]
