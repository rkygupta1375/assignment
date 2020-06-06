from rest_framework import serializers
from .models import File,InvoiceItem

class FileSerializer(serializers.ModelSerializer):
  class Meta():
    model = File
    fields = ('id','file', 'timestamp',)

class NonDigSerializer(serializers.ModelSerializer):
  class Meta():
    model = File
    fields = ('id','file','timestamp',)



class ItemSerializer(serializers.ModelSerializer):
  class Meta():
    model = InvoiceItem
    fields = '__all__'

class ParsedSerializer(serializers.ModelSerializer):
  iteminfo = ItemSerializer(many=True)
  class Meta():
    model = File
    fields = ('id','file','iteminfo','invoice_from','to','bill_to','ship_to','invoice_number','invoice_date','order_number','total_amount')

class UpdateSerializer(serializers.ModelSerializer):
  class Meta():
    model = File



