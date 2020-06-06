from django.db import models
from .validators import validate_file_extension

# Create your models here.
class File(models.Model):
    file = models.FileField(blank=False, null=False,validators=[validate_file_extension])
    digitizaton_status = models.CharField(max_length=25,default='digitization_pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    invoice_number = models.CharField(max_length=25,null=True)
    order_number = models.CharField(max_length=25,null=True)
    bill_to = models.TextField(null = True)
    ship_to = models.TextField(null = True)
    invoice_date = models.CharField(max_length=25,null=True)
    total_amount = models.CharField(max_length=25,null=True,blank=True)
    invoice_from = models.CharField(max_length=250,null=True)
    to = models.CharField(max_length=250,null=True)

class InvoiceItem(models.Model):
    File = models.ForeignKey('File',on_delete=models.CASCADE,related_name='iteminfo',null=True)
    item = models.CharField(max_length=100,null=True)
    quantity = models.CharField(max_length=25,null=True)
    price = models.CharField(max_length=25,null=True)
    item_tax = models.CharField(max_length=25,null=True,blank=True)
    item_total = models.CharField(max_length=25,null=True,blank=True)



    