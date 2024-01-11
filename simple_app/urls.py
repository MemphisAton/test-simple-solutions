from django.urls import path
from . import views

urlpatterns = [
    path('create-item/', views.create_item, name='create-item'),
    # path('buy/<int:id>/', create_stripe_session, name='create-stripe-session'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('create-intent/<int:item_id>/', views.create_payment_intent, name='create_payment_intent'),
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    path('add-to-order/<int:item_id>/', views.add_to_order, name='add_to_order'),
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout-order/<int:order_id>/', views.checkout_order, name='checkout_order'),
    path('create-checkout-session/<int:item_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('create-checkout-session-for-order/<int:order_id>/', views.create_checkout_session_for_order,
         name='create_checkout_session_for_order'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('create-payment-intent/<int:item_id>/', views.create_payment_intent, name='create_payment_intent'),

]