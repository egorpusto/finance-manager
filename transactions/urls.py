from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = routers.DefaultRouter()
router.register(r"transactions", views.TransactionViewSet, basename="transaction")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"budgets", views.BudgetLimitViewSet, basename="api-budget")

app_name = "transactions"

urlpatterns = [
    path("", views.TransactionListView.as_view(), name="home"),
    path(
        "login/",
        csrf_protect(LoginView.as_view(template_name="registration/login.html")),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("transactions/", views.TransactionListView.as_view(), name="list"),
    path("transactions/add/", views.CreateTransactionView.as_view(), name="create"),
    path("transactions/import/", views.import_transactions, name="import"),
    path(
        "transactions/<int:pk>/",
        views.TransactionDetailView.as_view(),
        name="transaction_detail",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
    path(
        "categories/<int:pk>/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path("export-transactions/", views.export_transactions, name="export"),
    path("statistics/", views.statistics_view, name="statistics"),
    path("budgets/", views.BudgetLimitListView.as_view(), name="budget-list"),
    path("budgets/add/", views.BudgetLimitCreateView.as_view(), name="budget-add"),
    path(
        "budgets/<int:pk>/edit/",
        views.BudgetLimitUpdateView.as_view(),
        name="budget-edit",
    ),
    path(
        "budgets/<int:pk>/delete/",
        views.BudgetLimitDeleteView.as_view(),
        name="budget-delete",
    ),
    # API
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="transactions:schema"),
        name="swagger-ui",
    ),
]
