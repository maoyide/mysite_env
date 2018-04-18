import datetime
from django.shortcuts import get_object_or_404,render,redirect
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache  #缓存
from django.contrib import auth
from django.urls import reverse 
from django.contrib.auth.models import User
from .models import Blog,BlogType 
from .forms import LoginForm,RegForm
from read_count.models import ReadNum,ReadDetail
from comment.models import Comment
from comment.forms import CommentForm

# Create your views here.


def home(request):
    blog_content_type=ContentType.objects.get_for_model(Blog)
    dates,read_nums = get_seven_days_read_data(blog_content_type)
    
    blogs =  Blog.objects.all()


    #获取7天热门博客的缓存数据
    seven_days_hot_data=cache.get('seven_days_hot_data')
    if  seven_days_hot_data is None:
        seven_days_hot_data = get_seven_days_hot_data()
        cache.set('seven_days_hot_data', seven_days_hot_data, 3600) # 缓存保留的时间单位秒

    context={}
    context['dates']=dates
    context['read_nums']=read_nums
    context['today_hot_data']=get_today_hot_data(blog_content_type)
    context['yesterday_hot_data']=get_yesterday_hot_data(blog_content_type)
    context['seven_days_hot_data']=seven_days_hot_data
    context['new_blog']=blogs[:10]
    context['thirty_days_hot_data']=get_thirty_days_hot_data()
    context['blog_types']=BlogType.objects.annotate(blog_count=Count('blog'))
    return render(request,'home.html',context)

def get_blog_list_common_data(request,blogs_all_list):
    paginator=Paginator(blogs_all_list,10) #按显示条数进行分页
    page_num=request.GET.get('page',1)  #获取页码参数（get请求）
    page_of_blogs=paginator.get_page(page_num)
    currentr_page_num = page_of_blogs.number  #获取当前页码 
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num )) + \
    list(range(currentr_page_num, min( currentr_page_num + 2, paginator.num_pages) + 1))    
                #  获取当前页码的前后2个页码，并去掉0和-1页和超出范围的2个页码

    if page_range[0] - 1 >= 2:
        page_range.insert(0,'...')                 #给隐藏的页码添加...         
    if paginator.num_pages - page_range[-1] >=2:
        page_range.append('...')

    if page_range[0] != 1:                      
        page_range.insert(0,1)
    if page_range[-1] != paginator.num_pages:      #添加判断，增加第一页和最后一页
        page_range.append(paginator.num_pages)



    ##获取分类的博客数量1
    # blog_types = BlogType.objects.all()
    # blog_types_list = []
    # for blog_type in blog_types:
    #    blog_type.blog_count = Blog.objects.filter(blog_type=blog_type).count()
    #    blog_types_list.append(blog_type)



    # ##日期分类的博客数量统计
    blog_dates=Blog.objects.dates('create_time','month',order="DESC")
    blog_dates_dict={}
    for blog_date in blog_dates:
        blog_count=Blog.objects.filter(create_time__year=blog_date.year, create_time__month=blog_date.month).count()
        blog_dates_dict[blog_date]=blog_count




    context={}
    context['blogs']=page_of_blogs.object_list
    context['page_of_blogs']=page_of_blogs
    context['page_range'] = page_range
    # context['blog_types']=BlogType.objects.all()
    # context['blog_types']=blog_types_list
    context['blog_types']=BlogType.objects.annotate(blog_count=Count('blog'))  #获取分类的博客数量2

    # context['blog_dates']=Blog.objects.dates('create_time','month',order="DESC") #获取到博客日期排序列表，order排序
    context['blog_dates']=blog_dates_dict
    return context

def blog_list(request):
    blogs_all_list=Blog.objects.all()
    context = get_blog_list_common_data(request,blogs_all_list)
    return render(request,'blog/blog_list.html',context)

def blog_defail(request,blog_pk):
    blog=get_object_or_404(Blog,pk=blog_pk)
    blog_content_type = ContentType.objects.get_for_model(blog)

    comments = Comment.objects.filter(content_type=blog_content_type,object_id=blog.pk)


    if  not request.COOKIES.get('blog_%s_readed' %blog_pk, ):  #统计总的阅读数
        ct = ContentType.objects.get_for_model(Blog) 

        readnum,created = ReadNum.objects.get_or_create(content_type=ct,object_id=blog.pk)
  
        readnum.read_num += 1
        readnum.save()


        date = timezone.now().date()    #统计每天的阅读数
        readDetail,created = ReadDetail.objects.get_or_create(content_type=ct,object_id=blog.pk,date=date)

        readDetail.read_num += 1
        readDetail.save()


  

    context={}
    context['previous_blog'] = Blog.objects.filter(create_time__gt = blog.create_time).last()
    context['next_blog'] = Blog.objects.filter(create_time__lt = blog.create_time).first()
    context['blog'] = blog
    context['comments']=comments 

    data = {}
    data['content_type']=blog_content_type
    data['object_id']=blog_pk
    context['comment_form']=CommentForm(initial=data)
    
    response=render(request,'blog/blog_defail.html',context)
    response.set_cookie('blog_%s_readed' %blog_pk, 'true') #设置cookie有效期，实现阅读计数,此处没有设置时间，关闭浏览器cookie失效
    return response

def blogs_with_type(request,blog_type_pk):
    blog_type= get_object_or_404(BlogType,pk=blog_type_pk)
    blogs_all_list=Blog.objects.filter(blog_type=blog_type) 
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blog_type']= blog_type    
    context['blog_dates']=Blog.objects.dates('create_time','month',order="DESC") #获取到博客日期排序列表，order排序
    return render(request,'blog/blogs_with_type.html',context)

def blogs_with_date(request,year,month):
    blogs_all_list=Blog.objects.filter(create_time__year=year,create_time__month=month)
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blogs_with_date']='%s年%s月' %(year,month)
    return render(request,'blog/blogs_with_date.html',context)

def get_seven_days_read_data(content_type):
    today = timezone.now().date()
    dates = []
    read_nums = []      
    for i in range(7, 0, -1):
        date = today - datetime.timedelta(days=i)
        dates.append(date.strftime('%m/%d'))
        read_details = ReadDetail.objects.filter(content_type=content_type, date=date)
        result = read_details.aggregate(read_num_sum = Sum('read_num'))
        read_nums.append(result['read_num_sum'] or 0)
    return dates, read_nums

def get_today_hot_data(content_type):
    today = timezone.now().date()
    read_details =  ReadDetail.objects.filter(content_type = content_type,date = today).order_by('-read_num')
    return read_details[:8]  #取前几篇显示
    
def get_yesterday_hot_data(content_type):
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    read_details =  ReadDetail.objects.filter(content_type = content_type,date = yesterday).order_by('-read_num')
    return read_details[:10]   #取前几篇显示
def get_seven_days_hot_data():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=7)
    blogs =  Blog.objects \
                            .filter(read_details__date__lt =today,read_details__date__gte=date) \
                            .values('id','title') \
                            .annotate(read_num_sum=Sum('read_details__read_num')) \
                            .order_by('-read_num_sum')
    return blogs[:8]  #取前几篇显示

def get_thirty_days_hot_data():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=30)
    blogs =  Blog.objects \
                            .filter(read_details__date__lt =today,read_details__date__gte=date) \
                            .values('id','title') \
                            .annotate(read_num_sum=Sum('read_details__read_num')) \
                            .order_by('-read_num_sum')
    return blogs[:8]  #取前几篇显示

def login(request):
    # username=request.POST.get('username','')
    # password=request.POST.get('password','')
    # user = auth.authenticate(request,username=username,password=password)
    # referer=request.META.get('HTTP_REFERER',reverse('home'))   # 反向解析到home
    # if user is not None:
    #     auth.login(request,user)
    #     return redirect(referer)
    # else:
    #     return render(request,'error.html',{'message':'用户名或密码不正确','redirect_to':referer})

    if request.method == 'POST':
        login_form=LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.cleaned_data['user']
            auth.login(request,user)
            return redirect(request.GET.get('from',reverse('home')))
    else:
        login_form=LoginForm()


    context={}
    context['login_form']=login_form
    return render(request,'login.html',context)

def register(request):
    if request.method == 'POST':
        reg_form=RegForm(request.POST)
        if reg_form.is_valid():
            username = reg_form.cleaned_data['username']
            email    = reg_form.cleaned_data['email']
            password = reg_form.cleaned_data['password']

            #创建用户
            user=User.objects.create_user(username,email,password)
            user.save()

            #登录用户
            user=auth.authenticate(username=username,password=password)
            auth.login(request,user)

            return redirect(request.GET.get('from',reverse('home')))
            # user=User()
            # user.username=username
            # user.email = email
            # user.set_password(password)
            # user.save()

    else:
        reg_form=RegForm()


    context={}
    context['reg_form']=reg_form
    return render(request,'register.html',context)


def logout(request):
    auth.logout(request)
    return redirect('login')   




'''
############-----------------------
def blog_list(request): 
    blogs_all_list=Blog.objects.all()
    paginator=Paginator(blogs_all_list,10) #按显示条数进行分页
    page_num=request.GET.get('page',1)  #获取页码参数（get请求）
    page_of_blogs=paginator.get_page(page_num)

    currentr_page_num = page_of_blogs.number  #获取当前页码 
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num )) + \
                list(range(currentr_page_num, min( currentr_page_num + 2, paginator.num_pages) + 1))
                #  获取当前页码的前后2个页码，并去掉0和-1页和超出范围的2个页码

    if page_range[0] - 1 >= 2:
        page_range.insert(0,'...')                   #给隐藏的页码添加...         
    if paginator.num_pages - page_range[-1] >=2:
        page_range.append('...')

    if page_range[0] != 1:                      
        page_range.insert(0,1)
    if page_range[-1] != paginator.num_pages:         #添加判断，增加第一页和最后一页
        page_range.append(paginator.num_pages)

    context={}
    context['blogs']=page_of_blogs.object_list
    context['page_of_blogs']=page_of_blogs
    context['page_range'] = page_range
    context['blog_types']=BlogType.objects.all()

    context['blog_dates']=Blog.objects.dates('create_time','month',order="DESC") #获取到博客日期排序列表，order排序

    # context={}
    # context['blogs']=Blog.objects.all()
    # context['blog_types']=BlogType.objects.all()
    ###### context['blogs_count']=Blog.objects.all().count()#统计博客总共多少篇的第二个方法
    return render(request,'blog/blog_list.html',context)

def blogs_with_type(request,blog_type_pk):
    context={}
    blog_type= get_object_or_404(BlogType,pk=blog_type_pk)
    #
    #
    #

    blogs_all_list=Blog.objects.filter(blog_type=blog_type)  #-----
    paginator=Paginator(blogs_all_list,5) #按显示条数进行分页
    page_num=request.GET.get('page',1)  #获取页码参数（get请求）
    page_of_blogs=paginator.get_page(page_num)

    currentr_page_num = page_of_blogs.number  #获取当前页码 
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num )) + \
                list(range(currentr_page_num, min( currentr_page_num + 2, paginator.num_pages) + 1))
                #  获取当前页码的前后2个页码，并去掉0和-1页和超出范围的2个页码

    if page_range[0] - 1 >= 2:
        page_range.insert(0,'...')                   #给隐藏的页码添加...         
    if paginator.num_pages - page_range[-1] >=2:
        page_range.append('...')

    if page_range[0] != 1:                      
        page_range.insert(0,1)
    if page_range[-1] != paginator.num_pages:         #添加判断，增加第一页和最后一页
        page_range.append(paginator.num_pages)



    context={}
    context['blog_type']= blog_type    #---
    context['blogs']=page_of_blogs.object_list
    context['page_of_blogs']=page_of_blogs
    context['page_range'] = page_range
    context['blog_types']=BlogType.objects.all()

    context['blog_dates']=Blog.objects.dates('create_time','month',order="DESC") #获取到博客日期排序列表，order排序
    return render(request,'blog/blogs_with_type.html',context)

def blogs_with_date(request,year,month):
    context={}
    blogs_all_list=Blog.objects.filter(create_time__year=year,create_time__month=month)

    paginator=Paginator(blogs_all_list,5) #按显示条数进行分页
    page_num=request.GET.get('page',1)  #获取页码参数（get请求）
    page_of_blogs=paginator.get_page(page_num)

    currentr_page_num = page_of_blogs.number  #获取当前页码 
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num )) + \
                list(range(currentr_page_num, min( currentr_page_num + 2, paginator.num_pages) + 1))
                #  获取当前页码的前后2个页码，并去掉0和-1页和超出范围的2个页码
    if page_range[0] - 1 >= 2:
        page_range.insert(0,'...')                   #给隐藏的页码添加...         
    if paginator.num_pages - page_range[-1] >=2:
        page_range.append('...')

    if page_range[0] != 1:                      
        page_range.insert(0,1)
    if page_range[-1] != paginator.num_pages:         #添加判断，增加第一页和最后一页
        page_range.append(paginator.num_pages)

    context={}
    context['blogs_with_date']='%s年%s月' %(year,month)
    context['blogs']=page_of_blogs.object_list
    context['page_of_blogs']=page_of_blogs
    context['page_range'] = page_range
    context['blog_types']=BlogType.objects.all()
    context['blog_dates']=Blog.objects.dates('create_time','month',order="DESC") #获取到博客日期排序列表，order排序
    return render(request,'blog/blogs_with_date.html',context)

def blog_defail(request,blog_pk):
    context={}
    blog=get_object_or_404(Blog,pk=blog_pk)

    context['previous_blog'] = Blog.objects.filter(create_time__gt = blog.create_time).last()
    context['next_blog'] = Blog.objects.filter(create_time__lt = blog.create_time).first()
    context['blog'] = blog


    return render(request,'blog/blog_defail.html',context)
## def blogs_with_type(request,blog_type_pk):
##     context={}
##    blog_type= get_object_or_404(BlogType,pk=blog_type_pk)
##     context['blog_type']= blog_type
##     context['blogs']=Blog.objects.filter(blog_type=blog_type)
##     context['blog_types']=BlogType.objects.all()
##     return render(request,'blog/blogs_with_type.html',context)
'''






