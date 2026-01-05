"""최저가 알림이 프로그램 엔트리 포인트"""

import tkinter as tk
from ui.app import PriceAlertApp


def main():
    """메인 함수"""
    root = tk.Tk()
    app = PriceAlertApp(root)
    app.run()


if __name__ == "__main__":
    main()
