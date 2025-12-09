from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .form import RegisterCustomerForm, CustomUserForm
from .form import UserUpdateForm
from django.contrib.auth.decorators import login_required
from .form import CustomPasswordChangeForm
from django.contrib.auth.decorators import user_passes_test
from .models import User
from ticket.untils import send_notification
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.shortcuts import get_object_or_404
API_URL = "https://account.base.vn/extapi/v1/users"
from django.contrib.auth.hashers import make_password
import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q,  F, Value
User = get_user_model()
from datetime import datetime
current_time = timezone.now()
from django.db.models.functions import Concat

def register_customer(request):
    if request.method == 'POST':
        form = RegisterCustomerForm (request.POST)
        if form.is_valid():
            var = form.save(commit=False)
            var.is_customer = True
            var.username = var.username
            var.save()
            messages.success(request,'Bạn đã đăng ký tài khoản thành công!')
            return redirect('login')
        else:
            form = RegisterCustomerForm()
            messages.warning(request, 'Tài khoản đã có người sử dụng.')
            return redirect('register_customer')
    else:
        form = RegisterCustomerForm()
        context = {'form': form}
        return render(request, 'accounts/register_customer.html', context)
    
def login_user(request):
    """
    Login function hỗ trợ cả API authentication và local authentication
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.warning(request, 'Vui lòng nhập email và mật khẩu.')
            return redirect('login')
        
        # Bước 1: Kiểm tra user đã tồn tại trong local DB
        user = User.objects.filter(email=email).first()
        
        if user:
            # User tồn tại trong DB, xác thực với password local
            authenticated_user = authenticate(request, username=user.username, password=password)
            
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, f'Chào mừng {authenticated_user.first_name or authenticated_user.email}!')
                return redirect('/')
            else:
                messages.warning(request, 'Email hoặc mật khẩu không chính xác.')
                return redirect('login')
        
        # Bước 2: User không tồn tại local, kiểm tra trong API
        users_api_url = getattr(settings, 'USERS_API_URL', None)
        api_token = getattr(settings, 'API_TOKEN', None)
        
        if not users_api_url or not api_token:
            messages.error(request, 'Cấu hình API không hợp lệ. Vui lòng liên hệ admin.')
            return redirect('login')
        
        try:
            # Gọi API để lấy danh sách users
            session = requests.Session()
            users_response = session.post(
                users_api_url, 
                data={'access_token': api_token},
                timeout=10
            )
            
            if users_response.status_code != 200:
                messages.error(request, f'Không thể kết nối API: {users_response.status_code}')
                return redirect('login')
            
            # Tìm user trong API response
            api_users = users_response.json().get('users', [])
            user_data = next((u for u in api_users if u.get('email', '').lower() == email.lower()), None)
            
            if not user_data:
                messages.warning(request, 'Email hoặc mật khẩu không chính xác.')
                return redirect('login')
            
            # Kiểm tra password từ API
            # LƯU Ý: API có thể không cấp cấp mật khẩu, trong trường hợp này tạo user với password default
            api_password = user_data.get('password', '')
            
            if api_password and api_password != password:
                # Nếu API trả về password và không khớp
                messages.warning(request, 'Email hoặc mật khẩu không chính xác.')
                return redirect('login')
            
            # Tạo user mới trong DB từ thông tin API
            new_user = User.objects.create_user(
                username=email,
                email=email,
                password=password  # Lưu password thật từ user input
            )
            new_user.is_customer = user_data.get('is_customer', True)
            new_user.is_engineer = user_data.get('is_engineer', False)
            
            # Cập nhật thông tin profile từ API
            if 'first_name' in user_data and user_data['first_name']:
                new_user.first_name = user_data['first_name']
            if 'last_name' in user_data and user_data['last_name']:
                new_user.last_name = user_data['last_name']
            if 'phone' in user_data and user_data['phone']:
                new_user.phone = user_data['phone']
            if 'title' in user_data and user_data['title']:
                new_user.title = user_data['title']
            if 'school' in user_data and user_data['school']:
                new_user.school = user_data['school']
            
            new_user.save()
            
            # Xác thực và đăng nhập user vừa tạo
            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, f'Chào mừng {authenticated_user.first_name or authenticated_user.email}!')
                return redirect('/')
            else:
                messages.error(request, 'Lỗi khi đăng nhập. Vui lòng thử lại.')
                return redirect('login')
        
        except requests.exceptions.Timeout:
            messages.error(request, 'Kết nối API timeout. Vui lòng thử lại.')
            return redirect('login')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Lỗi kết nối: {str(e)}')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Lỗi không xác định: {str(e)}')
            return redirect('login')
    
    # GET request - render login page
    return render(request, 'accounts/login.html')
    
def logout_user(request):
    logout(request)
    messages.success(request, 'Vui lòng đăng nhập để tiếp tục.')
    return redirect('login')

@login_required
def profile_user (request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/profile_user.html', {'user': user})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('view_profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    # Lấy danh sách phòng ban và sắp xếp
    from asset.models import Department
    departments = Department.objects.all().order_by('name')
    
    return render(request, 'accounts/update_profile.html', {
        'form': form,
        'departments': departments
    })

def custom_404(request, exception):
    return render(request, 'pages/error.html', status=404)
def custom_500(request):
    return render(request, 'pages/error.html', status=500)

@login_required
def view_profile(request):
    # Lấy thông tin người dùng hiện tại
    user = request.user
    
    # Chỉ gọi API nếu chưa có họ tên
    if not user.first_name or not user.last_name:
        # Gọi API để lấy thông tin
        api_url = "https://account.base.vn/extapi/v1/users"
        data = {'access_token': '7868-PHURYQYUGSH7JQQJXN4X73BVNY83RX67ZK7F2KKWKK3LMRGU4ZQVTM3925C7KAQS-HUE54EKMGU8E2SCY6AEH49KZV3FSFQGNQQY7JPG3V37TXFLR6JSSX2LGAHM8G4R7'}
        try:
            response = requests.post(api_url, data=data, timeout=5)
            
            if response.status_code == 200:
                response_data = response.json()
                # Tìm user trong danh sách trả về từ API
                for u in response_data.get('users', []):
                    if u.get('email', '').lower() == user.email.lower():
                        # Chỉ cập nhật first_name và last_name
                        if not user.first_name and 'first_name' in u:
                            user.first_name = u['first_name']
                        if not user.last_name and 'last_name' in u:
                            user.last_name = u['last_name']
                        user.save()
                        break
        except Exception as e:
            print(f"Error calling API: {e}")
    
    return render(request, 'accounts/view_profile.html', {'user': user})

# đổi mk - trong app

def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mật khẩu đã được thay đổi thành công!')
            return redirect('logout')
        else:
            messages.warning(request, 'Mật khẩu mới phải ít nhất 8 ký tự gồm: chữ in hoa, số và không được giống mật khẩu cũ.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    priority_user_ids = [105, 103, 106, 126, 104, 22, 168, 115, 9, 102, 107, 108, 112, 113, 116, 118]
    users = User.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name')
    ).order_by('-is_superuser')

    # Sắp xếp theo priority_user_ids
    sorted_users = sorted(users, key=lambda user: priority_user_ids.index(user.id) if user.id in priority_user_ids else len(priority_user_ids))

    query = request.GET.get('q', '')
    if query:
        query = query.lower().split()  # Tách query thành từng phần dựa trên khoảng trắng

        # Tạo một bộ lọc tìm kiếm linh hoạt
        filtered_users = []
        for user in sorted_users:
            user_full_name = f"{user.first_name.lower()} {user.last_name.lower()}"
            if all(part in user_full_name or part in user.email.lower() or part in user.phone.lower() or part in user.work_place.lower() or part in user.title.lower() for part in query):
                filtered_users.append(user)

        sorted_users = filtered_users

    paginator = Paginator(sorted_users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': ' '.join(query),  # Gộp lại để hiển thị trong input
        'request_user': request.user.email,
    }

    return render(request, 'accounts/manage_users.html', context)

@user_passes_test(lambda u: u.is_superuser)
def update_user_permissions(request):
    if request.method == 'POST':
        # Chỉ những user ID được gửi qua POST mới được xử lý
        user_ids = request.POST.getlist('user_ids')

        for user_id in user_ids:
            user = User.objects.get(id=user_id)

            is_customer = request.POST.get(f'is_customer_{user.id}') == 'on'
            is_engineer = request.POST.get(f'is_engineer_{user.id}') == 'on'

            if user.is_customer != is_customer or user.is_engineer != is_engineer:
                user.is_customer = is_customer
                user.is_engineer = is_engineer
                user.save()

                # Cập nhật thông báo
                current_time = timezone.now()
                update_permission_created_on = naturaltime(current_time)
                message = f'<a href = "/">Bạn đã được thay đổi vai trò.</a><br><small>{update_permission_created_on}</small>'
                send_notification(user.id, message)

    return redirect(request.META.get('HTTP_REFERER', '/fallback-url'))
@login_required
def all_users(request):
    query = request.GET.get('q', '')
    
    # Sắp xếp theo priority_user_ids
    priority_user_ids = [105, 103, 106, 126, 104, 22, 168, 115, 9, 102, 107, 108, 112, 113, 116, 118]
    query_parts = query.lower().split()
    # Make the API request
    api_key = 'access_token'
    api_url = "https://account.base.vn/extapi/v1/users"
    data = {'access_token': '7868-PHURYQYUGSH7JQQJXN4X73BVNY83RX67ZK7F2KKWKK3LMRGU4ZQVTM3925C7KAQS-HUE54EKMGU8E2SCY6AEH49KZV3FSFQGNQQY7JPG3V37TXFLR6JSSX2LGAHM8G4R7'}
    response = requests.post(api_url, data=data)

    # Check if request was successful
    if response.status_code == 200:
        response_data = response.json()
        api_users = response_data.get('users', [])
    else:
        print(f"Request failed with status code {response.status_code}")
        api_users = []
    api_users = sorted(api_users, key=lambda user: datetime.strptime(user.get('created_at', '1970-01-01'), '%Y-%m-%d'), reverse=True)
    # Get all local users
    users = User.objects.all()
    local_users = sorted(users, key=lambda user: priority_user_ids.index(user.id) if user.id in priority_user_ids else len(priority_user_ids))

    # Create a dictionary for fast lookup of local users
    local_users_dict = {user.email: user for user in local_users}

    # Update API users with local data if available
    all_users = []
    # Update API users with local data if available
    if api_users:
        for user in api_users:
            email = user.get('email')
            if email in local_users_dict:
                # Tài khoản có cả trong API và local
                local_user = local_users_dict[email]
                user.update({
                    'school': local_user.school,
                    'work_place': local_user.work_place,
                    'avatar': local_user.avatar.url if local_user.avatar else None,
                    'local_id': local_user.id,
                    'user_type': 'both'  # Đánh dấu là có cả trong API và local
                })
            else:
                # Tài khoản chỉ có trong API
                user['user_type'] = 'api_only'  # Đánh dấu là chỉ có trong API
            all_users.append(user)


    # Merge API users with local users
    all_users = list(api_users)
    for local_user in local_users:
        if local_user.email not in [user.get('email') for user in api_users]:
            # Tài khoản chỉ có trong local
            all_users.append({
                'first_name': local_user.first_name,
                'last_name': local_user.last_name,
                'email': local_user.email,
                'phone': local_user.phone,
                'work_place': local_user.work_place,
                'title': local_user.title,
                'school': local_user.school,
                'avatar': local_user.avatar.url if local_user.avatar else None,
                'local_id': local_user.id,
                'user_type': 'local_only'  # Đánh dấu là chỉ có trong local
            })

    # Perform search if query is provided
    if query:
        filtered_users = []
        for user in all_users:
            user_full_name = f"{(user.get('first_name') or '').lower()} {(user.get('last_name') or '').lower()}"
            if all(
                part in (user_full_name or '') or 
                part in (user.get('email') or '').lower() or 
                part in (user.get('phone') or '').lower() or 
                part in (user.get('school') or '').lower() or 
                part in (user.get('work_place') or '').lower() or 
                part in (user.get('title') or '').lower()
                for part in query_parts
            ):
                filtered_users.append(user)
        all_users = filtered_users

    # Sort all_users by priority_user_ids
    sorted_all_users = sorted(all_users, key=lambda user: priority_user_ids.index(user.get('local_id', -1)) if user.get('local_id', -1) in priority_user_ids else len(priority_user_ids))

    # Paginate results
    paginator = Paginator(sorted_all_users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': ''.join(query),
        'local_users_dict': local_users_dict,
        'request_user': request.user.email,
    }

    return render(request, 'accounts/all_users.html', context)


def can_delete_user(user):
    return user.is_superuser

@user_passes_test(can_delete_user)
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, pk=user_id)
    user_to_delete.delete()
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))
def can_delete_user(user):
    return user.is_superuser
@user_passes_test(can_delete_user)
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, pk=user_id)

    user_to_delete.delete()
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

def show_data(request):
    url = "https://account.base.vn/extapi/v1/users"
    data = {'access_token': '7868-RKLR6TUFT5TR5WVYGHGJPDF9USRC78YH22ZXHH9WVUC56T98C3RRLWXNFYTDKCET-CPEFY7VBYUYFRGAZDXB93GVGTXSNP2S46H4UCRKSJD8KUWUC9BRNCV9TWQTPJ6JB'}  # Replace 'token' with your actual token
    response = requests.post(url, data=data)
    users = response.json()
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

def get_user_from_api(email):
    api_url = "https://account.base.vn/extapi/v1/users"
    api_key = "7868-RKLR6TUFT5TR5WVYGHGJPDF9USRC78YH22ZXHH9WVUC56T98C3RRLWXNFYTDKCET-CPEFY7VBYUYFRGAZDXB93GVGTXSNP2S46H4UCRKSJD8KUWUC9BRNCV9TWQTPJ6JB"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    params = {'email': email}
    
    try:
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            user_data = response.json()
            return user_data  # Trả về dữ liệu người dùng từ API
        else:
            print(f"API request failed with status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return None
