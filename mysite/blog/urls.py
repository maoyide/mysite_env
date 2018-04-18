from django.urls import path
from . import views
urlpatterns = [
    path('', views.blog_list, name="blog_list"),
    path('<int:blog_pk>', views.blog_defail, name="blog_defail"),
    path('type/<int:blog_type_pk>', views.blogs_with_type, name="blogs_with_type"),
    path('date/<int:year>/<int:month>', views.blogs_with_date, name="blogs_with_date"),
    path('login/', views.login, name="login"),
    path('register/', views.register, name="register"),
    path('logout/',views.logout,name="logout"),
    
]