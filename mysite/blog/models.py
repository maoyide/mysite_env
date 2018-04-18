from django.db import models
from django.db.models.fields import exceptions
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from ckeditor_uploader.fields import RichTextUploadingField
from read_count.models import ReadNum,ReadDetail
# Create your models here.
class BlogType(models.Model):
    type_name = models.CharField(max_length=50)
    def __str__(self):
        return self.type_name


class Blog(models.Model):
    title   = models.CharField(max_length=50)
    blog_type = models.ForeignKey(BlogType,on_delete=models.DO_NOTHING)
    content = RichTextUploadingField(config_name ='blog_ckeditor')
    author  = models.ForeignKey(User,on_delete= models.DO_NOTHING)
    read_details = GenericRelation(ReadDetail) 
    create_time = models.DateTimeField( auto_now_add = True)
    last_updata_time = models.DateTimeField(auto_now=True)


    def get_read_num(self):
        ct = ContentType.objects.get_for_model(Blog) 
        try:
            readnum = ReadNum.objects.get(content_type=ct,object_id=self.pk)
            return readnum.read_num
        except exceptions.ObjectDoesNotExist:
            return 0

    def __str__(self):
        return "<Blog:%s>" % self.title

    class Meta():
        ordering = ["-create_time"]   #按创建时间最新的排序
'''
class ReadNum(models.Model):
    read_num = models.IntegerField(default=0)
    blog = models.OneToOneField(Blog,on_delete=models.DO_NOTHING)  #一对一关联外键
'''
