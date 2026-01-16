"""
リアルタイム翻訳オーバーレイアプリ
====================================
画面上の英語テキストをOCRで読み取り、日本語に翻訳してオーバーレイ表示します。

使い方:
1. アプリを起動し、透明ウィンドウを翻訳したいテキストの上に移動
2. ウィンドウの端をドラッグしてサイズを調整
3. 「翻訳」ボタンを押すか、自動翻訳をONにして翻訳を実行
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import mss
import mss.tools
import pytesseract
from deep_translator import GoogleTranslator
import threading
import time
import sys
import os

# ============================================================
# Tesseract OCRのパス設定（Windows用）
# ============================================================
# Tesseractがインストールされていない場合、以下からダウンロード:
# https://github.com/UB-Mannheim/tesseract/wiki
#
# インストール後、以下のコメントを解除してパスを設定してください:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# ============================================================

# Windows環境でのデフォルトパスを自動設定
if sys.platform == 'win32':
    default_tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(default_tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = default_tesseract_path


class TranslatorOverlay:
    """翻訳オーバーレイアプリのメインクラス"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("翻訳オーバーレイ")

        # ウィンドウの初期設定
        self.window_width = 600
        self.window_height = 200
        self.root.geometry(f"{self.window_width}x{self.window_height}")

        # 常に最前面に表示
        self.root.attributes('-topmost', True)

        # ウィンドウ枠をなくす
        self.root.overrideredirect(True)

        # 透明度設定（0.0が完全透明、1.0が不透明）
        self.root.attributes('-alpha', 0.85)

        # Windows用の透過設定
        self.root.configure(bg='black')
        self.root.attributes('-transparentcolor', 'black')

        # 状態変数
        self.is_auto_translate = False
        self.auto_translate_interval = 2000  # ミリ秒
        self.auto_job = None
        self.is_dragging = False
        self.is_resizing = False
        self.is_fullscreen = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_edge = None
        self.saved_geometry = None  # 全画面前のサイズ・位置を保存
        self.initial_x = 0
        self.initial_y = 0
        self.initial_width = 0
        self.initial_height = 0

        # 翻訳結果
        self.translated_text = ""
        self.original_text = ""

        # UIを構築
        self._create_ui()

        # イベントバインド
        self._bind_events()

    def _create_ui(self):
        """UIコンポーネントを作成"""

        # リサイズ用の外枠フレーム
        self.border_size = 6  # リサイズ用の枠の太さ

        # 上端
        self.border_top = tk.Frame(self.root, bg='#0f3460', height=self.border_size, cursor='size_ns')
        self.border_top.pack(fill=tk.X, side=tk.TOP)

        # 下端
        self.border_bottom = tk.Frame(self.root, bg='#0f3460', height=self.border_size, cursor='size_ns')
        self.border_bottom.pack(fill=tk.X, side=tk.BOTTOM)

        # 左端
        self.border_left = tk.Frame(self.root, bg='#0f3460', width=self.border_size, cursor='size_we')
        self.border_left.pack(fill=tk.Y, side=tk.LEFT)

        # 右端
        self.border_right = tk.Frame(self.root, bg='#0f3460', width=self.border_size, cursor='size_we')
        self.border_right.pack(fill=tk.Y, side=tk.RIGHT)

        # メインフレーム（半透明の背景）
        self.main_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 上部コントロールバー
        self.control_bar = tk.Frame(self.main_frame, bg='#16213e', height=40)
        self.control_bar.pack(fill=tk.X, side=tk.TOP)
        self.control_bar.pack_propagate(False)

        # タイトルラベル（ドラッグ用）
        self.title_label = tk.Label(
            self.control_bar,
            text="📝 翻訳オーバーレイ",
            bg='#16213e',
            fg='#e94560',
            font=('Yu Gothic UI', 10, 'bold'),
            cursor='fleur'
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 閉じるボタン
        self.close_btn = tk.Button(
            self.control_bar,
            text="✕",
            command=self.close_app,
            bg='#16213e',
            fg='#e94560',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#e94560',
            activeforeground='white'
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # 最小化ボタン
        self.minimize_btn = tk.Button(
            self.control_bar,
            text="─",
            command=self.minimize_app,
            bg='#16213e',
            fg='#0f3460',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#0f3460',
            activeforeground='white'
        )
        self.minimize_btn.pack(side=tk.RIGHT, padx=2, pady=5)

        # 全画面ボタン
        self.fullscreen_btn = tk.Button(
            self.control_bar,
            text="□",
            command=self.toggle_fullscreen,
            bg='#16213e',
            fg='#0f3460',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#0f3460',
            activeforeground='white'
        )
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=2, pady=5)

        # ボタンフレーム
        self.button_frame = tk.Frame(self.control_bar, bg='#16213e')
        self.button_frame.pack(side=tk.LEFT, padx=20, pady=5)

        # 翻訳ボタン
        self.translate_btn = tk.Button(
            self.button_frame,
            text="🔄 翻訳",
            command=self.translate_once,
            bg='#0f3460',
            fg='white',
            font=('Yu Gothic UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            activebackground='#e94560'
        )
        self.translate_btn.pack(side=tk.LEFT, padx=5)

        # 自動翻訳トグルボタン
        self.auto_btn = tk.Button(
            self.button_frame,
            text="⏸ 自動OFF",
            command=self.toggle_auto_translate,
            bg='#0f3460',
            fg='white',
            font=('Yu Gothic UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            padx=10,
            activebackground='#e94560'
        )
        self.auto_btn.pack(side=tk.LEFT, padx=5)

        # クリアボタン
        self.clear_btn = tk.Button(
            self.button_frame,
            text="🗑 クリア",
            command=self.clear_text,
            bg='#0f3460',
            fg='white',
            font=('Yu Gothic UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            padx=10,
            activebackground='#e94560'
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # コンテンツエリア（翻訳結果表示用）
        self.content_frame = tk.Frame(self.main_frame, bg='black')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 翻訳テキスト表示用Canvas
        self.text_canvas = tk.Canvas(
            self.content_frame,
            bg='black',
            highlightthickness=0
        )
        self.text_canvas.pack(fill=tk.BOTH, expand=True)

        # ステータスバー
        self.status_bar = tk.Frame(self.main_frame, bg='#16213e', height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_bar,
            text="待機中... ウィンドウを翻訳したいテキストの上に移動してください",
            bg='#16213e',
            fg='#7f8c8d',
            font=('Yu Gothic UI', 8)
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)

        # サイズ表示
        self.size_label = tk.Label(
            self.status_bar,
            text=f"{self.window_width}x{self.window_height}",
            bg='#16213e',
            fg='#7f8c8d',
            font=('Yu Gothic UI', 8)
        )
        self.size_label.pack(side=tk.RIGHT, padx=10, pady=2)

        # リサイズグリップ（右下）
        self.resize_grip = tk.Label(
            self.status_bar,
            text="⋮⋮",
            bg='#16213e',
            fg='#0f3460',
            font=('Arial', 10),
            cursor='size_nw_se'
        )
        self.resize_grip.pack(side=tk.RIGHT, padx=5)

    def _bind_events(self):
        """イベントをバインド"""

        # タイトルバーでのドラッグ移動
        self.title_label.bind('<Button-1>', self._start_drag)
        self.title_label.bind('<B1-Motion>', self._on_drag)
        self.title_label.bind('<ButtonRelease-1>', self._stop_drag)

        self.control_bar.bind('<Button-1>', self._start_drag)
        self.control_bar.bind('<B1-Motion>', self._on_drag)
        self.control_bar.bind('<ButtonRelease-1>', self._stop_drag)

        # リサイズグリップでのリサイズ
        self.resize_grip.bind('<Button-1>', self._start_resize_se)
        self.resize_grip.bind('<B1-Motion>', self._on_resize)
        self.resize_grip.bind('<ButtonRelease-1>', self._stop_resize)

        # 枠でのリサイズ（確実に検出）
        # 上端
        self.border_top.bind('<Button-1>', lambda e: self._start_border_resize('n'))
        self.border_top.bind('<B1-Motion>', self._on_resize)
        self.border_top.bind('<ButtonRelease-1>', self._stop_resize)

        # 下端
        self.border_bottom.bind('<Button-1>', lambda e: self._start_border_resize('s'))
        self.border_bottom.bind('<B1-Motion>', self._on_resize)
        self.border_bottom.bind('<ButtonRelease-1>', self._stop_resize)

        # 左端
        self.border_left.bind('<Button-1>', lambda e: self._start_border_resize('w'))
        self.border_left.bind('<B1-Motion>', self._on_resize)
        self.border_left.bind('<ButtonRelease-1>', self._stop_resize)

        # 右端
        self.border_right.bind('<Button-1>', lambda e: self._start_border_resize('e'))
        self.border_right.bind('<B1-Motion>', self._on_resize)
        self.border_right.bind('<ButtonRelease-1>', self._stop_resize)

        # キーボードショートカット
        self.root.bind('<Escape>', lambda e: self.close_app())
        self.root.bind('<F5>', lambda e: self.translate_once())
        self.root.bind('<F6>', lambda e: self.toggle_auto_translate())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())

    def _start_drag(self, event):
        """ドラッグ開始"""
        self.is_dragging = True
        self.drag_start_x = event.x_root - self.root.winfo_x()
        self.drag_start_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        """ドラッグ中"""
        if self.is_dragging:
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")

    def _stop_drag(self, event):
        """ドラッグ終了"""
        self.is_dragging = False

    def _check_resize_cursor(self, event):
        """マウス位置に応じてカーソルを変更"""
        if self.is_resizing:
            return

        edge_size = 20  # 端の検出範囲（ピクセル）- 広めに設定
        width = self.main_frame.winfo_width()
        height = self.main_frame.winfo_height()
        x, y = event.x, event.y

        # 角の検出
        on_left = x < edge_size
        on_right = x > width - edge_size
        on_top = y < edge_size
        on_bottom = y > height - edge_size

        if on_left and on_top:
            self.main_frame.config(cursor='size_nw_se')
            self.resize_edge = 'nw'
        elif on_right and on_top:
            self.main_frame.config(cursor='size_ne_sw')
            self.resize_edge = 'ne'
        elif on_left and on_bottom:
            self.main_frame.config(cursor='size_ne_sw')
            self.resize_edge = 'sw'
        elif on_right and on_bottom:
            self.main_frame.config(cursor='size_nw_se')
            self.resize_edge = 'se'
        elif on_left:
            self.main_frame.config(cursor='size_we')
            self.resize_edge = 'w'
        elif on_right:
            self.main_frame.config(cursor='size_we')
            self.resize_edge = 'e'
        elif on_top:
            self.main_frame.config(cursor='size_ns')
            self.resize_edge = 'n'
        elif on_bottom:
            self.main_frame.config(cursor='size_ns')
            self.resize_edge = 's'
        else:
            self.main_frame.config(cursor='')
            self.resize_edge = None

    def _reset_cursor(self, event):
        """カーソルをリセット"""
        if not self.is_resizing:
            self.main_frame.config(cursor='')
            self.resize_edge = None

    def _start_border_resize(self, edge):
        """枠からのリサイズ開始"""
        self.resize_edge = edge
        self.is_resizing = True
        self.drag_start_x = self.root.winfo_pointerx()
        self.drag_start_y = self.root.winfo_pointery()
        self.initial_width = self.root.winfo_width()
        self.initial_height = self.root.winfo_height()
        self.initial_x = self.root.winfo_x()
        self.initial_y = self.root.winfo_y()

    def _start_edge_resize(self, event):
        """端からのリサイズ開始"""
        if self.resize_edge:
            self.is_resizing = True
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.initial_width = self.root.winfo_width()
            self.initial_height = self.root.winfo_height()
            self.initial_x = self.root.winfo_x()
            self.initial_y = self.root.winfo_y()

    def _start_resize_se(self, event):
        """右下グリップからのリサイズ開始"""
        self.resize_edge = 'se'
        self.is_resizing = True
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.initial_width = self.root.winfo_width()
        self.initial_height = self.root.winfo_height()
        self.initial_x = self.root.winfo_x()
        self.initial_y = self.root.winfo_y()

    def _on_resize(self, event):
        """リサイズ中"""
        if not self.is_resizing or not self.resize_edge:
            return

        delta_x = event.x_root - self.drag_start_x
        delta_y = event.y_root - self.drag_start_y

        new_width = self.initial_width
        new_height = self.initial_height
        new_x = self.initial_x
        new_y = self.initial_y

        min_width = 400
        min_height = 150

        # 方向に応じてサイズと位置を計算
        if 'e' in self.resize_edge:
            new_width = max(min_width, self.initial_width + delta_x)
        if 'w' in self.resize_edge:
            new_width = max(min_width, self.initial_width - delta_x)
            if new_width > min_width:
                new_x = self.initial_x + delta_x
            else:
                new_x = self.initial_x + self.initial_width - min_width
        if 's' in self.resize_edge:
            new_height = max(min_height, self.initial_height + delta_y)
        if 'n' in self.resize_edge:
            new_height = max(min_height, self.initial_height - delta_y)
            if new_height > min_height:
                new_y = self.initial_y + delta_y
            else:
                new_y = self.initial_y + self.initial_height - min_height

        self.window_width = new_width
        self.window_height = new_height

        self.root.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
        self.size_label.config(text=f"{new_width}x{new_height}")

    def _stop_resize(self, event):
        """リサイズ終了"""
        self.is_resizing = False

    def capture_screen(self):
        """ウィンドウ位置のスクリーンショットを撮影"""
        # ウィンドウの位置とサイズを取得
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # コントロールバーとステータスバーの高さを考慮
        control_height = 40
        status_height = 25

        # キャプチャ領域（コンテンツ部分のみ）
        capture_region = {
            'left': x + 2,
            'top': y + control_height,
            'width': width - 4,
            'height': height - control_height - status_height - 4
        }

        with mss.mss() as sct:
            # 一時的にウィンドウを非表示にしてスクリーンショット
            self.root.withdraw()
            time.sleep(0.05)  # ウィンドウが非表示になるのを待つ

            try:
                screenshot = sct.grab(capture_region)
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            finally:
                self.root.deiconify()

        return img

    def perform_ocr(self, image):
        """画像からテキストを抽出"""
        try:
            # OCR設定（英語テキスト用）
            custom_config = r'--oem 3 --psm 6 -l eng'
            text = pytesseract.image_to_string(image, config=custom_config)
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            raise Exception(
                "Tesseract OCRが見つかりません。\n"
                "1. Tesseractをインストールしてください:\n"
                "   https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. main.pyのTesseractパス設定を確認してください。"
            )
        except Exception as e:
            raise Exception(f"OCRエラー: {str(e)}")

    def translate_text(self, text):
        """英語を日本語に翻訳"""
        if not text:
            return ""

        try:
            translator = GoogleTranslator(source='en', target='ja')
            translated = translator.translate(text)
            return translated
        except Exception as e:
            raise Exception(f"翻訳エラー: {str(e)}")

    def display_text(self, text, original=""):
        """翻訳テキストを表示"""
        self.text_canvas.delete("all")

        if not text:
            return

        # Canvas サイズを取得
        self.text_canvas.update_idletasks()
        canvas_width = self.text_canvas.winfo_width()
        canvas_height = self.text_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.window_width - 4
            canvas_height = self.window_height - 65

        # テキストを描画（白文字に黒縁取り効果）
        padding = 10
        font_size = 14
        line_height = font_size + 8

        # テキストを行に分割（長い行は折り返し）
        lines = self._wrap_text(text, canvas_width - padding * 2, font_size)

        y_pos = padding
        for line in lines:
            if y_pos + line_height > canvas_height:
                break

            # 縁取り効果（黒い影を4方向に）
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-2, 0), (2, 0), (0, -2), (0, 2)]:
                self.text_canvas.create_text(
                    padding + dx, y_pos + dy,
                    text=line,
                    anchor='nw',
                    fill='#1a1a2e',
                    font=('Yu Gothic UI', font_size, 'bold')
                )

            # メインテキスト（白）
            self.text_canvas.create_text(
                padding, y_pos,
                text=line,
                anchor='nw',
                fill='#ffffff',
                font=('Yu Gothic UI', font_size, 'bold')
            )

            y_pos += line_height

    def _wrap_text(self, text, max_width, font_size):
        """テキストを指定幅で折り返し"""
        # 簡易的な文字数ベースの折り返し
        chars_per_line = max(10, int(max_width / (font_size * 0.8)))

        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                continue
            while len(paragraph) > chars_per_line:
                lines.append(paragraph[:chars_per_line])
                paragraph = paragraph[chars_per_line:]
            if paragraph:
                lines.append(paragraph)

        return lines

    def translate_once(self):
        """一度だけ翻訳を実行"""
        self.status_label.config(text="🔍 スクリーンショットを取得中...")
        self.root.update()

        def do_translate():
            try:
                # スクリーンショット取得
                image = self.capture_screen()

                self.root.after(0, lambda: self.status_label.config(text="📖 テキストを認識中..."))

                # OCR実行
                original = self.perform_ocr(image)

                if not original:
                    self.root.after(0, lambda: self.status_label.config(text="⚠ テキストが検出されませんでした"))
                    return

                self.root.after(0, lambda: self.status_label.config(text="🌐 翻訳中..."))

                # 翻訳実行
                translated = self.translate_text(original)

                self.original_text = original
                self.translated_text = translated

                # UIスレッドで表示を更新
                self.root.after(0, lambda: self.display_text(translated, original))
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ 翻訳完了 | 元: {len(original)}文字 → 訳: {len(translated)}文字"
                ))

            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"❌ エラー: {str(e)[:50]}"))
                self.root.after(0, lambda: messagebox.showerror("エラー", str(e)))

        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=do_translate, daemon=True)
        thread.start()

    def toggle_auto_translate(self):
        """自動翻訳のON/OFF切り替え"""
        self.is_auto_translate = not self.is_auto_translate

        if self.is_auto_translate:
            self.auto_btn.config(text="▶ 自動ON", bg='#e94560')
            self.status_label.config(text=f"🔄 自動翻訳ON ({self.auto_translate_interval/1000}秒間隔)")
            self._auto_translate_loop()
        else:
            self.auto_btn.config(text="⏸ 自動OFF", bg='#0f3460')
            self.status_label.config(text="⏸ 自動翻訳OFF")
            if self.auto_job:
                self.root.after_cancel(self.auto_job)
                self.auto_job = None

    def _auto_translate_loop(self):
        """自動翻訳ループ"""
        if self.is_auto_translate:
            self.translate_once()
            self.auto_job = self.root.after(self.auto_translate_interval, self._auto_translate_loop)

    def clear_text(self):
        """翻訳テキストをクリア"""
        self.text_canvas.delete("all")
        self.translated_text = ""
        self.original_text = ""
        self.status_label.config(text="🗑 クリアしました")

    def toggle_fullscreen(self):
        """全画面表示の切り替え"""
        if self.is_fullscreen:
            # 全画面解除 - 元のサイズに戻す
            if self.saved_geometry:
                self.root.geometry(self.saved_geometry)
                # 保存していたサイズを復元
                parts = self.saved_geometry.split('+')[0].split('x')
                self.window_width = int(parts[0])
                self.window_height = int(parts[1])
            self.fullscreen_btn.config(text="□")
            self.is_fullscreen = False
            self.size_label.config(text=f"{self.window_width}x{self.window_height}")
        else:
            # 全画面表示
            self.saved_geometry = self.root.geometry()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.window_width = screen_width
            self.window_height = screen_height
            self.fullscreen_btn.config(text="❐")
            self.is_fullscreen = True
            self.size_label.config(text=f"{screen_width}x{screen_height} (全画面)")

    def minimize_app(self):
        """アプリを最小化"""
        self.root.iconify()

    def close_app(self):
        """アプリを終了"""
        if self.auto_job:
            self.root.after_cancel(self.auto_job)
        self.root.destroy()

    def run(self):
        """アプリを実行"""
        # 画面中央に配置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        self.root.mainloop()


def main():
    """メイン関数"""
    try:
        print("=" * 50)
        print("Real-time Translation Overlay")
        print("=" * 50)
        print("\nStarting...")
        print("\n[Controls]")
        print("  - Drag title bar: Move window")
        print("  - Drag bottom-right corner: Resize")
        print("  - F5: Translate")
        print("  - F6: Auto translate ON/OFF")
        print("  - ESC: Exit")
        print("-" * 50)
    except UnicodeEncodeError:
        pass  # コンソール出力エラーを無視

    try:
        app = TranslatorOverlay()
        app.run()
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        messagebox.showerror("起動エラー", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

