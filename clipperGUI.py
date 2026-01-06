import tkinter as tk
import tkinter.messagebox
import sys
import json
import os
import glob
from yt_dlp import YoutubeDL
from threading import Thread # スレッドをインポート



root = tkinter.Tk()
root.title(u"clips downloder")
root.geometry("400x350")
#1=動画のみ 2=コメントのみ 3=両方
progress_text = tk.StringVar(value="URLを入力して実行してください")
download = tkinter.IntVar()
download.set(1)

tkinter.Radiobutton(root, text="動画のみ", variable=download, value=1).place(x=20,y=30)
tkinter.Radiobutton(root, text="コメントのみ", variable=download, value=2).place(x=20,y=50)
tkinter.Radiobutton(root, text="両方", variable=download, value=3).place(x=20,y=70)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def progress_hook(d):
    if d['status'] == 'downloading':
        # 進捗率を取得して変数に格納
        p = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', '')
        progress_text.set(f"ダウンロード中: {p} ({speed})")
    elif d['status'] == 'finished':
        progress_text.set("ダウンロード完了。変換中...")
        
# --- 2. スレッドで実行する関数 ---
def start_process_thread(event):
    progress_text.set("実行中...")
    # GUIを止めないために別スレッドで実行
    thread = Thread(target=action)
    thread.daemon = True # アプリを閉じたらスレッドも終了するように
    thread.start()
    


#ボタンを押されたとき
def action():
  value = download.get()
  URL = URLBox.get()
  action_button.config(state=tk.DISABLED) #ボタン無効化
  #入力チェック
  if not URL:
    progress_text.set("エラー: URLを入力してください")
    action_button.config(state=tk.NORMAL) #有効化
    return
  
  URLBox.delete(0, tkinter.END)
  progress_text.set("処理を開始します...")
  try :
    if value == 1 :
      gen_video(URL)
    elif value == 2 :
      get_comment(URL)
    elif value == 3 :
      get_comment(URL)
      gen_video(URL)
    #get_comment(URL)
    progress_text.set("すべての処理が完了しました")
  
  except Exception as e:
    # ネットワークエラーやその他のエラーをキャッチ
    print(f"Error detail: {e}") # ログにも詳細を出す
    progress_text.set(f"エラーが発生しました。再試行してください。")
    action_button.config(state=tk.NORMAL) #有効化
        # メッセージボックスで通知しても良い
        # tkinter.messagebox.showerror("エラー", f"ダウンロードに失敗しました:\n{e}")

#window追加
def setting_window(event):
  window2 = tkinter.Toplevel(root)
  window2.grab_set()
  window2.title("設定画面")
  window2.geometry("400x100")
  window2.focus_set()
  #enterbox追加
  #enterbox更新時の動作

#コンバート
def convert(json_file_path, base_title):
  
  # base_titleはここでは動画ID（%(id)s）を使用します
  output_file_path = base_title + '_chatdata.txt'
  
  chat_lines = []
  
  try:
    # JSONファイルの読み込み（ストリームされたJSONオブジェクトに対応）
    with open(json_file_path, 'r', encoding='utf-8') as f:
      for line in f:
        line = line.strip()
        if line:
          try:
            chat_lines.append(json.loads(line))
          except json.JSONDecodeError:
            continue
  except Exception as e:
    print(f"エラー: 一時ファイルの読み込みに失敗しました: {e}")
    return 0
      
  
  output_data = []
  # ヘッダー行
  header = "Elapsed_Time\tType\tAuthor\tMessage\tAmount_String\tCurrency\tAmount_Value\tColor_Code\n"
  output_data.append(header)

  # データ抽出と整形
  for item in chat_lines:
    actions = item.get('replayChatItemAction', {}).get('actions', [])
    for action in actions:
      if 'addChatItemAction' in action:
        chat_item = action['addChatItemAction']['item']
        renderer_key = next(iter(chat_item.keys()), None)
        renderer = chat_item.get(renderer_key, {})

        # 各項目を初期化
        elapsed_time = renderer.get('videoOffsetTimeText', {}).get('simpleText', '')
        author_name = renderer.get('authorName', {}).get('simpleText', '')
        message = ''
        amount_string = ''
        currency = ''
        amount_value = ''
        color_code = ''
        chat_type = 'TextMessage'

        # メッセージ内容の抽出
        runs = renderer.get('message', {}).get('runs', [])
        message = ''.join(run.get('text', '') for run in runs)
        
        if 'liveChatTextMessageRenderer' in chat_item:
          chat_type = 'TextMessage'
        elif 'liveChatPaidMessageRenderer' in chat_item:
          chat_type = 'SuperChat'
          amount_string = renderer.get('purchaseAmountText', {}).get('simpleText', '')
          color = renderer.get('bodyBackgroundColor', 0)
          color_code = f"#{color:06X}" if color else ''
        elif 'liveChatPaidStickerRenderer' in chat_item:
          chat_type = 'SuperSticker'
          amount_string = renderer.get('purchaseAmountText', {}).get('simpleText', '')
          color = renderer.get('backgroundColor', 0)
          color_code = f"#{color:06X}" if color else ''

        # タブ区切り形式に整形（改行などはスペースに置換）
        cleaned_message = message.replace('\n', ' ').replace('\t', ' ')
        
        line = (
            f"{elapsed_time}\t{chat_type}\t{author_name}\t{cleaned_message}\t"
            f"{amount_string}\t{currency}\t{amount_value}\t{color_code}\n"
        )
        output_data.append(line)

  # ファイル出力
  try:
    with open(output_file_path, 'w', encoding='utf-8') as f:
      f.writelines(output_data)
    return len(output_data) - 1
  except IOError as e:
    print(f"エラー: ファイルの書き込みに失敗しました: {e}")
    return 0

#ダウンロード-コメント
def get_comment(URL) :
  ydl_opts = {
    'skip_download': True,
    'outtmpl': {'default': '%(id)s_.mp4'}, # 投稿日_タイトル_動画ID.mp4   %(upload_date)s_%(title)s_
    'format': 'best',
    'writesubtitles': True, #字幕の書き込み
    'progress_hooks': [progress_hook], #これ追加
    'ffmpeg_location': resource_path('ffmpeg.exe'), #ffmpegの場所を入れる
        
    # チャットデータ取得に必要なオプション
    'writeinfojson': True,
    'writeinfojson_comment': True,     
        
    # その他の安全オプション
    'windowsfilenames': True,          
    'quiet': True,                     
    'ignoreerrors': True,
    'no_warnings': True
  }
   
   #動画情報とチャットデータの一時取得を開始
  # 変数を初期化
  temp_json_path = None
  info_dict = None
  video_id = None # 動画IDを保持する変数
  try:
    with YoutubeDL(ydl_opts) as ydl:
      # 情報を取得してJSONを書き出す
      info_dict = ydl.extract_info(URL, download=True)
            
      # 動画IDを取得し、後片付けのキーとする
      video_id = info_dict.get('id')
      if not video_id:
        raise Exception("動画IDの取得に失敗しました。")
            
      # yt-dlpが出力するファイル名のベースを取得 (例: "3qNu0OjZ1pA_.mp4")
      filename_base = ydl.prepare_filename(info_dict)
            
      # チャットファイル名候補（添付ファイル名も考慮）
      possible_names = [
        f"{filename_base}.live_chat.json",
        f"{filename_base}.comments.json",
        f"{video_id}_.live_chat.json", # 添付ファイル名パターン
        ]
            
      # 実際に作成されたファイルを探す
      for name in possible_names:
        if os.path.exists(name):
          temp_json_path = name
          break
            
      if temp_json_path and os.path.exists(temp_json_path):
          # データ処理を実行
        count = convert(temp_json_path, video_id)
        if count > 0:
          print(f"\n 処理完了: {count} 件のチャットデータを保存しました。")
          print(f"出力ファイル: {video_id}_chatdata.txt")
        else:
          print("\n チャットデータが見つからなかったか、0件でした。")
      else:
        print("\n チャットファイルが生成されませんでした。アーカイブが存在しない可能性があります。")

  except Exception as e:
    print(f"\n 処理中にエラーが発生しました: {e}")
    
  finally:
    #ボタンを有効化
    action_button.config(state=tk.NORMAL)
    # 後片付け処理: 動画IDに関連する全ての一時ファイルを削除（最重要）
    if video_id:
      # 動画IDで始まる全てのファイルを検索 (例: 3qNu0OjZ1pA_*)
      # globを使用してワイルドカード検索を行います
      search_pattern = f"{video_id}_*"
      files_to_delete = glob.glob(search_pattern)
            
      if files_to_delete:
        print(f"\n 一時ファイルの後片付け中...")
            
      for file_path in files_to_delete:
          # ユーザーの出力ファイル（3qNu0OjZ1pA_chatdata.txt）を誤って削除しないように除外
          if not file_path.endswith('_chatdata.txt'):
            if os.path.exists(file_path):
              try:
                os.remove(file_path)
                # print(f"（削除: {file_path}）") # デバッグ用
              except Exception as e:
                print(f"警告: ファイル '{file_path}' の削除に失敗しました: {e}")
            
      print("後片付け完了。")
    else:
      print(  "後片付け処理: 動画IDが特定できなかったため、一時ファイルの削除はスキップされました。")
#ダウンロード　動画
def gen_video(URL) :
  ydl_opts = {
    'outtmpl': {'default': '%(upload_date)s_%(title)s_%(id)s_.mp4'}, # 投稿日_タイトル_動画ID.mp4   %(upload_date)s_%(title)s_
    'format': 'best',
    'writesubtitles': True, #字幕の書き込み
    'progress_hooks': [progress_hook], #これ追加
    'ffmpeg_location': resource_path('ffmpeg.exe'), #ffmpegの場所を入れる
  }
  with YoutubeDL(ydl_opts) as ydl:
    ydl.download([URL])

#入力欄追加
URLBox = tkinter.Entry(width=50)
URLBox.place(x=20,y=11)

# 進捗表示ラベル
progress_label = tk.Label(root, textvariable=progress_text, fg="blue")
progress_label.place(x=20, y=200)

#ボタン追加
action_button = tkinter.Button(text=u'実行')
action_button.bind("<Button-1>",start_process_thread)
action_button.place(x=335,y=8)

#設定用
setting_button = tkinter.Button(text=u'⚙')
setting_button.bind("<Button-1>",setting_window)
setting_button.place(x=335,y=250)
root.mainloop()