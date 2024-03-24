import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import *
import subprocess
import webbrowser
import os
import urllib.request
import ssl
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox

class Launcher:

    # 拡張子.txtのファイル名を取得
    FILE_NAME_LIST=os.listdir("./")
    TEXT_FILE_NAME_LIST=[]
    for i in range(len(FILE_NAME_LIST)):
        if ".txt"==os.path.splitext(FILE_NAME_LIST[i])[1]:
            TEXT_FILE_NAME_LIST.append(FILE_NAME_LIST[i])

    ssl._create_default_https_context = ssl._create_unverified_context

    def main(self):
        global nb
        global root
        # ウィンドウ設定
        root = TkinterDnD.Tk()
        root.title("Launcher")
        root.geometry("325x400")
        root.resizable(width=False, height=False)

        # タブ作成
        nb = ttk.Notebook(root)
        self.create_tab(Launcher.TEXT_FILE_NAME_LIST)

        root.mainloop()

    @classmethod
    def create_tab(cls, file_name_list):
        # タブ作成
        global nb

        # タブのインスタンスを作成
        tab_dict={}
        for file_name in file_name_list: 
            tab = tk.Frame(nb)
            tab_dict[tab]=file_name

            # タブに表示する文字列の作成
            nb.add(tab, text=file_name.replace(".txt",""), padding=2)

        nb.pack(expand=True, fill=tk.BOTH)

        # タブの中身を作成
        for tab, file_path in tab_dict.items():
            # ラベルを作成
            label = cls.create_label(tab)
            label.pack(expand=True, fill=tk.BOTH)

            # ファイル読み込み
            link_dict, not_link_dict = cls.read_file(file_path)

            # ラベルの中にボタン作成
            cls.create_button(label, link_dict, not_link_dict)

    @classmethod
    def create_label(cls, tab):
        # ラベル作成
        global nb

        # labelにスクロールが付けれないため、スクロールを紐づけられるcavasを作成
        canvas = tk.Canvas(tab, width=200, relief=tk.RIDGE, cursor="hand2")
        # スクロールバーの作成
        scrollbar = tk.Scrollbar(canvas, orient=tk.VERTICAL, command=canvas.yview)
        # Canvasのスクロール範囲を設定
        canvas.configure(scrollregion=(0, 0, 300, 1000))
        canvas.configure(yscrollcommand=scrollbar.set)
        # 表示
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(expand=True, fill=tk.BOTH)

        frame=tk.Frame(canvas)
        # Canvas上の座標(0, 0)に対してFrameの左上（nw=north-west）をあてがうように、Frameを埋め込む
        canvas.create_window((0, 0), window=frame, anchor="nw", width=300, height=1000)

        label = ttk.Label(frame, text=nb.tab(tab, "text"), width=200, relief=tk.RIDGE, cursor="hand2")
        label.drop_target_register(DND_FILES)
        # drop_pathメソッドとラベルを紐づけ
        label.dnd_bind("<<Drop>>", cls.drop_path)
        # ラベルとメニューを紐づけ
        cls.link_label_and_menu(label)

        return label

    @classmethod
    def create_button(cls, label, link_dict, not_link_dict):
        # link
        row = 0
        col = 0
        for name, url in link_dict.items():
            # ボタン作成
            cls.create_link_button(label, name, url, row, col)
            if col == 1:
                row += 1
                col = 0
                continue
            col += 1

        # link以外
        for name, path in not_link_dict.items():
            # ボタン作成
            cls.create_not_link_button(label, name, path, row, col)
            if col == 1:
                row += 1
                col = 0
                continue
            col += 1

    @classmethod
    def create_link_button(cls, label, button_name, url, row, col):
        # ボタン作成
        button = tk.Button(label, text=button_name,
                        command=lambda: cls.jump_to_link(url), width=20, relief="raised", fg="#0000ff")
        button.grid(column=col, row=row)

        # ボタンとメニューの紐づけ
        cls.link_button_and_menu(button)

    @classmethod
    def create_not_link_button(cls, label, button_name, path, row, col):
        # ボタン作成
        button = tk.Button(label, text=button_name,
                        command=lambda: cls.open_path(path), width=20, relief="raised")
        button.grid(column=col, row=row)

        # ボタンとメニューの紐づけ
        cls.link_button_and_menu(button)

    @classmethod
    def drop_path(cls, event):
        global nb
        # 入力ダイアログを表示し、ボタン名を取得
        button_name = simpledialog.askstring("Input Box", "ボタン名を入力してください")

        # ドラッグ&ドロップされたパスから先頭と末尾の""を取り除く
        path = event.data[1:]
        path = path[:-1]

        # 選択されたタブを取得
        frame_id = nb.select()
        selected_frame = nb.nametowidget(frame_id)
        canvases = selected_frame.winfo_children()
        frames = canvases[0].winfo_children()
        labels = frames[1].winfo_children()

        # タブの中にあるボタンのmax col,rowを取得
        max_row, max_col = cls.get_max_row_col(labels[0])
        # 新しいボタンのcol,rowを取得
        if max_row is None and max_col is None:
            row = 0
            col = 0
        else:
            row, col = cls.get_next_row_col(max_row, max_col)

        # ボタン作成
        cls.create_not_link_button(labels[0], button_name, path, row, col)

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # 新ボタンをファイルに書き込み
        txt_name = f"{tab_name}.txt"
        cls.append_to_file(txt_name, button_name, path)

    @classmethod
    def get_max_row_col(cls, label):
        max_row = max_col = None

        buttons = label.winfo_children()
        grid_info = [button.grid_info() for button in buttons]
        grid_info.pop(0)

        # そのタブにボタンが一つでもあるか判定
        if grid_info:
            # そのタブで一番最後のボタンを取得
            info = grid_info[-1]

            max_row = info["row"]
            max_col = info["column"]

        return max_row, max_col

    @classmethod
    def get_next_row_col(cls, row, col):
        next_row = row
        next_col = col

        if col == 1:
            next_col = 0
            next_row += 1
        else:
            next_col += 1

        return next_row, next_col

    @classmethod
    def link_button_and_menu(cls, button):
        global pmenu
        pmenu=tk.Menu(button, tearoff=0)
        pmenu.add_command(label="ボタン名変更", command=cls.change_button_name)
        pmenu.add_command(label="ボタン削除", command=cls.delete_button)
        # 右クリックでメニュー表示
        button.bind("<Button-3>", cls.show_button_menu)

    @classmethod
    def show_button_menu(cls, e):
        global select_button
        global pmenu
        select_button=e.widget.cget("text")
        pmenu.post(e.x_root, e.y_root)

    @classmethod
    def change_button_name(cls):
        global nb
        global select_button
        # 入力ダイアログを表示し、新しいボタン名を取得
        new_name = simpledialog.askstring("Input Box", "ボタン名を入力してください")

        # 選択されたタブを取得
        frame_id = nb.select()
        selected_frame = nb.nametowidget(frame_id)
        canvases = selected_frame.winfo_children()
        frames = canvases[0].winfo_children()
        labels = frames[1].winfo_children()
        buttons = labels[0].winfo_children()
        buttons.pop(0)

        # ボタン名更新
        for i, button in enumerate(buttons):
            if button.cget("text") == select_button:
                button.config(text=new_name)

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # ファイル読み込み
        file_path = f"{tab_name}.txt"
        link_dict, not_link_dict = cls.read_file(file_path)

        # リンクを格納した辞書に変更するボタン名があるか判定
        link_path = link_dict.get(select_button, None)
        if link_path is not None:
            link_dict = cls.change_key(link_dict, select_button, new_name)
        else:
            # リンク以外を格納した辞書に変更するボタン名があるか判定
            not_link_path = not_link_dict.get(select_button, None)
            if not_link_path is not None:
                not_link_dict = cls.change_key(not_link_dict, select_button, new_name)

        # ファイル書き込み
        cls.write_file(file_path, link_dict, not_link_dict)

    @classmethod
    def change_key(cls, target_dict, old_key, new_key):
        # key名を変更する
        new_dict = {}
        key_list = []
        value_list = []

        for key, value in target_dict.items():
            key_list.append(key)
            value_list.append(value)

        for i, key in enumerate(key_list):
            if key_list[i] == old_key:
                key_list[i] = new_key
                break

        for i, key in enumerate(key_list):
            new_dict[key] = value_list[i]

        return new_dict

    @classmethod
    def delete_button(cls):
        global nb
        global select_button

        # 選択されたタブを取得
        frame_id = nb.select()
        selected_frame = nb.nametowidget(frame_id)
        canvases = selected_frame.winfo_children()
        frames = canvases[0].winfo_children()
        labels = frames[1].winfo_children()
        buttons = labels[0].winfo_children()
        buttons.pop(0)

        # ボタン削除
        for i, button in enumerate(buttons):
            if button.cget("text") == select_button:
                button.destroy()
                del buttons[i]

        # ボタン再配置
        cls.rearrange_buttons(buttons)

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # ファイル書き込み
        file_path = f"{tab_name}.txt"
        link_dict, not_link_dict = cls.read_file(file_path)
        # ボタン名と一致するものを削除
        for k in link_dict:
            if k == select_button:
                link_dict.pop(k, None)
                break

        for k in not_link_dict:
            if k == select_button:
                not_link_dict.pop(k, None)
                break

        # ファイル書き込み
        cls.write_file(file_path, link_dict, not_link_dict)

    @classmethod
    def rearrange_buttons(cls, buttons):
        row = col = 0

        for button in buttons:
            button.grid(column=col, row=row)
            row, col = cls.get_next_row_col(row, col)

    @classmethod
    def link_label_and_menu(cls, label):
        global label_menu
        label_menu=tk.Menu(label, tearoff=0)
        label_menu.add_command(label="リンク登録", command=cls.show_link_dialog)
        # 右クリックでメニュー表示
        label.bind("<Button-3>", cls.show_label_menu)

    @classmethod
    def show_label_menu(cls, e):
        global label_menu
        label_menu.post(e.x_root, e.y_root)

    @classmethod
    def show_link_dialog(cls):
        # サブウインドウの作成
        global root
        global sub_window
        sub_window = tk.Toplevel(root)
        sub_window.geometry("300x100")

        input_link_name_label = tk.Label(sub_window, text='リンク名：')
        input_link_name_label.place(x=20, y=20)

        input_link_name = tk.Entry(sub_window, width=30)
        input_link_name.place(x=80, y=20)

        input_url_label = tk.Label(sub_window, text='url        ：')
        input_url_label.place(x=20, y=50)

        input_url = tk.Entry(sub_window, width=30)
        input_url.place(x=80, y=50)

        button = tk.Button(sub_window, text='登録', command=lambda: cls.register_link(input_link_name, input_url))
        button.place(x=140, y=70)

    @classmethod
    def register_link(cls, input_link_name, input_url):
        global nb
        global sub_window

        link_name = input_link_name.get()
        url = input_url.get()

        # リンク判定
        is_link = cls.check_url(url)

        if not is_link:
            messagebox.showerror("エラー", "リンクが有効ではありません")

        # 選択されたタブを取得
        frame_id = nb.select()
        selected_frame = nb.nametowidget(frame_id)
        canvases = selected_frame.winfo_children()
        frames = canvases[0].winfo_children()
        labels = frames[1].winfo_children()

        # タブの中にあるボタンのmax col,rowを取得
        max_row, max_col = cls.get_max_row_col(labels[0])
        # 新しいボタンのcol,rowを取得
        if max_row is None and max_col is None:
            row = 0
            col = 0
        else:
            row, col = cls.get_next_row_col(max_row, max_col)

        # ボタン作成
        cls.create_link_button(labels[0], link_name, url, row, col)

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # 新ボタンをファイルに書き込み
        txt_name = f"{tab_name}.txt"
        cls.append_to_file(txt_name, link_name, url)

        # サブウィンドウを閉じる
        sub_window.destroy()

    @classmethod
    def read_file(cls, file_path):
        # ファイル読み込み

        link_dict = {}
        not_link_dict = {}

        f = open(file_path, 'r', encoding='utf-8')
        while True:
            data = f.readline().rstrip('\n')
            if data == '':
                break

            data_list = data.split(',')
            key = data_list[0]
            value = data_list[1]

            # パスがリンクかを判定
            is_link = cls.check_url(value)

            if is_link:
                link_dict[key] = value
            else:
                not_link_dict[key] = value

        return link_dict, not_link_dict

    @classmethod
    def write_file(cls, file_path, link_dict, not_link_dict):
        # ファイル書き込み
        write_list=[]

        for name, url in link_dict.items():
            row = name + ',' + url
            write_list.append(row)

        for name, path in not_link_dict.items():
            row = name + ',' + path
            write_list.append(row)

        file_path = './' + file_path

        with open(file_path, mode='w',encoding='utf-8')as f:
            for data in write_list:
                f.write(data + '\n')

    @classmethod
    def append_to_file(cls, txt_name, name, path):
        # ファイルにボタン情報を追加
        row = name + ',' + path + '\n'
        file_path = './' + txt_name

        with open(file_path, mode='a',encoding='utf-8')as f:
            f.write(row)

    @classmethod
    def check_url(cls, url):
        # urlのリンクが有効か判定
        is_link = True
        try:
            f = urllib.request.urlopen(url)
            f.close()
        except Exception as e:
            is_link = False

        return is_link

    @classmethod
    def jump_to_link(cls, url):
        # リンクを開く
        webbrowser.open(url)

    @classmethod
    def open_path(cls, path):
        # 指定されたパスを開く
        subprocess.Popen(["start", path], shell=True)

if __name__ == "__main__":
    launcher = Launcher()
    launcher.main()
