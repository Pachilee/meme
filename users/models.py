from django.db import models

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    pass

#create a table for database 
class UserList(models.Model):
    #create name for added list name and allow to delete
    user = models.ForeignKey(CustomUser, verbose_name="user", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#creating a list of items for movie id and movie name
class ListItem(models.Model):
    list = models.ForeignKey(UserList, verbose_name="list", on_delete=models.CASCADE)
    movie_id = models.CharField(max_length=255)
    movie_name = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"Movie Id: {self.movie_id} in {self.list}"
