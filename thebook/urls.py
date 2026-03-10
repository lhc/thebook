"""
URL configuration for thebook project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from debug_toolbar.toolbar import debug_toolbar_urls

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("thebook.base.urls", namespace="base")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("bookkeeping/", include("thebook.bookkeeping.urls", namespace="bookkeeping")),
    path("members/", include("thebook.members.urls", namespace="members")),
    path(
        "reimbursements/",
        include("thebook.reimbursements.urls", namespace="reimbursements"),
    ),
    path("webhooks/", include("thebook.webhooks.urls", namespace="webhooks")),
    path(
        "fornecedores/",
        include("thebook.fornecedores.urls", namespace="fornecedores"),
    ),
] + debug_toolbar_urls()
