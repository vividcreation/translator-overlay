# 🌐 リアルタイム翻訳オーバーレイ - セットアップ手順書

画面上の英語テキストをリアルタイムで日本語に翻訳するデスクトップアプリです。

---

## 📋 必要な環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10 / 11 |
| Python | 3.8 以上 |
| インターネット | 翻訳時に必要 |

---

## 🚀 セットアップ手順

### Step 1: Pythonのインストール

Pythonがインストールされていない場合は、以下の手順でインストールしてください。

1. [Python公式サイト](https://www.python.org/downloads/) にアクセス
2. 「Download Python 3.x.x」をクリックしてダウンロード
3. インストーラーを実行
4. **⚠️ 重要**: 「Add Python to PATH」にチェックを入れる
5. 「Install Now」をクリック

#### 確認方法
コマンドプロンプトまたはPowerShellで以下を実行：
```
py --version
```
バージョンが表示されればOKです。

---

### Step 2: Tesseract OCRのインストール

文字認識（OCR）に必要なソフトウェアです。

1. 以下のURLからインストーラーをダウンロード：

   👉 https://github.com/UB-Mannheim/tesseract/wiki

   「tesseract-ocr-w64-setup-x.x.x.exe」をクリック

2. ダウンロードしたインストーラーを実行

3. インストール設定：
   - 「Install for anyone using this computer」を選択 → Next
   - インストール先はデフォルト（`C:\Program Files\Tesseract-OCR`）のまま → Next
   - **Additional language data** で **English** が選択されていることを確認 → Next
   - Install をクリック

4. インストール完了後、「Finish」をクリック

---

### Step 3: translator-overlayのファイルを配置

1. 以下のファイルを任意のフォルダにコピーしてください：
   ```
   translator-overlay/
   ├── main.py                 （メインプログラム）
   ├── requirements.txt        （依存ライブラリ一覧）
   └── TranslatorOverlay.bat   （起動用バッチファイル）
   ```

2. 推奨の配置場所：
   - `C:\Tools\translator-overlay\`
   - `D:\Apps\translator-overlay\`
   - デスクトップのフォルダ など

---

### Step 4: Pythonライブラリのインストール

1. コマンドプロンプトまたはPowerShellを開く
   - Windowsキー + R → `cmd` と入力 → Enter
   - または、スタートメニューで「PowerShell」を検索

2. translator-overlayのフォルダに移動：
   ```
   cd "C:\配置したフォルダのパス"
   ```
   例：
   ```
   cd "C:\Tools\translator-overlay"
   ```

3. 以下のコマンドを実行してライブラリをインストール：
   ```
   pip install -r requirements.txt
   ```

   または個別にインストール：
   ```
   pip install mss Pillow pytesseract deep-translator
   ```

4. 「Successfully installed...」と表示されれば完了です。

---

### Step 5: デスクトップショートカットの作成（任意）

1. `TranslatorOverlay.bat` を右クリック
2. 「ショートカットの作成」を選択
3. 作成されたショートカットをデスクトップに移動
4. 必要に応じて名前を「翻訳オーバーレイ」などに変更

---

## ✅ 起動方法

### 方法1: バッチファイルから起動
`TranslatorOverlay.bat` をダブルクリック

### 方法2: コマンドラインから起動
```
py main.py
```

### 方法3: デスクトップショートカットから起動
作成したショートカットをダブルクリック

---

## 🎮 操作方法

| 操作 | 説明 |
|------|------|
| タイトルバーをドラッグ | ウィンドウを移動 |
| 青い枠をドラッグ | ウィンドウサイズを変更 |
| 右下の⋮⋮をドラッグ | 斜めにサイズ変更 |
| **🔄 翻訳** ボタン / **F5** | 1回翻訳を実行 |
| **自動ON/OFF** ボタン / **F6** | 自動翻訳の切り替え（2秒間隔） |
| **□** ボタン / **F11** | 全画面表示の切り替え |
| **🗑 クリア** ボタン | 翻訳結果をクリア |
| **ESC** キー | アプリを終了 |

---

## 📖 使い方

1. アプリを起動
2. 翻訳したい英語テキスト（Webページ、動画字幕など）の上にウィンドウを移動
3. ウィンドウサイズをテキストに合わせて調整
4. **🔄 翻訳** ボタンを押す（または **F5** キー）
5. 翻訳結果がウィンドウ内に表示されます

---

## ❗ トラブルシューティング

### 「Tesseract OCRが見つかりません」エラー

**原因**: Tesseractがインストールされていない、またはパスが違う

**解決方法**:
1. Tesseractが正しくインストールされているか確認
2. インストール先がデフォルト以外の場合、`main.py` の30行目あたりを編集：
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\インストール先\tesseract.exe'
   ```

---

### 「pip が見つかりません」エラー

**原因**: Pythonのパスが通っていない

**解決方法**:
1. Pythonを再インストールし、「Add Python to PATH」にチェックを入れる
2. または、以下のコマンドを試す：
   ```
   py -m pip install -r requirements.txt
   ```

---

### 翻訳が実行されない

**原因**: インターネットに接続されていない

**解決方法**:
- インターネット接続を確認してください
- 翻訳にはGoogle翻訳へのアクセスが必要です

---

### 文字が認識されない

**原因**: 画像の品質が低い、またはフォントが特殊

**解決方法**:
- ウィンドウサイズを大きくして、テキストがはっきり見えるようにする
- 装飾的なフォントは認識しにくい場合があります
- 白背景に黒文字、または黒背景に白文字が認識しやすいです

---

## 📁 ファイル構成

```
translator-overlay/
├── main.py                 # メインプログラム（編集可）
├── requirements.txt        # 依存ライブラリ一覧
├── TranslatorOverlay.bat   # 起動用バッチファイル
├── SETUP_GUIDE.md          # この手順書
├── 翻訳オーバーレイ.bat    # 起動用バッチファイル（日本語名）
└── create_shortcut.vbs     # ショートカット作成スクリプト
```

---

## 📞 サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください：
- エラーメッセージの内容
- Windowsのバージョン
- Pythonのバージョン（`py --version` の結果）

---

**作成日**: 2025年1月
**バージョン**: 1.0



