from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Department, Asset, District, School, LabRoom
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .form import CreateDepartmentForm, CreateAssetDepartmentForm, MoveAssetForm, EditAssetForm,CreateDistrictForm, CreateAssetDistrictForm, CreateSchoolForm, CreateLabRoomForm, CreateAssetLabRoomForm, AssetSplitForm
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, Value, IntegerField, Count, Case, When, Q
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.template import loader
from django.views import View
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from babel.dates import format_datetime
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

formatted_time = timezone.localtime(timezone.now())
current_time = format_datetime(formatted_time, "H:mm, d MMMM YYYY ", locale='vi')

def generate_unique_name(original_name):
    counter = 1
    new_name = f"{original_name} ({counter})"
    while Asset.objects.filter(name=new_name).exists():
        counter += 1
        new_name = f"{original_name} ({counter})"
    return new_name

@login_required
def create_departments(request):
    departments_data = [
        {'name': 'Ban lãnh đạo'},
        {'name': 'Phòng mầm non 1'},
        {'name': 'Phòng mầm non 2'},
        {'name': 'Phòng mầm non 3'},
        {'name': 'Phòng tiểu học'},
        {'name': 'Phòng hành chính'},
        {'name': 'Ban kiểm soát'},
        {'name': 'Phòng kế toán'},
        {'name': 'Phòng kinh doanh marketing'},
        {'name': 'Phòng nhân sự'},
        {'name': 'Học viện Enspire Láng Hạ'},
        {'name': 'Enspire Hải Phòng'},
    ]

    for data in departments_data:
        Department.objects.get_or_create(**data)
        
@login_required
def all_asset(request):
    query = request.GET.get('q')
    departments = Department.objects.all()
    
    if query:
        departments = departments.filter(
            Q(name__icontains=query) |  
            Q(district__name__icontains=query) |  
            Q(district__school__name__icontains=query) |  
            Q(district__school__labroom__name__icontains=query) |  
            Q(assets__name__icontains=query) |  
            Q(district__asset__name__icontains=query) |  
            Q(district__school__asset__name__icontains=query) |  
            Q(district__school__labroom__asset__name__icontains=query)  
        ).distinct()
    
    assets_list = []  # List to hold all assets and display information
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0
    
    for department in departments:

        department_assets_qs = Asset.objects.filter(
            Q(department=department) |
            Q(district__department=department) |
            Q(school__district__department=department) |
            Q(lab_room__school__district__department=department)
        )
        if query:
            department_assets_qs = department_assets_qs.filter(
                Q(name__icontains=query) |
                Q(department__name__icontains=query)
            ).distinct()

        if "Ban lãnh đạo" in department.name:
            department_assets_aggregate = department_assets_qs.aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )
        else:
            department_assets_aggregate =  Asset.objects.filter(
            Q(lab_room__school__district__department=department) |
            Q(district__department=department) |
            Q(school__district__department=department) 
            ).aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )

        department_asset_count = department_assets_aggregate['total_amount']
        department_active_asset_count = department_assets_aggregate['total_active']
        department_broken_asset_count = department_assets_aggregate['total_broken']
        total_asset_count += department_asset_count
        total_active_asset_count += department_active_asset_count
        total_broken_asset_count += department_broken_asset_count

        assets_list.append({
            'type': 'department',
            'name': department.name,
            'asset_count': department_asset_count,
            'active_asset_count': department_active_asset_count,
            'broken_asset_count': department_broken_asset_count,
        })

        # Tài sản của phòng ban
        if "Ban lãnh đạo" in department.name:
            for asset in department.assets.filter(name__icontains=query) if query else department.assets.all():
                assets_list.append({
                    'type': 'asset',
                    'name': asset.name,
                    'amount': asset.asset_amount,
                    'status': asset.asset_status,
                    'location': f"{department.name}",
                })

        for district in department.district_set.all():
            district_assets_qs = Asset.objects.filter(
                Q(district=district) |
                Q(lab_room__school__district=district)
            )

            if query:
                district_assets_qs = district_assets_qs.filter(
                    Q(name__icontains=query) |
                    Q(district__name__icontains=query)
                ).distinct()

            district_assets_aggregate = district_assets_qs.aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )

            district_asset_count = district_assets_aggregate['total_amount']
            district_active_asset_count = district_assets_aggregate['total_active']
            district_broken_asset_count = district_assets_aggregate['total_broken']

            assets_list.append({
                'type': 'district',
                'name': district.name,
                'asset_count': district_asset_count,
                'active_asset_count': district_active_asset_count,
                'broken_asset_count': district_broken_asset_count,
            })
            if "Văn phòng" in district.name or "Kho" in district.name or "Server" in district.name:
                for asset in district.asset_set.filter(name__icontains=query) if query else district.asset_set.all():
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{department.name} - {district.name}",
                    })

            for school in district.school_set.all():
                school_assets_qs = Asset.objects.filter(
                    Q(school=school) |
                    Q(lab_room__school=school)
                )

                if query:
                    school_assets_qs = school_assets_qs.filter(
                        Q(name__icontains=query) |
                        Q(school__name__icontains=query)
                    ).distinct()

                school_assets_aggregate = school_assets_qs.aggregate(
                    total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                    total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                    total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
                )

                school_asset_count = school_assets_aggregate['total_amount']
                school_active_asset_count = school_assets_aggregate['total_active']
                school_broken_asset_count = school_assets_aggregate['total_broken']

                assets_list.append({
                    'type': 'school',
                    'name': school.name,
                    'asset_count': school_asset_count,
                    'active_asset_count': school_active_asset_count,
                    'broken_asset_count': school_broken_asset_count,
                    'school_status': school.school_status,
                })

                for labroom in school.labroom_set.all():
                    labroom_assets_qs = Asset.objects.filter(
                        lab_room=labroom
                    )

                    if query:
                        labroom_assets_qs = labroom_assets_qs.filter(
                            Q(name__icontains=query) |
                            Q(lab_room__name__icontains=query)
                        ).distinct()

                    labroom_assets_aggregate = labroom_assets_qs.aggregate(
                        total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                        total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                        total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
                    )

                    labroom_asset_count = labroom_assets_aggregate['total_amount']
                    labroom_active_asset_count = labroom_assets_aggregate['total_active']
                    labroom_broken_asset_count = labroom_assets_aggregate['total_broken']

                    assets_list.append({
                        'type': 'labroom',
                        'name': labroom.name,
                        'asset_count': labroom_asset_count,
                        'active_asset_count': labroom_active_asset_count,
                        'broken_asset_count': labroom_broken_asset_count,
                    })

                    for asset in labroom.asset_set.filter(name__icontains=query) if query else labroom.asset_set.all():
                        assets_list.append({
                            'type': 'asset',
                            'name': asset.name,
                            'amount': asset.asset_amount,
                            'status': asset.asset_status,
                            'location': f"{school.name} - {district.name}",
                        })

    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'query': query,
    }

    return render(request, 'asset/all_asset.html', context)       

@login_required
def all_broken_asset(request):
    query = request.GET.get('q')
    departments = Department.objects.all()

    if query:
        # Lọc phòng ban, trường, hoặc tài sản theo từ khóa tìm kiếm
        departments = departments.filter(
            Q(name__icontains=query) |  # Tìm theo tên phòng ban
            Q(district__school__labroom__asset__name__icontains=query) |  # Tìm theo tên tài sản
            Q(district__school__name__icontains=query)  # Tìm theo tên trường
        ).distinct()

    assets_list = []  # List để chứa các tài sản hỏng
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0

    for department in departments:
        # Tính tổng tài sản của phòng ban
        department_assets_aggregate = Asset.objects.filter(
            Q(lab_room__school__district__department=department) |
            Q(district__department=department) |
            Q(school__district__department=department) |
            Q(department=department)
        ).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0)),
            total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
            total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
        )

        # Tính tổng số lượng tài sản
        department_asset_count = department_assets_aggregate['total_amount']
        department_active_asset_count = department_assets_aggregate['total_active']
        department_broken_asset_count = department_assets_aggregate['total_broken']
        total_asset_count += department_asset_count
        total_active_asset_count += department_active_asset_count
        total_broken_asset_count += department_broken_asset_count

        # Lấy các tài sản hỏng của phòng ban
        if "Ban lãnh đạo" in department.name:
            for asset in department.assets.filter(asset_status='Hỏng'):
                assets_list.append({
                    'type': 'asset',
                    'name': asset.name,
                    'amount': asset.asset_amount,
                    'status': asset.asset_status,
                    'location': f"{department.name}"
                })

        # Lặp qua các quận thuộc phòng ban
        for district in department.district_set.all():
            if "Văn phòng" in district.name or "Kho" in district.name or "Server" in district.name:
                for asset in district.asset_set.filter(asset_status='Hỏng'):
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{district.name} - {department.name}"
                    })

            # Lặp qua các trường thuộc quận
            for school in district.school_set.all():
                for asset in school.asset_set.filter(asset_status='Hỏng'):
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{school.name} - {district.name}"
                    })

                # Lặp qua các phòng lab thuộc trường
                for labroom in school.labroom_set.all():
                    for asset in labroom.asset_set.filter(asset_status='Hỏng'):
                        assets_list.append({
                            'type': 'asset',
                            'name': asset.name,
                            'amount': asset.asset_amount,
                            'status': asset.asset_status,
                            'location': f"{labroom.name} - {school.name} - {district.name}"
                        })

    # Pagination với 50 tài sản mỗi trang
    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'query': query,
    }

    return render(request, 'asset/all_broken_asset.html', context)

@login_required
def all_active_asset(request):
    query = request.GET.get('q')
    departments = Department.objects.all()

    if query:
        # Lọc phòng ban, trường, hoặc tài sản theo từ khóa tìm kiếm
        departments = departments.filter(
            Q(name__icontains=query) |  # Tìm theo tên phòng ban
            Q(district__school__labroom__asset__name__icontains=query) |  # Tìm theo tên tài sản
            Q(district__school__name__icontains=query)  # Tìm theo tên trường
        ).distinct()

    assets_list = []  # List để chứa các tài sản hỏng
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0

    for department in departments:
        # Tính tổng tài sản của phòng ban
        department_assets_aggregate = Asset.objects.filter(
            Q(lab_room__school__district__department=department) |
            Q(district__department=department) |
            Q(school__district__department=department) |
            Q(department=department)
        ).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0)),
            total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
            total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
        )

        # Tính tổng số lượng tài sản
        department_asset_count = department_assets_aggregate['total_amount']
        department_active_asset_count = department_assets_aggregate['total_active']
        department_broken_asset_count = department_assets_aggregate['total_broken']
        total_asset_count += department_asset_count
        total_active_asset_count += department_active_asset_count
        total_broken_asset_count += department_broken_asset_count

        # Lấy các tài sản hỏng của phòng ban
        if "Ban lãnh đạo" in department.name:
            for asset in department.assets.filter(asset_status='Tốt'):
                assets_list.append({
                    'type': 'asset',
                    'name': asset.name,
                    'amount': asset.asset_amount,
                    'status': asset.asset_status,
                    'location': f"{department.name}"
                })

        # Lặp qua các quận thuộc phòng ban
        for district in department.district_set.all():
            if "Văn phòng" in district.name or "Kho" in district.name or "Server" in district.name:
                for asset in district.asset_set.filter(asset_status='Tốt'):
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{district.name} - {department.name}"
                    })

            # Lặp qua các trường thuộc quận
            for school in district.school_set.all():
                for asset in school.asset_set.filter(asset_status='Tốt'):
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{school.name} - {district.name}"
                    })

                # Lặp qua các phòng lab thuộc trường
                for labroom in school.labroom_set.all():
                    for asset in labroom.asset_set.filter(asset_status='Tốt'):
                        assets_list.append({
                            'type': 'asset',
                            'name': asset.name,
                            'amount': asset.asset_amount,
                            'status': asset.asset_status,
                            'location': f"{labroom.name} - {school.name} - {district.name}"
                        })

    # Pagination với 50 tài sản mỗi trang
    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'query': query,
    }

    return render(request, 'asset/all_active_asset.html', context)

def view_department(request):
    create_departments(request)
    try:
        ban_lanh_dao = Department.objects.get(id=1)
    except Department.DoesNotExist:
        ban_lanh_dao = None
    
    # Sắp xếp theo trường order trong model
    departments = Department.objects.all().order_by('order', 'id')
    
    
    total_asset_count = 0
    total_active_asset_count = 0
    total_asset_broken_count = 0
    
    total_school_count = 0
    total_linking_school_count = School.objects.filter(school_status='Đang liên kết').count()
    total_negotiating_school_count = School.objects.filter(school_status='Đang đàm phán').count()
    total_stopped_school_count = School.objects.filter(school_status='Ngưng liên kết').count()
    department_data = []
    total_school_count_per_department = {}
    
    for department in departments:
        # Tính tổng số lượng tài sản (assets) cho mỗi phòng ban (department)
        # và đảm bảo rằng kết quả không bao giờ là NULL bằng cách sử dụng Coalesce

        if "Ban lãnh đạo" in department.name:
            department_assets_aggregate = Asset.objects.filter(
                # Điều kiện tìm kiếm các tài sản thuộc về phòng ban này
                # Lưu ý: Điều kiện cụ thể phụ thuộc vào mối quan hệ trong mô hình dữ liệu của bạn
                Q(lab_room__school__district__department=department) |
                Q(district__department=department) |
                Q(school__district__department=department) |
                Q(department=department)  
            ).aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )
        else:
            department_assets_aggregate = Asset.objects.filter(
                # Điều kiện tìm kiếm các tài sản thuộc về phòng ban này
                # Lưu ý: Điều kiện cụ thể phụ thuộc vào mối quan hệ trong mô hình dữ liệu của bạn
                Q(lab_room__school__district__department=department) |
                Q(district__department=department) |
                Q(school__district__department=department)
            ).aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )
        
        # Cập nhật tổng số lượng tài sản cho mỗi trạng thái
        department.asset_count = department_assets_aggregate['total_amount']
        department.asset_active_count = department_assets_aggregate['total_active']
        department.asset_broken_count = department_assets_aggregate['total_broken']
        
        labroom_count = LabRoom.objects.filter(school__district__department=department).count()
        department.labroom_count = labroom_count
        total_labroom_count = LabRoom.objects.count()
        
        linking_school_count = School.objects.filter(district__department=department, school_status='Đang liên kết').count()
        negotiating_school_count = School.objects.filter(district__department=department, school_status='Đang đàm phán').count()
        stopped_school_count = School.objects.filter(district__department=department, school_status='Ngưng liên kết').count()
        department_school_count = linking_school_count + negotiating_school_count + stopped_school_count
        
        # Cập nhật tổng số lượng trường cho từng phòng ban
        # The above code is declaring a variable named `total_school_count` in Python. However, the
        # code snippet seems to have some extra characters like `
        total_school_count += department_school_count
        total_linking_school_count = School.objects.filter(school_status='Đang liên kết').count()
        total_negotiating_school_count = School.objects.filter(school_status='Đang đàm phán').count()
        total_stopped_school_count = School.objects.filter(school_status='Ngưng liên kết').count()
        # Cập nhật tổng số lượng trường cho toàn bộ hệ thống
        total_asset_count += department.asset_count 
        total_active_asset_count += department.asset_active_count
        total_asset_broken_count += department.asset_broken_count
        
        department.school_count = School.objects.filter(
            district__department=department
        ).count()
        linking_percentage = School.objects.filter(
            district__department=department, school_status='Đang liên kết'
        ).count()
        negotiating_percentage = School.objects.filter(
            district__department=department, school_status='Đang đàm phán'
        ).count()
        stopped_percentage = School.objects.filter(
            district__department=department, school_status='Ngưng liên kết'
        ).count()
        
        department_data.append({
        'department': department,
        'asset_count': department.asset_count,
        'asset_active_count': department.asset_active_count,
        'asset_broken_count': department.asset_broken_count,
        'linking_school_count': linking_school_count,
        'negotiating_school_count': negotiating_school_count,
        'stopped_school_count': stopped_school_count,
        'total_school_count': department_school_count,
        'school_count': department.school_count,
        'linking_percentage': linking_percentage,
        'negotiating_percentage': negotiating_percentage,
        'stopped_percentage': stopped_percentage,
        })
        department.linking_school_count = linking_school_count
        department.negotiating_school_count = negotiating_school_count
        department.stopped_school_count = stopped_school_count
        
    all_school = total_school_count
    linking_percentage = (total_linking_school_count / all_school) * 100 if all_school != 0 else 0
    negotiating_percentage = (total_negotiating_school_count / all_school) * 100 if all_school != 0 else 0
    stopped_percentage = (total_stopped_school_count / all_school) * 100 if all_school != 0 else 0
    # Tính phần trăm tài sản hoạt động và hỏng trên tổng số tài sản
    all_asset = total_asset_count
    percentage_active = (total_active_asset_count / all_asset) * 100 if all_asset != 0 else 0
    percentage_broken = (total_asset_broken_count / all_asset) * 100 if all_asset != 0 else 0
    
    context = {
        'departments': departments,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_asset_broken_count': total_asset_broken_count,
        'all_percentages_active': percentage_active,
        'all_percentages_broken': percentage_broken,
        'department_data': department_data,
        'linking_percentage': linking_percentage,
        'negotiating_percentage': negotiating_percentage,
        'stopped_percentage': stopped_percentage,
        'total_school_count': total_school_count,
        'total_labroom_count': total_labroom_count,
    }
    
    return render(request, 'asset/view_department.html', context)

@login_required
def department_all_asset(request, department_id):
    # Retrieve the department
    query = request.GET.get('q')
    department = get_object_or_404(Department, id=department_id)
    assets_list = []
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0
    
    # Lọc tài sản của toàn bộ phòng ban
    department_assets_qs = Asset.objects.filter(
        Q(district__department=department) |
        Q(school__district__department=department) |
        Q(lab_room__school__district__department=department)
    )

    # Áp dụng bộ lọc tìm kiếm nếu có từ khóa
    if query:
        department_assets_qs = department_assets_qs.filter(
            Q(name__icontains=query) |
            Q(district__name__icontains=query) |
            Q(school__name__icontains=query)
        ).distinct()

    # Tính toán tổng hợp số lượng tài sản và bộ lọc tài sản
    department_assets_aggregate = department_assets_qs.aggregate(
        total_amount=Coalesce(Sum('asset_amount'), Value(0)),
        total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
        total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
    )

    # Tổng hợp tài sản của phòng ban
    department_asset_count = department_assets_aggregate['total_amount']
    department_active_asset_count = department_assets_aggregate['total_active']
    department_broken_asset_count = department_assets_aggregate['total_broken']

    total_asset_count += department_asset_count
    total_active_asset_count += department_active_asset_count
    total_broken_asset_count += department_broken_asset_count

    assets_list.append({
        'type': 'department',
        'name': department.name,
        'asset_count': department_asset_count,
        'active_asset_count': department_active_asset_count,
        'broken_asset_count': department_broken_asset_count,
    })

    for district in department.district_set.all():
    # Kiểm tra query cho district
        district_assets_qs = Asset.objects.filter(
            Q(district=district) |
            Q(lab_room__school__district=district)
        )

        if query:
            district_assets_qs = district_assets_qs.filter(
                Q(name__icontains=query) |
                Q(district__name__icontains=query)
            ).distinct()

        # Tính toán tổng hợp tài sản cho district
        district_assets_aggregate = district_assets_qs.aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0)),
            total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
            total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
        )

        # Thêm dữ liệu trực tiếp của district vào assets_list nếu là "Văn phòng" hoặc "Kho"
        if "Văn phòng" in district.name or "Kho" in district.name or "Server" in district.name:
            district_assets = district_assets_qs.filter(district=district)
            asset_data = [{
                'name': asset.name,
                'amount': asset.asset_amount,
                'status': asset.asset_status,
                'location': f"{district.name}"
            } for asset in district_assets]
        else:
            asset_data = []

        assets_list.append({
            'type': 'district',
            'name': district.name,
            'asset_count': district_assets_aggregate['total_amount'],
            'active_asset_count': district_assets_aggregate['total_active'],
            'broken_asset_count': district_assets_aggregate['total_broken'],
            'assets': asset_data,
        })

        # Vòng lặp cho trường
        for school in district.school_set.all():
            school_assets_qs = Asset.objects.filter(
                Q(school=school) |
                Q(lab_room__school=school)
            )

            if query:
                school_assets_qs = school_assets_qs.filter(
                    Q(name__icontains=query) |
                    Q(school__name__icontains=query)
                ).distinct()

            # Tính toán tài sản của trường
            school_assets_aggregate = school_assets_qs.aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )

            assets_list.append({
                'type': 'school',
                'name': school.name,
                'asset_count': school_assets_aggregate['total_amount'],
                'active_asset_count': school_assets_aggregate['total_active'],
                'broken_asset_count': school_assets_aggregate['total_broken'],
                'school_status': school.school_status,
            })

            # Vòng lặp cho phòng thí nghiệm
            for labroom in school.labroom_set.all():
                labroom_assets_qs = Asset.objects.filter(lab_room=labroom)

                if query:
                    labroom_assets_qs = labroom_assets_qs.filter(
                        Q(name__icontains=query)
                    ).distinct()

                # Tính toán tài sản của phòng thí nghiệm
                labroom_assets_aggregate = labroom_assets_qs.aggregate(
                    total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                    total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                    total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
                )

                assets_list.append({
                    'type': 'labroom',
                    'name': labroom.name,
                    'asset_count': labroom_assets_aggregate['total_amount'],
                    'active_asset_count': labroom_assets_aggregate['total_active'],
                    'broken_asset_count': labroom_assets_aggregate['total_broken'],
                })

                # Thêm từng tài sản trong phòng thí nghiệm vào danh sách assets_list
                for asset in labroom_assets_qs:
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{school.name} - {district.name}",
                    })

    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    formatted_time = timezone.localtime(timezone.now())
    created_on = format_datetime(formatted_time, "H:mm, d MMMM YYYY", locale='vi')

    context = {
        'department': department,
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'created_on': created_on,
        'query': query,
    }

    return render(request, 'asset/department_all_asset.html', context)

@login_required
def department_all_asset(request, department_id):
    # Retrieve the department
    query = request.GET.get('q')
    department = get_object_or_404(Department, id=department_id)
    assets_list = []
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0
    
    # Lọc tài sản của toàn bộ phòng ban
    department_assets_qs = Asset.objects.filter(
        Q(district__department=department) |
        Q(school__district__department=department) |
        Q(lab_room__school__district__department=department)
    )

    # Áp dụng bộ lọc tìm kiếm nếu có từ khóa
    if query:
        department_assets_qs = department_assets_qs.filter(
            Q(name__icontains=query) |
            Q(district__name__icontains=query) |
            Q(school__name__icontains=query)
        ).distinct()

    # Tính toán tổng hợp số lượng tài sản và bộ lọc tài sản
    department_assets_aggregate = department_assets_qs.aggregate(
        total_amount=Coalesce(Sum('asset_amount'), Value(0)),
        total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
        total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
    )

    # Tổng hợp tài sản của phòng ban
    department_asset_count = department_assets_aggregate['total_amount']
    department_active_asset_count = department_assets_aggregate['total_active']
    department_broken_asset_count = department_assets_aggregate['total_broken']

    total_asset_count += department_asset_count
    total_active_asset_count += department_active_asset_count
    total_broken_asset_count += department_broken_asset_count

    assets_list.append({
        'type': 'department',
        'name': department.name,
        'asset_count': department_asset_count,
        'active_asset_count': department_active_asset_count,
        'broken_asset_count': department_broken_asset_count,
    })

    for district in department.district_set.all():
    # Kiểm tra query cho district
        district_assets_qs = Asset.objects.filter(
            Q(district=district) |
            Q(lab_room__school__district=district)
        )

        if query:
            district_assets_qs = district_assets_qs.filter(
                Q(name__icontains=query) |
                Q(district__name__icontains=query)
            ).distinct()

        # Tính toán tổng hợp tài sản cho district
        district_assets_aggregate = district_assets_qs.aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0)),
            total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
            total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
        )

        # Thêm dữ liệu trực tiếp của district vào assets_list nếu là "Văn phòng" hoặc "Kho"
        if "Văn phòng" in district.name or "Kho" in district.name or "Server" in district.name:
            district_assets = district_assets_qs.filter(district=district)
            asset_data = [{
                'name': asset.name,
                'amount': asset.asset_amount,
                'status': asset.asset_status,
                'location': f"{district.name}"
            } for asset in district_assets]
        else:
            asset_data = []

        assets_list.append({
            'type': 'district',
            'name': district.name,
            'asset_count': district_assets_aggregate['total_amount'],
            'active_asset_count': district_assets_aggregate['total_active'],
            'broken_asset_count': district_assets_aggregate['total_broken'],
            'assets': asset_data,
        })

        # Vòng lặp cho trường
        for school in district.school_set.all():
            school_assets_qs = Asset.objects.filter(
                Q(school=school) |
                Q(lab_room__school=school)
            )

            if query:
                school_assets_qs = school_assets_qs.filter(
                    Q(name__icontains=query) |
                    Q(school__name__icontains=query)
                ).distinct()

            # Tính toán tài sản của trường
            school_assets_aggregate = school_assets_qs.aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )

            assets_list.append({
                'type': 'school',
                'name': school.name,
                'asset_count': school_assets_aggregate['total_amount'],
                'active_asset_count': school_assets_aggregate['total_active'],
                'broken_asset_count': school_assets_aggregate['total_broken'],
                'school_status': school.school_status,
            })

            # Vòng lặp cho phòng thí nghiệm
            for labroom in school.labroom_set.all():
                labroom_assets_qs = Asset.objects.filter(lab_room=labroom)

                if query:
                    labroom_assets_qs = labroom_assets_qs.filter(
                        Q(name__icontains=query)
                    ).distinct()

                # Tính toán tài sản của phòng thí nghiệm
                labroom_assets_aggregate = labroom_assets_qs.aggregate(
                    total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                    total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                    total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
                )

                assets_list.append({
                    'type': 'labroom',
                    'name': labroom.name,
                    'asset_count': labroom_assets_aggregate['total_amount'],
                    'active_asset_count': labroom_assets_aggregate['total_active'],
                    'broken_asset_count': labroom_assets_aggregate['total_broken'],
                })

                # Thêm từng tài sản trong phòng thí nghiệm vào danh sách assets_list
                for asset in labroom_assets_qs:
                    assets_list.append({
                        'type': 'asset',
                        'name': asset.name,
                        'amount': asset.asset_amount,
                        'status': asset.asset_status,
                        'location': f"{school.name} - {district.name}",
                    })

    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    formatted_time = timezone.localtime(timezone.now())
    created_on = format_datetime(formatted_time, "H:mm, d MMMM YYYY", locale='vi')

    context = {
        'department': department,
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'created_on': created_on,
        'query': query,
    }

    return render(request, 'asset/department_all_asset.html', context)

@login_required
def district_all_asset(request, department_id, district_id):
    query = request.GET.get('q')
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)

    assets_list = []
    total_asset_count = 0
    total_active_asset_count = 0
    total_broken_asset_count = 0

    # Tính tổng tài sản cho toàn quận
    total_aggregate = Asset.objects.filter(
        Q(school__district=district) | Q(lab_room__school__district=district)
    ).aggregate(
        total_count=Coalesce(Sum('asset_amount'), Value(0)),
        total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
        total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
    )

    total_asset_count = total_aggregate['total_count']
    total_active_asset_count = total_aggregate['total_active']
    total_broken_asset_count = total_aggregate['total_broken']

    # Lặp qua từng trường
    for school in district.school_set.all():
        school_assets_qs = Asset.objects.filter(
            Q(school=school) |
            Q(lab_room__school=school)
        )

        if query:
            school_assets_qs = school_assets_qs.filter(
                Q(name__icontains=query) |
                Q(school__name__icontains=query)
            ).distinct()

        school_assets_aggregate = school_assets_qs.aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0)),
            total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
            total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
        )

        assets_list.append({
            'type': 'school',
            'name': school.name,
            'asset_count': school_assets_aggregate['total_amount'],
            'active_asset_count': school_assets_aggregate['total_active'],
            'broken_asset_count': school_assets_aggregate['total_broken'],
            'school_status': school.school_status,
        })

        for labroom in school.labroom_set.all():
            labroom_assets_qs = Asset.objects.filter(lab_room=labroom)

            if query:
                labroom_assets_qs = labroom_assets_qs.filter(
                    Q(name__icontains=query)
                ).distinct()

            labroom_assets_aggregate = labroom_assets_qs.aggregate(
                total_amount=Coalesce(Sum('asset_amount'), Value(0)),
                total_active=Coalesce(Sum('asset_amount', filter=Q(asset_status='Tốt')), Value(0)),
                total_broken=Coalesce(Sum('asset_amount', filter=Q(asset_status='Hỏng')), Value(0))
            )

            assets_list.append({
                'type': 'labroom',
                'name': labroom.name,
                'asset_count': labroom_assets_aggregate['total_amount'],
                'active_asset_count': labroom_assets_aggregate['total_active'],
                'broken_asset_count': labroom_assets_aggregate['total_broken'],
            })

            for asset in labroom_assets_qs:
                assets_list.append({
                    'type': 'asset',
                    'name': asset.name,
                    'amount': asset.asset_amount,
                    'status': asset.asset_status,
                    'location': f"{school.name} - {district.name}",
                })

    paginator = Paginator(assets_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    formatted_time = timezone.localtime(timezone.now())
    created_on = format_datetime(formatted_time, "H:mm, d MMMM YYYY", locale='vi')

    context = {
        'department': department,
        'district': district,
        'page_obj': page_obj,
        'total_asset_count': total_asset_count,
        'total_active_asset_count': total_active_asset_count,
        'total_broken_asset_count': total_broken_asset_count,
        'created_on': created_on,
        'query': query,
    }

    return render(request, 'asset/district_all_asset.html', context)

@login_required
def create_department_2(request):
    if request.method == 'POST':
        form = CreateDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Phòng ban đã được tạo thành công.')
            return redirect('view_department')
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateDepartmentForm()

    context = {'form': form}
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def department_detail(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    departments=Department.objects.all()
    assets = department.assets.all().order_by('-created_at')
    formatted_time = timezone.localtime(timezone.now())
    created_on = format_datetime(formatted_time, "H:mm, d MMMM YYYY ", locale='vi')
    districts = District.objects.filter(department=department)
    district_list = list(districts)
    
    schools = School.objects.filter(district__in=districts)
    school_list = list(schools)
    labrooms = LabRoom.objects.filter(school__in=schools)
    labrooms_list = labrooms_list = list(labrooms)
    
    department_asset_count = Asset.objects.filter(department=department).aggregate(
    total_amount=Coalesce(Sum('asset_amount'), Value(0))
)['total_amount']
    department_active_asset_count = Asset.objects.filter(asset_status = 'Tốt',department=department).aggregate(
    total_amount=Coalesce(Sum('asset_amount'), Value(0))
)['total_amount']
    department_broken_asset_count = Asset.objects.filter(asset_status = 'Hỏng', department=department).aggregate(
    total_amount=Coalesce(Sum('asset_amount'), Value(0))
)['total_amount']
    
    total_department_asset = department_asset_count
    query = request.GET.get('q')
    if query:
        assets = assets.filter(
            Q(name__icontains=query) |
            Q(asset_status__icontains=query) |
            Q(asset_amount__icontains=query)
        )

    
    percentage_active = (department_active_asset_count / total_department_asset) * 100 if total_department_asset != 0 else 0
    percentage_broken = (department_broken_asset_count / total_department_asset) * 100 if total_department_asset != 0 else 0
    paginator = Paginator(assets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'department':department,
        'departments':departments,
        'districts':districts,
        'district_list':district_list,
        'schools':schools,
        'school_list':school_list,
        'labrooms':labrooms,
        'labrooms_list':labrooms_list,
        'department_asset_count': department_asset_count,
        'department_active_asset_count' : department_active_asset_count,
        'department_broken_asset_count' : department_broken_asset_count,
        'department_percentage_active' : percentage_active,
        'department_percentage_broken' : percentage_broken,
        'assets': assets,
        'page_obj': page_obj,
        'query': query,
        'created_on':created_on,
        }
    return render(request, 'asset/department_detail.html', context)

@login_required
def department_detail_2(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    districts = District.objects.filter(department=department)
    priority_districts = [district for district in districts if district.name == 'Văn phòng Hà Nội' in district.name or 'Kho' in district.name]

    # Lọc quận bình thường: không thuộc nhóm ưu tiên
    normal_districts = [district for district in districts if district.name != 'Văn phòng Hà Nội' and 'Kho' not in district.name]

    # Kết hợp danh sách ưu tiên và danh sách bình thường
    sorted_districts = priority_districts + normal_districts
    district_data = []
    all_school_count = 0
    all_labroom_count = 0
    all_linking_school_count = 0
    all_negotiating_school_count = 0
    all_stopped_school_count = 0
    total_asset_count = 0  # Tổng tài sản từ quận
    total_active_asset_count = 0
    total_broken_asset_count = 0

    for district in districts:
        # Đếm tài sản trong quận
        district.asset_count = Asset.objects.filter(district=district).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount'] or 0

        district.active_asset_count = Asset.objects.filter(asset_status='Tốt', district=district).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount'] or 0
        
        district.broken_asset_count = Asset.objects.filter(asset_status='Hỏng', district=district).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount'] or 0
        
        # Đếm tài sản trong các phòng lab của trường thuộc quận
        district.asset_count_2 = Asset.objects.filter(lab_room__school__district=district).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount'] or 0
        
        # Tính tổng tài sản trong quận (không tính tài sản trong lab)
        district.total_asset_count = district.asset_count_2 + district.asset_count

        # Tính số tài sản hoạt động và bị hỏng
        district.active_asset_count_2 = Asset.objects.filter(
            asset_status='Tốt', lab_room__school__district=district
        ).aggregate(total_amount=Coalesce(Sum('asset_amount'), Value(0)))['total_amount'] or 0

        district.broken_asset_count_2 = Asset.objects.filter(
            asset_status='Hỏng', lab_room__school__district=district
        ).aggregate(total_amount=Coalesce(Sum('asset_amount'), Value(0)))['total_amount'] or 0

        # Cộng dồn số tài sản hoạt động và bị hỏng
        district.total_active_count = district.active_asset_count + district.active_asset_count_2
        district.total_broken_count = district.broken_asset_count + district.broken_asset_count_2

        # Đếm số lượng phòng lab
        labroom_count = LabRoom.objects.filter(school__district=district).count()
        all_labroom_count += labroom_count
        
        # Cộng dồn vào các biến tổng
        total_asset_count += district.total_asset_count  # Chỉ cộng từ quận
        total_active_asset_count += district.total_active_count
        total_broken_asset_count += district.total_broken_count
        
        # Đếm số lượng trường trong quận
        school_count = School.objects.filter(district=district).count()
        all_school_count += school_count
        
        # Đếm trạng thái của trường
        linking_count = School.objects.filter(district=district, school_status='Đang liên kết').count()
        negotiating_count = School.objects.filter(district=district, school_status='Đang đàm phán').count()
        stopped_count = School.objects.filter(district=district, school_status='Ngưng liên kết').count()
        
        all_linking_school_count += linking_count
        all_negotiating_school_count += negotiating_count
        all_stopped_school_count += stopped_count
        
        # Lưu thông tin quận vào danh sách
        district_data.append({
            'district': district,
            'asset_count': district.total_asset_count,
            'asset_active_count': district.total_active_count,
            'asset_broken_count': district.total_broken_count,
            'school_count': school_count,
            'linking_count': linking_count,
            'negotiating_count': negotiating_count,
            'stopped_count': stopped_count,
            'labroom_count': labroom_count,
        })
        district.labroom_count = labroom_count
        district.school_count = school_count
        district.linking_school_count = linking_count
        district.negotiating_school_count = negotiating_count
        district.stopped_school_count = stopped_count
        
    # Tính tỷ lệ phần trăm cho các trường
    linking_percentage = (all_linking_school_count / all_school_count) * 100 if all_school_count != 0 else 0
    negotiating_percentage = (all_negotiating_school_count / all_school_count) * 100 if all_school_count != 0 else 0
    stopped_percentage = (all_stopped_school_count / all_school_count) * 100 if all_school_count != 0 else 0
    
    # Tính tỷ lệ tài sản bị hỏng và tài sản hoạt động
    district_percentage_active = (total_active_asset_count / total_asset_count) * 100 if total_asset_count != 0 else 0
    district_percentage_broken = (total_broken_asset_count / total_asset_count) * 100 if total_asset_count != 0 else 0
    
    context = {
        'department': department,
        'districts': sorted_districts,
        'sorted_districts':sorted_districts,
        'total_asset_count': total_asset_count,
        'total_active_asset': total_active_asset_count,
        'total_broken_asset': total_broken_asset_count,
        'district_percentage_active': district_percentage_active,
        'district_percentage_broken': district_percentage_broken,
        'all_labroom_count': all_labroom_count,
        'all_school_count': all_school_count,
        'linking_percentage': linking_percentage,
        'negotiating_percentage': negotiating_percentage,
        'stopped_percentage': stopped_percentage,
        'district_data': district_data,
        
    }
    
    return render(request, 'asset/department_detail_2.html', context)

@login_required
def HaNoienspire(request, department_id, district_id):
    department = get_object_or_404(Department, id=department_id)
    departments = Department.objects.all()
    
    district = get_object_or_404(District, id=district_id, department=department)
    
    districts = District.objects.filter(department=department)
    
    district_list = list(districts)
    
    schools = School.objects.filter(district=district)
    school_list = list(schools)
    
    labrooms = LabRoom.objects.filter(school__in=school_list)
    labrooms_list = list(labrooms)
    
    assetdistricts = Asset.objects.filter(district=district).order_by('-created_at')
    asset_district_count = assetdistricts.aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0
    active_asset_district_count = Asset.objects.filter(district=district, asset_status = 'Tốt').aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0
    broken_asset_district_count = Asset.objects.filter(district=district, asset_status = 'Hỏng').aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0

    total_assets_in_district = asset_district_count

    query = request.GET.get('q')
    if query:
        assetdistricts = assetdistricts.filter(
            Q(name__icontains=query) |
            Q(asset_status__icontains=query) |
            Q(asset_amount__icontains=query)
        )
    created_on = naturaltime(current_time)
    percentage_active = (active_asset_district_count / total_assets_in_district) * 100 if total_assets_in_district != 0 else 0
    percentage_broken = (broken_asset_district_count / total_assets_in_district) * 100 if total_assets_in_district != 0 else 0
    paginator = Paginator(assetdistricts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'broken_asset_district_count':broken_asset_district_count,
        'active_asset_district_count':active_asset_district_count,
        'asset_district_count':asset_district_count,
        'department': department,
        'departments':departments,
        'district': district,
        'districts': districts,
        'district_list':district_list,
        'schools':schools,
        'school_list':school_list,
        'labrooms':labrooms,
        'labrooms_list':labrooms_list,
        'assetdistricts':assetdistricts,
        'percentages_active': percentage_active,
        'percentages_broken':percentage_broken,
        'page_obj': page_obj,
        'query': query,
        'created_on':created_on,
    }

    return render(request, 'asset/HaNoienspire.html', context)

def update_asset_status(request):
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        new_status = request.POST.get('new_status')
        try:
            asset = Asset.objects.get(pk=asset_id)
            asset.asset_status = new_status
            asset.save()
            return JsonResponse({'success': True})
        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def update_school_status(request):
    if request.method == 'POST':
        school_id = request.POST.get('school_id')
        new_status = request.POST.get('new_status')
        status_color_mapping = {
            'Đang liên kết': 'btn-success',
            'Đang đàm phán': 'btn-warning',
            'Ngưng liên kết': 'btn-danger',
        }
        try:
            school = School.objects.get(pk=school_id)
            school.school_status = new_status
            school.school_status_color = status_color_mapping[new_status]
            school.save()
            return JsonResponse({'success': True})
        except School.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'School not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def district_detail(request, department_id, district_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id, department=department)
    districts = District.objects.filter(department=department)
    schools = School.objects.filter(district=district)
    
    district_data_2=[]
    asset_school_count = 0
    active_asset_school_count = 0
    broken_asset_school_count = 0
    all_school_asset = 0  # Di chuyển khai báo ra khỏi vòng lặp
    all_labroom_count = 0
    linking_count = 0
    negotiating_count = 0
    stopped_count = 0
    all_schools = 0
    all_linking_school_count = 0
    all_negotiating_school_count = 0
    all_stopped_school_count = 0
    for school in schools:
        labrooms = LabRoom.objects.filter(school=school)
        labroom_count = labrooms.count()
        school.asset_count = Asset.objects.filter(lab_room__in=labrooms).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount']
        school.active_asset_count = Asset.objects.filter(asset_status='Tốt', lab_room__in=labrooms).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount']
        school.broken_asset_count = Asset.objects.filter(asset_status='Hỏng', lab_room__in=labrooms).aggregate(
            total_amount=Coalesce(Sum('asset_amount'), Value(0))
        )['total_amount']
        
        school.labroom_count = labroom_count
        asset_school_count += school.asset_count
        active_asset_school_count += school.active_asset_count
        broken_asset_school_count += school.broken_asset_count
        all_school_asset += school.asset_count  # Tính toán tổng số lượng tài sản của tất cả các trường

        district_data_2.append({
            'school': school,
            'labroom_count': labroom_count,
            'schools': schools,
            'asset_count': school.asset_count,
            'asset_active_count': school.active_asset_count,
            'asset_broken_count': school.broken_asset_count,
        })
        all_labroom_count += labroom_count

        # Đếm số lượng trường đang liên kết, đàm phán và ngưng liên kết
        linking_count += School.objects.filter(district=district, school_status='Đang liên kết').count()
        negotiating_count += School.objects.filter(district=district, school_status='Đang đàm phán').count()
        stopped_count += School.objects.filter(district=district, school_status='Ngưng liên kết').count()
        all_linking_school_count += linking_count
        all_negotiating_school_count += negotiating_count
        all_stopped_school_count += stopped_count
        
    all_school_count = schools.count()
    total_school_count = all_linking_school_count + all_negotiating_school_count + all_stopped_school_count
    all_schools += total_school_count
    # Tính toán tỷ lệ tài sản của các trường
    school_percentage_active = (active_asset_school_count / all_school_asset) * 100 if all_school_asset != 0 else 0
    school_percentage_broken = (broken_asset_school_count / all_school_asset) * 100 if all_school_asset != 0 else 0
    
    # Tính toán tỷ lệ các trường trong Quận
    linking_percentage = (all_linking_school_count  / all_schools) *100 if all_schools != 0 else 0
    negotiating_percentage = (all_negotiating_school_count / all_schools) *100 if all_schools != 0 else 0
    stopped_percentage = (all_stopped_school_count / all_schools) *100 if all_schools != 0 else 0
    
    
    context = {
        'asset_school_count': asset_school_count,
        'active_asset_school_count': active_asset_school_count,
        'broken_asset_school_count': broken_asset_school_count,
        'department': department,
        'district': district,
        'districts': districts,
        'schools': schools,
        'school_percentage_active': school_percentage_active,
        'school_percentage_broken': school_percentage_broken,
        'district_data_2': district_data_2,  # Truyền danh sách thông tin các trường vào context
        'all_school_count': all_school_count,
        'all_labroom_count': all_labroom_count,
        'linking_count': linking_count,
        'negotiating_count': negotiating_count,
        'stopped_count': stopped_count,
        'linking_percentage': linking_percentage,
        'negotiating_percentage': negotiating_percentage,
        'stopped_percentage': stopped_percentage,
        
    }
    
    return render(request, 'asset/district_detail.html', context)


@login_required
def school_detail(request, department_id, district_id, school_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id, department=department)
    school = get_object_or_404(School, id=school_id,district=district)
    districts = District.objects.filter(department=department)
    schools = School.objects.filter(district=district)
    labrooms = LabRoom.objects.filter(school=school)
    
    school_data = []
    labroom_asset = 0
    labroom_active_asset = 0
    labroom_broken_asset = 0
    
    for labroom in labrooms:
        labroom.asset_count = Asset.objects.filter(lab_room=labroom).aggregate(
        total_amount=Coalesce(Sum('asset_amount'), Value(0))
    )['total_amount']
        labroom.active_asset_count = Asset.objects.filter(asset_status = 'Tốt', lab_room=labroom).aggregate(
        total_amount=Coalesce(Sum('asset_amount'), Value(0))
    )['total_amount']
        labroom.broken_asset_count = Asset.objects.filter(asset_status = 'Hỏng', lab_room=labroom).aggregate(
        total_amount=Coalesce(Sum('asset_amount'), Value(0))
    )['total_amount']
        labroom_asset += labroom.asset_count
        labroom_active_asset += labroom.active_asset_count
        labroom_broken_asset += labroom.broken_asset_count
        
        
        school_data.append({
        'labroom': labroom,
        'labroom_asset': labroom.asset_count,
        'labroom_active_asset': labroom.active_asset_count,
        'labroom_broken_asset': labroom.broken_asset_count,
        })
        
    school_percentage_active = (sum(labroom.active_asset_count for labroom in labrooms) / labroom_asset) * 100 if labroom_asset != 0 else 0
    school_percentage_broken = (sum(labroom.broken_asset_count for labroom in labrooms) / labroom_asset) * 100 if labroom_asset != 0 else 0
    context = {
        'labroom_asset':labroom_asset,
        'labroom_active_asset': labroom_active_asset,
        'labroom_broken_asset': labroom_broken_asset,
        'department': department,
        'district': district,
        'districts': districts,
        'school':school,
        'schools':schools,
        'labrooms':labrooms,
        'school_percentage_active': school_percentage_active,
        'school_percentage_broken': school_percentage_broken
    }
    return render(request, 'asset/school_detail.html', context)

@login_required
def labroom_detail(request, department_id, district_id, school_id, labroom_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id, department=department)
    school = get_object_or_404(School, id=school_id,district=district)
    labroom = get_object_or_404(LabRoom, id=labroom_id,school=school)
    
    departments = Department.objects.all()
    
    districts = District.objects.filter(department=department)
    district_list = list(districts)
    
    schools = School.objects.filter(district=district)
    school_list = list(schools)
    
    labrooms = LabRoom.objects.filter(school=school)
    labrooms_list = list(labrooms)
    
    
    assetlabs = Asset.objects.filter(lab_room=labroom).order_by('-created_at')
    asset_in_lab_count = assetlabs.aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0
    active_asset_in_lab_count = Asset.objects.filter(lab_room=labroom, asset_status = 'Tốt').aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0
    broken_asset_in_lab_count = Asset.objects.filter(lab_room=labroom, asset_status = 'Hỏng').aggregate(total_amount=Sum('asset_amount'))['total_amount'] or 0
    query = request.GET.get('q')
    if query:
        assetlabs = assetlabs.filter(
            Q(name__icontains=query) |
            Q(asset_status__icontains=query) |
            Q(asset_amount__icontains=query)
        )
    created_on = naturaltime(current_time)
    total_asset_lab = asset_in_lab_count
    lab_percentage_active = (active_asset_in_lab_count / total_asset_lab) * 100 if total_asset_lab != 0 else 0
    lab_percentage_broken = (broken_asset_in_lab_count / total_asset_lab) * 100 if total_asset_lab != 0 else 0
    paginator = Paginator(assetlabs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'asset_in_lab_count':asset_in_lab_count,
        'active_asset_in_lab_count':active_asset_in_lab_count,
        'broken_asset_in_lab_count':broken_asset_in_lab_count,
        'department': department,
        'district': district,
        'districts': districts,
        'district_list': district_list,
        'school':school,
        'schools':schools,
        'school_list':school_list,
        'labroom':labroom,
        'labrooms':labrooms,
        'labrooms_list':labrooms_list,
        'assetlabs':assetlabs,
        'lab_percentage_active': lab_percentage_active,
        'lab_percentage_broken': lab_percentage_broken,
        'departments': departments,
        'page_obj': page_obj,
        'query': query,
        'created_on':created_on,
    }
    return render(request, 'asset/labroom_detail.html', context)

@login_required
def create_asset_department(request, department_id, asset_id=None):
    department = get_object_or_404(Department, id=department_id)

    if asset_id:
        # Nếu asset_id được cung cấp, nghĩa là bạn đang cập nhật một tài sản tồn tại
        asset = get_object_or_404(Asset, id=asset_id)
    else:
        # Nếu asset_id không được cung cấp, nghĩa là bạn đang tạo mới một tài sản
        asset = None

    if request.method == 'POST':
        form = CreateAssetDepartmentForm(request.POST, instance=asset)
        if form.is_valid():
            new_asset = form.save(commit=False)
            new_asset.department = department

            # Kiểm tra xem tài sản đã tồn tại trong phòng ban không
            existing_asset = Asset.objects.filter(department=department, name=new_asset.name, asset_status=new_asset.asset_status).first()

            if existing_asset:
                # Nếu tài sản đã tồn tại và cùng trạng thái, cộng thêm số lượng
                existing_asset.asset_amount += new_asset.asset_amount
                existing_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được cập nhật thành công.')
            else:
                # Nếu tài sản chưa tồn tại hoặc trạng thái khác, tạo mới
                new_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được tạo thành công.')

            return redirect('department_detail', department_id=department_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateAssetDepartmentForm(instance=asset)

    context = {'form': form, 'department': department, 'asset': asset}
    return render(request, 'asset/department_detail.html', context)

@method_decorator(login_required, name='dispatch')
class UpdateAssetsDepartmentView(View):
    template_name = 'asset/department_detail.html'
    form_class = AssetSplitForm

    def get(self, request, department_id):
        department = get_object_or_404(Department, id=department_id)
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'department': department
        })

    def post(self, request, department_id):
        department = get_object_or_404(Department, id=department_id)
        form = self.form_class(request.POST)
        
        if form.is_valid():
            split_amount = form.cleaned_data.get('asset_amount')  # Lấy số lượng tài sản cần tách
            asset_id = form.cleaned_data.get('asset_id')  # Lấy ID của tài sản

            if asset_id:
                try:
                    asset_id = int(asset_id)
                except ValueError:
                    print(f"Could not convert 'asset_id' to int: {asset_id}")
                    # Log the error for debugging purposes
                    return redirect('department_detail', department_id=department_id)

                try:
                    asset = Asset.objects.get(id=asset_id, department=department)
                    
                    # Kiểm tra điều kiện tách tài sản
                    if split_amount >= asset.asset_amount:
                        # Nếu số lượng tách lớn hơn hoặc bằng lượng tài sản hiện có, báo lỗi
                        messages.error(request, 'Số lượng cần tách đang lớn hơn số lượng tài sản đang có.')
                        return redirect('department_detail', department_id=department_id)

                    # Cập nhật số lượng tài sản gốc
                    asset.asset_amount -= split_amount
                    asset.save()
                    new_name = generate_unique_name(asset.name)
                    
                    # Tạo tài sản mới với số lượng tài sản được tách ra
                    Asset.objects.create(
                        name=new_name,
                        asset_amount=split_amount,
                        department=department  # Giả sử gán cho cùng một phòng ban
                    )

                    messages.success(request, 'Chia thành công.')
                    return redirect('department_detail', department_id=department_id)

                except Asset.DoesNotExist:
                    messages.error(request, 'Tài sản không tồn tại.')
            else:
                print("'asset_id' is empty or missing in form data.")
        else:
            # Nếu form không hợp lệ, hiển thị lỗi và quay trở lại trang form
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in the {field} field - {error}")
        
        return redirect('department_detail', department_id=department_id)


@login_required
def create_district(request, department_id):
    department = get_object_or_404(Department, id=department_id)

    if request.method == 'POST':
        form = CreateDistrictForm(request.POST)
        if form.is_valid():
            # Set the department before saving
            district = form.save(commit=False)
            district.department = department
            district.save()

            messages.success(request, 'Đã tạo Quận thành công.')
            
            # Use reverse to generate the URL for department_detail_2
            return redirect(reverse('department_detail_2', kwargs={'department_id': department.id}))
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateDistrictForm()

    context = {'form': form, 'department': department}
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def create_asset_HaNoi(request, department_id, district_id, asset_id=None):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    if asset_id:
        # Nếu asset_id được cung cấp, nghĩa là bạn đang cập nhật một tài sản tồn tại
        asset = get_object_or_404(Asset, id=asset_id)
    else:
        # Nếu asset_id không được cung cấp, nghĩa là bạn đang tạo mới một tài sản
        asset = None

    if request.method == 'POST':
        form = CreateAssetDistrictForm(request.POST, instance=asset, initial={'district': district})
        if form.is_valid():
            new_asset = form.save(commit=False)
            new_asset.district = district

            # Kiểm tra xem tài sản đã tồn tại trong phòng ban không
            existing_asset = Asset.objects.filter(district=district, name=new_asset.name, asset_status=new_asset.asset_status).first()

            if existing_asset:
                # Nếu tài sản đã tồn tại và cùng trạng thái, cộng thêm số lượng
                existing_asset.asset_amount += new_asset.asset_amount
                existing_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được cập nhật thành công.')
            else:
                # Nếu tài sản chưa tồn tại hoặc trạng thái khác, tạo mới
                new_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được tạo thành công.')

            return redirect('HaNoienspire', department_id=department_id, district_id = district_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateAssetDistrictForm(request.POST, instance=asset, initial={'district': district})

    context = {'form': form, 'department': department, 'district':district}
    return render(request, 'asset/HaNoienspire.html', context)

@login_required
def create_school(request, department_id, district_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)

    if request.method == 'POST':
        form = CreateSchoolForm(request.POST)
        if form.is_valid():
            # Set the department before saving
            school = form.save(commit=False)
            school.district = district
            school.save()

            messages.success(request, 'Đã tạo trường thành công.')
            
            # Use reverse to generate the URL for department_detail_2
            return redirect(reverse('district_detail', kwargs={'department_id': department.id, 'district_id':district.id}))
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateSchoolForm()

    context = {'form': form, 'department': department, 'district':district}
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def create_labroom(request, department_id, district_id, school_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    school = get_object_or_404(School, id=school_id)

    if request.method == 'POST':
        form = CreateLabRoomForm(request.POST)
        if form.is_valid():
            # Set the department before saving
            lab = form.save(commit=False)
            lab.school = school
            lab.save()

            messages.success(request, 'Đã tạo phòng lab thành công.')
            
            # Use reverse to generate the URL for department_detail_2
            return redirect(reverse('school_detail', kwargs={'department_id': department.id, 'district_id':district.id, 'school_id':school.id}))
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateLabRoomForm()

    context = {'form': form, 'department': department, 'district':district, 'school':school}
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def create_asset_lab(request, department_id, district_id, school_id, labroom_id, asset_id=None):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    school = get_object_or_404(School, id=school_id)
    labroom = get_object_or_404(LabRoom, id=labroom_id)
    if asset_id:
        # Nếu asset_id được cung cấp, nghĩa là bạn đang cập nhật một tài sản tồn tại
        asset = get_object_or_404(Asset, id=asset_id)
    else:
        # Nếu asset_id không được cung cấp, nghĩa là bạn đang tạo mới một tài sản
        asset = None

    if request.method == 'POST':
        form = CreateAssetLabRoomForm(request.POST, instance=asset, initial={'labroom': labroom})
        if form.is_valid():
            new_asset = form.save(commit=False)
            new_asset.lab_room = labroom

            # Kiểm tra xem tài sản đã tồn tại trong phòng ban không
            existing_asset = Asset.objects.filter(lab_room=labroom, name=new_asset.name, asset_status=new_asset.asset_status).first()

            if existing_asset:
                # Nếu tài sản đã tồn tại và cùng trạng thái, cộng thêm số lượng
                existing_asset.asset_amount += new_asset.asset_amount
                existing_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được cập nhật thành công.')
            else:
                # Nếu tài sản chưa tồn tại hoặc trạng thái khác, tạo mới
                new_asset.save()
                messages.success(request, f'Tài sản "{new_asset.name}" đã được tạo thành công.')

            return redirect('labroom_detail', department_id=department_id, district_id = district_id, school_id=school_id, labroom_id=labroom_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng tạo lại.')
    else:
        form = CreateAssetLabRoomForm(request.POST, instance=asset, initial={'labroom': labroom})

    context = {'form': form, 'department': department, 'district':district,'school':school,'labroom':labroom, 'asset': asset}
    return render(request, 'asset/labroom_detail.html', context)

@login_required
def edit_asset_lab(request, department_id, district_id, school_id, labroom_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    school = get_object_or_404(School, id=school_id)
    labroom = get_object_or_404(LabRoom, id=labroom_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    if request.method == 'POST':
        form = EditAssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thành công.')
            return redirect('labroom_detail', department_id=department_id, district_id=district_id, school_id=school_id, labroom_id=labroom_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng thử lại.')
            # Nếu form không hợp lệ, bạn có thể hiển thị lại form để người dùng nhập lại
    else:
        form = EditAssetForm(instance=asset)
    
    context = {'form': form, 'department': department, 'district': district, 'school': school, 'labroom': labroom, 'asset': asset}
    return render(request, 'asset/labroom_detail.html', context)

        
@login_required
def edit_asset_HaNoi(request, department_id, district_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    asset = get_object_or_404(Asset, id=asset_id)

    if request.method == 'POST':
        form = EditAssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thành công.')
            return redirect('HaNoienspire', department_id=department_id, district_id=district_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng thử lại.')
            # Nếu form không hợp lệ, bạn có thể hiển thị lại form để người dùng nhập lại
    else:
        form = EditAssetForm(instance=asset)
    
    context = {'form': form, 'HaNoienspire': department, 'district': district, 'asset': asset}
    return render(request, 'asset/HaNoienspire.html', context)

@login_required
def edit_asset_department(request, department_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    asset = get_object_or_404(Asset, id=asset_id)

    if request.method == 'POST':
        form = EditAssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thành công.')
            return redirect('department_detail', department_id=department_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng thử lại.')
            # Nếu form không hợp lệ, bạn có thể hiển thị lại form để người dùng nhập lại
    else:
        form = EditAssetForm(instance=asset)
    
    context = {'form': form, 'department_detail': department, 'asset': asset}
    return render(request, 'asset/department_detail.html', context)

@login_required
def move_asset_labroom(request, department_id, district_id, school_id, labroom_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    school = get_object_or_404(School, id=school_id)
    labroom = get_object_or_404(LabRoom, id=labroom_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    form = MoveAssetForm(request.POST or None, instance=asset)

    if request.method == 'POST':
        form = MoveAssetForm(request.POST, instance=asset)
        if form.is_valid():
            new_department = form.cleaned_data.get('new_department')
            new_district = form.cleaned_data.get('new_district')
            new_school = form.cleaned_data.get('new_school')
            new_labroom = form.cleaned_data.get('new_labroom')
            quantity = form.cleaned_data.get('quantity')

            if new_department or new_district or new_school or new_labroom:
                if quantity > asset.asset_amount:
                    messages.error(request, 'Số lượng chuyển không thể lớn hơn số lượng hiện có.')
                    return redirect(request.META.get('HTTP_REFERER', '/'))

                # Tìm kiếm tài sản cùng tên và trạng thái tại địa điểm mới
                existing_asset = Asset.objects.filter(
                    name=asset.name,
                    asset_status=asset.asset_status,
                    department=new_department,
                    district=new_district,
                    school=new_school,
                    lab_room=new_labroom
                ).first()

                if existing_asset:
                    # Nếu tồn tại, gộp số lượng
                    existing_asset.asset_amount += quantity
                    existing_asset.save()
                else:
                    # Nếu không tồn tại, tạo mới tài sản tại địa điểm mới
                    Asset.objects.create(
                        name=asset.name,
                        asset_status=asset.asset_status,
                        asset_amount=quantity,
                        department=new_department,
                        district=new_district,
                        school=new_school,
                        lab_room=new_labroom
                    )

                # Trừ số lượng tại địa điểm cũ
                asset.asset_amount -= quantity
                if asset.asset_amount == 0:
                    asset.delete()
                else:
                    asset.save()

                messages.success(request, f'{asset.name} đã được chuyển đi.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                messages.error(request, 'Phải chọn ít nhất một địa điểm mới để chuyển asset')
        else:
            messages.error(request, 'Có lỗi xảy ra với biểu mẫu. Vui lòng kiểm tra lại.')
    
    context = {
        'form': form,
        'asset': asset,
        'department': department,
        'district': district,
        'school': school,
        'labroom': labroom
    }
    return render(request, 'asset/labroom_detail.html', context)

def get_districts(request):
    department_id = request.GET.get('department_id')
    districts = District.objects.filter(department_id=department_id).values('id', 'name')
    district_list = list(districts)  # Chuyển QuerySet thành list để sử dụng trong JsonResponse

    return JsonResponse({'districts': district_list})

def get_schools(request):
    district_id = request.GET.get('district_id') 
    schools = School.objects.filter(district_id=district_id).values('id', 'name')
    schools_list = list(schools)  

    return JsonResponse({'schools': schools_list})

def get_labrooms(request):
    school_id = request.GET.get('school_id') 
    labrooms = LabRoom.objects.filter(school_id=school_id).values('id', 'name')
    labrooms_list = list(labrooms)  

    return JsonResponse({'labrooms': labrooms_list})

@login_required
def move_asset_Hanoi(request, department_id, district_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    form = MoveAssetForm(request.POST or None, instance=asset)

    if request.method == 'POST':
        form = MoveAssetForm(request.POST, instance=asset)
        if form.is_valid():
            new_department = form.cleaned_data.get('new_department')
            new_district = form.cleaned_data.get('new_district')
            new_school = form.cleaned_data.get('new_school')
            new_labroom = form.cleaned_data.get('new_labroom')
            quantity = form.cleaned_data.get('quantity')

            if new_department or new_district or new_school or new_labroom:
                if quantity > asset.asset_amount:
                    messages.error(request, 'Số lượng chuyển không thể lớn hơn số lượng hiện có.')
                    return redirect(request.META.get('HTTP_REFERER', '/'))

                # Tìm kiếm tài sản cùng tên và trạng thái tại địa điểm mới
                existing_asset = Asset.objects.filter(
                    name=asset.name,
                    asset_status=asset.asset_status,
                    department=new_department,
                    district=new_district,
                    school=new_school,
                    lab_room=new_labroom
                ).first()

                if existing_asset:
                    # Nếu tồn tại, gộp số lượng
                    existing_asset.asset_amount += quantity
                    existing_asset.save()
                else:
                    # Nếu không tồn tại, tạo mới tài sản tại địa điểm mới
                    Asset.objects.create(
                        name=asset.name,
                        asset_status=asset.asset_status,
                        asset_amount=quantity,
                        department=new_department,
                        district=new_district,
                        school=new_school,
                        lab_room=new_labroom
                    )

                # Trừ số lượng tại địa điểm cũ
                asset.asset_amount -= quantity
                if asset.asset_amount == 0:
                    asset.delete()
                else:
                    asset.save()

                messages.success(request, f'{asset.name} đã được chuyển đi.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                messages.error(request, 'Phải chọn ít nhất một địa điểm mới để chuyển asset')
        else:
            messages.error(request, 'Có lỗi xảy ra với biểu mẫu. Vui lòng kiểm tra lại.')
    
    context = {
        'form': form,
        'asset': asset,
        'department': department,
        'district': district,
    }
    return render(request, 'asset/HaNoienspire.html', context)

@login_required
def move_asset_department(request, department_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    form = MoveAssetForm(request.POST or None, instance=asset)

    if request.method == 'POST':
        form = MoveAssetForm(request.POST, instance=asset)
        if form.is_valid():
            new_department = form.cleaned_data.get('new_department')
            new_district = form.cleaned_data.get('new_district')
            new_school = form.cleaned_data.get('new_school')
            new_labroom = form.cleaned_data.get('new_labroom')
            quantity = form.cleaned_data.get('quantity')

            if new_department or new_district or new_school or new_labroom:
                if quantity > asset.asset_amount:
                    messages.error(request, 'Số lượng chuyển không thể lớn hơn số lượng hiện có.')
                    return redirect(request.META.get('HTTP_REFERER', '/'))

                # Tìm kiếm tài sản cùng tên và trạng thái tại địa điểm mới
                existing_asset = Asset.objects.filter(
                    name=asset.name,
                    asset_status=asset.asset_status,
                    department=new_department,
                    district=new_district,
                    school=new_school,
                    lab_room=new_labroom
                ).first()

                if existing_asset:
                    # Nếu tồn tại, gộp số lượng
                    existing_asset.asset_amount += quantity
                    existing_asset.save()
                else:
                    # Nếu không tồn tại, tạo mới tài sản tại địa điểm mới
                    Asset.objects.create(
                        name=asset.name,
                        asset_status=asset.asset_status,
                        asset_amount=quantity,
                        department=new_department,
                        district=new_district,
                        school=new_school,
                        lab_room=new_labroom
                    )

                # Trừ số lượng tại địa điểm cũ
                asset.asset_amount -= quantity
                if asset.asset_amount == 0:
                    asset.delete()
                else:
                    asset.save()

                messages.success(request, f'{asset.name} đã được chuyển đi.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                messages.error(request, 'Phải chọn ít nhất một địa điểm mới để chuyển asset')
        else:
            messages.error(request, 'Có lỗi xảy ra với biểu mẫu. Vui lòng kiểm tra lại.')
    
    context = {
        'form': form,
        'asset': asset,
        'department': department,
    }
    return render(request, 'asset/department_detail.html', context)

def delete_asset_lab (request, department_id, district_id, school_id, labroom_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    school = get_object_or_404(School, id=school_id)
    labroom = get_object_or_404(LabRoom, id=labroom_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    asset.delete()
    messages.success(request, f'Đã xóa {asset.name}.')
    context = {'department':department, 'district':district, 'school':school, 'labroom':labroom}
    return redirect(request.META.get('HTTP_REFERER', '/'))

def delete_asset_Hanoi(request, department_id, district_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    district = get_object_or_404(District, id=district_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    asset.delete()
    messages.success(request, f'Đã xóa {asset.name}.')
    context = {'department':department, 'district':district}
    return redirect(request.META.get('HTTP_REFERER', '/'))

def delete_asset_department(request, department_id, asset_id):
    department = get_object_or_404(Department, id=department_id)
    asset = get_object_or_404(Asset, id=asset_id)
    
    asset.delete()
    messages.success(request, f'Đã xóa {asset.name}.')
    context = {'department':department}
    return redirect(request.META.get('HTTP_REFERER', '/'))


def generate_unique_name_labroom(original_name, department, district, school, labroom):
    counter = 1
    new_name = "{} ({})".format(original_name, counter)
    while Asset.objects.filter(
        name=new_name,
        department=department,
        district=district,
        school=school,
        lab_room=labroom
    ).exists():
        counter += 1
        new_name = "{} ({})".format(original_name, counter)
    return new_name

@method_decorator(login_required, name='dispatch')
class UpdateAssetsLabroomView(View):
    template_name = 'asset/labroom_detail.html'
    form_class = AssetSplitForm

    def get(self, request, department_id, district_id, school_id, labroom_id):
        department = get_object_or_404(Department, id=department_id)
        district = get_object_or_404(District, id=district_id)
        school = get_object_or_404(School, id=school_id)
        lab_room = get_object_or_404(LabRoom, id=labroom_id)
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'department': department,
            'district': district,
            'school': school,
            'labroom': lab_room
        })

    def post(self, request, department_id, district_id, school_id, labroom_id):
        department = get_object_or_404(Department, id=department_id)
        district = get_object_or_404(District, id=district_id)
        school = get_object_or_404(School, id=school_id)
        lab_room = get_object_or_404(LabRoom, id=labroom_id)
        form = self.form_class(request.POST)
        
        if form.is_valid():
            split_amount = form.cleaned_data.get('asset_amount')  # Lấy số lượng tài sản cần tách
            asset_id = form.cleaned_data.get('asset_id')  # Lấy ID của tài sản

            if asset_id:
                try:
                    asset_id = int(asset_id)
                except ValueError:
                    print(f"Could not convert 'asset_id' to int: {asset_id}")
                    # Log the error for debugging purposes
                    return redirect('labroom_detail', department_id=department_id, district_id=district_id, school_id=school_id, labroom_id=labroom_id)

                try:
                    asset = Asset.objects.get(id=asset_id, lab_room=lab_room)
                    
                    # Kiểm tra điều kiện tách tài sản
                    if split_amount >= asset.asset_amount:
                        # Nếu số lượng tách lớn hơn hoặc bằng lượng tài sản hiện có, báo lỗi
                        messages.error(request, 'Số lượng cần tách đang lớn hơn số lượng tài sản đang có.')
                        return redirect('labroom_detail', department_id=department_id, district_id=district_id, school_id=school_id, labroom_id=labroom_id)

                    # Cập nhật số lượng tài sản gốc
                    asset.asset_amount -= split_amount
                    asset.save()
                    new_name = generate_unique_name_labroom(asset.name, department, district, school, lab_room)
                    
                    # Tạo tài sản mới với số lượng tài sản được tách ra
                    Asset.objects.create(
                        name=new_name,
                        asset_amount=split_amount,
                        department=department,  # Giả sử gán cho cùng một phòng ban
                        district=district,
                        school=school,
                        lab_room=lab_room
                    )

                    messages.success(request, 'Chia thành công.')
                    return redirect('labroom_detail', department_id=department_id, district_id=district_id, school_id=school_id, labroom_id=labroom_id)

                except Asset.DoesNotExist:
                    messages.error(request, 'Tài sản không tồn tại.')
            else:
                print("'asset_id' is empty or missing in form data.")
        else:
            # Nếu form không hợp lệ, hiển thị lỗi và quay trở lại trang form
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in the {field} field - {error}")
        
        return redirect('labroom_detail', department_id=department_id, district_id=district_id, school_id=school_id, labroom_id=labroom_id)
    
def generate_unique_name_district(original_name, department, district):
    counter = 1
    new_name = "{} ({})".format(original_name, counter)
    while Asset.objects.filter(
        name=new_name,
        department=department,
        district=district,
    ).exists():
        counter += 1
        new_name = "{} ({})".format(original_name, counter)
    return new_name

@method_decorator(login_required, name='dispatch')
class UpdateAssetsDistrictView(View):
    template_name = 'asset/district_detail.html'
    form_class = AssetSplitForm

    def get(self, request, department_id, district_id):
        department = get_object_or_404(Department, id=department_id)
        district = get_object_or_404(District, id=district_id)
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'department': department,
            'district': district,

        })

    def post(self, request, department_id, district_id):
        department = get_object_or_404(Department, id=department_id)
        district = get_object_or_404(District, id=district_id)
        form = self.form_class(request.POST)
        
        if form.is_valid():
            split_amount = form.cleaned_data.get('asset_amount')  # Lấy số lượng tài sản cần tách
            asset_id = form.cleaned_data.get('asset_id')  # Lấy ID của tài sản

            if asset_id:
                try:
                    asset_id = int(asset_id)
                except ValueError:
                    print(f"Could not convert 'asset_id' to int: {asset_id}")
                    # Log the error for debugging purposes
                    return redirect('HaNoienspire', department_id=department_id, district_id=district_id)

                try:
                    asset = Asset.objects.get(id=asset_id, district=district)
                    
                    # Kiểm tra điều kiện tách tài sản
                    if split_amount >= asset.asset_amount:
                        # Nếu số lượng tách lớn hơn hoặc bằng lượng tài sản hiện có, báo lỗi
                        messages.error(request, 'Số lượng cần tách đang lớn hơn số lượng tài sản đang có.')
                        return redirect('HaNoienspire', department_id=department_id, district_id=district_id)

                    # Cập nhật số lượng tài sản gốc
                    asset.asset_amount -= split_amount
                    asset.save()
                    new_name = generate_unique_name_district(asset.name, department, district)
                    
                    # Tạo tài sản mới với số lượng tài sản được tách ra
                    Asset.objects.create(
                        name=new_name,
                        asset_amount=split_amount,
                        department=department,  # Giả sử gán cho cùng một phòng ban
                        district=district,
                    )

                    messages.success(request, 'Chia thành công.')
                    return redirect('HaNoienspire', department_id=department_id, district_id=district_id)

                except Asset.DoesNotExist:
                    messages.error(request, 'Tài sản không tồn tại.')
            else:
                print("'asset_id' is empty or missing in form data.")
        else:
            # Nếu form không hợp lệ, hiển thị lỗi và quay trở lại trang form
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in the {field} field - {error}")
        
        return redirect('HaNoienspire', department_id=department_id, district_id=district_id)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_department_order(request):
    """API endpoint để cập nhật thứ tự phòng ban"""
    try:
        data = json.loads(request.body)
        department_orders = data.get('department_orders', [])
        
        for item in department_orders:
            department_id = item.get('id')
            new_order = item.get('order')
            
            if department_id and new_order is not None:
                Department.objects.filter(id=department_id).update(order=new_order)
        
        return JsonResponse({'success': True, 'message': 'Cập nhật thứ tự thành công'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
