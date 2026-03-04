import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import zipfile
import shutil
from PIL import Image
from concurrent.futures import ProcessPoolExecutor, as_completed

class ImageOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("画像最適化ツール")
        self.root.geometry("600x600")
        
        # 実行ファイルのディレクトリを取得
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた場合
            self.exe_dir = os.path.dirname(sys.executable)
        else:
            # 通常のPythonスクリプトとして実行された場合
            self.exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        # デフォルトパス
        self.default_input = os.path.join(self.exe_dir, "input")
        self.default_output = os.path.join(self.exe_dir, "output")
        
        self.setup_ui()
        
    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 入力フォルダ選択
        ttk.Label(main_frame, text="入力フォルダ:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.input_var = tk.StringVar(value=self.default_input)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Entry(input_frame, textvariable=self.input_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="参照", command=self.browse_input).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 出力フォルダ選択
        ttk.Label(main_frame, text="出力フォルダ:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.output_var = tk.StringVar(value=self.default_output)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="参照", command=self.browse_output).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 処理タイプ選択
        ttk.Label(main_frame, text="処理タイプ:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.process_type = tk.StringVar(value="folder")
        process_frame = ttk.Frame(main_frame)
        process_frame.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Radiobutton(process_frame, text="フォルダ内の画像ファイル", variable=self.process_type, value="folder").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(process_frame, text="ZIPファイル", variable=self.process_type, value="zip").pack(side=tk.LEFT)
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="10")
        settings_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        
        # JPEG品質
        ttk.Label(settings_frame, text="JPEG品質:").grid(row=0, column=0, sticky=tk.W)
        self.quality_var = tk.IntVar(value=87)
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Scale(quality_frame, from_=50, to=100, variable=self.quality_var, orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT)
        self.quality_label = ttk.Label(quality_frame, text="87")
        self.quality_label.pack(side=tk.LEFT, padx=(10, 0))
        self.quality_var.trace('w', self.update_quality_label)
        
        # 目標高さ
        ttk.Label(settings_frame, text="目標高さ(ピクセル):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.height_var = tk.IntVar(value=1200)
        ttk.Entry(settings_frame, textvariable=self.height_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 最小ファイルサイズ（KB）
        ttk.Label(settings_frame, text="最小ファイルサイズ(KB, 0で無制限):").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.min_size_var = tk.IntVar(value=400)
        ttk.Entry(settings_frame, textvariable=self.min_size_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 処理ボタン
        self.process_button = ttk.Button(main_frame, text="処理開始", command=self.start_processing)
        self.process_button.grid(row=7, column=0, columnspan=2, pady=(20, 10))
        
        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ログエリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=10, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.insert(tk.END, "文字が滲むのは仕様やで\n")
        self.log_text.insert(tk.END, "JPEG品質は80～90くらいがオススメやで。それ以上は区別できないのに重い\n")
        self.log_text.insert(tk.END, "目標高さ（ピクセル）が元画像より小さい場合は縮小リサイズ\n")


        # グリッドの重みを設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        input_frame.columnconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def update_quality_label(self, *args):
        self.quality_label.config(text=str(self.quality_var.get()))
        
    def browse_input(self):
        folder = filedialog.askdirectory(initialdir=self.input_var.get())
        if folder:
            self.input_var.set(folder)
            
    def browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)
            
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def optimize_image(self, input_path, output_path, quality, target_height):
        """1つの画像を最適化"""
        try:
            img = Image.open(input_path)
            icc_profile = img.info.get('icc_profile')
            
            # RGBA → RGB変換
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # リサイズ
            if img.height > target_height:
                aspect_ratio = img.width / img.height
                target_width = int(target_height * aspect_ratio)
                img = img.resize((target_width, target_height), Image.LANCZOS)
            
            # サイズ計算（上書き前の元サイズを先に取得）
            original_size = os.path.getsize(input_path) / 1024

            # JPEG保存
            img.save(output_path, 'JPEG', quality=quality, icc_profile=icc_profile)
            
            # 新しいサイズを取得
            new_size = os.path.getsize(output_path) / 1024
            reduction = original_size - new_size
            
            return reduction, original_size, new_size
            
        except Exception as e:
            self.log(f"エラー {input_path}: {e}")
            return 0, 0, 0
    
    def process_folder_images(self, input_dir, output_dir, quality, target_height, min_size_kb):
        """フォルダ内の画像ファイルを処理"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 画像ファイル一覧取得
        image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if not image_files:
            self.log("処理対象の画像ファイルが見つかりません")
            return
            
        self.log(f"処理対象: {len(image_files)} ファイル")
        total_reduction = 0
        i=0
        
        # 処理
        for image_file in image_files:
            i+=1
            input_path = os.path.join(input_dir, image_file)
            original_size_kb = os.path.getsize(input_path) / 1024
            if min_size_kb > 0 and original_size_kb < min_size_kb:
                self.log(f"{image_file}: {original_size_kb:.2f} KB (しきい値未満のためスキップ)")
                self.log(f"処理中: {i}/{len(image_files)}")
                continue
            base_name = os.path.splitext(image_file)[0]
            output_path = os.path.join(output_dir, f"{base_name}.jpg")
            reduction, original_size, new_size = self.optimize_image(input_path, output_path, quality, target_height)
            if new_size > 0:  # エラーでない場合
                self.log(f"{image_file}: {original_size:.2f} KB -> {new_size:.2f} KB")
            self.log(f"処理中: {i}/{len(image_files)}")
            total_reduction += reduction
        
        total_reduction_mb = total_reduction / 1024
        self.log(f"総削減量: {total_reduction_mb:.2f} MB")
        self.log("フォルダ処理完了！")
    
    def process_zip_file(self, zip_path, output_dir, temp_dir, quality, target_height, min_size_kb):
        """単一のZIPファイルを処理"""
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        temp_zip_dir = os.path.join(temp_dir, zip_name)
        os.makedirs(temp_zip_dir, exist_ok=True)
        output_jpg_dir = os.path.join(temp_zip_dir, "_jpgs")
        os.makedirs(output_jpg_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_zip_dir)
        except zipfile.BadZipFile:
            self.log(f"エラー: {zip_path} は壊れたZIPファイルです")
            return
        
        # 画像ファイルを再帰的に取得
        image_files = []
        for root, dirs, files in os.walk(temp_zip_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, temp_zip_dir)
                    image_files.append((abs_path, rel_path))
        
        self.log(f"ZIP処理: {zip_name} ({len(image_files)} ファイル)")
        
        # 画像を変換
        for i, (abs_path, rel_path) in enumerate(image_files, 1):
            original_size_kb = os.path.getsize(abs_path) / 1024
            if min_size_kb > 0 and original_size_kb < min_size_kb:
                self.log(f"{rel_path}: {original_size_kb:.2f} KB (しきい値未満のためスキップ)")
                self.log(f"ZIP内処理中: {i}/{len(image_files)}")
                continue
            rel_jpg_path = os.path.splitext(rel_path)[0] + ".jpg"
            out_abs_path = os.path.join(output_jpg_dir, rel_jpg_path)
            out_abs_dir = os.path.dirname(out_abs_path)
            os.makedirs(out_abs_dir, exist_ok=True)
            
            reduction, original_size, new_size = self.optimize_image(abs_path, out_abs_path, quality, target_height)
            if new_size > 0:  # エラーでない場合
                self.log(f"{rel_path}: {original_size:.2f} KB -> {new_size:.2f} KB")
            self.log(f"ZIP内処理中: {i}/{len(image_files)}")
        
        # JPEGをZIPに再圧縮
        zip_output = os.path.join(output_dir, f"{zip_name}_resized.zip")
        with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(output_jpg_dir):
                for file in files:
                    abs_file = os.path.join(root, file)
                    rel_file = os.path.relpath(abs_file, output_jpg_dir)
                    zip_ref.write(abs_file, rel_file)
        
        # 一時ディレクトリ削除
        shutil.rmtree(temp_zip_dir, ignore_errors=True)
        
    def process_zip_files(self, input_dir, output_dir, quality, target_height, min_size_kb):
        """ZIPファイルを処理"""
        temp_dir = os.path.join(self.exe_dir, "temp_extracted")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # ZIPファイル一覧取得
        zip_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.zip')]
        if not zip_files:
            self.log(f"エラー: {input_dir} にZIPファイルが見つかりません")
            return
        
        self.log(f"処理対象ZIP: {len(zip_files)} ファイル")
        
        # 各ZIPを処理
        for zip_file in zip_files:
            self.process_zip_file(os.path.join(input_dir, zip_file), output_dir, temp_dir, quality, target_height, min_size_kb)
        
        # 一時ディレクトリ削除
        shutil.rmtree(temp_dir, ignore_errors=True)
        self.log("全ZIP処理完了！")
    
    def start_processing(self):
        """処理開始"""
        input_dir = self.input_var.get()
        output_dir = self.output_var.get()
        quality = self.quality_var.get()
        target_height = self.height_var.get()
        process_type = self.process_type.get()
        min_size_kb = self.min_size_var.get()
        
        # 入力検証
        if not os.path.exists(input_dir):
            messagebox.showerror("エラー", "入力フォルダが存在しません")
            return
        
        # ログクリア
        self.log_text.delete(1.0, tk.END)
        
        # UIを無効化
        self.process_button.config(state="disabled")
        self.progress.start()
        
        # 別スレッドで処理実行
        def process_thread():
            try:
                if process_type == "folder":
                    self.process_folder_images(input_dir, output_dir, quality, target_height, min_size_kb)
                else:
                    self.process_zip_files(input_dir, output_dir, quality, target_height, min_size_kb)
            except Exception as e:
                self.log(f"処理中にエラーが発生しました: {e}")
            finally:
                # UIを有効化
                self.root.after(0, self.finish_processing)
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def finish_processing(self):
        """処理完了時の処理"""
        self.progress.stop()
        self.process_button.config(state="normal")
        messagebox.showinfo("完了", "処理が完了しました！")

def main():
    root = tk.Tk()
    app = ImageOptimizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()