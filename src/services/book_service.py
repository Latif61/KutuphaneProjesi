from src.repositories.book_repository import BookRepository
class BookService:
    def __init__(self): self.repo = BookRepository()
    def add_new_book(self, **kwargs):
        if self.repo.add_book(kwargs): return {"success": True}
        return {"success": False, "message": "Hata"}
    def get_books(self): return {"success": True, "data": self.repo.get_all_books()}
    def add_copy(self, kitap_id, barkod, raf_konumu):
        if self.repo.add_book_copy(kitap_id, barkod, raf_konumu): return {"success": True}
        return {"success": False, "message": "Hata"}
    def search(self, query): return {"success": True, "data": self.repo.search_books(query)}