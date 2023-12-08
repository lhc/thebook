from django.db import models


class TransactionManager(models.Manager):
    def for_year(self, year):
        return self.filter(date__year=year)
