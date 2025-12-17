from src.repositories.loan_repository import LoanRepository
class LoanService:
    def __init__(self): self.repo = LoanRepository()
    def lend_book(self, kopya_id, kullanici_id): return {"success": False, "message": "Eski yöntem kapalı."} # Artık assign_book kullanıyoruz
    def return_book(self, kopya_id): return self.repo.return_book(kopya_id)
    def get_active_loans_report(self): return {"success": True, "data": self.repo.get_all_active_loans()}
    def get_fines_report(self): return {"success": True, "data": self.repo.get_overdue_fines()}
    def get_stats(self): return self.repo.get_stats()