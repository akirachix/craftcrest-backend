from rest_framework import serializers
from cart.models import ShoppingCart
from products.models import Inventory


from rest_framework import serializers
from cart.models import ShoppingCart , Item

class ShoppingCartSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(many=True, queryset=Item.objects.all())
    class Meta:
        model = ShoppingCart
        fields = '__all__'
    def update(self, instance, validated_data):
        items = validated_data.pop('item', None)
        if items is not None:
            instance.item.set(items)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class ItemSerializer (serializers.ModelSerializer):
    class Meta:
        model= Item
        fields = '__all__'       

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'



    