
class ProgressBar:
    def __init__(self, total: int, label: str = "Progress"):
        self.total = total
        self.current = 0
        self.label = label
    
    def update(self, n: int = 1):
        self.current += n
        percent = (self.current / self.total) * 100
        bar_len = 40
        filled = int(bar_len * self.current / self.total)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f'\r{self.label}: |{bar}| {percent:.1f}% ({self.current}/{self.total})', end='', flush=True)
        if self.current >= self.total:
            print()