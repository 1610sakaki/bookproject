from venv import create
from django.core.paginator import Paginator  # ページネーションの追加
from django.contrib.auth.mixins import LoginRequiredMixin  # ログインしていない状態ではViewを表示しない
from django.core.exceptions import PermissionDenied  # ログインしているユーザーだけが編集できる仕組み
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.db.models import Avg
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
)
#from requests import request
from .models import Book, Review

#from pyrsistent import field
from .models import Book

from .consts import ITEM_PER_PAGE


class ListBookView(LoginRequiredMixin, ListView):
    template_name = 'book/book_list.html'
    model = Book
    paginate_by = ITEM_PER_PAGE


class DetailBookView(LoginRequiredMixin, DetailView):
    template_name = 'book/book_detail.html'
    model = Book


class CreateBookView(LoginRequiredMixin, CreateView):
    template = 'book/book_form.html'
    model = Book
    fields = ('title', 'text', 'category')
    success_url = reverse_lazy('list-book')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class DeleteBookView(LoginRequiredMixin, DeleteView):
    template = 'book/book_delete.html'
    model = Book
    success_url = reverse_lazy('list-book')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj


class UpdateBookView(LoginRequiredMixin, UpdateView):
    model = Book
    fields = ('title', 'text', 'category')
    template_name = 'book/book_update.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
            #raise NameError("あなたは変更の権限がありません")
        return obj

    def get_success_url(self):
        return reverse('detail-book', kwargs={'pk': self.object.id})


class CreateReviewView(LoginRequiredMixin, CreateView):  # レビュー機能
    model = Review
    fields = ('book', 'title', 'text', 'rate')
    template_name = 'book/review_form.html'

    def get_context_data(self, **kwargs):  # 選んだ書籍のデータ（オブジェクト）を作成（辞書型）
        context = super().get_context_data(**kwargs)
        context['book'] = Book.objects.get(pk=self.kwargs['book_id'])
        '''
        print(context)
        {'form': <ReviewForm bound=False, valid=Unknown, fields=(book;title;text;rate)>, 
         'view': <book.views.CreateReviewView object at 0x7f2170080190>, 
         'book': <Book: Djangoについて詳しくなれる本>}
        '''
        return context

    def form_valid(self, form):  # フォームのデータにユーザーの情報を与える。
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('detail-book', kwargs={'pk': self.object.book.id})


def index_view(request):  # データ作成後に、redirect先のurlを指定する
    #print('index_view is called')
    object_list = Book.objects.order_by('-id')  # '-'をつけると降順
    ranking_list = Book.objects.annotate(
        avg_rating=Avg('review__rate')).order_by('-avg_rating')
    paginator = Paginator(ranking_list, ITEM_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.page(page_number)
    print(page_obj.has_previous)
    return render(request, 'book/index.html', {'object_list': object_list, 'ranking_list': ranking_list, 'page_obj': page_obj})
