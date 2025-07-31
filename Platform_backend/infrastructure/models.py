from django.db import models
from organizations.models import Workspace

class Machine(models.Model):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.workspace}"

class NodeType(models.Model):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

class Node(models.Model):
    name = models.CharField(max_length=255)
    node_data = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    node_type = models.ForeignKey(NodeType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.node_data} - {self.machine}"

class Service(models.Model):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    node_type = models.ForeignKey(NodeType, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.node_type}"

class Gateway(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.workspace}"