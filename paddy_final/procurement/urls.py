"""
URL configuration for Procurement Portal
"""
from django.urls import path
from . import views
from . import ai_views
from . import marketplace_views
from . import ml_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('farmer/login/', views.farmer_login, name='farmer_login'),
    path('officer/login/', views.officer_login, name='officer_login'),
    path('admin-portal/login/', views.admin_login, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('farmer/register/', views.farmer_register, name='farmer_register'),

    # Farmer
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/book-slot/', views.farmer_book_slot, name='farmer_book_slot'),
    path('farmer/booking-status/', views.farmer_booking_status, name='farmer_booking_status'),
    path('farmer/payment-status/', views.farmer_payment_status, name='farmer_payment_status'),
    path('farmer/invoice/<int:bill_id>/', views.farmer_download_invoice, name='farmer_download_invoice'),

    # Officer
    path('officer/dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('officer/verify-land/', views.officer_verify_land, name='officer_verify_land'),
    path('officer/verify-land/<int:land_id>/approve/', views.officer_verify_land_approve, name='officer_verify_land_approve'),
    path('officer/approve-booking/', views.officer_approve_booking, name='officer_approve_booking'),
    path('officer/approve-booking/<int:booking_id>/', views.officer_approve_booking_do, name='officer_approve_booking_do'),
    path('officer/validate-procurement/', views.officer_validate_procurement, name='officer_validate_procurement'),
    path('officer/validate-procurement/<int:procurement_id>/', views.officer_validate_weight, name='officer_validate_weight'),

    # Admin
    path('admin-portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin-portal/set-msp/', views.admin_set_msp, name='admin_set_msp'),
    path('admin-portal/reports/', views.admin_reports, name='admin_reports'),
    path('admin-portal/approve-payments/', views.admin_approve_payments, name='admin_approve_payments'),
    path('admin-portal/approve-payment/<int:payment_id>/', views.admin_approve_payment_do, name='admin_approve_payment_do'),

    # ── AI Features ──
    path('ai/chat/', ai_views.farm_chatbot, name='ai_chatbot'),
    path('ai/risk/<int:booking_id>/', ai_views.analyze_booking_risk, name='ai_risk'),
    path('ai/price-advisory/', ai_views.price_advisory, name='ai_price_advisory'),
    path('ai/explain-rejection/<int:booking_id>/', ai_views.explain_rejection, name='ai_explain_rejection'),

    # ── Marketplace — Dual Channel ──
    path('marketplace/', marketplace_views.farmer_marketplace, name='farmer_marketplace'),
    path('marketplace/offer/<int:offer_id>/', marketplace_views.farmer_offer_detail, name='farmer_offer_detail'),
    path('marketplace/my-deals/', marketplace_views.farmer_my_deals, name='farmer_my_deals'),
    path('marketplace/cancel-deal/<int:deal_id>/', marketplace_views.farmer_cancel_deal, name='farmer_cancel_deal'),
    path('marketplace/api/offers/<int:crop_id>/', marketplace_views.api_crop_offers, name='api_crop_offers'),

    # Buyer
    path('buyer/register/', marketplace_views.buyer_register, name='buyer_register'),
    path('buyer/login/', marketplace_views.buyer_login, name='buyer_login'),
    path('buyer/dashboard/', marketplace_views.buyer_dashboard, name='buyer_dashboard'),
    path('buyer/create-offer/', marketplace_views.buyer_create_offer, name='buyer_create_offer'),
    path('buyer/offer/<int:offer_id>/deals/', marketplace_views.buyer_offer_deals, name='buyer_offer_deals'),
    path('buyer/deal/<int:deal_id>/action/', marketplace_views.buyer_confirm_deal, name='buyer_confirm_deal'),

    # Admin marketplace
    path('admin-portal/buyers/', marketplace_views.admin_manage_buyers, name='admin_manage_buyers'),
    path('admin-portal/buyers/<int:buyer_id>/action/', marketplace_views.admin_approve_buyer, name='admin_approve_buyer'),
    path('admin-portal/marketplace/', marketplace_views.admin_marketplace_overview, name='admin_marketplace_overview'),

    # ── ML Features ──
    path('ml/predict-yield/',        ml_views.predict_yield,    name='ml_predict_yield'),
    path('ml/fraud-score/<int:booking_id>/', ml_views.ml_fraud_score, name='ml_fraud_score'),
    path('ml/predict-quality/',      ml_views.predict_quality,  name='ml_predict_quality'),
    path('ml/dashboard/',            ml_views.ml_dashboard,     name='ml_dashboard'),
]
