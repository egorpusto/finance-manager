from rest_framework import serializers

from .models import BudgetLimit, Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "amount",
            "date",
            "type",
            "type_display",
            "category",
            "category_name",
            "description",
        ]
        read_only_fields = ["id"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_category(self, value):
        user = self.context["request"].user
        if value and value.user != user:
            raise serializers.ValidationError("Invalid category.")
        return value


class BudgetLimitSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    period_display = serializers.CharField(source="get_period_display", read_only=True)

    class Meta:
        model = BudgetLimit
        fields = [
            "id",
            "category",
            "category_name",
            "limit_amount",
            "period",
            "period_display",
        ]
        read_only_fields = ["id"]
