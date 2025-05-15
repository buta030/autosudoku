import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import simpledialog

# 数字テンプレート画像（0-9）のパス
TEMPLATE_PATHS = {
    '0': 'templates/0.png',
    '1': 'templates/1.png',
    '2': 'templates/2.png',
    '3': 'templates/3.png',
    '4': 'templates/4.png',
    '5': 'templates/5.png',
    '6': 'templates/6.png',
    '7': 'templates/7.png',
    '8': 'templates/8.png',
    '9': 'templates/9.png',
}

# 1. スクリーンショットを撮る
def capture_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save('screenshot.png')
    print("スクリーンショットが保存されました。")

# 2. 正方形のグリッド部分を手動で切り取る
def crop_grid_manually(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print("画像が正しく読み込まれませんでした。パスを確認してください。")
        return None

    # 画像を表示して手動で選択範囲を指定
    r = cv2.selectROI("グリッド選択", image)
    
    # ROI選択がキャンセルされていないかチェック
    if r == (0, 0, 0, 0):
        print("範囲選択がキャンセルされました。")
        return None

    # 正方形のサイズを強制する
    x, y, w, h = r
    size = min(w, h)  # 幅と高さの最小値を選んで正方形にする

    # 正方形の切り取り範囲を調整
    cropped_grid = image[y:y+size, x:x+size]

    # 切り取った画像を保存
    cv2.imwrite('cropped_grid.png', cropped_grid)
    print("グリッド部分が保存されました。")

    # 画像表示を終了
    cv2.destroyWindow("グリッド選択")

    return cropped_grid

# 3. テンプレートマッチングを使用して数字を検出
def extract_numbers(cropped_grid):
    board = np.zeros((9, 9), dtype=int)

    # 数字のテンプレート画像を読み込んで、テンプレートマッチングを行う
    for digit, template_path in TEMPLATE_PATHS.items():
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

        if template is None:
            print(f"テンプレート画像 '{template_path}' が見つかりません。")
            continue

        # グリッドをグレースケールに変換
        gray_grid = cv2.cvtColor(cropped_grid, cv2.COLOR_BGR2GRAY)

        # テンプレートマッチングを使って、画像内で数字を探す
        result = cv2.matchTemplate(gray_grid, template, cv2.TM_CCOEFF_NORMED)

        # 一定の閾値を超えた部分を検出（マッチした位置を抽出）
        threshold = 0.8  # マッチングの精度を調整
        loc = np.where(result >= threshold)

        for pt in zip(*loc[::-1]):  # 位置を逆順にして(横, 縦)に合わせる
            # (pt) は検出されたテンプレート位置
            # 数独ボードにその位置に対応する数字をセット
            row, col = pt[1] // 50, pt[0] // 50  # 50ピクセルごとに分割（グリッドセルサイズによる調整）
            board[row, col] = int(digit)

    return board

# 4. 数独ボードを表示する
def print_board(board):
    for row in board:
        print(row)

# 5. 数独の解法（バックトラッキング法）
def is_valid(board, row, col, num):
    # 行に同じ数字がないか確認
    for i in range(9):
        if board[row][i] == num:
            return False
    
    # 列に同じ数字がないか確認
    for i in range(9):
        if board[i][col] == num:
            return False
    
    # 3x3のブロックに同じ数字がないか確認
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

# tkinterを使ってダイアログで数字を入力
def ask_for_number(row, col):
    # tkinterウィンドウの作成
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示にする

    # ダイアログボックスを表示して数字を入力
    number = simpledialog.askstring("数字入力", f"セル ({row}, {col}) に入力する数字を選んでください（1-9）:")

    if number and number.isdigit() and 1 <= int(number) <= 9:
        return int(number)
    elif number == '':
        return 0  # 空白セルの場合
    else:
        print("無効な入力です。1から9の範囲で入力してください。")
        return None

# 6. 数字ボタンを作成してクリックで修正
def create_number_buttons(image, board):
    def on_mouse_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            row, col = y // 50, x // 50  # セルの位置を計算
            if row < 9 and col < 9:
                number = ask_for_number(row, col)
                if number is not None:
                    board[row][col] = number
                    print(f"ボードが更新されました: ({row}, {col}) = {number}")
            
            # ボードを再描画し、リアルタイムで表示を更新
            draw_board(image, board)
            cv2.imshow("数独ボード", image)

    return on_mouse_click

# 数独ボードを画像に描画する
def draw_board(image, board):
    # 画像の背景を白に設定
    image.fill(255)

    for i in range(9):
        for j in range(9):
            # 各セルに数字を描画
            text = str(board[i][j]) if board[i][j] != 0 else ''
            cv2.putText(image, text, (j * 50 + 15, i * 50 + 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # グリッドを描画
    for i in range(10):
        thickness = 2 if i % 3 == 0 else 1
        cv2.line(image, (i * 50, 0), (i * 50, 450), (0, 0, 0), thickness)
        cv2.line(image, (0, i * 50), (450, i * 50), (0, 0, 0), thickness)

# 実行部分
if __name__ == "__main__":
    capture_screenshot()  # スクリーンショットをキャプチャ
    time.sleep(1)  # 少し待機してから画像を処理

    cropped_grid = crop_grid_manually('screenshot.png')  # 手動でグリッド部分を切り取る

    if cropped_grid is None:
        print("グリッドの切り取りに失敗しました。")
    else:
        # 数字をテンプレートマッチングで検出して数独ボードを作成
        board = extract_numbers(cropped_grid)
        print("検出された数独ボード:")
        print_board(board)

        # ボードの描画
        image = np.ones((450, 450, 3), dtype=np.uint8) * 255  # 白い背景の画像
        draw_board(image, board)

        # 数字ボタンを作成して、修正するためのクリックイベントを追加
        cv2.imshow("数独ボード", image)
        cv2.setMouseCallback("数独ボード", create_number_buttons(image, board))

        # ユーザーがウィンドウを閉じるまで待機
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # 数独を解く
        if solve(board):
            print("\n解いた数独ボード:")
            print_board(board)
        else:
            print("\n解けませんでした。")
