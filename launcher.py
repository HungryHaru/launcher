import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import *
import subprocess
import webbrowser
import os
import sys
import urllib.request
import ssl
import tkinter.simpledialog as simpledialog

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
        global tab_list

        # タブのインスタンスを作成
        tab_dict={}
        tab_list = []
        for file_name in file_name_list:
            tab = tk.Frame(nb)
            tab_dict[tab]=file_name

            # タブに表示する文字列の作成
            nb.add(tab, text=file_name.replace(".txt",""), padding=2)

            tab_list.append(tab)

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
            name = data_list[0]
            path = data_list[1]

            # パスがリンクかを判定
            is_link = cls.check_url(path)

            if is_link:
                link_dict[name] = path
            else:
                not_link_dict[name] = path

        return link_dict, not_link_dict

    @classmethod
    def check_url(cls, path):
        # パスがリンクかを判定
        is_link = True
        try:
            f = urllib.request.urlopen(path)
            f.close()
        except Exception as e:
            is_link = False

        return is_link

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

        return label

    @classmethod
    def drop_path(cls, event):
        global nb
        global tab_list
        # 入力ダイアログを表示し、ボタン名を取得
        input_data = simpledialog.askstring("Input Box", "ボタン名を入力してください")

        # ドラッグ&ドロップされたパスから先頭と末尾の""を取り除く
        path = event.data[1:]
        path = path[:-1]

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # ファイル読み込み
        file_path = f"{tab_name}.txt"
        link_dict, not_link_dict=cls.read_file(file_path)

        # パスがリンクかを判定
        is_link = cls.check_url(path)

        if is_link:
            link_dict[input_data] = path
        else:
            not_link_dict[input_data] = path

        # ファイル書き込み
        cls.write_file(file_path, link_dict, not_link_dict)

        # 現在のタブ削除
        for tab in tab_list:
            nb.forget(tab)
        # タブから再作成
        cls.create_tab(cls.TEXT_FILE_NAME_LIST)

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
            f.write('\n'.join(write_list))

    @classmethod
    def create_link_button(cls, label, button_name, url, row, col):
        # ボタン作成
        button = tk.Button(label, text=button_name,
                        command=lambda: cls.jump_to_link(url), width=20, relief="raised")
        button.grid(column=col, row=row)

        # ボタンとメニューの紐づけ
        cls.link_button_and_menu(button)

    @classmethod
    def link_button_and_menu(cls, button):
        global pmenu
        pmenu=tk.Menu(button, tearoff=0)
        pmenu.add_command(label="ボタン名変更", command=cls.change_button_name)
        pmenu.add_command(label="ボタン削除", command=cls.delete_button)
        # 右クリックでメニュー表示
        button.bind("<Button-3>", cls.show_menu)

    @classmethod
    def show_menu(cls, e):
        global select_button
        global pmenu
        select_button=e.widget.cget("text")
        pmenu.post(e.x_root, e.y_root)

    @classmethod
    def change_button_name(cls):
        global nb
        global tab_list
        global select_button
        # 入力ダイアログを表示し、新しいボタン名を取得
        input_data = simpledialog.askstring("Input Box", "ボタン名を入力してください")

        # タブ名取得
        tab_name = nb.tab(nb.select(), "text")

        # ファイル読み込み
        file_path = f"{tab_name}.txt"
        link_dict, not_link_dict = cls.read_file(file_path)

        # リンクを格納した辞書に変更するボタン名があるか判定
        link_path = link_dict.get(select_button, None)
        if link_path is not None:
            link_dict = cls.change_key(link_dict, select_button, input_data)
        else:
            # リンク以外を格納した辞書に変更するボタン名があるか判定
            not_link_path = not_link_dict.get(select_button, None)
            if not_link_path is not None:
                not_link_dict = cls.change_key(not_link_dict, select_button, input_data)

        # ファイル書き込み
        cls.write_file(file_path, link_dict, not_link_dict)

        # 現在のタブ削除
        for tab in tab_list:
            nb.forget(tab)
        # タブから再作成
        cls.create_tab(cls.TEXT_FILE_NAME_LIST)

    @classmethod
    def change_key(cls, target_dict, old_key, new_key):
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
        global tab_list

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

        # 現在のタブ削除
        for tab in tab_list:
            nb.forget(tab)
        # タブから再作成
        cls.create_tab(cls.TEXT_FILE_NAME_LIST)

    @classmethod
    def create_not_link_button(cls, label, button_name, path, row, col):
        # ボタン作成
        button = tk.Button(label, text=button_name,
                        command=lambda: cls.open_path(path), width=20, relief="raised")
        button.grid(column=col, row=row)

        # ボタンとメニューの紐づけ
        cls.link_button_and_menu(button)

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
