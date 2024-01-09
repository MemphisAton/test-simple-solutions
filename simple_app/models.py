import stripe
from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)  # Например, 'USD'


class Order(models.Model):
    items = models.ManyToManyField(Item, through="OrderItem")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='pending')  # Например: pending, paid, shipped, etc.

    def calculate_total_price(self):
        '''
        Вычисляет общую стоимость с налогом и скидкой
        '''
        items_total = sum(item.get_cost() for item in self.order_items.all())
        discounts = sum(items_total * (discount.rate / 100) for discount in self.discount_set.all())
        taxes = sum((items_total - discounts) * tax.rate / 100 for tax in self.tax_set.all())
        self.total_price = items_total - discounts + taxes
        self.save()

    @property
    def total_price_before_discounts(self):
        """Возвращает общую стоимость заказа без учета скидок."""
        return sum(order_item.item.price * order_item.quantity for order_item in self.order_items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.item.price * self.quantity



def create_payment_intent(order):
    """
    функция для создания PaymentIntent в Stripe при подтверждении заказа
    """
    # Предполагается, что все товары в заказе в одной валюте
    currency = order.items.first().currency
    amount = int(order.total_price * 100)  # Stripe работает с центами/копейками

    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        metadata={'order_id': order.id},
    )
    return payment_intent


class Discount(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Процент скидки от общей стоимости заказа")

    @property
    def amount(self):
        return (self.rate / 100) * self.order.total_price_before_discounts

    def __str__(self):
        return f"{self.rate}% discount for Order {self.order.id}"


class Tax(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
