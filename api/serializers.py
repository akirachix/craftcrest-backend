from rest_framework import serializers
from cart.models import ShoppingCart
from products.models import Inventory


from rest_framework import serializers
from cart.models import ShoppingCart

class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = '__all__'
       



class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'