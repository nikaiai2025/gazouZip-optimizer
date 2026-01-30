import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ファイル名リネームツール (YYYY-MM-DD -> YYYY-MM)")
        self.root.geometry("600x500")

        # UI Components
        self.create_widgets()

    def create_widgets(self):
        # Folder Selection
        folder_frame = tk.Frame(self.root, padx=10, pady=10)
        folder_frame.pack(fill=tk.X)

        self.folder_path = tk.StringVar()
        tk.Label(folder_frame, text="対象フォルダ:").pack(side=tk.LEFT)
        tk.Entry(folder_frame, textvariable=self.folder_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="参照", command=self.browse_folder).pack(side=tk.LEFT)

        # Instructions
        instr_text = "仕様: YYYY-MM-DD_... を YYYY-MM_... に変換します。\n(IDが7桁以上の数字である規則に基づきパースします)"
        tk.Label(self.root, text=instr_text, justify=tk.LEFT, fg="blue").pack(pady=5)

        # Log Area
        tk.Label(self.root, text="実行ログ:").pack(anchor=tk.W, padx=10)
        self.log_area = scrolledtext.ScrolledText(self.root, height=15, padx=5, pady=5)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Run Button
        tk.Button(self.root, text="リネーム実行", command=self.run_rename, bg="#4CAF50", fg="white", height=2).pack(fill=tk.X, padx=10, pady=10)

    def browse_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder_path.set(selected)
            self.log_area.insert(tk.END, f"Selected: {selected}\n")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def run_rename(self):
        directory = self.folder_path.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("エラー", "有効なフォルダを選択してください。")
            return

        self.log_area.delete(1.0, tk.END)
        self.log("処理を開始します...")

        # Regex Pattern Explanation:
        # ^(\d{4}-\d{2})  : Group 1 - Year and Month (YYYY-MM)
        # (?:-\d{2})?     : Non-capturing group - matches -DD optionally (for mixed YYYY-MM and YYYY-MM-DD)
        # _               : Literal separator
        # (.*)            : Group 2 - Everything else (Title, ID, Page)
        # _(\d{7,})       : Group 3 - ID (7 digits or more) preceded by underscore
        # _(p\d+)$        : Group 4 - Page number suffix (p + digits) at the end
        # Note: We focus on changing the date part while preserving the rest.
        
        # Simple pattern to target the date prefix safely
        pattern = re.compile(r"^(\d{4}-\d{2})-\d{2}_(.+)$")

        count = 0
        error_count = 0
        skipped_count = 0

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        for i, filename in enumerate(files):
            # 数件ごとにGUIを更新して「固まってない」ことが分かるようにする
            if (i + 1) % 5 == 0 or i == 0:
                self.root.update_idletasks()
            # Separate extension
            name, ext = os.path.splitext(filename)
            
            match = pattern.match(name)
            if match:
                yyyy_mm = match.group(1)
                rest = match.group(2)
                new_name = f"{yyyy_mm}_{rest}{ext}"
                
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_name)

                try:
                    if os.path.exists(new_path) and filename != new_name:
                        self.log(f"[重複スキップ] {filename} -> すでに存在します")
                        skipped_count += 1
                    else:
                        os.rename(old_path, new_path)
                        self.log(f"[成功] {filename} -> {new_name}")
                        count += 1
                except Exception as e:
                    self.log(f"[エラー] {filename}: {str(e)}")
                    error_count += 1
            else:
                # Check if it's already YYYY-MM format to avoid double processing
                if re.match(r"^\d{4}-\d{2}_", name):
                    self.log(f"[スキップ] {filename} (すでにYYYY-MM形式です)")
                else:
                    self.log(f"[対象外] {filename} (命名規則に一致しません)")
                skipped_count += 1

        messagebox.showinfo("完了", f"処理が完了しました。\n成功: {count}\nスキップ: {skipped_count}\nエラー: {error_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()