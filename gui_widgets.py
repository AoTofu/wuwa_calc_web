# gui_widgets.py (Web用にクリーンアップしたバージョン)

import os
from PIL import Image

# ImageHandlerはGUIに依存しない純粋なPythonロジックなので残す。
# ただし、ctk.CTkImageに依存しているため、その部分をPillowのImageオブジェクトを
# そのまま返すように変更する必要があるが、exporters.pyはパスしか使っていないため、
# このクラスは実質的にWebアプリのPythonバックエンドでは現在使用されていない。
# 将来的に画像処理が必要になった場合のために骨格だけ残す。
class ImageHandler:
    _image_cache = {}
    _placeholder = None

    @classmethod
    def get_placeholder(cls, size):
        # Webではこの関数は直接使われない
        pass

    @classmethod
    def get_image(cls, image_key, size=(24, 24)):
        # Webではこの関数は直接使われない
        pass

    @staticmethod
    def select_and_copy(dtype, name):
        # Webではこの関数は直接使われない (ファイル選択はJSが担当)
        pass

#
# --- ここから下のGUI関連クラスはすべて削除 ---
#
# class RotationRow(ctk.CTkFrame): ...
# class EchoInputWidget(ctk.CTkFrame): ...
# class Tooltip: ...
# class AbnormalEffectEditorPopup(Toplevel): ...
#