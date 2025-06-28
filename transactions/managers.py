from django.db import models


class BudgetLimitManager(models.Manager):
    def for_user(self, user):
        return self.filter(user=user)

    def get_by_period(self, user, period):
        return self.filter(user=user, period=period)


class TransactionManager(models.Manager):
    def income(self, user):
        return self.filter(user=user, type=self.model.INCOME)

    def expenses(self, user):
        return self.filter(user=user, type=self.model.EXPENSE)
